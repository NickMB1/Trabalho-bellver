---
name: nfse-retencao-excel
description: Gera a planilha Excel (.xlsx) final do pipeline de retenções em NFS-e, a partir das notas já classificadas pela skill nfse-retencao-classificador — uma aba "Resumo" com uma linha por nota (valores de cada tipo de retenção em colunas) e uma aba "Detalhe Retenções" com uma linha por retenção individual. Use como último passo, depois de identificar e classificar as retenções, sempre que o usuário pedir para "gerar o excel", "montar a planilha" ou "consolidar o relatório" das notas fiscais de serviço — precisa do JSON do nfse-retencao-classificador como entrada.
---

# nfse-retencao-excel

Monta o relatório final em Excel a partir do JSON já classificado, com duas
abas complementares.

## Como usar

```
python <diretório-desta-skill>/scripts/gerar_excel.py --input notas_classificadas.json --output relatorio_retencoes.xlsx
```

- `--input`: o JSON gerado pela skill `nfse-retencao-classificador`.
- `--output`: caminho do `.xlsx` final. Salve num nome que o usuário
  reconheça (ex.: `Retencoes_NFSe_<periodo>.xlsx`), na pasta onde ele espera
  encontrar o resultado (ex.: ao lado da pasta de PDFs, ou onde ele pedir).

## Estrutura do Excel gerado

**Aba "Resumo"** — uma linha por nota processada (com ou sem retenção),
colunas: Arquivo, Número NFS-e, Situação (Ativa/Cancelada/Substituída — vem
`null`/em branco para DANFSe v1.0, que não tem esse campo), Chave de Acesso,
Competência, Data Emissão, Prestador, CNPJ/CPF Prestador, Tomador, CNPJ/CPF
Tomador, Valor do Serviço,
Valor Líquido, Tem Retenção (Sim/Não), uma coluna para cada uma das 4
categorias de retenção (IRRF, INSS, PIS/COFINS/CSLL, ISSQN Retido) já com o
valor de cada uma quando presente, Município ISSQN (o município de
incidência do ISSQN quando houver retenção desse tipo — em branco para as
demais categorias, que são federais e não têm município associado), e Total
Retenções.

**Aba "Detalhe Retenções"** — formato longo, uma linha por retenção
individual (só notas com retenção aparecem aqui, podendo ter mais de uma
linha se tiverem mais de um tipo): Arquivo, Número NFS-e, Competência,
Prestador, CNPJ/CPF Prestador, Tomador, CNPJ/CPF Tomador, Tipo de Retenção,
Valor, Município (só preenchido em linhas de ISSQN Retido), Observação (base
legal). Essa aba é a que responde diretamente "qual o tipo de retenção, o
valor específico e (quando for ISSQN) o município de cada retenção" por
nota.

Cabeçalhos vêm formatados (negrito, fundo azul, congelados) e colunas de
valor já em formato monetário — não precisa reformatar depois.

## Ao terminar

Diga ao usuário onde o arquivo `.xlsx` foi salvo e o resumo que o script
imprime (total de notas e quantas têm retenção). Se ele pedir para abrir o
arquivo, use o comando apropriado do sistema operacional (`Invoke-Item` no
Windows) só se ele pedir explicitamente — não abra automaticamente.
