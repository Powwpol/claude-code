---
description: Prépare un handoff brief sans spawner de nouvelle instance — sauvegarde l'état pour reprise ultérieure
allowed-tools: Bash, Read, Write, Glob, Grep
---

# /handoff — Préparer un Handoff Brief

Sauvegarde l'état complet de la session courante pour permettre la reprise par une future instance.

## Process

### 1. Collecter l'état git

```bash
git branch --show-current 2>/dev/null
git status --short 2>/dev/null
git log --oneline -5 2>/dev/null
git stash list 2>/dev/null
```

### 2. Lire le log d'exécution

```bash
cat .claude/state/execution-log.jsonl 2>/dev/null || echo "Pas de log"
```

### 3. Lire les mémoires persistantes

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/memory.py dump
```

### 4. Lire les cron jobs en attente

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/core/cron.py list
```

### 5. Construire le handoff brief

Écris un fichier `.claude/state/handoff-brief.md` avec :

```markdown
# Handoff Brief — [date et heure ISO]

## Tâche en cours
[Résumé de la tâche principale de cette session]

## Décisions prises
- [Chaque décision importante avec son rationnel]

## Fichiers modifiés cette session
[Liste extraite du execution-log.jsonl]

## Prochaines étapes
1. [Étape immédiate suivante]
2. [...]

## Contexte important
[Tout ce que la prochaine instance doit absolument savoir]

## Mémoires clés
[Résumé des entries les plus importantes de nika-memory]

## État git
- Branch: [branche courante]
- Commits non poussés: [oui/non + count]
- Fichiers non commités: [liste]

## Cron jobs actifs
[Liste des jobs actifs avec leur schedule]
```

### 6. Sauvegarder les métadonnées

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/save_state.py
```

### 7. Confirmer

Affiche un résumé du handoff brief et confirme que la sauvegarde est complète.

Indique à l'utilisateur :
- Pour spawner maintenant : `bash ${CLAUDE_PLUGIN_ROOT}/scripts/spawn_instance.sh`
- Pour reprendre plus tard : le hook SessionStart chargera automatiquement le brief
