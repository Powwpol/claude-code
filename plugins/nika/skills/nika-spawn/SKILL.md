---
name: Nika Spawn
description: This skill activates when the user mentions "spawn", "relaunch", "new instance", "context full", "handoff", "relancer", "nouvelle instance", "reprendre", or needs to save state and launch a fresh Claude Code instance to continue work.
version: 1.0.0
---

# Nika Spawn — Instance Lifecycle Management

## Overview

Le système de spawn/relaunch permet de sauvegarder l'état complet d'une session,
lancer une nouvelle instance de Claude Code, et reprendre exactement où on s'était arrêté.

C'est le mécanisme de **survie** de Nika quand le contexte se remplit.

## Quand spawner ?

| Situation | Action |
|-----------|--------|
| Contexte à 50% | ⚠️ Warning — commence à penser au handoff |
| Contexte à 60% | 🔶 Prépare le handoff brief automatiquement |
| Contexte à 75% | 🔴 Spawn immédiat recommandé |
| Tâche terminée, nouvelle tâche lourde | Spawn propre pour contexte frais |
| Changement de domaine complet | Spawn pour nettoyer le contexte |

## Workflow de spawn

### 1. Préparer le handoff

```bash
# Via le script
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/save_state.py

# Ou via la commande
/handoff
```

Ceci produit :
- `.claude/state/handoff-brief.md` — résumé pour la prochaine instance
- `.claude/state/session-meta.json` — métadonnées de session

### 2. Spawner la nouvelle instance

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/spawn_instance.sh
```

Ce script :
1. Vérifie que le handoff brief existe
2. Lance `claude` avec le contexte du handoff brief injecté
3. La nouvelle instance charge automatiquement le brief via le hook SessionStart

### 3. Reprise automatique

Le hook SessionStart de la nouvelle instance :
1. Détecte le handoff brief dans `.claude/state/`
2. L'injecte comme contexte additionnel
3. La nouvelle instance reprend avec toutes les informations

## Handoff Brief Format

```markdown
# Handoff Brief — 2024-01-15 14:30:00

## Tâche en cours
Implémentation du système d'authentification OAuth2

## Décisions prises
- Utiliser PKCE flow pour le SPA
- Stocker les tokens dans httpOnly cookies
- Refresh token rotation activée

## Fichiers modifiés cette session
- src/auth/oauth.ts — Nouveau provider OAuth2
- src/middleware/auth.ts — Middleware de vérification
- .env.example — Ajouté les variables OAuth

## Prochaines étapes
1. Implémenter le callback handler
2. Ajouter les tests pour le flow PKCE
3. Mettre à jour la documentation API

## Contexte important
- Le endpoint /api/auth/callback existe mais est vide
- La base de données a une table `sessions` mais pas encore `refresh_tokens`
- Le front-end attend un cookie `auth_token` (pas un header Authorization)

## État git
- Branch: feature/oauth2-auth
- 3 commits non poussés
- Fichiers non commités: src/auth/oauth.ts
```

## Scripts

### save_state.py

Sauvegarde automatique de l'état :
- Récupère git status, branch, recent commits
- Lit le log d'exécution
- Récupère les mémoires persistantes
- Produit le handoff brief et les métadonnées

### spawn_instance.sh

Lance une nouvelle instance :
- Vérifie les prérequis
- Passe le handoff brief comme prompt initial
- Gère les notifications desktop

### check_context.py

Monitoring du contexte :
- Estime l'utilisation du contexte
- Émet des alertes selon les seuils
- Recommande des actions (rien, warning, handoff, spawn)
