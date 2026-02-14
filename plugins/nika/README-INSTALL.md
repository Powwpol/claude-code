# Nika OS — Installation Guide

## Structure du package

Ce package contient tout ce qu'il faut pour transformer Claude Code en Nika OS
avec gestion native des sub-agents, hooks, et spawn/relaunch.

```
nika/
├── CLAUDE.md                          # Prompt systeme principal
├── settings.json                      # Hooks + permissions (reference)
│
├── agents/                            # Sub-agents (11 total)
│   ├── context-monitor.md             # Surveillance contexte
│   ├── state-saver.md                 # Sauvegarde etat
│   ├── task-executor.md               # Execution isolee
│   ├── researcher.md                  # Recherche read-only
│   ├── verifier.md                    # Verification qualite
│   ├── orchestrator.md                # K8s-like control plane
│   ├── worker.md                      # Worker generique
│   ├── merger.md                      # Merge multi-agent
│   ├── memory-keeper.md               # Gestion memoire
│   ├── cron-scheduler.md              # Gestion cron
│   └── skill-creator.md               # Super-instance auto-gen
│
├── skills/
│   ├── nika-os/SKILL.md               # Skill principal Nika OS
│   └── nika-spawn/SKILL.md            # Skill de spawn/relaunch
│
├── commands/
│   ├── nika.md                        # /nika — orchestration multi-agent
│   ├── nika-spawn.md                  # /nika-spawn — spawn N agents
│   ├── nika-memory.md                 # /nika-memory — gestion memoire
│   ├── nika-cron.md                   # /nika-cron — gestion cron jobs
│   ├── nika-status.md                 # /nika-status — dashboard
│   ├── status.md                      # /status — rapport systeme
│   └── handoff.md                     # /handoff — prepare le handoff
│
├── hooks/
│   └── hooks.json                     # Configuration complete des hooks
│
├── hooks-handlers/
│   ├── session-start.py               # SessionStart: banner + memoire + cron
│   ├── session-end.py                 # Stop: persist memoire
│   └── cron-check.py                  # UserPromptSubmit: check cron jobs
│
├── scripts/
│   ├── check_context.py               # Monitoring contexte (seuils 50/60/75%)
│   ├── save_state.py                  # Sauvegarde etat + handoff brief
│   ├── spawn_instance.sh              # Relance nouvelle instance
│   └── notify.sh                      # Notifications desktop cross-platform
│
├── core/
│   ├── __init__.py
│   ├── colors.py                      # Palette #FA4616 / #F5F5F5
│   ├── memory.py                      # Moteur memoire persistante
│   ├── orchestrator.py                # Moteur orchestration K8s-like
│   ├── prompt_partitioner.py          # Partitionnement de prompts
│   ├── merger.py                      # Fusion resultats multi-agent
│   └── cron.py                        # Systeme cron jobs
│
└── state/                             # Dossier etat (cree automatiquement)
```

## Installation

### Option 1 : Plugin (recommande)

Si le plugin marketplace est disponible, Nika s'installe automatiquement.
Verifie qu'il apparait dans la liste des plugins actifs.

### Option 2 : Installation manuelle dans un projet

```bash
# Depuis la racine de ton projet
cp -r plugins/nika/ .claude/nika/

# Rendre les scripts executables
chmod +x .claude/nika/scripts/*.sh
chmod +x .claude/nika/scripts/*.py

# Creer le dossier state
mkdir -p .claude/state

# Merge les hooks dans ton settings.json existant
# (voir settings.json dans le package pour reference)
```

### Option 3 : Merge avec settings.json existant

Si tu as deja un `.claude/settings.json`, merge manuellement les sections
`hooks` et `permissions` depuis `settings.json` dans ce package.
Les hooks de Nika OS s'ajoutent aux hooks existants.

## Verification

Lance Claude Code dans ton projet et tape :

```
/status
```

Tu devrais voir le rapport d'etat Nika OS avec :
- Banner Nika
- Etat du contexte
- Memoire persistante
- Cron jobs
- Etat git

## Utilisation

### Commandes slash

| Commande         | Description                                  |
|-----------------|----------------------------------------------|
| `/nika <tache>` | Orchestration multi-agent sur une tache      |
| `/nika-spawn`   | Spawn N agents en parallele                  |
| `/status`       | Rapport d'etat systeme complet               |
| `/handoff`      | Prepare un handoff brief sans spawner        |
| `/nika-memory`  | Gestion memoire persistante                  |
| `/nika-cron`    | Gestion des cron jobs                        |

### Sub-agents

Invoque-les explicitement :

```
Utilise le sub-agent researcher pour investiguer comment fonctionne l'authentification.
Utilise le sub-agent task-executor pour implementer la feature X.
Utilise le sub-agent verifier pour valider les changements.
```

### Hooks automatiques

Les hooks fonctionnent automatiquement :

- **SessionStart** : charge le handoff brief, affiche le banner, init contexte
- **PreToolUse (Bash)** : verifie le contexte + bloque les commandes dangereuses
- **PostToolUse (Write|Edit)** : log les fichiers modifies
- **Stop** : sauvegarde l'etat + notification desktop
- **SubagentStop** : notification quand un sub-agent termine
- **PreCompact** : sauvegarde avant compaction du contexte

### Workflow spawn automatique

```
1. Tu travailles normalement dans Claude Code
2. Le contexte atteint 50% -> Hook affiche un warning
3. Tu continues -> Le contexte atteint 60% -> Hook affiche URGENCE
4. Tu tapes /handoff pour sauvegarder l'etat
5. Tu executes: bash scripts/spawn_instance.sh
6. Une nouvelle instance demarre et lit le handoff brief
7. La nouvelle instance reprend exactement ou tu en etais
```

## Personnalisation

### Ajuster les seuils de contexte

Edite `scripts/check_context.py` :

```python
THRESHOLDS = {
    "warning": 50,    # Premier avertissement
    "critical": 60,   # Prepare le handoff
    "emergency": 75   # Spawn immediat
}
```

### Ajouter un sub-agent

Cree un fichier `agents/mon-agent.md` :

```markdown
---
name: mon-agent
description: Description pour que Claude sache quand l'utiliser
tools: Read, Write, Bash
model: sonnet
color: yellow
---

Tu es un agent specialise pour...
```

### Ajouter un cron job

```bash
python3 core/cron.py add "mon-job" '{"every_hours": 1}' "Instruction pour l'agent" "user"
```

## Compatibilite

- **Claude Code** : v1.0.41+ (SubagentStop support)
- **OS** : macOS, Linux, Windows (Git Bash/WSL)
- **Python** : 3.8+
- **Prerequis** : `jq` recommande mais pas obligatoire
