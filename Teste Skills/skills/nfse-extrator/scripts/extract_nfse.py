#!/usr/bin/env python3
"""
Extrai dados estruturados de XMLs de NFS-e no modelo do Ambiente Nacional
(namespace http://www.sped.fazenda.gov.br/nfse, leiaute NFS-e Nacional v1.01).

Uso:
    python extract_nfse.py --input <arquivo.xml ou pasta> --output <saida.json>

A pasta apontada por --input é varrida recursivamente por *.xml. Ela deve
conter tanto os XMLs de NFS-e recebidas/emitidas (pasta "Recebidas" ou
"Emitidas", tipicamente) quanto, se existir, a pasta "Eventos" -- os eventos
de cancelamento são documentos `<evento>` à parte, e são a ÚNICA forma de
saber se uma nota foi cancelada (ver função `build_situacao_map`). Se
--input apontar só para a pasta de notas sem a pasta de eventos irmã,
cancelamentos não serão detectados e todas as notas sairão como "Ativa".
"""
import argparse
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

NS = "{http://www.sped.fazenda.gov.br/nfse}"

# Tabela oficial de cStat (Manual de Integração NFS-e Nacional v1.01,
# domínio TStat) -- NÃO é status de cancelamento, é o tipo de emissão da
# NFS-e. Cancelamento só existe como evento separado (ver EVENTOS_*).
CSTAT_DESCRICOES = {
    "100": "NFS-e Gerada",
    "101": "NFS-e de Substituição Gerada",
    "102": "NFS-e de Decisão Judicial",
    "103": "NFS-e Avulsa",
    "107": "NFS-e MEI",
}

OPSIMPNAC_DESCRICOES = {
    "1": "Não Optante",
    "2": "Optante - Microempreendedor Individual (MEI)",
    "3": "Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP)",
}

REGESPTRIB_DESCRICOES = {
    "0": "Nenhum",
    "1": "Ato Cooperado (Cooperativa)",
    "2": "Estimativa",
    "3": "Microempresa Municipal",
    "4": "Notário ou Registrador",
    "5": "Profissional Autônomo",
    "6": "Sociedade de Profissionais",
}

TPRETISSQN_DESCRICOES = {
    "1": "Não Retido",
    "2": "Retido pelo Tomador",
    "3": "Retido pelo Intermediário",
}

TRIBISSQN_DESCRICOES = {
    "1": "Operação tributável",
    "2": "Imunidade",
    "3": "Exportação de serviço",
    "4": "Não Incidência",
}

# Código do evento = nome do elemento wrapper dentro de infPedReg (ex.:
# <e101101> para o evento "Cancelamento de NFS-e", <e105102> para
# "Cancelamento de NFS-e por Substituição"). Só esses tipos finalizam a
# situação da nota; "confirmação", "rejeição" e "solicitação de análise
# fiscal" sozinhos não cancelam nada.
EVENTOS_CANCELAMENTO = {"101101", "105104"}  # cancelamento direto / deferido por análise fiscal
EVENTOS_SUBSTITUICAO = {"105102"}  # cancelamento por substituição


def qn(tag):
    return f"{NS}{tag}"


def find(el, *tags):
    cur = el
    for t in tags:
        if cur is None:
            return None
        cur = cur.find(qn(t))
    return cur


def gtext(el, *tags):
    node = find(el, *tags)
    if node is None or node.text is None:
        return None
    v = node.text.strip()
    return v if v else None


def gfloat(el, *tags):
    v = gtext(el, *tags)
    if v is None:
        return None
    try:
        return round(float(v), 2)
    except ValueError:
        return None


def local_name(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def chave_from_id(id_attr):
    """'NFS4205...' -> '4205...' (mesmo formato numérico usado em chNFSe/chSubstda)."""
    if not id_attr:
        return None
    for prefix in ("NFS", "DPS", "EVT", "PRE"):
        if id_attr.startswith(prefix):
            return id_attr[len(prefix):]
    return id_attr


def find_xmls(input_path: Path):
    if input_path.is_file():
        return [input_path]
    return sorted(input_path.rglob("*.xml"))


def parse_evento(xml_path: Path):
    """Extrai (chave_da_nfse_afetada, codigo_do_evento) de um XML de evento."""
    root = ET.parse(xml_path).getroot()
    if root.tag != qn("evento"):
        return None
    inf_ped_reg = find(root, "infEvento", "pedRegEvento", "infPedReg")
    if inf_ped_reg is None:
        return None
    chave = gtext(inf_ped_reg, "chNFSe")
    if not chave:
        return None
    codigo = None
    for child in inf_ped_reg:
        name = local_name(child.tag)
        if name.startswith("e") and len(name) == 7 and name[1:].isdigit():
            codigo = name[1:]
            break
    return chave, codigo


def build_situacao_map(xml_paths):
    """Cruza eventos de cancelamento/substituição com a chave da NFS-e.

    A NFS-e cancelada NÃO é reemitida com outro cStat -- o documento
    original continua com cStat=100 para sempre. A única forma de saber que
    ela foi cancelada é achar o evento <evento> correspondente (pasta
    "Eventos"), casando pela chave de acesso. Por isso é essencial que
    --input inclua essa pasta quando existir.
    """
    canceladas, substituidas = set(), set()
    for path in xml_paths:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if root.tag != qn("evento"):
            continue
        try:
            parsed = parse_evento(path)
        except ET.ParseError:
            continue
        if not parsed:
            continue
        chave, codigo = parsed
        if codigo in EVENTOS_CANCELAMENTO:
            canceladas.add(chave)
        elif codigo in EVENTOS_SUBSTITUICAO:
            substituidas.add(chave)
    situacoes = {chave: "Substituída" for chave in substituidas}
    situacoes.update({chave: "Cancelada" for chave in canceladas})  # cancelamento tem prioridade
    return situacoes


def add_chsubstda_substituicoes(xml_paths, situacoes):
    """Segundo sinal de substituição: a NFS-e substituta declara, ela mesma,
    a chave da nota que substituiu (DPS/infDPS/subst/chSubstda). Isso
    funciona mesmo sem a pasta "Eventos" no escopo, então complementa (não
    substitui) o cruzamento feito em build_situacao_map.
    """
    for path in xml_paths:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if root.tag != qn("NFSe"):
            continue
        subst = find(root, "infNFSe", "DPS", "infDPS", "subst")
        chave_substituida = gtext(subst, "chSubstda") if subst is not None else None
        if chave_substituida and chave_substituida not in situacoes:
            situacoes[chave_substituida] = "Substituída"


def extract_nfse(xml_path: Path):
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as e:
        raise ValueError(f"XML mal formado: {e}")

    if root.tag != qn("NFSe"):
        raise ValueError(
            "não parece ser um XML de NFS-e do modelo nacional (Ambiente "
            "Nacional) -- raiz/namespace não reconhecidos. Se for um XML de "
            "evento (cancelamento), isso é esperado: ele não vira nota no "
            "JSON, só é usado para marcar a situação da nota original."
        )

    inf_nfse = find(root, "infNFSe")
    if inf_nfse is None:
        raise ValueError("XML de NFS-e sem elemento infNFSe")

    inf_dps = find(inf_nfse, "DPS", "infDPS")
    prest = find(inf_dps, "prest") if inf_dps is not None else None
    toma = find(inf_dps, "toma") if inf_dps is not None else None
    interm = find(inf_dps, "interm") if inf_dps is not None else None
    serv = find(inf_dps, "serv") if inf_dps is not None else None
    c_serv = find(serv, "cServ") if serv is not None else None
    info_compl = find(serv, "infoCompl") if serv is not None else None
    valores_dps = find(inf_dps, "valores") if inf_dps is not None else None
    trib = find(valores_dps, "trib") if valores_dps is not None else None
    trib_mun = find(trib, "tribMun") if trib is not None else None
    trib_fed = find(trib, "tribFed") if trib is not None else None
    piscofins = find(trib_fed, "piscofins") if trib_fed is not None else None
    tot_trib = find(trib, "totTrib", "vTotTrib") if trib is not None else None

    emit = find(inf_nfse, "emit")
    ender_nac = find(emit, "enderNac") if emit is not None else None
    valores_top = find(inf_nfse, "valores")
    tot_cibs = find(inf_nfse, "totCIBS")

    cstat = gtext(inf_nfse, "cStat")
    chave_id = inf_nfse.get("Id")
    chave = chave_from_id(chave_id)

    reg_trib = find(prest, "regTrib") if prest is not None else None
    op_simp_nac = gtext(reg_trib, "opSimpNac") if reg_trib is not None else None
    reg_esp_trib = gtext(reg_trib, "regEspTrib") if reg_trib is not None else None

    tp_ret_issqn = gtext(trib_mun, "tpRetISSQN") if trib_mun is not None else None
    trib_issqn = gtext(trib_mun, "tribISSQN") if trib_mun is not None else None

    v_total_ret = gfloat(valores_top, "vTotalRet") if valores_top is not None else None
    irrf = gfloat(trib_fed, "vRetIRRF") if trib_fed is not None else None
    inss_retido = gfloat(trib_fed, "vRetCP") if trib_fed is not None else None
    v_issqn_top = gfloat(valores_top, "vISSQN") if valores_top is not None else None
    issqn_retido_valor = v_issqn_top if tp_ret_issqn in ("2", "3") else None

    # Contribuições sociais retidas (PIS+COFINS+CSLL combinados, o mesmo
    # valor único que o DANFSe mostra em "Contribuições Sociais - Retidas").
    # Deriva-se por SUBTRAÇÃO do total já validado pelo Ambiente Nacional
    # (vTotalRet), em vez de somar vPis+vCofins+vRetCSLL diretamente: em
    # XMLs reais, diferentes emissores preenchem esses três campos de forma
    # inconsistente (alguns colocam o valor já combinado em vRetCSLL,
    # duplicando o que já está em vPis/vCofins). vTotalRet é o valor que o
    # Ambiente Nacional efetivamente valida, então subtrair dele IRRF+INSS+
    # ISSQN retido é o jeito confiável de isolar a parcela de contribuições
    # sociais sem contar nada em dobro.
    contrib_sociais_retidas = None
    if v_total_ret is not None:
        residual = round(v_total_ret - (irrf or 0) - (inss_retido or 0) - (issqn_retido_valor or 0), 2)
        if residual > 0.005:
            contrib_sociais_retidas = residual

    tp_ret_pis_cofins = gtext(piscofins, "tpRetPisCofins") if piscofins is not None else None
    v_pis = gfloat(piscofins, "vPis") if piscofins is not None else None
    v_cofins = gfloat(piscofins, "vCofins") if piscofins is not None else None
    v_ret_csll = gfloat(trib_fed, "vRetCSLL") if trib_fed is not None else None
    desc_partes = []
    if tp_ret_pis_cofins == "1":
        if v_pis:
            desc_partes.append(f"PIS: R$ {v_pis:.2f}")
        if v_cofins:
            desc_partes.append(f"COFINS: R$ {v_cofins:.2f}")
    if v_ret_csll:
        desc_partes.append(f"CSLL (campo vRetCSLL do XML): R$ {v_ret_csll:.2f}")
    descricao_contrib_sociais_retidas = "; ".join(desc_partes) if desc_partes else None

    endereco_prestador = None
    if ender_nac is not None:
        partes = [gtext(ender_nac, "xLgr"), gtext(ender_nac, "nro"), gtext(ender_nac, "xBairro")]
        endereco_prestador = ", ".join(p for p in partes if p) or None

    tomador = None
    if toma is not None:
        end = find(toma, "end")
        end_nac = find(end, "endNac") if end is not None else None
        partes = [gtext(end, "xLgr"), gtext(end, "nro"), gtext(end, "xCpl"), gtext(end, "xBairro")]
        tomador = {
            "cnpj_cpf": gtext(toma, "CNPJ") or gtext(toma, "CPF"),
            "inscricao_municipal": gtext(toma, "IM"),
            "telefone": gtext(toma, "fone"),
            "nome": gtext(toma, "xNome"),
            "email": gtext(toma, "email"),
            "endereco": ", ".join(p for p in partes if p) or None,
            "municipio_ibge": gtext(end_nac, "cMun") if end_nac is not None else None,
            "cep": gtext(end_nac, "CEP") if end_nac is not None else None,
        }

    intermediario = None
    if interm is not None:
        intermediario = {
            "cnpj_cpf": gtext(interm, "CNPJ") or gtext(interm, "CPF"),
            "nome": gtext(interm, "xNome"),
        }

    return {
        "arquivo": xml_path.name,
        "arquivo_caminho": str(xml_path.resolve()),
        "versao_leiaute": root.get("versao"),
        "tipo_emissao_nfse": CSTAT_DESCRICOES.get(cstat, cstat),
        "situacao": None,  # preenchido em main(), cruzando com os eventos
        "chave_acesso": chave_id,
        "_chave_numerica": chave,  # uso interno p/ cruzar com eventos; removido antes de salvar
        "numero_nfse": gtext(inf_nfse, "nNFSe"),
        "competencia": gtext(inf_dps, "dCompet") if inf_dps is not None else None,
        "data_hora_emissao_nfse": gtext(inf_nfse, "dhProc"),
        "numero_dps": gtext(inf_dps, "nDPS") if inf_dps is not None else None,
        "serie_dps": gtext(inf_dps, "serie") if inf_dps is not None else None,
        "data_hora_emissao_dps": gtext(inf_dps, "dhEmi") if inf_dps is not None else None,
        "prestador": {
            "cnpj_cpf": (gtext(prest, "CNPJ") or gtext(prest, "CPF")) if prest is not None
                        else ((gtext(emit, "CNPJ") or gtext(emit, "CPF")) if emit is not None else None),
            "inscricao_municipal": gtext(emit, "IM") if emit is not None else None,
            "telefone": (gtext(prest, "fone") if prest is not None else None)
                        or (gtext(emit, "fone") if emit is not None else None),
            "nome": gtext(emit, "xNome") if emit is not None else None,
            "email": (gtext(prest, "email") if prest is not None else None)
                     or (gtext(emit, "email") if emit is not None else None),
            "endereco": endereco_prestador,
            "municipio": gtext(inf_nfse, "xLocEmi"),
            "cep": gtext(ender_nac, "CEP") if ender_nac is not None else None,
            "simples_nacional": OPSIMPNAC_DESCRICOES.get(op_simp_nac, op_simp_nac),
            "regime_especial_tributacao": REGESPTRIB_DESCRICOES.get(reg_esp_trib, reg_esp_trib),
        },
        "tomador": tomador,
        "intermediario": intermediario,
        "servico": {
            "codigo_tributacao_nacional": gtext(c_serv, "cTribNac") if c_serv is not None else None,
            "codigo_tributacao_municipal": gtext(c_serv, "cTribMun") if c_serv is not None else None,
            "codigo_nbs": gtext(c_serv, "cNBS") if c_serv is not None else None,
            "local_prestacao": gtext(inf_nfse, "xLocPrestacao"),
            "descricao": gtext(c_serv, "xDescServ") if c_serv is not None else None,
        },
        "tributacao_municipal": {
            "tributacao_issqn": TRIBISSQN_DESCRICOES.get(trib_issqn, trib_issqn),
            "municipio_incidencia_issqn": gtext(inf_nfse, "xLocIncid") or gtext(inf_nfse, "cLocIncid"),
            "retencao_issqn": TPRETISSQN_DESCRICOES.get(tp_ret_issqn, tp_ret_issqn),
            "bc_issqn": gfloat(valores_top, "vBC") if valores_top is not None else None,
            "aliquota_issqn": gtext(valores_top, "pAliqAplic") if valores_top is not None else None,
            "issqn_apurado": v_issqn_top,
        },
        "tributacao_federal": {
            "irrf": irrf,
            "inss_retido": inss_retido,
            "contrib_sociais_retidas": contrib_sociais_retidas,
            "descricao_contrib_sociais_retidas": descricao_contrib_sociais_retidas,
        },
        "tributacao_ibs_cbs": {
            "ibs_total_apurado": gfloat(tot_cibs, "gIBS", "vIBSTot") if tot_cibs is not None else None,
            "cbs_total_apurado": gfloat(tot_cibs, "gCBS", "vCBS") if tot_cibs is not None else None,
        },
        "valor_total": {
            "valor_servico": gfloat(valores_dps, "vServPrest", "vServ") if valores_dps is not None else None,
            "desconto_condicionado": gfloat(valores_dps, "vDescCondIncond", "vDescCond") if valores_dps is not None else None,
            "desconto_incondicionado": gfloat(valores_dps, "vDescCondIncond", "vDescIncond") if valores_dps is not None else None,
            "issqn_retido": issqn_retido_valor,
            "total_retencoes": v_total_ret,
            "valor_liquido": gfloat(valores_top, "vLiq") if valores_top is not None else None,
        },
        "totais_aproximados": {
            "federais": gfloat(tot_trib, "vTotTribFed") if tot_trib is not None else None,
            "estaduais": gfloat(tot_trib, "vTotTribEst") if tot_trib is not None else None,
            "municipais": gfloat(tot_trib, "vTotTribMun") if tot_trib is not None else None,
        },
        "informacoes_complementares": gtext(info_compl, "xInfComp") if info_compl is not None else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Extrai dados de NFS-e (XML - modelo nacional / Ambiente Nacional)")
    parser.add_argument("--input", required=True, help="Arquivo XML ou pasta com XMLs (varre recursivamente)")
    parser.add_argument("--output", required=True, help="Caminho do JSON de saída")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERRO: caminho não encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    all_xmls = find_xmls(input_path)
    if not all_xmls:
        print(f"ERRO: nenhum XML encontrado em: {input_path}", file=sys.stderr)
        sys.exit(1)

    situacoes = build_situacao_map(all_xmls)
    n_eventos_cancelamento = len(situacoes)

    records, erros = [], []
    for xml_path in all_xmls:
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError as e:
            erros.append({"arquivo": xml_path.name, "erro": f"XML mal formado: {e}"})
            continue
        if root.tag == qn("evento"):
            continue  # eventos não viram registro; só alimentam `situacoes`
        try:
            records.append(extract_nfse(xml_path))
        except ValueError as e:
            erros.append({"arquivo": xml_path.name, "erro": str(e)})

    add_chsubstda_substituicoes(all_xmls, situacoes)

    for record in records:
        record["situacao"] = situacoes.get(record.pop("_chave_numerica"), "Ativa")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    n_canceladas = sum(1 for r in records if r["situacao"] == "Cancelada")
    n_substituidas = sum(1 for r in records if r["situacao"] == "Substituída")
    print(f"Processados: {len(records)} nota(s) de {len(all_xmls)} XML(s)")
    print(f"Eventos de cancelamento/substituição casados com notas do lote: {n_eventos_cancelamento}")
    if n_canceladas or n_substituidas:
        print(f"  -> {n_canceladas} nota(s) Cancelada(s), {n_substituidas} Substituída(s)")
    if erros:
        print(f"Falhas: {len(erros)}")
        for e in erros:
            print(f"  - {e['arquivo']}: {e['erro']}")
    print(f"JSON salvo em: {output_path.resolve()}")


if __name__ == "__main__":
    main()
