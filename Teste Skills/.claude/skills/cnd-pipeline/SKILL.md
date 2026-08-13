---
name: cnd-pipeline
description: Orquestra a emissão completa das Certidões Negativas de Débitos (CND) de uma empresa — federal, estadual e municipal — a partir do CNPJ e do município/UF informados, chamando em sequência as skills cnd-federal, cnd-estadual e cnd-municipal e consolidando um relatório final que avisa explicitamente quais certidões não puderam ser geradas. Use esta skill como ponto de entrada sempre que o usuário pedir "as certidões negativas de uma empresa", "CND federal, estadual e municipal", "situação fiscal completa do CNPJ", ou peça o fluxo inteiro em vez de uma certidão isolada.
---

# cnd-pipeline

Esta skill não acessa nenhum portal sozinha — ela é o maestro que chama, em
sequência, as 3 skills especializadas:

```
cnd-federal  →  cnd-estadual  →  cnd-municipal
```

Cada uma delas abre um portal governamental diferente via `claude-in-chrome`
e baixa um PDF. Ao final, esta skill consolida o resultado e **avisa
claramente quais certidões não foram geradas e por quê** — esse aviso final
é o requisito mais importante do fluxo, não um detalhe opcional.

## Passo a passo

1. **Colete e confirme a entrada** com o usuário, se faltar algo:
   - `cnpj` — obrigatório.
   - `municipio` e `uf` — obrigatórios. Se o usuário só der o nome do
     município sem a UF, pergunte a UF explicitamente (necessária para
     escolher o portal estadual e desambiguar municípios homônimos em
     estados diferentes).
   - `output_dir` — **sempre pergunte** onde salvar os PDFs antes de
     começar (ex.: sugestão padrão `CND/<cnpj>/` dentro do diretório atual,
     mas confirme com o usuário em vez de assumir).
   - Opcionalmente, `inscricao_estadual` e `inscricao_municipal`, caso o
     usuário já tenha essas informações à mão — algumas SEFAZ/prefeituras
     exigem em vez do CNPJ puro (as skills individuais avisam quando isso
     acontece).

2. **Valide o CNPJ** rodando:
   ```
   python <diretório-desta-skill>/scripts/validar_cnpj.py <cnpj>
   ```
   Se o script falhar (exit code 1), pare aqui e avise o usuário do motivo
   — não adianta tentar emitir certidão de um CNPJ com dígito verificador
   inválido.

3. **Avise o usuário sobre a automação de navegador** antes de começar (só
   na primeira vez da conversa): as 3 skills seguintes abrem abas reais no
   Chrome dele via `claude-in-chrome`, e podem pedir para ele resolver
   manualmente algum CAPTCHA visual que aparecer.

4. **Invoque a skill `cnd-federal`** passando `cnpj` e
   `output_dir/federal.pdf`. Guarde o `status` e o resultado retornado.

5. **Invoque a skill `cnd-estadual`** passando `cnpj`, `uf`,
   `inscricao_estadual` (se houver) e `output_dir/estadual_<uf>.pdf`.
   Guarde `status` e resultado.

6. **Invoque a skill `cnd-municipal`** passando `cnpj`, `municipio`, `uf`,
   `inscricao_municipal` (se houver) e `output_dir/municipal.pdf`. Guarde
   `status` e resultado.

   Sempre execute as 3 etapas mesmo que uma anterior falhe — a falha em
   uma esfera (ex.: municipal indisponível) não impede as outras.

7. **Monte o relatório final**, sempre no mesmo formato, uma linha por
   esfera:

   | Esfera | Status | Resultado | Arquivo |
   |---|---|---|---|
   | Federal | ✅ Emitida | Negativa / Positiva com efeito de negativa / Positiva | caminho do PDF |
   | Estadual | ✅ Emitida / ❌ Indisponível | resultado ou motivo | caminho do PDF ou — |
   | Municipal | ✅ Emitida / ❌ Indisponível | resultado ou motivo | caminho do PDF ou — |

   Logo abaixo da tabela, **liste em destaque** (não só na tabela) cada
   certidão que ficou indisponível, com o motivo relatado pela skill
   correspondente, para garantir que o usuário não passe batido por essa
   informação. Se as 3 certidões foram emitidas com sucesso, diga isso
   explicitamente também.

## Por que chamar as skills em vez de acessar os portais direto

Cada skill de esfera carrega o conhecimento específico daquele passo (URL
fixa e estável no caso federal; como localizar via busca web e validar
domínio oficial nos casos estadual/municipal; como tratar exigência de
Inscrição Estadual/Municipal; como lidar com CAPTCHA sem tentar
contorná-lo). Invocar a skill garante que essas regras sejam seguidas
mesmo que este orquestrador não repita todos os detalhes.

## Limitações conhecidas

- Não existe API oficial para nenhuma das 3 certidões — tudo depende de
  automação de navegador em portais públicos, então falhas pontuais
  (CAPTCHA, manutenção, mudança de layout do site) são esperadas e não
  indicam bug nas skills.
- A certidão municipal é a que mais frequentemente fica indisponível: boa
  parte dos municípios brasileiros não tem emissão online. Isso é normal.
- Esta skill nunca tenta contornar CAPTCHA visual, criar cadastro/login em
  nome do usuário, ou adivinhar Inscrição Estadual/Municipal — sempre pede
  para o usuário resolver ou fornecer o dado.
