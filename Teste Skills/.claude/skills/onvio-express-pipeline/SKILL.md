---
name: onvio-express-pipeline
description: Orquestra o envio completo de uma pasta local de arquivos para o Onvio Express (aba dentro de Processos no portal Onvio) — lê a pasta, abre o portal, sobe os arquivos em lotes e envia clicando no botão de joinha, chamando em sequência as skills onvio-ler-pasta, onvio-abrir-express, onvio-subir-lote e onvio-enviar-lote. Use esta skill como ponto de entrada sempre que o usuário pedir para "mandar/subir/enviar arquivos para o Onvio", "colocar os arquivos no Onvio Express", apontando uma pasta — em vez de chamar uma etapa isolada.
---

# onvio-express-pipeline

Esta skill não processa nada sozinha — ela é o maestro que chama, nesta
ordem, as skills especializadas:

```
onvio-ler-pasta (uma vez)
        ↓
onvio-abrir-express (uma vez, abre a aba e mantém o tabId)
        ↓
para cada lote: onvio-subir-lote → [pendentes? confirmar com usuário] → onvio-enviar-lote
```

O Onvio Express identifica sozinho a qual cliente/processo cada arquivo
pertence — este fluxo nunca abre um processo específico nem escolhe cliente
manualmente.

## Passo a passo

1. **Confirme a entrada com o usuário** se não estiver clara: qual `pasta`
   local contém os arquivos a enviar.

2. **Invoque `onvio-ler-pasta`** passando a pasta. Guarde `lotes`,
   `arquivos_grandes_demais` e `subpastas_ignoradas`.
   - Se a pasta estiver vazia ou não existir, pare e reporte isso — não
     prossiga para abrir o navegador sem ter o que enviar.
   - Se houver `subpastas_ignoradas`, avise o usuário e pergunte se elas
     também devem ser enviadas antes de continuar.
   - Se houver `arquivos_grandes_demais`, avise quais são e que eles não
     serão enviados por esta via (ultrapassam o limite de upload sozinhos).

3. **Avise o usuário sobre a automação de navegador** antes de começar (só
   na primeira vez da conversa): a próxima etapa abre uma aba real no Chrome
   dele via `claude-in-chrome`, e pode pedir para ele fazer login
   manualmente se a sessão do Onvio não estiver ativa.

4. **Invoque `onvio-abrir-express`** uma única vez. Guarde o `tabId`. Se
   `status` vier `"indisponivel"`, pare e reporte o motivo — não tem sentido
   tentar os lotes sem a aba pronta.

5. **Para cada lote da lista, nesta ordem**:

   a. **Invoque `onvio-subir-lote`** passando o `tabId` e os `arquivos` do
      lote. Guarde `identificados`, `pendentes` e `falhas_upload`.

   b. **Se houver `pendentes`**, pare e mostre ao usuário exatamente quais
      arquivos ficaram sem identificação automática. Pergunte como
      proceder: enviar só os `identificados` agora e deixar os pendentes de
      fora, esperar mais um pouco e reverificar, ou pular o lote inteiro.
      **Nunca envie um arquivo pendente sem essa confirmação explícita.**

   c. **Invoque `onvio-enviar-lote`** passando o `tabId`, só depois de
      resolvida a situação dos pendentes (ou direto, se não houver
      nenhum). Guarde o `status` e a contagem enviada.

   d. Se qualquer etapa do lote falhar de forma técnica (portal fora do ar,
      erro ao clicar, etc.), registre a falha daquele lote e **continue para
      o próximo lote** em vez de abortar o envio inteiro.

6. **Monte o relatório final**, sempre com um resumo direto no início:
   quantos arquivos foram enviados com sucesso no total, quantos ficaram
   pendentes sem identificação (e não foram enviados), e quantos falharam
   por outro motivo. Em seguida, detalhe por lote/arquivo.

## Por que chamar as skills em vez de fazer tudo aqui

Cada skill de etapa carrega o conhecimento específico daquele passo (como
montar lotes dentro do limite de upload; como confirmar a sessão de login
sem nunca digitar credenciais; como localizar e usar o elemento de upload
sem abrir o seletor nativo do sistema operacional; a diferença entre
"selecionar todos" e o botão de envio de fato). Invocar a skill garante que
essas regras sejam seguidas mesmo que este orquestrador não repita todos os
detalhes.

## O que esta skill nunca faz sozinha

- Nunca abre um cliente/processo específico — o Onvio Express identifica
  sozinho.
- Nunca preenche login/senha do usuário.
- Nunca envia (clica no joinha) um lote que tenha arquivos pendentes sem
  antes perguntar ao usuário o que fazer com eles.
- Nunca tenta contornar CAPTCHA ou qualquer verificação de segurança —
  se aparecer algo assim, pausa e pede para o usuário resolver manualmente.
