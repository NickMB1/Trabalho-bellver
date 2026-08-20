---
name: simples-optantes-pipeline
description: Orquestra a verificação em lote de eventos futuros no Simples Nacional (ex.: exclusão de ofício) para todos os CNPJs de um arquivo (.csv, .txt ou .xlsx), consultando cada um na Consulta Optantes da Receita Federal e gerando ao final uma planilha Excel só com os CNPJs que têm evento futuro e qual é o evento. Use esta skill como ponto de entrada sempre que o usuário pedir para "verificar eventos futuros de uma lista/CSV de CNPJs no Simples Nacional", "checar exclusão de ofício em lote", ou peça o fluxo inteiro em vez de consultar um CNPJ isolado (nesse caso use simples-optantes-consulta diretamente).
---

# simples-optantes-pipeline

Orquestra, em sequência, as 3 skills especializadas:

```
simples-optantes-lista-cnpjs  →  simples-optantes-consulta (uma vez por CNPJ)  →  simples-optantes-excel
```

A skill do meio abre o portal "Consulta Optantes" via `claude-in-chrome` e
é chamada repetidamente, uma vez por CNPJ do arquivo, reaproveitando a
mesma aba do navegador entre as chamadas.

## Passo a passo

1. **Colete a entrada** com o usuário, se faltar algo:
   - `arquivo`: caminho do `.csv`/`.txt`/`.xlsx` com os CNPJs —
     obrigatório, pergunte se não vier na mensagem.
   - `output_path`: caminho do `.xlsx` final — **sempre pergunte** onde
     salvar antes de começar (sugestão padrão: mesma pasta do arquivo de
     entrada, nome `eventos_futuros_simples.xlsx`, mas confirme em vez de
     assumir).

2. **Invoque a skill `simples-optantes-lista-cnpjs`** passando `arquivo`.
   Se ela reportar falha, pare e mostre o motivo ao usuário. Se sucesso,
   mostre a contagem de CNPJs encontrados antes de seguir — para o
   usuário poder cancelar se o número estiver muito diferente do
   esperado.

3. **Avise o usuário sobre a automação de navegador** antes de começar (só
   na primeira vez da conversa): o próximo passo abre uma aba real no
   Chrome dele e consulta um CNPJ de cada vez — para lotes grandes (dezenas
   de CNPJs), isso pode levar alguns minutos.

4. **Para cada CNPJ da lista**, invoque a skill `simples-optantes-consulta`
   passando o `cnpj` e o `tabId` retornado pela chamada anterior (na
   primeira chamada, sem `tabId`). Acumule cada registro retornado numa
   lista em memória — não descarte nenhum, inclusive os `nao_encontrado`.

   Não pare o lote se um CNPJ individual falhar (inválido, não
   encontrado, portal indisponível naquele momento) — registre o motivo
   e siga para o próximo.

5. **Salve a lista acumulada** como um JSON temporário (ex.:
   `resultados_simples_<timestamp>.json`, no diretório de scratch) com um
   registro por CNPJ, no formato descrito pela skill
   `simples-optantes-consulta`.

6. **Invoque a skill `simples-optantes-excel`** passando o JSON salvo e o
   `output_path`. Guarde a contagem final reportada.

7. **Monte o relatório final** para o usuário, sempre destacando:
   - Total de CNPJs consultados.
   - Quantos têm evento futuro (com uma prévia — CNPJ, empresa e
     descrição do evento — direto na conversa, não só "veja a planilha").
   - Quantos não puderam ser processados, com o motivo de cada um, se
     houver — esse aviso é tão importante quanto o resultado positivo,
     não é um detalhe opcional.
   - Caminho final do arquivo `.xlsx` gerado.

## Por que chamar as skills em vez de fazer tudo aqui

Cada skill carrega o conhecimento específico daquele passo (como extrair
CNPJs de qualquer formato de arquivo; a URL estável do portal e como ler
a tabela de eventos futuros, incluindo a ressalva sobre `get_page_text`
não ser confiável nesse site; o layout exato da planilha final). Invocar
a skill garante que essas regras sejam seguidas mesmo que este
orquestrador não repita todos os detalhes.

## Limitações conhecidas

- Não existe API oficial para a Consulta Optantes — tudo depende de
  automação de navegador no portal público, então falhas pontuais
  (timeout, portal fora do ar) são esperadas para CNPJs isolados e não
  indicam bug no pipeline.
- Lotes muito grandes (centenas de CNPJs) podem demorar bastante, já que
  cada consulta é sequencial no navegador — avise o usuário da estimativa
  antes de começar se a lista for grande.
- Esta skill nunca tenta contornar CAPTCHA ou qualquer desafio anti-robô
  que eventualmente apareça — se isso acontecer, pausa e pede para o
  usuário resolver manualmente antes de continuar o lote.
