#!/usr/bin/env bash
# ──────────────────────────────────────────────────
# Nika OS — Spawn Instance
#
# Launches a fresh Claude Code instance with the
# handoff brief injected as initial context.
#
# Usage:
#   bash spawn_instance.sh [--no-brief]
# ──────────────────────────────────────────────────

set -euo pipefail

# ── Colors (FA4616 orange) ─────────────────────────
ORANGE='\033[38;2;250;70;22m'
GRAY='\033[38;2;176;176;176m'
RESET='\033[0m'
BOLD='\033[1m'

# ── Find project root ─────────────────────────────
find_root() {
    local dir="$PWD"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.claude" ]; then
            echo "$dir"
            return
        fi
        dir="$(dirname "$dir")"
    done
    echo "$PWD"
}

ROOT="$(find_root)"
STATE_DIR="$ROOT/.claude/state"
HANDOFF_BRIEF="$STATE_DIR/handoff-brief.md"

# ── Banner ─────────────────────────────────────────
echo -e "${BOLD}${ORANGE}"
echo "    ███╗   ██╗██╗██╗  ██╗ █████╗"
echo "    ████╗  ██║██║██║ ██╔╝██╔══██╗"
echo "    ██╔██╗ ██║██║█████╔╝ ███████║"
echo "    ██║╚██╗██║██║██╔═██╗ ██╔══██║"
echo "    ██║ ╚████║██║██║  ██╗██║  ██║"
echo "    ╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝"
echo -e "${RESET}"
echo -e "${GRAY}  Spawning new instance...${RESET}"
echo ""

# ── Check for handoff brief ───────────────────────
if [ ! -f "$HANDOFF_BRIEF" ]; then
    echo -e "${ORANGE}⚠️  Aucun handoff brief trouvé.${RESET}"
    echo -e "${GRAY}  Exécute /handoff d'abord, ou lance sans brief :${RESET}"
    echo ""

    if [ "${1:-}" = "--no-brief" ]; then
        echo -e "${GRAY}  Lancement sans brief...${RESET}"
        PROMPT="Tu es Nika OS. Nouvelle session sans handoff brief. Vérifie la mémoire persistante avec /nika-memory et les cron jobs avec /nika-cron."
    else
        echo -e "${GRAY}  Pour forcer: bash spawn_instance.sh --no-brief${RESET}"
        exit 1
    fi
else
    echo -e "${ORANGE}● Handoff brief trouvé${RESET}"
    echo -e "${GRAY}  $(wc -l < "$HANDOFF_BRIEF") lignes de contexte${RESET}"
    echo ""

    # Read the brief and use it as the initial prompt
    BRIEF_CONTENT="$(cat "$HANDOFF_BRIEF")"
    PROMPT="Tu es Nika OS. Voici le handoff brief de la session précédente, reprends là où elle s'est arrêtée :

---

$BRIEF_CONTENT

---

Lis le brief, charge la mémoire persistante, et reprends le travail."
fi

# ── Notify ─────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/notify.sh" "Nika OS" "Nouvelle instance en cours de lancement..." 2>/dev/null || true

# ── Spawn ──────────────────────────────────────────
echo -e "${ORANGE}● Lancement de claude...${RESET}"
echo ""

# Check if claude command exists
if command -v claude &>/dev/null; then
    exec claude --print "$PROMPT"
else
    echo -e "${ORANGE}❌ Commande 'claude' non trouvée.${RESET}"
    echo -e "${GRAY}  Installe Claude Code: npm install -g @anthropic-ai/claude-code${RESET}"
    echo ""
    echo -e "${GRAY}  En attendant, le prompt pour la nouvelle session :${RESET}"
    echo ""
    echo "─────────────────────────────────────────────"
    echo "$PROMPT"
    echo "─────────────────────────────────────────────"
    exit 1
fi
