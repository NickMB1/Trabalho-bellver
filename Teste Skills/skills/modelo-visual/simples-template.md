---
name: simples-nacional-template
description: Standard compact single-screen HTML template to use for every Simples Nacional document the user sends
metadata:
  node_type: memory
  type: feedback
  modified: 2026-08-03
---

The visual source of truth is `.claude/skills/modelo-visual/template.html` — a literal HTML/CSS file with `{{PLACEHOLDER}}` tokens, not a prose description to reinterpret. Always copy that file and substitute values into it; never redesign the page from scratch or re-derive colors/layout from this description (that's what caused visual drift between documents — see incident below).

**Why:** The user approved this exact compact, single-screen, responsive design (built 2026-07-31 for BN3 Contabilidade, Junho de 2026) as the template for every future Simples Nacional apuração document and wants every document to share the same aesthetic. On 2026-08-03, generating a document from this file's prose description alone (via the artifact-design/dataviz skills) produced a different palette and layout than the approved one — the fix was converting the template to a literal `template.html` so future generations copy fixed markup/CSS instead of reinventing it.

**How to apply:**
1. Read `.claude/skills/modelo-visual/template.html`.
2. Replace each `{{PLACEHOLDER}}` with real data (see list below). Do not change CSS, class names, layout structure, or the `--s1`..`--s6` / `--blue` / `--accent` color tokens.
3. Splice in the embedded font: replace the `/*__FONT_FACE__*/` marker with the full contents of `.claude/skills/modelo-visual/font-base64.css`. Do this via a script/PowerShell text substitution with explicit UTF-8 encoding (see note below) — never by reading the giant base64 blob into context and retyping it.
4. The donut chart and legend must use the SAME six colors in the SAME fixed order (`--s1` blue → `--s6` violet) regardless of which tax they represent in a given document — color is assigned by legend position (1st tax listed = s1, 2nd = s2, …), not by tax identity, and not re-ordered by value size.
5. Double-check the legend `name`/`val` pairs against the source `.md` before finalizing — a past incident (BN3 and Alfa Consultoria documents, 2026-08) shipped with tax names and values shifted/mismatched relative to each other despite the donut proportions being correct. Sum the six legend values and confirm it equals the DAS total before treating the document as done.

**Placeholder list in `template.html`:**
- `{{EMPRESA_CURTA}}`, `{{PERIODO_EXTENSO}}` — used in `<title>`
- `{{EMPRESA_NOME}}`, `{{CNPJ}}`, `{{ANEXO_TAG}}` — header card
- `{{DAS_VALOR}}`, `{{ALIQUOTA_PCT}}` — destaque card
- `{{FATURAMENTO_MES}}`, `{{FATURAMENTO_12M}}`, `{{FAIXA_ENQUADRAMENTO}}` — stat row
- `{{DONUT_GRADIENT_STOPS}}` — comma-separated `var(--sN) start% end%` stops, cumulative, summing to 100%
- `{{LEGEND_ITEMS}}` — one `<li>` per tax, in the same order as the donut stops
- `{{RODAPE}}` — footer line (e.g. "PGDAS-D · CPF resp. {{cpf}} · Emitido em {{data}}")

**Card opcional — "Ajustes no valor a recolher":**
Approved 2026-08-04 (prototyped and refined against the Horizonte Soluções Administrativas document). Include this card **only if** at least one of these source fields is non-zero: Outros Acréscimos, Outras Deduções, Valor Diferido, Valor Fixo ICMS, Valor Fixo ISS. If all are zero, omit the card entirely — don't insert an empty shell.

Position: immediately after the "Para onde vai o imposto" card, before `<footer>`.

Each field has a fixed sign and color (not derived from the document, always the same):

| Campo | Sinal | Cor (chip e valor) |
|---|---|---|
| Outros Acréscimos | `+` | `var(--s3)` — same green as the Cofins chip |
| Valor Fixo ICMS | `+` | `var(--s3)` |
| Valor Fixo ISS | `+` | `var(--s3)` |
| Outras Deduções | `−` | `var(--s2)` — same red/orange as the CSLL chip |
| Valor Diferido | `−` | `var(--s2)` |

Markup (copy literally; include only the `<li>` for fields that are non-zero in the source — list ALL the `+` items first, then ALL the `−` items; this order is mandatory, it's what makes paired rows line up in the 2-column grid via `grid-auto-flow: column`):

```html
  <div class="card">
    <h2 class="section-title">Ajustes no valor a recolher</h2>
    <ul class="legend adj-grid" style="grid-template-rows: repeat({{N_LINHAS}}, auto);">
      <li><span class="chip pos"></span><span class="name">Outros Acréscimos</span><span class="val pos">+ R$ {{VALOR}}</span></li>
      <li><span class="chip pos"></span><span class="name">Valor Fixo ICMS</span><span class="val pos">+ R$ {{VALOR}}</span></li>
      <li><span class="chip pos"></span><span class="name">Valor Fixo ISS</span><span class="val pos">+ R$ {{VALOR}}</span></li>
      <li><span class="chip neg"></span><span class="name">Outras Deduções</span><span class="val neg">− R$ {{VALOR}}</span></li>
      <li><span class="chip neg"></span><span class="name">Valor Diferido</span><span class="val neg">− R$ {{VALOR}}</span></li>
    </ul>
    <p class="stat-note" style="margin-top: 0.6rem;">Simples Nacional apurado R$ {{SIMPLES_NACIONAL_TOTAL}} → a recolher R$ {{DAS_VALOR}}</p>
  </div>
```

- `{{N_LINHAS}}` = ceil(number of `<li>` included / 2). E.g. 5 items → 3, 4 → 2, 3 → 2, 2 → 1, 1 → 1.
- The CSS for `.adj-grid`, `.chip.pos/.neg`, `.val.pos/.neg` already lives in `template.html`'s `<style>` — don't redefine it per document.
- The `stat-note` below the list needs `style="margin-top: 0.6rem;"` (overriding the class's default `0.2rem`) so its gap from the list matches the gap between the section title and the list above it (`.section-title` has `margin: 0 0 0.6rem`) — without it the note sits too close to the last `<li>`.
- `{{DAS_VALOR}}` in the top destaque card is **always** "Simples Nacional a recolher" (never "Simples Nacional Total") — this was already the rule, but it only becomes visible once adjustments exist and the two values diverge.

**Other rules (unchanged):**
- Cut verbose explanatory paragraphs and any redundant summary sections.
- The artifact's `<title>/<style>/<div class="page">` content already forms a complete `<!doctype html>` document in this template (no extra wrapping needed). Write it as a disposable temp file (`_tmp_<slug>.html`) inside `clientes/`, convert it to PDF with headless Edge, then delete the temp HTML — the final deliverable is `Empresa - Período.pdf` in `clientes/`, not a saved HTML. See `.claude/skills/simplificador-simples/SKILL.md` steps 5-6 for the exact command and the multi-file batching optimization.
- Editing large embedded-font HTML files: never round-trip the file through PowerShell `Get-Content`/`Set-Content` without explicit UTF-8 encoding — Windows PowerShell 5.1 defaults corrupt accented Portuguese characters (mojibake like "â€”"). Use `[System.IO.File]::ReadAllText/WriteAllText` with explicit `UTF8Encoding` instead.
