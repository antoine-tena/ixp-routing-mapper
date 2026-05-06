pour faire un commit (git commit -m "feat: ")
feat: nouvelle fonctionnalité
fix: correction de bug
refactor: changement interne sans nouveau comportement
style: CSS / formatage (pas de logique)
docs: documentation / README
perf: performance
test: tests
build/ci: tooling
chore: petites tâches, ménage
revert: annule un commit

## Bonnes pratiques de commit

**Privilégier plusieurs petits commits plutôt qu'un gros commit :**
- Grouper les modifications par logique/fonctionnalité, et faire un maximum de commits
- Ne JAMAIS faire un commit de plus de 10 fichiers
- Faire des commits atomiques (une modification = un commit)
- Messages courts et descriptifs (max 50 caractères pour le titre)
- Exemple : au lieu de "feat: add cart system with products and checkout"
  → Faire 3 commits : 
    - "feat: add cart model"
    - "feat: add cart API endpoints"
    - "feat: add checkout flow"

**Ne JAMAIS committer directement sur develop :**
- Toujours créer une branche feature/fix/etc
- Merger via pull request ou merge --no-ff
- Supprimer la branche après merge

respecter ce nommage pour créer une branche : 
exemples :
git branch feature/login-page
git branch feature/add-dark-mode
git branch fix/login-error-message
git branch fix/broken-navbar-link
git branch chore/update-dependencies
git branch chore/configure-eslint
git branch docs/update-readme
git branch style/reformat-css
git branch refactor/simplify-user-auth
git branch hotfix/fix-production-crash
git branch release/v1.0.0

tout en minuscules, pas d'espace (utiliser des tirets ou underscores)
sois explicite : en lisant la branche on doit directement comprendre de quoi il est question