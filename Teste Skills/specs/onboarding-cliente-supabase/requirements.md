# Requisitos — Onboarding de Cliente online (Supabase)

## Objetivo
Transformar a ficha de onboarding (`onboarding-cliente.html`), hoje local e sem persistência,
em um checklist online e compartilhado: qualquer pessoa da equipe, em qualquer máquina, deve
conseguir abrir o site, ver os checklists já preenchidos por outras pessoas, criar novos e
editar os existentes — tudo salvo em um banco Supabase compartilhado.

## Requisitos funcionais
- RF1 — Ao abrir o site, exibir uma tela de **lista** com todos os checklists já salvos no
  Supabase (nome do cliente, CNPJ, quem criou, última atualização, % de progresso).
- RF2 — Permitir criar um **novo checklist** (abre a ficha em branco).
- RF3 — Permitir **abrir/editar** um checklist existente a partir da lista.
- RF4 — Ao salvar, gravar no Supabase quem gerou o checklist (`criado_por`) e quem fez a
  última alteração (`atualizado_por`), com base em um nome informado pela pessoa.
- RF5 — A lista deve refletir checklists salvos por **outras máquinas/pessoas**, sem precisar
  compartilhar arquivo — a fonte de verdade é o banco Supabase, não o navegador local.
- RF6 — Manter as funcionalidades já existentes da ficha: checklist de documentos, dados do
  sócio administrador, funcionários, anexo do Simples Nacional, impressão/PDF.

## Identificação de quem gerou
- Sem login/senha (ferramenta interna). A pessoa informa o nome uma vez; o nome fica salvo no
  navegador dela (`localStorage`) e é reaproveitado nos próximos checklists que ela criar ou
  editar naquela máquina.

## Requisitos não funcionais
- Site estático (HTML/CSS/JS), sem servidor próprio — hospedável em qualquer lugar (ou aberto
  localmente) e conectado direto ao Supabase via `supabase-js` (CDN).
- Deve funcionar assim que a pessoa preenche `SUPABASE_URL` e `SUPABASE_ANON_KEY` no topo do
  script — ver [design.md](design.md).
- Lista atualiza automaticamente quando alguém salva um checklist em outra máquina (Supabase
  Realtime), sem precisar dar F5.

## Fora de escopo (por decisão do usuário)
- Login com e-mail/senha.
- Controle de permissão por usuário (qualquer pessoa com o link pode ver/editar qualquer
  checklist — é uma ferramenta interna de equipe).
- Histórico de versões / auditoria de alterações campo a campo.
