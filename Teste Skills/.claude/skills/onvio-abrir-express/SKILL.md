---
name: onvio-abrir-express
description: Abre o portal Onvio (https://onvio.com.br), confirma que a sessão de login está ativa e navega até a aba "Onvio Express" dentro de Processos, deixando a aba pronta para upload de arquivos. Use como segundo passo do fluxo orquestrado pela skill onvio-express-pipeline, uma única vez por execução — nunca reabra o Onvio a cada lote de arquivos.
---

# onvio-abrir-express

Prepara a aba do navegador no Onvio Express, pronta para receber uploads.
Depende da skill `claude-in-chrome` — não chame `mcp__claude-in-chrome__*`
diretamente antes de invocá-la.

## Passo a passo

1. **Invoque a skill `claude-in-chrome`** e abra uma aba em
   `https://onvio.com.br/login/#/`.

2. **Confira a sessão de login**:
   - Se a página carregar direto em área logada (Processos, Dashboard etc.),
     prossiga.
   - Se cair numa tela de login, **pare** e peça para o usuário fazer login
     manualmente (usuário/senha/2FA são dele) na aba aberta. Só continue
     depois que o usuário confirmar que está logado. Nunca digite
     credenciais por conta própria nem tente adivinhar/preencher senha.

3. **Navegue até "Processos"** no menu principal do Onvio.

4. **Dentro de Processos, abra a aba "Onvio Express"** (é uma aba/seção
   dentro dessa área, não um cliente/processo específico — não é preciso
   abrir nenhum processo individual).

5. **Confirme que a tela do Onvio Express carregou** (área de upload/lista
   de arquivos visível) usando `get_page_text` ou `find` antes de reportar
   sucesso.

## O que reportar ao final

- `tabId`: o ID da aba aberta, para ser reaproveitado pelas próximas etapas
  (`onvio-subir-lote` e `onvio-enviar-lote`) — **não abra uma aba nova para
  cada lote**.
- `status`: `"pronto"` ou `"indisponivel"` (com o motivo: portal fora do ar,
  usuário não conseguiu logar, aba "Onvio Express" não encontrada, etc.).
