# Git Flow — BlueChat Branching Strategy

## Branch overview

| Branch | Purpose | Merges into | Protected? |
|---|---|---|---|
| `main` | Production releases only | — | Yes (require PR + review) |
| `develop` | Integration branch for features | `main` (via release) | Yes (require PR) |
| `feature/*` | New features | `develop` | No |
| `release/*` | Release preparation | `main` + `develop` | No |
| `hotfix/*` | Emergency production fixes | `main` + `develop` | No |
| `bugfix/*` | Non-urgent bug fixes | `develop` | No |

---

## Workflow diagrams

```
main      ──●─────────────────────────────●── (v1.1.0)
             \                           /
develop        ●──●──────────────────●──
                   \               /
feature/*           ●──●──●──●────  (feature/gui)
```

```
main      ──●────────────────────────────────●── (v1.2.0)
             \                              /
develop        ●──●──●────────────────●───●
                              \      / ↗
release/1.2.0                  ●──●    (bump version + fix bugs)
```

---

## Daily workflow — adding a new feature

```bash
# 1. Always start from develop
git checkout develop
git pull origin develop

# 2. Create a feature branch
git checkout -b feature/gui-interface

# 3. Work on your feature — commit often
git add .
git commit -m "feat: add main window layout"
git commit -m "feat: add scan button with progress bar"
git commit -m "test: add tests for scan UI"

# 4. Push and open a PR → develop
git push origin feature/gui-interface
# On GitHub: New Pull Request → base: develop, compare: feature/gui-interface

# 5. After PR is approved and merged, delete the branch
git branch -d feature/gui-interface
git push origin --delete feature/gui-interface
```

---

## Releasing — when develop is ready to ship

```bash
# 1. Cut a release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/1.2.0

# 2. Update version number, changelog, final bug fixes ONLY
#    No new features allowed on release branches
vim CHANGELOG.md
git commit -m "chore: bump version to 1.2.0"

# 3. Merge into main (production)
git checkout main
git merge --no-ff release/1.2.0 -m "release: v1.2.0"
git tag -a v1.2.0 -m "v1.2.0 — GUI, notifications, BLE support"
git push origin main --tags

# 4. Back-merge into develop (capture release fixes)
git checkout develop
git merge --no-ff release/1.2.0 -m "chore: back-merge release/1.2.0 into develop"
git push origin develop

# 5. Delete release branch
git branch -d release/1.2.0
git push origin --delete release/1.2.0
```

---

## Hotfix — emergency fix on production

```bash
# 1. Branch from main (not develop!)
git checkout main
git pull origin main
git checkout -b hotfix/crash-on-disconnect

# 2. Fix the bug, commit
git commit -m "fix: prevent crash when remote disconnects mid-call"

# 3. Merge into main + tag
git checkout main
git merge --no-ff hotfix/crash-on-disconnect -m "hotfix: prevent crash on disconnect"
git tag -a v1.1.1 -m "v1.1.1 — hotfix: crash on disconnect"
git push origin main --tags

# 4. Also merge into develop so the fix isn't lost
git checkout develop
git merge --no-ff hotfix/crash-on-disconnect -m "hotfix: back-merge into develop"
git push origin develop

# 5. Clean up
git branch -d hotfix/crash-on-disconnect
```

---

## Commit message convention

Format: `<type>: <short description>`

| Type | When to use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `test` | Adding / fixing tests |
| `docs` | Documentation only |
| `chore` | Build, deps, CI, tooling |
| `refactor` | Code restructure, no behaviour change |
| `hotfix` | Emergency production fix |
| `release` | Version bump / changelog |

---

## GitHub branch protection rules (set in Settings → Branches)

### For `main`:
- Require pull request before merging
- Require 1 approving review
- Require status checks to pass (CI: lint + test)
- Do not allow bypassing the above settings

### For `develop`:
- Require pull request before merging
- Require status checks to pass (CI: lint + test)
