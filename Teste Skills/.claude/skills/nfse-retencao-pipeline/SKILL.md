---
name: nfse-retencao-pipeline
description: Orquestra o processo completo de análise de retenções em notas fiscais de serviço (NFS-e) do Portal Nacional — lê os PDFs, identifica quais notas têm retenção, classifica o tipo de cada retenção e gera o Excel final com o tipo e o valor de cada retenção por nota — chamando em sequência, uma a uma, as skills nfse-extrator, nfse-retencao-identificador, nfse-retencao-classificador e nfse-retencao-excel. Use esta skill como ponto de entrada sempre que o usuário pedir para processar um PDF/pasta de notas fiscais de serviço "de ponta a ponta", "gerar o relatório de retenções", ou peça o fluxo inteiro em vez de uma etapa isolada.
---

# nfse-retencao-pipeline

Esta skill não processa nada sozinha — ela é só o maestro que chama, nesta
ordem, as 4 skills especializadas, repassando o arquivo de saída de uma como
entrada da próxima:

```
nfse-extrator → nfse-retencao-identificador → nfse-retencao-classificador → nfse-retencao-excel
```

## Passo a passo

Ao ser acionada (ex.: "processa essa pasta de notas e me dá o excel de
retenções"), siga esta sequência, invocando cada skill pela Skill tool (não
rode os scripts das outras skills diretamente por conta própria — invoque
cada skill para que as instruções específicas dela sejam seguidas):

1. **Confirme a entrada com o usuário** se não estiver clara: qual pasta (ou
   arquivo) contém os PDFs das notas, e onde deve ficar o Excel final. Se o
   usuário já passou os caminhos, não precisa perguntar de novo.

2. **Crie uma pasta de trabalho** para os JSONs intermediários (ex.: dentro
   da própria pasta de PDFs, ou no scratchpad da sessão) — algo como
   `notas_extraidas.json`, `notas_identificadas.json`,
   `notas_classificadas.json`.

3. **Invoke a skill `nfse-extrator`** passando a pasta/arquivo de PDFs de
   entrada e o caminho do primeiro JSON de saída.

4. **Invoke a skill `nfse-retencao-identificador`** passando o JSON do passo
   anterior como entrada, e um novo caminho de saída.

5. **Invoke a skill `nfse-retencao-classificador`** passando o JSON do passo
   anterior como entrada, e um novo caminho de saída.

6. **Invoke a skill `nfse-retencao-excel`** passando o JSON classificado
   como entrada e o caminho do `.xlsx` final que o usuário espera.

7. **Reporte o resultado**: quantas notas foram processadas no total,
   quantas têm retenção, o total retido por categoria (os scripts das
   etapas 2 e 3 já imprimem esses números — reaproveite-os em vez de
   recalcular) e onde o Excel final foi salvo.

## Por que chamar as skills em vez de rodar os scripts direto

Cada skill intermediária carrega no contexto o conhecimento específico do
seu passo (schema exato de campos, o que conta como retenção, as 4
categorias de classificação, a estrutura do Excel) — invocar a skill garante
que essas regras sejam seguidas mesmo que este arquivo orquestrador não
repita todos os detalhes. Só rode os scripts Python diretamente se uma das
skills não estiver disponível por algum motivo.

## Se algo falhar no meio do caminho

Se o `nfse-extrator` reportar falhas em alguns arquivos (PDF corrompido, não
é um DANFSe do portal nacional), não interrompa o pipeline — as notas que
extraíram com sucesso seguem normalmente para as próximas etapas. Informe ao
usuário quais arquivos falharam e por quê, junto do relatório final.

## Requisitos

Este pipeline depende de Python 3 com `pdfplumber` e `openpyxl` instalados no
ambiente onde os scripts rodam (bundled nas skills `nfse-extrator` e
`nfse-retencao-excel`, respectivamente). Se algum comando falhar por módulo
ausente, instale com `pip install pdfplumber openpyxl` antes de tentar de
novo.
