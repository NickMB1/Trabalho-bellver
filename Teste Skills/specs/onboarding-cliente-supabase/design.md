# Design — Onboarding de Cliente online (Supabase)

## Arquitetura
Continua sendo um único arquivo estático `onboarding-cliente.html` (sem build, sem servidor).
Ele carrega a biblioteca `supabase-js` via CDN e fala diretamente com o Supabase (Postgres +
Realtime) usando a chave `anon` (pública). Não existe backend próprio.

```
onboarding-cliente.html  ──fetch/insert/update──>  Supabase (Postgres)
                          <──realtime (websocket)──
```

## Tela única, dois "modos"
O arquivo passa a ter duas telas dentro do mesmo HTML, alternadas por JS (`hidden`):

- **`#listScreen`** (tela inicial) — campo "Seu nome", botão "+ Novo checklist", botão
  "Atualizar" e a lista de checklists salvos (cliente, CNPJ, criado por, atualizado em, %).
- **`#formScreen`** — a ficha que já existia (abas Checklist / Sócio / Funcionários / Anexo),
  com um botão **Salvar** novo e um botão **Voltar** para a lista.

## Modelo de dados (Supabase / Postgres)
Tabela `checklists`, ver [schema.sql](schema.sql):

| coluna          | tipo        | descrição                                            |
|------------------|-------------|-------------------------------------------------------|
| id               | uuid (PK)   | gerado automaticamente                                 |
| created_at       | timestamptz | quando o checklist foi criado                          |
| updated_at       | timestamptz | atualizado automaticamente a cada save (trigger)        |
| criado_por       | text        | nome informado por quem criou o checklist               |
| atualizado_por   | text        | nome informado por quem fez a última alteração          |
| nome_cliente     | text        | espelha o campo "Razão Social" da ficha (para a lista)  |
| cnpj             | text        | espelha o campo "CNPJ" da ficha (para a lista)          |
| dados            | jsonb       | todo o resto da ficha (itens, sócio, funcionários, anexos) |

Guardar `nome_cliente`/`cnpj` como colunas soltas (além de estarem implícitos em `dados`)
permite listar/ordenar sem precisar processar o JSON no cliente.

O formato de `dados`:
```json
{
  "itens": {
    "contrato": { "checked": true, "valor": "10/01/2026" },
    "certificado_digital": { "checked": false, "valor": "" },
    "...": "um registro por item do checklist, chave = data-key do item"
  },
  "socio": { "nome": "", "cpf": "", "telefone": "", "email": "" },
  "funcionarios": { "possui": false, "quantidade": "" },
  "anexos": ["III", "V"]
}
```

## Fluxo
1. Página carrega → lê nome salvo em `localStorage` (`onboarding_user_name`) e preenche o
   campo "Seu nome" → busca todos os checklists (`select * order by updated_at desc`) →
   renderiza a lista.
2. Uma subscription Realtime (`postgres_changes` na tabela `checklists`) refaz a busca
   automaticamente sempre que qualquer pessoa insere/atualiza um checklist — assim quem está
   com a lista aberta em outra máquina vê a mudança sem precisar recarregar.
3. **Novo checklist**: limpa o formulário, `currentRecord = null`, mostra `#formScreen`.
4. **Abrir um checklist da lista**: carrega o JSON salvo nos campos do formulário,
   `currentRecord = <linha vinda do Supabase>`, mostra `#formScreen`.
5. **Salvar**: exige que "Seu nome" esteja preenchido. Monta o payload a partir dos campos do
   formulário. Se `currentRecord` é `null` → `insert` (com `criado_por` = nome atual). Se já
   existe → `update` por `id` (mantém o `criado_por` original, atualiza `atualizado_por` para
   o nome atual). Depois do save, volta para a lista.

## Segurança / RLS
Sem login, então o acesso ao Supabase é feito só com a chave `anon`. As policies em
`schema.sql` liberam `select`/`insert`/`update` para qualquer requisição autenticada com essa
chave — ou seja, **qualquer pessoa que tiver a URL do site e a chave anon consegue ler e
editar todos os checklists**. Isso é aceitável para uma ferramenta interna de equipe, mas:
- Não coloque a chave `service_role` no HTML (só a `anon`).
- Se o site for publicado num domínio público, considere restringir por outros meios (ex.:
  Cloudflare Access, VPN, ou rede interna), já que a chave `anon` sozinha não tem senha.

## Configuração (o que falta para funcionar)
`onboarding-cliente.html` é um HTML estático aberto direto no navegador — não existe processo
de build, então ele **não lê `.env`** (isso só funcionaria com Node/Vite/etc.). Quem alimenta
as chaves é um arquivo `config.js`, carregado por `<script src="config.js">` antes do script
principal:

1. Copie `config.example.js` para `config.js` (mesma pasta do HTML).
2. Preencha com os valores de **Project Settings → API** no painel do Supabase:
   ```js
   window.SUPABASE_URL = 'https://xxxxx.supabase.co';
   window.SUPABASE_ANON_KEY = 'chave-anon-publica';
   ```
3. Rode o [schema.sql](schema.sql) uma vez no SQL Editor do projeto.

O `.env` na raiz do projeto existe só como anotação/backup dos mesmos valores — o site não o
lê. Sem `config.js` preenchido, a tela de lista mostra um aviso e os botões de salvar ficam
bloqueados.
