---
name: nfse-retencao-identificador
description: Identifica, dentro de um lote de notas de NFS-e já extraídas (JSON produzido pela skill nfse-extrator), quais notas têm alguma retenção de tributo (IRRF, INSS/Contribuição Previdenciária Retida, Contribuições Sociais Retidas PIS/COFINS/CSLL, ou ISSQN Retido) e quais não têm nenhuma. Use depois de extrair os dados dos PDFs e antes de classificar o tipo de cada retenção — é o segundo passo do pipeline de retenções em NFS-e, nunca o primeiro (precisa do JSON do nfse-extrator como entrada).
---

# nfse-retencao-identificador

Marca, em cada registro de nota já extraído pela skill `nfse-extrator`, se há
alguma retenção de tributo e qual o valor total retido — sem ainda quebrar
por tipo (isso é trabalho da skill `nfse-retencao-classificador`, o próximo
passo).

## Como usar

```
python <diretório-desta-skill>/scripts/identificar_retencoes.py --input notas_extraidas.json --output notas_identificadas.json
```

- `--input`: o JSON gerado pela skill `nfse-extrator`.
- `--output`: mesmo JSON, com dois campos novos em cada registro:
  - `tem_retencao`: `true`/`false`.
  - `valor_total_retencoes`: soma de todas as retenções da nota, ou `null`
    se não houver nenhuma.

## O que conta como retenção

Uma nota "tem retenção" se qualquer um destes 4 campos (já extraídos pelo
`nfse-extrator`) vier maior que zero:

- `tributacao_federal.irrf` — IRRF retido
- `tributacao_federal.inss_retido` — Contribuição Previdenciária Retida (INSS)
- `tributacao_federal.contrib_sociais_retidas` — Contribuições Sociais Retidas (PIS/COFINS/CSLL)
- `valor_total.issqn_retido` — ISS retido na fonte

Não conta como retenção os campos "Débito Apuração Própria" (PIS/COFINS que
o próprio prestador apura e recolhe, sem ser retenção de terceiro) — esses
ficam de fora do cálculo de propósito.

## Notas Canceladas ou Substituídas não contam

Uma nota com `situacao` igual a `"Cancelada"` ou `"Substituída"` (campo que
vem do `nfse-extrator` — atenção: nessas notas o texto "Situação da NFS-e"
do próprio PDF costuma continuar dizendo "regular (Autorizada)", quem
manda é o carimbo diagonal que o extrator já leu) sempre recebe
`tem_retencao: false` e `valor_total_retencoes: null`, **mesmo que o PDF
mostre valores de retenção impressos** — a obrigação fiscal não existe mais,
então contar esses valores infla o total real a repassar. A nota continua
no JSON de saída normalmente (não é removida do lote), só não entra na
contagem. `situacao: null` (DANFSe v1.0, que não tem esse campo) conta
normalmente, como se fosse "Ativa".

O script imprime, quando existirem, quais arquivos tiveram retenção anulada
por causa disso — sempre repasse essa lista ao usuário, não só o total
líquido, para que ele saiba que houve algo excluído e possa conferir.

## Depois deste passo

O JSON de saída (`notas_identificadas.json`) alimenta a skill
`nfse-retencao-classificador`, que quebra `valor_total_retencoes` por tipo.
Ao terminar, informe ao usuário quantas notas têm retenção e quantas não têm
(o script já imprime esse resumo).
