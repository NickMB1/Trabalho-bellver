---
name: mei-ler-lista-cnpjs
description: Extrai a lista de CNPJs de um arquivo (.txt, .csv ou .xlsx) informado pelo usuário, um CNPJ por linha/célula. Use sempre que o usuário pedir para gerar guias do MEI "para uma lista de CNPJs", "para todas as empresas de um arquivo/planilha", ou passar um arquivo em vez de digitar um único CNPJ — como primeiro passo do fluxo em lote orquestrado pela skill mei-guia-pipeline.
---

# mei-ler-lista-cnpjs

É um passo puramente local de leitura de arquivo, sem rede nem automação
de navegador. Existe para separar "extrair os CNPJs de um arquivo
qualquer" de "validar cada CNPJ" (isso continua sendo responsabilidade da
skill `mei-validar-cnpj`, chamada uma vez por CNPJ depois desta etapa).

## Entrada esperada

- `arquivo`: caminho de um arquivo `.txt`, `.csv` ou `.xlsx` contendo os
  CNPJs. Aceita CNPJs com ou sem máscara, um por linha (`.txt`) ou
  espalhados em qualquer célula/coluna (`.csv`/`.xlsx`) — inclusive
  misturados com outras colunas (nome, IE, etc.), já que o script filtra
  apenas sequências de 14 dígitos.

Se o usuário não informar o caminho do arquivo, pergunte antes de
prosseguir. Não tente adivinhar um arquivo pelo nome parecido no diretório
atual.

## Passo a passo

1. Rode:
   ```
   python <diretório-desta-skill>/scripts/ler_lista_cnpjs.py <arquivo>
   ```
2. Se o script sair com código 0: cada linha do stdout é um CNPJ
   normalizado (14 dígitos, sem máscara, sem duplicatas, na ordem em que
   apareceram no arquivo).
3. Se sair com código 1 ou 2 (arquivo não encontrado, formato não
   suportado, ou nenhum CNPJ de 14 dígitos encontrado): pare e reporte o
   motivo exato ao usuário — não invente CNPJs nem tente prosseguir com
   lista vazia.

## O que reportar ao final

- `status`: `"sucesso"` ou `"falha"`.
- Se sucesso: `cnpjs` (lista de strings de 14 dígitos) e a contagem total
  encontrada — mostre essa contagem ao usuário antes de seguir para a
  emissão em lote, para que ele possa cancelar se o número estiver muito
  diferente do esperado.
- Se falha: o motivo.

## Limitação conhecida

Esta skill só filtra sequências de exatamente 14 dígitos — não confirma
que cada uma é, de fato, um CNPJ válido (dígito verificador correto) nem
que corresponde a um MEI. Essa validação é sempre feita depois, uma a uma,
pela skill `mei-validar-cnpj`.
