-- Rode este script uma vez no SQL Editor do seu projeto Supabase.

create table if not exists public.checklists (
  id             uuid primary key default gen_random_uuid(),
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  criado_por     text not null,
  atualizado_por text,
  nome_cliente   text,
  cnpj           text,
  dados          jsonb not null default '{}'::jsonb
);

-- mantém updated_at sempre atual a cada alteração
create or replace function public.set_checklists_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_checklists_updated_at on public.checklists;
create trigger trg_checklists_updated_at
before update on public.checklists
for each row execute function public.set_checklists_updated_at();

-- RLS: ferramenta interna sem login -> libera leitura/gravação para quem tiver a chave anon
alter table public.checklists enable row level security;

drop policy if exists "checklists_select_publico" on public.checklists;
create policy "checklists_select_publico" on public.checklists
  for select using (true);

drop policy if exists "checklists_insert_publico" on public.checklists;
create policy "checklists_insert_publico" on public.checklists
  for insert with check (true);

drop policy if exists "checklists_update_publico" on public.checklists;
create policy "checklists_update_publico" on public.checklists
  for update using (true) with check (true);

-- habilita realtime (lista atualiza sozinha quando alguém salva em outra máquina)
alter publication supabase_realtime add table public.checklists;
