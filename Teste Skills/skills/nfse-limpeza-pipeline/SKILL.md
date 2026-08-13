---
name: nfse-limpeza-pipeline
description: Orquestra a limpeza de XMLs de NFS-e do Ambiente Nacional — identifica os eventos de cancelamento/substituição em uma pasta e move (ou remove) os XMLs das notas Canceladas/Substituídas, chamando em sequência as skills nfse-evento-identificador e nfse-limpeza-executor, com confirmação explícita do usuário no meio do caminho. Use esta skill como ponto de entrada sempre que o usuário pedir para "verificar os XMLs da NFS-e nacional e identificar os eventos", "remover/tirar os XMLs das notas canceladas e substituídas", ou peça o fluxo inteiro em vez de rodar uma etapa isolada.
---

# nfse-limpeza-pipeline

Esta skill não processa nada sozinha — ela é o maestro que chama, nesta
ordem, as 2 skills especializadas, com uma parada obrigatória de confirmação
no meio:

```
nfse-evento-identificador → [confirmação do usuário] → nfse-limpeza-executor
```

## Passo a passo

1. **Confirme a entrada com o usuário** se não estiver clara: qual pasta
   contém os XMLs (deve incluir tanto as notas quanto a pasta "Eventos"
   irmã — sem ela, nenhum cancelamento é detectado). Se o usuário já passou
   o caminho, não precisa perguntar de novo.

2. **Pergunte a ação desejada**, se o usuário não tiver especificado: mover
   os XMLs afetados para uma pasta de backup (reversível, recomendado por
   padrão) ou apagá-los definitivamente do disco. Deixe claro que "mover"
   não perde nenhum arquivo, só tira da pasta original, e sugira essa opção
   como padrão quando o usuário não tiver preferência forte.

3. **Crie uma pasta de trabalho** para o JSON intermediário (ex.: no
   scratchpad da sessão) — algo como `situacao_notas.json`.

4. **Invoque a skill `nfse-evento-identificador`** (pela Skill tool, não
   rodando o script diretamente) passando a pasta de entrada e o caminho do
   JSON de saída.

5. **Pare e mostre ao usuário** a lista completa de notas Canceladas/
   Substituídas encontradas (arquivo, situação, evento responsável — o
   próprio script já imprime isso). **Não prossiga para a remoção sem
   confirmação explícita do usuário** — apagar/mover XMLs fiscais é uma
   ação sensível, e a lista pode conter algo que o usuário queira revisar
   antes (ex.: uma nota que ele não esperava estar cancelada).

6. **Invoque a skill `nfse-limpeza-executor`** só depois da confirmação,
   passando o JSON do passo 4, a ação escolhida (`mover` ou `remover`) e,
   se `mover`, a pasta de destino. Para `remover`, é aceitável (e mais
   seguro) rodar primeiro sem `--confirmar` para mostrar a prévia, e só
   então rodar de novo com `--confirmar` depois do "sim, pode apagar" do
   usuário.

7. **Reporte o resultado final**: quantos XMLs de nota e de evento foram
   processados no total, quantas notas eram Ativa/Cancelada/Substituída, e
   quantos arquivos foram efetivamente movidos/apagados e para onde (os
   scripts das duas etapas já imprimem esses números — reaproveite-os em
   vez de recalcular).

## Por que chamar as skills em vez de rodar os scripts direto

Cada skill intermediária carrega no contexto o conhecimento específico do
seu passo (os códigos de evento reconhecidos, os cuidados de segurança
antes de apagar arquivo) — invocar a skill garante que essas regras sejam
seguidas mesmo que este arquivo orquestrador não repita todos os detalhes.
Só rode os scripts Python diretamente se uma das skills não estiver
disponível por algum motivo.

## Se algo falhar no meio do caminho

Se o `nfse-evento-identificador` reportar XMLs mal formados, não interrompa
o pipeline — os arquivos que processaram com sucesso seguem normalmente.
Informe ao usuário quais falharam e por quê. Se `--input` não incluir a
pasta "Eventos", avise antes de prosseguir: sem ela, o resultado será "0
notas canceladas" mesmo que existam cancelamentos reais, o que pode levar o
usuário a concluir erroneamente que não há nada para limpar.

## O que esta skill nunca faz sozinha

Nunca pula a etapa de confirmação do passo 5, mesmo que o usuário tenha
pedido o pipeline inteiro de uma vez ("roda tudo e já remove") — sempre
mostre a lista antes de mover/apagar qualquer arquivo, porque essa é uma
ação sobre os arquivos originais do usuário e pode ser difícil de reverter
(no caso de `--acao remover`).
