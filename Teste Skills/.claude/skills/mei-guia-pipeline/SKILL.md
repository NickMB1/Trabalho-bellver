---
name: mei-guia-pipeline
description: Orquestra a geração completa da(s) guia(s) DAS do MEI com vencimento no mês corrente, a partir de um único CNPJ ou de um arquivo (.txt/.csv/.xlsx) com vários CNPJs — chamando em sequência as skills mei-ler-lista-cnpjs (se houver arquivo), mei-validar-cnpj, mei-calcular-competencia, mei-emitir-das e mei-salvar-guia para cada CNPJ, e salvando cada PDF na pasta indicada com o nome da empresa, competência e vencimento. Use esta skill como ponto de entrada sempre que o usuário pedir "a guia do MEI", "o DAS do mês", "gerar/baixar a guia de pagamento do MEI" a partir de um CNPJ ou de uma lista/planilha de CNPJs — em vez de chamar uma etapa isolada.
---

# mei-guia-pipeline

Esta skill não faz nada sozinha — ela é o maestro que chama, em sequência,
as skills especializadas:

```
(mei-ler-lista-cnpjs, só se a entrada for um arquivo)
        ↓
mei-calcular-competencia (uma vez só, para todo o lote)
        ↓
para cada CNPJ: mei-validar-cnpj → mei-emitir-das → mei-salvar-guia
```

Cada uma cuida de uma responsabilidade única (leitura de arquivo,
validação local, cálculo de data local, automação de navegador no portal
oficial, e organização de arquivo local). Isso mantém cada etapa simples e
reutilizável fora do pipeline também, e permite processar 1 ou N CNPJs com
a mesma lógica.

## Passo a passo

1. **Colete a entrada com o usuário**, se faltar algo:
   - `cnpj` (um único) **ou** `arquivo_cnpjs` (caminho de `.txt`, `.csv` ou
     `.xlsx` com vários CNPJs) — exatamente uma das duas formas.
   - `pasta_destino` — **sempre pergunte** onde salvar o(s) PDF(s) antes de
     começar, se o usuário não tiver dito de forma explícita. Não assuma
     downloads nem o diretório atual. Todos os PDFs do lote vão para a
     mesma pasta.

2. **Se a entrada for `arquivo_cnpjs`**, invoque a skill
   `mei-ler-lista-cnpjs` passando o caminho do arquivo. Guarde a lista de
   CNPJs retornada (`cnpjs`) e **mostre a contagem ao usuário** antes de
   seguir (ex.: "encontrei 37 CNPJs no arquivo") — se o número parecer
   claramente errado para o que o usuário descreveu, confirme antes de
   continuar. Se vier `status: "falha"`, pare e reporte o motivo.

   Se a entrada for um único `cnpj`, trate como uma lista de um item só —
   o resto do fluxo é idêntico para 1 ou N CNPJs.

3. **Invoque a skill `mei-calcular-competencia`** uma única vez para todo o
   lote (sem argumentos, para usar a data real de hoje) — a menos que o
   usuário já tenha informado explicitamente qual competência/vencimento
   quer, caso em que essa etapa é dispensada e os valores informados são
   usados diretamente. Guarde `competencia`, `competencia_extenso` e
   `vencimento_mes_extenso`.

4. **Avise o usuário sobre a automação de navegador** antes de começar (só
   na primeira vez da conversa): as próximas etapas abrem uma aba real no
   Chrome dele via `claude-in-chrome`, e podem pedir para ele resolver
   manualmente algum CAPTCHA visual que aparecer. Se o lote tiver muitos
   CNPJs, avise também que o processamento é sequencial (um CNPJ por vez)
   e pode demorar.

5. **Para cada CNPJ da lista, nesta ordem, sem pular nenhum mesmo que um
   anterior falhe**:

   a. **Invoque `mei-validar-cnpj`** passando o CNPJ. Se `status` vier
      `"invalido"`, registre esse CNPJ como falha (motivo: CNPJ inválido)
      e **passe para o próximo CNPJ da lista** — não aborte o lote inteiro
      por causa de um item ruim.

   b. **Invoque `mei-emitir-das`** passando o `cnpj_normalizado` e a
      `competencia`. Se `status` vier `"indisponivel"`, registre esse CNPJ
      como falha com o motivo relatado e **passe para o próximo**. Se
      sucesso, guarde `nome_empresa`, `arquivo_baixado`, `valor_das` e
      `data_vencimento`.

   c. **Invoque `mei-salvar-guia`** passando `arquivo_origem`
      (=`arquivo_baixado`), `pasta_destino`, `nome_empresa`,
      `competencia`, `data_vencimento` e `cnpj` (como reserva). Guarde o
      `status` e o caminho final.

6. **Monte o relatório final**, sempre em formato de tabela, uma linha por
   CNPJ processado:

   | CNPJ | Empresa | Status | Valor | Vencimento | Arquivo/Motivo |
   |---|---|---|---|---|---|
   | 12.345.678/0001-99 | ✅ Nome da Empresa | Emitida | R$ 86,05 | 20/08/2026 | caminho do PDF |
   | 98.765.432/0001-11 | ❌ — | Indisponível | — | — | motivo relatado |

   Logo abaixo da tabela, **destaque em texto** (não só na tabela) quantos
   CNPJs foram processados com sucesso e quantos falharam, e liste
   explicitamente o motivo de cada falha — esse resumo é o requisito mais
   importante do fluxo em lote, para o usuário não precisar vasculhar a
   tabela linha a linha para saber o que faltou.

## Por que chamar as skills em vez de fazer tudo aqui

Cada skill de etapa carrega o conhecimento específico daquele passo
(como extrair CNPJs de formatos de arquivo variados; algoritmo de
validação de dígito verificador; a relação não-óbvia entre competência e
mês de vencimento; layout e comportamento do portal PGMEI; regra de nomear
o arquivo final pelo nome da empresa/competência/vencimento e nunca
sobrescrever o arquivo original ao salvar). Invocar a skill garante que
essas regras sejam seguidas mesmo que este orquestrador não repita todos
os detalhes, e vale tanto para 1 quanto para N CNPJs.

## Limitações conhecidas

- Não existe API oficial para o PGMEI — a emissão depende de automação de
  navegador no portal público da Receita Federal, então falhas pontuais
  (CAPTCHA, manutenção, mudança de layout do site) são esperadas e não
  indicam bug nas skills. Em lote, isso significa que algumas linhas do
  relatório final naturalmente virão como indisponíveis.
- Um CNPJ que não seja MEI, que ainda não tenha sido optante do Simples
  Nacional naquela competência, ou que já tenha sido baixado/desenquadrado,
  não terá guia disponível para aquele período — isso é reportado pela
  skill `mei-emitir-das` como indisponível, não como erro do pipeline.
- O processamento em lote é sequencial, um CNPJ por vez (a automação de
  navegador não paraleliza) — para arquivos muito grandes, avise o usuário
  que pode demorar antes de começar.
- Esta skill nunca tenta contornar CAPTCHA visual nem adivinhar dados que
  o usuário não forneceu — sempre pede para ele resolver ou informar.
