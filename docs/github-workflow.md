# GitHub synchronization workflow

The local archive is the source of truth until repository write permission is restored. No remote branch or pull request was created.

```powershell
cd D:\WeatherSentinel
git init
git remote add origin https://github.com/Itzx-kush/WeatherSentinel.git
git fetch origin
git checkout -b feature/project-foundation
git add .
git status
git commit -m "Initialize WeatherSentinel architecture and Part 1 data foundation"
git push -u origin feature/project-foundation
```

Then open a pull request from `feature/project-foundation` to `main`. Before pushing, inspect `git diff --cached`, confirm that `.env`, `.venv`, credentials, caches, and generated outputs are absent, and rerun `scripts/test.ps1`.

Because the remote currently contains an independent initial README commit, do not force-push. If Git reports unrelated histories, create the branch from fetched `origin/main`, copy these verified files into that checkout, and commit normally.
