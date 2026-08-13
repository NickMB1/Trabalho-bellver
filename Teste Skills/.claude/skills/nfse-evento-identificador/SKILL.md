---
name: nfse-evento-identificador
description: Varre uma pasta de XMLs de NFS-e do Ambiente Nacional (namespace sped.fazenda.gov.br/nfse) e identifica todos os XMLs de evento (cancelamento, cancelamento por substituição, e outros) presentes, cruzando-os com as notas para determinar a situação de cada uma (Ativa, Cancelada, Substituída). Use como primeiro passo sempre que o usuário pedir para "identificar os eventos", "achar as notas canceladas/substituídas", ou como primeiro passo do fluxo orquestrado pela skill nfse-limpeza-pipeline (que depois remove/move os XMLs das notas Canceladas/Substituídas). Não remove nem move nenhum arquivo — só identifica e lista.
---

# nfse-evento-identificador

Identifica, de forma determinística, todos os XMLs de **evento** dentro de
uma pasta de NFS-e do Ambiente Nacional (namespace
`http://www.sped.fazenda.gov.br/nfse`) e usa esses eventos para determinar
a **situação** de cada nota (`Ativa`, `Cancelada` ou `Substituída`) — usando
o script `scripts/identificar_eventos.py`, não leitura manual do XML.

Esta skill só **identifica e reporta**. Ela não apaga nem move nenhum
arquivo — isso é trabalho da skill `nfse-limpeza-executor`, o próximo passo
do pipeline.

## Por que não basta olhar o XML da nota

O XML de uma nota cancelada **nunca muda** — ele continua para sempre com
`cStat=100` (ou outro código de emissão normal) e nenhum campo interno
indicando cancelamento. A única forma de saber que uma nota foi cancelada
ou substituída é encontrar o XML de **evento** correspondente (documento
`<evento>` à parte, tipicamente na pasta "Eventos" de um download do Portal
Nacional), que referencia a nota pela chave de acesso (`chNFSe`).

## Como usar

```
python <diretório-desta-skill>/scripts/identificar_eventos.py --input <pasta> --output <caminho.json>
```

- `--input`: a pasta que contém tanto os XMLs de nota (pastas
  "Recebidas"/"Emitidas", tipicamente) quanto a pasta **"Eventos" irmã**,
  quando ela existir. O script varre recursivamente (`*.xml`). **Sempre
  aponte para a pasta-mãe que contém as duas** (ex.: `.../2026/06`, que
  contém `Recebidas/` e `Eventos/`) — se só a pasta de notas for passada,
  sem a de eventos ao lado, nenhum cancelamento será detectado e todas as
  notas sairão como "Ativa". Avise o usuário se perceber isso.
- `--output`: caminho do JSON de saída. Crie em uma pasta de trabalho da
  tarefa (ex.: `situacao_notas.json`, no scratchpad da sessão).

## Códigos de evento reconhecidos

Código do evento = nome do elemento wrapper dentro de `infPedReg` (ex.:
`<e101101>`). Só estes dois grupos mudam a situação de uma nota — os
demais (confirmação do tomador/prestador, rejeição, solicitação de análise
fiscal ainda não julgada) são listados como `tipo: "Outro"`, informativos,
sem efeito sobre a situação:

| Código | Descrição | Efeito |
|--------|-----------|--------|
| `e101101` | Cancelamento de NFS-e | `situacao = "Cancelada"` |
| `e105104` | Cancelamento Deferido por Análise Fiscal | `situacao = "Cancelada"` |
| `e105102` | Cancelamento de NFS-e por Substituição | `situacao = "Substituída"` |

Além dos eventos, uma nota também é marcada `Substituída` se **ela mesma**
(a nota substituta) declarar `DPS/infDPS/subst/chSubstda` apontando para a
chave de outra nota do lote — esse sinal funciona mesmo que a pasta
"Eventos" não esteja no escopo de `--input`.

Cancelamento tem prioridade sobre substituição se, por algum motivo raro,
os dois eventos existirem para a mesma chave.

## Estrutura do JSON de saída

```json
{
  "notas": [
    {
      "arquivo": "108903_STARIAN_856.xml",
      "arquivo_caminho": "C:\\...\\Recebidas\\108903_STARIAN_856.xml",
      "chave_acesso": "NFS4205407225869...",
      "numero_nfse": "108903",
      "situacao": "Cancelada",
      "evento_responsavel": "evento_cancelamento_108903.xml"
    }
  ],
  "eventos": [
    {
      "arquivo": "evento_cancelamento_108903.xml",
      "arquivo_caminho": "C:\\...\\Eventos\\evento_cancelamento_108903.xml",
      "codigo_evento": "101101",
      "descricao_evento": "Cancelamento de NFS-e",
      "tipo": "Cancelamento",
      "chave_nfse_afetada": "4205407225869...",
      "data_hora_evento": "2026-06-25T10:00:00"
    }
  ]
}
```

`notas` é a lista completa (todas as situações, não só as
Canceladas/Substituídas) — é a `nfse-limpeza-executor` quem filtra pelo
campo `situacao` na próxima etapa. `eventos` é a lista de **todos** os XMLs
de evento encontrados, inclusive os que não afetam situação (`tipo:
"Outro"`), para que o usuário veja o panorama completo se pedir.

## Depois deste passo

Sempre reporte ao usuário o resumo que o script já imprime (quantos XMLs de
nota e de evento foram processados, quantas notas ficaram Ativa/
Cancelada/Substituída, e a lista de arquivos afetados com o evento
responsável) antes de prosseguir para a remoção — o usuário precisa
confirmar essa lista antes que qualquer arquivo seja apagado ou movido pela
skill `nfse-limpeza-executor`.
