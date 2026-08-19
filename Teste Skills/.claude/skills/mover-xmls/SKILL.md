---
name: mover-xmls
description: Move os arquivos de uma competência (XML e tudo que estiver junto, como o PDF pareado) que ficaram estacionados dentro da árvore "XML/<empresa>/<ano>/<mes>/..." de uma pasta de mês errada, para a mesma estrutura de subpastas dentro da pasta do mês correto, limpando as pastas vazias que sobrarem na origem. Use sempre que o usuário disser algo como "na pasta do mês X tem XMLs da competência Y, mova para a pasta do mês Y" — não é uma movimentação simples de arquivos soltos: preserva a árvore de subpastas e move os arquivos pareados junto (peça confirmação se não estiver claro se deve levar arquivos não-XML como PDF).
---

# mover-xmls

Localiza, dentro da árvore de uma pasta de mês (padrão observado nas
pastas de clientes: `.../<MM-AAAA>/XML/<empresa>/<ano>/<mes>/...`), a
subpasta de uma competência específica que ficou estacionada no lugar
errado, e move **todo o conteúdo dela** (XML, PDF, qualquer arquivo,
preservando subpastas como "Recebidas"/"Emitidas") para o mesmo caminho
relativo dentro da pasta do mês correto — usando o script
`scripts/mover_xmls.py`, não movendo arquivos manualmente um a um.

## Entrada esperada

- `origem`: pasta do mês onde os arquivos estão mal posicionados (ex.:
  `.../ALTITUDE DIGITAL/2026/06-2026`). Pergunte ao usuário se não foi
  informada.
- `destino`: pasta do mês correto para aquela competência (ex.:
  `.../ALTITUDE DIGITAL/2026/07-2026`). Pergunte ao usuário se não foi
  informada.
- `competência` (mês, e ano se não for óbvio pelo nome da pasta de
  origem): qual competência mover. Pergunte ao usuário se não ficou claro
  na mensagem original (ex.: "competência 7" → mês 07).

**Antes de mover, confirme com o usuário se arquivos não-XML pareados com
o mesmo nome (tipicamente o PDF/DANFSe da mesma nota) devem ir junto** —
o script sempre move a pasta inteira daquela competência (todos os tipos
de arquivo), então avise que é isso que vai acontecer e pergunte se é o
esperado, a menos que o usuário já tenha deixado isso explícito.

## Como usar

```
python <diretório-desta-skill>/scripts/mover_xmls.py --origem <pasta-mes-origem> --destino <pasta-mes-destino> --competencia <MM>/<AAAA>
```

Exemplo (competência 07/2026, pasta de origem contém o ano no nome):

```
python <diretório-desta-skill>/scripts/mover_xmls.py --origem ".../06-2026" --destino ".../07-2026" --competencia 07
```

Se `--competencia` vier só com o mês (ex.: `07`), o script tenta inferir
o ano a partir do nome da pasta `--origem` (ex.: `06-2026` → ano 2026).
Se não conseguir, passe `--ano` explicitamente.

O script:

- Procura recursivamente, dentro de `origem`, qualquer subpasta cujo nome
  seja o mês (2 dígitos) e cujo pai tenha o nome do ano (4 dígitos) —
  ex.: `.../XML/<empresa>/2026/07`. Pode haver mais de uma ocorrência
  (várias empresas), todas são processadas.
- Move **a pasta inteira** encontrada (arquivos de qualquer tipo e
  subpastas como "Recebidas") para o mesmo caminho relativo dentro de
  `destino`, criando as pastas necessárias.
- Se a pasta de destino correspondente já existir, mescla arquivo a
  arquivo em vez de sobrescrever a pasta.
- Se algum arquivo de mesmo nome já existir no destino, **não
  sobrescreve** — pula e lista em "conflitos"; nesse caso a pasta de
  origem correspondente não é removida, mesmo que quase vazia.
- Depois de mover com sucesso (sem conflitos), remove as pastas que
  ficaram vazias do lado da origem, subindo na árvore até (mas sem
  remover) a pasta `origem` informada.

Use `--dry-run` para conferir antes o que seria movido/removido, sem
tocar em nenhum arquivo:

```
python <diretório-desta-skill>/scripts/mover_xmls.py --origem <pasta-mes-origem> --destino <pasta-mes-destino> --competencia 07/2026 --dry-run
```

## Depois de rodar

Repasse ao usuário o resumo que o script já imprime: quantos arquivos
foram movidos, quais tiveram conflito (não foram movidos) e quais pastas
vazias foram removidas. Se nenhuma pasta da competência informada for
encontrada dentro de `origem`, reporte isso diretamente em vez de seguir
como se tivesse funcionado — pode ser sinal de competência/ano errados ou
de estrutura de pastas diferente da esperada.
