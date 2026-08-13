#!/usr/bin/env python3
"""
Varre uma pasta de XMLs de NFS-e do Ambiente Nacional (namespace
http://www.sped.fazenda.gov.br/nfse) e:

1. Lista todos os XMLs de evento (<evento>) encontrados, classificando cada
   um pelo código do elemento wrapper (ex.: <e101101> = "Cancelamento de
   NFS-e").
2. Cruza esses eventos com as notas (<NFSe>) do mesmo lote pela chave de
   acesso, determinando a situação de cada nota: Ativa, Cancelada ou
   Substituída.

Uso:
    python identificar_eventos.py --input <pasta> --output <saida.json>

A pasta apontada por --input deve conter tanto as notas (pastas
"Recebidas"/"Emitidas", tipicamente) quanto a pasta "Eventos" irmã -- é a
ÚNICA forma de saber se uma nota foi cancelada, pois o XML da nota
cancelada nunca muda (nunca é reemitido com outro status).
"""
import argparse
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

NS = "{http://www.sped.fazenda.gov.br/nfse}"

# Código do evento = nome do elemento wrapper dentro de infPedReg (ex.:
# <e101101> para "Cancelamento de NFS-e"). Só os dois grupos abaixo mudam a
# situação de uma nota; qualquer outro código é listado como "outro evento"
# (informativo), sem efeito sobre a situação.
EVENTOS_CANCELAMENTO = {
    "101101": "Cancelamento de NFS-e",
    "105104": "Cancelamento Deferido por Análise Fiscal",
}
EVENTOS_SUBSTITUICAO = {
    "105102": "Cancelamento de NFS-e por Substituição",
}


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


def descricao_evento(codigo):
    if codigo in EVENTOS_CANCELAMENTO:
        return EVENTOS_CANCELAMENTO[codigo], "Cancelamento"
    if codigo in EVENTOS_SUBSTITUICAO:
        return EVENTOS_SUBSTITUICAO[codigo], "Substituição"
    return f"Evento e{codigo} (sem efeito de cancelamento/substituição)", "Outro"


def parse_evento(xml_path: Path):
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
    dh_evento = gtext(inf_ped_reg, "dhEvento") or gtext(root, "infEvento", "dhProc")
    return chave, codigo, dh_evento


def find_xmls(input_path: Path):
    if input_path.is_file():
        return [input_path]
    return sorted(input_path.rglob("*.xml"))


def main():
    parser = argparse.ArgumentParser(
        description="Identifica eventos e a situação (Ativa/Cancelada/Substituída) de XMLs de NFS-e Nacional"
    )
    parser.add_argument("--input", required=True, help="Pasta com os XMLs de notas e eventos (varre recursivamente)")
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

    eventos = []
    eventos_por_chave = {}  # chave -> lista de (codigo, tipo, arquivo)
    erros = []

    for path in all_xmls:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as e:
            erros.append({"arquivo": path.name, "erro": f"XML mal formado: {e}"})
            continue
        if root.tag != qn("evento"):
            continue
        try:
            parsed = parse_evento(path)
        except ET.ParseError as e:
            erros.append({"arquivo": path.name, "erro": f"XML mal formado: {e}"})
            continue
        if not parsed:
            continue
        chave, codigo, dh_evento = parsed
        descricao, tipo = descricao_evento(codigo)
        eventos.append({
            "arquivo": path.name,
            "arquivo_caminho": str(path.resolve()),
            "codigo_evento": codigo,
            "descricao_evento": descricao,
            "tipo": tipo,
            "chave_nfse_afetada": chave,
            "data_hora_evento": dh_evento,
        })
        eventos_por_chave.setdefault(chave, []).append((codigo, tipo, path.name))

    # Situação final por chave: cancelamento tem prioridade sobre substituição
    # quando os dois aparecem para a mesma chave (nunca deveria acontecer, mas
    # por segurança).
    situacao_map = {}
    evento_responsavel = {}
    for chave, ocorrencias in eventos_por_chave.items():
        for codigo, tipo, arquivo in ocorrencias:
            if tipo == "Substituição" and situacao_map.get(chave) != "Cancelada":
                situacao_map[chave] = "Substituída"
                evento_responsavel[chave] = arquivo
            elif tipo == "Cancelamento":
                situacao_map[chave] = "Cancelada"
                evento_responsavel[chave] = arquivo

    notas = []
    for path in all_xmls:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if root.tag != qn("NFSe"):
            continue
        inf_nfse = find(root, "infNFSe")
        if inf_nfse is None:
            erros.append({"arquivo": path.name, "erro": "XML de NFS-e sem elemento infNFSe"})
            continue
        chave_id = inf_nfse.get("Id")
        chave = chave_from_id(chave_id)
        numero_nfse = gtext(inf_nfse, "nNFSe")

        # Segundo sinal de substituição: a nota substituta declara, ela
        # mesma, a chave da nota que substituiu (DPS/infDPS/subst/chSubstda).
        # Funciona mesmo sem a pasta "Eventos" no escopo.
        subst = find(inf_nfse, "DPS", "infDPS", "subst")
        chave_substituida = gtext(subst, "chSubstda") if subst is not None else None
        if chave_substituida and chave_substituida not in situacao_map:
            situacao_map[chave_substituida] = "Substituída"
            evento_responsavel[chave_substituida] = f"(declarado pela nota substituta {path.name}, sem evento próprio)"

        notas.append({
            "arquivo": path.name,
            "arquivo_caminho": str(path.resolve()),
            "chave_acesso": chave_id,
            "_chave_numerica": chave,
            "numero_nfse": numero_nfse,
        })

    for nota in notas:
        chave = nota.pop("_chave_numerica")
        situacao = situacao_map.get(chave, "Ativa")
        nota["situacao"] = situacao
        nota["evento_responsavel"] = evento_responsavel.get(chave) if situacao != "Ativa" else None

    output = {"notas": notas, "eventos": eventos}
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    n_canceladas = sum(1 for n in notas if n["situacao"] == "Cancelada")
    n_substituidas = sum(1 for n in notas if n["situacao"] == "Substituída")
    n_ativas = len(notas) - n_canceladas - n_substituidas

    print(f"XMLs de nota processados: {len(notas)}")
    print(f"XMLs de evento encontrados: {len(eventos)}")
    if eventos:
        por_tipo = {}
        for e in eventos:
            por_tipo[e["tipo"]] = por_tipo.get(e["tipo"], 0) + 1
        for tipo, qtd in sorted(por_tipo.items()):
            print(f"  - {tipo}: {qtd}")
    print(f"Situação das notas: {n_ativas} Ativa(s), {n_canceladas} Cancelada(s), {n_substituidas} Substituída(s)")
    if n_canceladas or n_substituidas:
        print("Notas Canceladas/Substituídas:")
        for n in notas:
            if n["situacao"] != "Ativa":
                print(f"  - {n['arquivo']} ({n['situacao']}) -> evento: {n['evento_responsavel']}")
    if erros:
        print(f"Falhas: {len(erros)}")
        for e in erros:
            print(f"  - {e['arquivo']}: {e['erro']}")
    print(f"JSON salvo em: {output_path.resolve()}")


if __name__ == "__main__":
    main()
