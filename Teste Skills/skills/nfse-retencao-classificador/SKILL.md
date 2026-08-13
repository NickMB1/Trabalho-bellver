---
name: nfse-retencao-classificador
description: Classifica o tipo e o valor específico de cada retenção de tributo dentro das notas de NFS-e já identificadas pela skill nfse-retencao-identificador — separando em IRRF, INSS (Contribuição Previdenciária Retida), PIS/COFINS/CSLL (Contribuições Sociais Retidas) e ISSQN Retido. Use depois de identificar quais notas têm retenção e antes de gerar o Excel final — é o terceiro passo do pipeline de retenções em NFS-e, precisa do JSON do nfse-retencao-identificador como entrada.
---

# nfse-retencao-classificador

Para cada nota já marcada com `tem_retencao: true` pela skill
`nfse-retencao-identificador`, monta a lista detalhada de retenções: qual o
tipo de tributo, o valor exato e a base legal/observação de cada uma.

## Como usar

```
python <diretório-desta-skill>/scripts/classificar_retencoes.py --input notas_identificadas.json --output notas_classificadas.json
```

- `--input`: o JSON gerado pela skill `nfse-retencao-identificador`.
- `--output`: mesmo JSON, com um campo novo `retencoes` em cada registro —
  lista vazia para notas sem retenção, ou uma lista de objetos
  `{"tipo": ..., "valor": ..., "observacao": ..., "municipio": ...}` para
  notas com retenção. `municipio` só vem preenchido para o tipo "ISSQN
  Retido" (vem de `tributacao_municipal.municipio_incidencia_issqn` — o
  município de incidência do ISSQN, que pode ser diferente do município do
  prestador quando o serviço é prestado em outra cidade). Para os 3 tipos
  federais (IRRF, INSS, PIS/COFINS/CSLL) `municipio` fica `null`, já que
  retenção federal não tem município associado.

## As 4 categorias de retenção

O DANFSe (modelo Portal Nacional) só expõe estes 4 campos de retenção, então
são exatamente as 4 categorias possíveis — não existe "categoria não
identificada" neste modelo de nota:

| Categoria | Campo de origem | Observação |
|---|---|---|
| IRRF | `tributacao_federal.irrf` | Imposto de Renda Retido na Fonte (federal) |
| INSS (Contribuição Previdenciária Retida) | `tributacao_federal.inss_retido` | Retenção previdenciária sobre cessão de mão de obra (federal) |
| PIS/COFINS/CSLL (Contribuições Sociais Retidas) | `tributacao_federal.contrib_sociais_retidas` | Retenção unificada de PIS, COFINS e CSLL — Lei 10.833/2003 (federal) |
| ISSQN Retido | `valor_total.issqn_retido` | ISS retido na fonte pelo tomador (municipal) |

Note que "Contribuições Sociais Retidas" já vem como valor único no DANFSe
(a nota não abre quanto é PIS, quanto é COFINS e quanto é CSLL dentro desse
total) — por isso a classificação trata esse trio como uma categoria só. Se
o usuário precisar do detalhamento individual de PIS/COFINS/CSLL, avise que
o documento de origem não fornece essa quebra; teria que vir de outro
sistema (ex.: a apuração do prestador).

## Depois deste passo

O JSON de saída (`notas_classificadas.json`) alimenta a skill
`nfse-retencao-excel`, que monta o relatório final. Ao terminar, informe ao
usuário o resumo por tipo de retenção que o script já imprime (quantas notas
e o total em R$ de cada categoria).
