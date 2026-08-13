---
name: nfse-extrator
description: Extrai dados estruturados de XMLs de Nota Fiscal de Serviço Eletrônica (NFS-e) no modelo do Ambiente Nacional (namespace sped.fazenda.gov.br/nfse, leiaute NFS-e Nacional) — número da nota, prestador, tomador, valores e, principalmente, todos os campos de tributos retidos (IRRF, INSS/Contribuição Previdenciária Retida, Contribuições Sociais Retidas PIS/COFINS/CSLL, ISSQN Retido). Use sempre que o usuário pedir para ler, importar, extrair ou processar XMLs de "nota fiscal de serviço", "NFS-e" do modelo/ambiente nacional, um arquivo único ou uma pasta com vários (tipicamente as pastas "Recebidas"/"Emitidas" e "Eventos" de um download do Portal Nacional). É o primeiro passo antes de identificar/classificar retenções ou montar qualquer relatório sobre essas notas — não tente ler os XMLs manualmente com o Read tool quando houver mais de um arquivo, use este script.
---

# nfse-extrator

Extrai, de forma determinística, os campos do XML de NFS-e do Ambiente
Nacional (namespace `http://www.sped.fazenda.gov.br/nfse`, leiaute NFS-e
Nacional v1.01) usando um script Python (`scripts/extract_nfse.py`), não
leitura manual do XML.

## Por que não ler o XML diretamente

Cada nota tem dezenas de campos aninhados (`infNFSe` > `DPS` > `infDPS` >
`valores` > `trib` > `tribFed` > `piscofins`...) e o cálculo do valor de
"Contribuições Sociais Retidas" não é uma leitura direta de campo — ver
seção própria abaixo. Além disso, saber se uma nota foi **cancelada**
exige cruzar o XML da nota com um XML de **evento** à parte (a nota
cancelada nunca é reemitida com outro status). Fazer isso manualmente nota
por nota é lento e sujeito a erro; por isso, para mais de um arquivo (ou
mesmo um único, para manter consistência com o resto do pipeline), sempre
rode o script.

## Como usar

```
python <diretório-desta-skill>/scripts/extract_nfse.py --input <arquivo.xml ou pasta> --output <caminho.json>
```

- `--input`: um XML único, ou uma pasta (varre recursivamente `*.xml`).
  **Aponte para a pasta que contém tanto as notas quanto a pasta
  "Eventos" irmã**, quando ela existir (ex.: aponte para `.../2026/06`, que
  contém `Recebidas/`, `Eventos/` e `Outros/`, em vez de apontar só para
  `.../2026/06/Recebidas`) — ver "Situação da nota" abaixo sobre por que
  isso importa.
- `--output`: caminho do JSON com um registro por nota (lista). Crie o
  arquivo em uma pasta de trabalho da tarefa (ex.: `notas_extraidas.json`
  ao lado dos XMLs, ou no scratchpad da sessão).

O script imprime quantas notas foram processadas, quantos eventos de
cancelamento/substituição foram casados com notas do lote, e lista falhas
por arquivo (XML corrompido, não é NFS-e do modelo nacional, etc.) sem
interromper o lote inteiro. XMLs de evento (`<evento>`, pasta "Eventos")
são varridos automaticamente só para alimentar a situação das notas — não
viram registro próprio no JSON de saída.

## Estrutura do JSON de saída

Cada item da lista tem esta forma (campos ausentes no XML viram `null`,
valores monetários já convertidos para número):

```json
{
  "arquivo": "108903_STARIAN_856.xml",
  "versao_leiaute": "1.01",
  "tipo_emissao_nfse": "NFS-e Gerada",
  "situacao": "Ativa",
  "chave_acesso": "NFS4205407225869...",
  "numero_nfse": "108903",
  "competencia": "2026-06-19",
  "prestador": { "cnpj_cpf": "...", "nome": "...", "municipio": "...", "simples_nacional": "...", ... },
  "tomador": { "cnpj_cpf": "...", "nome": "...", "municipio_ibge": "4314902", ... },
  "servico": { "codigo_tributacao_nacional": "...", "descricao": "..." },
  "tributacao_municipal": {
    "retencao_issqn": "Não Retido",
    "bc_issqn": 2010.37, "aliquota_issqn": "2.00", "issqn_apurado": 40.21
  },
  "tributacao_federal": {
    "irrf": 30.16,
    "inss_retido": null,
    "contrib_sociais_retidas": 93.48,
    "descricao_contrib_sociais_retidas": "CSLL (campo vRetCSLL do XML): R$ 93.48"
  },
  "valor_total": {
    "valor_servico": 2010.37,
    "issqn_retido": null,
    "total_retencoes": 123.64,
    "valor_liquido": 1886.73
  }
}
```

Os campos que importam para retenção estão em `tributacao_federal` (IRRF,
INSS, Contribuições Sociais) e em `valor_total.issqn_retido` (ISS retido na
fonte) — são exatamente os que a skill `nfse-retencao-identificador` lê em
seguida. **O schema do JSON é o mesmo de quando esta skill lia PDF** (mesmos
nomes/aninhamento de campo), então `nfse-retencao-identificador`,
`nfse-retencao-classificador` e `nfse-retencao-excel` continuam funcionando
sem alteração.

### Diferenças em relação à versão anterior (baseada em PDF)

- `municipio` do tomador agora é só o **código IBGE** (`municipio_ibge`) —
  o XML nacional não traz o nome do município do tomador em texto, só o
  código. Para o prestador, `municipio` continua sendo texto (vem de
  `xLocEmi`, a descrição do município emissor).
- `prestador.simples_nacional` agora é uma descrição mais completa (ex.:
  "Optante - Microempreendedor Individual (MEI)") em vez do texto livre
  "Sim"/"Não" que aparecia no PDF.
- `tipo_emissao_nfse` substitui o antigo `situacao_nfse` (texto livre do
  PDF) — vem do código `cStat` do XML e **não tem nada a ver com
  cancelamento** (ver tabela abaixo). Não confundir com `situacao`.
- Campos que só existiam no DANFSe v2.0 (Reforma Tributária/IBS-CBS
  completos, totais aproximados detalhados por UF/Município) foram
  reduzidos a `tributacao_ibs_cbs.ibs_total_apurado` /
  `cbs_total_apurado` — os totais já validados pelo Ambiente Nacional,
  sem o detalhamento completo de alíquotas.

## `tipo_emissao_nfse` não é status de cancelamento

O campo `cStat` do XML (exposto aqui como `tipo_emissao_nfse`) é o **tipo**
de emissão da nota, não seu status de cancelamento — é um erro fácil de
cometer porque parece um "status geral". Os valores possíveis (tabela
oficial do Manual de Integração NFS-e Nacional v1.01) são:

| cStat | Significado |
|-------|-------------|
| 100 | NFS-e Gerada |
| 101 | NFS-e de Substituição Gerada |
| 102 | NFS-e de Decisão Judicial |
| 103 | NFS-e Avulsa |
| 107 | NFS-e MEI |

Uma nota com `cStat=107` (MEI) é uma nota **ativa normal**, só emitida por
um Microempreendedor Individual — não é uma nota cancelada ou com
problema. Não trate nenhum valor de `cStat` como sinal de cancelamento.

## Situação da nota (`situacao`): Ativa / Cancelada / Substituída

Diferente do DANFSe em PDF (que tinha um carimbo diagonal "CANCELADA"
sobreposto ao próprio arquivo), **o XML da nota cancelada nunca muda** —
ele continua para sempre com `cStat=100` e nenhum campo interno indicando
cancelamento. A única forma de saber que uma nota foi cancelada é um XML
de **evento** separado (pasta "Eventos" do Portal Nacional, arquivo raiz
`<evento>`), que referencia a nota pela chave de acesso.

O script casa automaticamente os eventos com as notas por chave de acesso,
usando dois sinais:

1. **Evento de cancelamento** (`<evento>` cujo elemento interno é
   `<e101101>` "Cancelamento de NFS-e" ou `<e105104>` "Cancelamento
   Deferido por Análise Fiscal") → `situacao = "Cancelada"`.
2. **Evento de substituição** (`<e105102>` "Cancelamento de NFS-e por
   Substituição") **ou** a própria nota substituta declarando
   `DPS/infDPS/subst/chSubstda` → `situacao = "Substituída"` na nota
   antiga.

Outros eventos (confirmação do tomador/prestador, rejeição, solicitação de
análise fiscal ainda não julgada) **não** mudam a situação — só um
cancelamento efetivamente deferido conta.

**Isso só funciona se os XMLs de evento estiverem dentro da árvore
apontada por `--input`.** Se o usuário passar só a pasta "Recebidas" (sem
a pasta "Eventos" irmã), notas canceladas vão sair como "Ativa" por falta
de informação — sempre prefira apontar `--input` para a pasta-mãe que
contém as duas, e avise o usuário se perceber que só uma pasta de notas
foi passada sem a de eventos ao lado.

Assim como na versão em PDF, retenção reportada numa nota cancelada ou
substituída não representa uma obrigação fiscal real — a skill
`nfse-retencao-identificador` já exclui essas notas dos totais
automaticamente, mas sempre avise o usuário quando o lote tiver alguma.

## Contribuições Sociais Retidas (PIS/COFINS/CSLL): por que não é soma direta

O valor de `tributacao_federal.contrib_sociais_retidas` **não** é
`vPis + vCofins + vRetCSLL` somados diretamente do XML. Em XMLs reais de
diferentes emissores (prefeituras/ERPs que geram o XML nacional), esses
três campos são preenchidos de forma inconsistente — em alguns casos
`vRetCSLL` já vem com o valor combinado de PIS+COFINS+CSLL (duplicando o
que já está em `vPis`/`vCofins`), somar tudo infla o valor.

Em vez disso, o script parte do total que o **Ambiente Nacional já validou**
(`vTotalRet`, no bloco `infNFSe/valores`) e subtrai IRRF, INSS e ISSQN
retido — o resíduo é o valor combinado de contribuições sociais retidas.
Esse cálculo foi validado contra uma nota real: bateu exatamente com a
soma de CSLL+PIS+COFINS que aparecia no texto livre
`informacoes_complementares` da própria nota. `descricao_contrib_sociais_retidas`
continua trazendo o detalhamento (PIS/COFINS/CSLL) quando os campos
filhos do XML permitem, só para referência — o valor usado nos cálculos é
sempre o campo `contrib_sociais_retidas`.

## Limitações conhecidas

- Foi validado contra o leiaute NFS-e Nacional v1.01 (mesmo XML em
  qualquer município/prefeitura que já migrou para o Ambiente Nacional).
  XMLs de layouts municipais próprios anteriores à unificação nacional
  (ABRASF antigo, layouts de importação de ERPs como Softplan/GeisWeb) têm
  estrutura completamente diferente e são rejeitados com erro explícito —
  avise o usuário para conferir a origem do XML antes de assumir que a
  extração falhou.
- `municipio_ibge` do tomador é só o código IBGE (sem nome) — o XML
  nacional não traz o nome do município do tomador em texto.
- `codigo_tributacao_municipal` frequentemente sai `null`: no leiaute
  atual, o código municipal específico é opcional e muitos municípios só
  preenchem o código de tributação nacional (`codigo_tributacao_nacional`).
