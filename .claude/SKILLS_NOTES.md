# SKILLS_NOTES

## 1. Skills instaladas em `.claude/skills/` (vendorizadas, **não versionadas**)

`.claude/skills/` está no `.gitignore` — é código de terceiros baixado localmente.
Para recriar num clone novo, rode o script de sync abaixo (ou os comandos manuais).

### Repos-fonte

| Origem | O que foi copiado | Skills |
|---|---|---|
| https://github.com/anthropics/skills | curadoria frontend/design (de ~19 disponíveis) | `frontend-design`, `brand-guidelines`, `theme-factory`, `web-artifacts-builder`, `canvas-design` |
| https://github.com/emilkowalski/skills | todas (`skills/*`) | `animate`, `animate-expo`, `animation-vocabulary`, `apple-design`, `ask-sonner`, `emil-design-eng`, `find-animation-opportunities`, `improve-animations`, `pick-ui-library`, `prototype`, `review-animations`, `write-swift` |
| https://github.com/mattpocock/skills | todas (`skills/**`, achatadas) | `ask-matt`, `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `grill-with-docs`, `implement`, `improve-codebase-architecture`, `prototype-matt`, `research`, `resolving-merge-conflicts`, `setup-matt-pocock-skills`, `tdd`, `to-spec`, `to-tickets`, `triage`, `wayfinder`, `wizard`, `claude-handoff`, `implement-spec`, `loop-me`, `retro`, `setup-ts-deep-modules`, `writing-beats`, `writing-fragments`, `writing-shape`, `git-guardrails-claude-code`, `migrate-to-shoehorn`, `scaffold-exercises`, `setup-pre-commit`, `grill-me`, `grilling`, `handoff`, `teach`, `to-questionnaire`, `wait-what`, `writing-for-agents` |
| https://github.com/pbakaus/impeccable | 1, deduplicada (repo replica em ~17 pastas de agentes; usar a versão `.claude/`) | `impeccable` (+ `reference/` e `scripts/`) |
| https://github.com/DietrichGebert/ponytail | todas (`skills/*`) | `ponytail`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`, `ponytail-review` |

### Colisões de nome resolvidas
- `prototype` existe em emilkowalski **e** mattpocock → a do mattpocock foi renomeada para `prototype-matt`.
- `code-review` (mattpocock) tem o mesmo nome do comando embutido do Claude Code; a skill do projeto pode sombrear — renomear se atrapalhar.

### Script de sync (bash / git-bash no Windows)

```bash
#!/usr/bin/env bash
set -euo pipefail
DEST="$(git rev-parse --show-toplevel)/.claude/skills"
TMP="$(mktemp -d)"
mkdir -p "$DEST"
trap 'rm -rf "$TMP"' EXIT

git clone --depth 1 https://github.com/anthropics/skills        "$TMP/anthropics"
git clone --depth 1 https://github.com/emilkowalski/skills      "$TMP/emil"
git clone --depth 1 https://github.com/mattpocock/skills        "$TMP/matt"
git clone --depth 1 https://github.com/pbakaus/impeccable       "$TMP/impeccable"
git clone --depth 1 https://github.com/DietrichGebert/ponytail  "$TMP/ponytail"

# anthropics — curadoria
for s in frontend-design brand-guidelines theme-factory web-artifacts-builder canvas-design; do
  cp -R "$TMP/anthropics/skills/$s" "$DEST/$s"
done

# emilkowalski — todas
for d in "$TMP"/emil/skills/*/; do
  [ -f "$d/SKILL.md" ] && cp -R "${d%/}" "$DEST/$(basename "$d")"
done

# mattpocock — todas (achatadas); resolve colisão prototype -> prototype-matt
find "$TMP/matt/skills" -name SKILL.md -not -path '*/.git/*' | while read -r f; do
  src="$(dirname "$f")"; base="$(basename "$src")"
  [ -e "$DEST/$base" ] && base="${base}-matt"
  cp -R "$src" "$DEST/$base"
done

# pbakaus/impeccable — só a versão .claude/
cp -R "$TMP/impeccable/.claude/skills/impeccable" "$DEST/impeccable"

# DietrichGebert/ponytail — todas
for d in "$TMP"/ponytail/skills/*/; do
  [ -f "$d/SKILL.md" ] && cp -R "${d%/}" "$DEST/$(basename "$d")"
done

echo "OK — $(find "$DEST" -maxdepth 1 -mindepth 1 -type d | wc -l) skills em $DEST"
```

---

## 2. Ferramentas de referência (nem skill nem MCP)

Projetos/serviços externos para ter à mão durante o desenvolvimento (clonagem de UI,
screenshot-to-code, geração 3D a partir de imagem, roteamento de LLM, etc.).

| Ferramenta | Link | Para que serve |
|---|---|---|
| screenshot-to-code | https://github.com/abi/screenshot-to-code | Converte um screenshot / mockup / URL em código (HTML+Tailwind, React, Vue, etc.) usando modelos de visão. |
| ai-website-cloner-template | https://github.com/JCodesMore/ai-website-cloner-template | Template para clonar sites existentes com IA; ponto de partida para um "clonador" próprio. |
| video-use | https://github.com/browser-use/video-use | Transforma um vídeo de navegação em fluxo/automação de browser reproduzível (browser-use). |
| img2threejs | https://github.com/hoainho/img2threejs | Gera uma cena/objeto Three.js a partir de uma imagem. |
| OmniRoute | https://github.com/diegosouzapw/OmniRoute | Roteador/gateway para múltiplos provedores de LLM (troca de modelo, fallback, custo). |
| Three.js Skills | https://agenticskills.io/skills/threejs-skills | Coleção de skills focadas em Three.js (referência externa; avaliar importar depois). |
| DESIGN.md Examples for AI Agents | https://styles.refero.design/?q=quiet+luxury | Exemplos de `DESIGN.md` / diretrizes de estilo para agentes de IA (ex.: busca "quiet luxury"). |

### Notas
- Reavaliar "Three.js Skills" — se as pastas expuserem `SKILL.md`, podem ser adicionadas ao
  script de sync acima e copiadas para `.claude/skills/`.
- `screenshot-to-code` e `ai-website-cloner-template` combinam com os MCP servers
  `magic-mcp` e `shadcn-ui` configurados em `.mcp.json`.

---

## 3. MCP servers (`.mcp.json`, **versionado**)

| Server | Pacote | Env var necessária |
|---|---|---|
| `shadcn-ui` | `@jpisnice/shadcn-ui-mcp-server` | `GITHUB_PERSONAL_ACCESS_TOKEN` (opcional; sem ele = 60 req/h, com ele = 5000 req/h) |
| `magic-mcp` | `@21st-dev/magic@latest` | `TWENTY_FIRST_API_KEY` (chave em https://21st.dev/mcp) |

Exportar as env vars antes de abrir o projeto; o Claude Code pede aprovação para carregar
os servers do `.mcp.json` na primeira vez.
