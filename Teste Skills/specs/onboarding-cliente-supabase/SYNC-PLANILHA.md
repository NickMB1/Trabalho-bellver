# Sincronizar checklists com uma planilha Google Sheets

Objetivo: os checklists da tabela `checklists` no Supabase aparecem automaticamente
numa planilha do Google Sheets — uma linha por checklist, atualizada pelo `id`
(edição não duplica a linha). Cada checklist vai para a aba correspondente ao seu
**tipo de processo** (campo "Tipo de processo" na primeira aba do formulário):

| Tipo de processo (no site) | Aba na planilha    |
| --------------------------- | ------------------- |
| Novo cliente                 | Novas empresas       |
| Abertura                     | Aberturas            |
| Alteração                    | Alterações           |
| Transformação                | Transformação        |
| (sem tipo definido)          | Sem tipo definido    |

> Se o tipo de processo de um checklist for alterado depois de já ter sincronizado,
> a linha antiga na aba anterior não é removida automaticamente (fica órfã) — o
> registro passa a ser mantido só na aba do novo tipo a partir da próxima
> sincronização. Nesses casos, apague manualmente a linha antiga na aba anterior.

Como funciona: um **Google Apps Script** vinculado à planilha busca periodicamente
(a cada 1 minuto, via gatilho de tempo) todos os checklists direto da API REST do
Supabase e atualiza/insere a linha de cada um.

> Por que polling e não webhook do Supabase? A forma "instantânea" seria um
> Database Webhook do Supabase chamando o script a cada INSERT/UPDATE. Mas esse
> projeto está sem o schema interno `supabase_functions` (normalmente vem pronto
> em todo projeto Supabase — só falta quando o banco foi restaurado/migrado por
> SQL em vez de criado do zero pela plataforma), e recriar esse schema manualmente
> envolve mexer em internals do Postgres que a Supabase gerencia — arriscado demais
> para fazer por fora. O polling evita esse problema inteiro: não depende de
> nenhum schema/extensão especial, só da API REST pública (que já está em uso no
> site). O preço é um atraso de até 1 minuto em vez de instantâneo.

Planilha já configurada: **Checklists Onboarding - Sync**
(`https://docs.google.com/spreadsheets/d/1TnEe39sYiejDW5iKEkmIB7kaFxnZ6yDfK2lJ6PgFLik/edit`),
uma aba por tipo de processo (ver tabela acima). O projeto de Apps Script se chama
**Sync Checklists -> Planilha** (Extensões → Apps Script dentro dessa planilha). As
abas são criadas automaticamente na primeira sincronização — não precisa criá-las
à mão.

## Se precisar recriar do zero

1. Crie/abra a planilha → **Extensões → Apps Script**.
2. Cole o conteúdo de [`sync-planilha.gs`](sync-planilha.gs) desta pasta (já vem
   com a URL e a chave `anon` do projeto Supabase preenchidas — mesmas de
   `Site/config.js`, que são públicas por design).
3. Salve (ícone de disquete ou Ctrl+S).
4. No seletor de função (barra de cima, ao lado de "Depuração"), escolha
   **`criarGatilho`** e clique em **Executar**. Na primeira vez o Google vai
   pedir autorização (acesso à internet + gerenciar gatilhos) — como é seu
   próprio script, aceite ("Avançado" → "Acessar [nome do projeto] (não
   seguro)" caso apareça o aviso padrão de app não verificado). Isso instala
   o gatilho automático de 1 em 1 minuto — só precisa rodar uma vez.
5. (Opcional) Escolha **`syncFromSupabase`** e clique em **Executar** para
   popular a planilha imediatamente, sem esperar o próximo minuto.

## Testar

1. Abra `onboarding-cliente.html`, crie ou edite um checklist e defina o
   "Tipo de processo" na primeira aba do formulário.
2. Espere até 1 minuto (ou rode `syncFromSupabase` manualmente no Apps Script
   para forçar agora) — a linha correspondente aparece/atualiza na aba da
   planilha referente ao tipo de processo escolhido.
3. Editar de novo um checklist já sincronizado atualiza a mesma linha (chave =
   `id`), não cria uma linha nova.
4. Para ver erros: no editor do Apps Script, ícone de relógio (esquerda) →
   **Execuções**, mostra o histórico e qualquer falha de `syncFromSupabase`.

## Ajustar a frequência

Em `criarGatilho()`, troque `.everyMinutes(1)` por `.everyMinutes(1|5|10|15|30)`
ou `.everyHours(n)` e rode a função de novo (ela remove o gatilho antigo antes de
criar o novo, então não duplica).

## Colunas da planilha

`nome_cliente, cnpj, tipo_processo, situacao_processo, criado_por, atualizado_por,
data_abertura, data_liberacao_junta_comercial, competencia_inicial, socio_nome,
socio_cpf, socio_telefone, socio_email, funcionarios_possui, funcionarios_qtd,
anexos, created_at, updated_at`

Existe também uma coluna `id` na coluna A, mas ela fica **oculta** — não é pensada
para leitura pelas pessoas que usam a planilha, só existe para a sincronização saber
qual linha atualizar (em vez de duplicar) a cada rodada. Para ver/editar essa coluna,
selecione as colunas ao redor dela e use Formatar → Colunas → Reexibir colunas.
