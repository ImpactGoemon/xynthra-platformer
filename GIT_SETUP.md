# Git setup (run on your Windows machine)

Version control must be initialized from Windows directly — not through the
assistant's sandbox, which can't write Git's internal files over the mount.
A `.gitignore` is already in place.

## 1. Open a terminal in the project folder

PowerShell or Git Bash, in:
`C:\Users\impac\Documents\Riqui\Proyectos_Personales\Python\Xynthra_Plat`

## 2. Remove the broken `.git` stub the sandbox left behind

PowerShell:
```powershell
Remove-Item -Recurse -Force .git
```
(Git Bash: `rm -rf .git`)

## 3. Initialize and make the first commit

```bash
git init -b main           # older Git: git init && git branch -M main
git config user.name  "Ricardo"
git config user.email "ricardo.aguayo1990@gmail.com"
git add .
git commit -m "Initial commit: engine skeleton + movement (Milestones 1-2)"
```

## 4. Verify

```bash
git status          # caches/__pycache__ should NOT appear (they're ignored)
git log --oneline
```

## Notes

- Commit per milestone, e.g. `git commit -m "Milestone 3: drop-through platforms"`.
- The `Graphics/GandalfHardcore` assets are a paid pack with redistribution
  restrictions. A local or PRIVATE remote is fine; do NOT push them to a PUBLIC
  repo. If you want a public repo, add `Graphics/GandalfHardcore/` to
  `.gitignore` first (the game still runs locally from your own copy).
- `user.name`/`user.email` above are set per-repo; change them if you prefer a
  different commit identity.
