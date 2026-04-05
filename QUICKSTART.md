# Quick Start Guide

## 30-Second Setup

```bash
cd ~/copilot-changelog-digest
python3 -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -q -r requirements.txt
python3 src/main.py --days 7 --repo .
```

**Done!** You'll see a markdown report of the most important Copilot updates for your repo.

## Common Commands

```bash
# Analyze last 7 days (default)
python3 src/main.py --repo .

# Analyze last 30 days
python3 src/main.py --days 30 --repo .

# Output as JSON instead of markdown
python3 src/main.py --output json

# Analyze a different repository
python3 src/main.py --repo ~/my-other-project

# Run integration tests
python3 tests/test_integration.py
```

## What the Report Contains

✅ **Top 5 most impactful Copilot updates** (ranked by your workflow)  
✅ **Why each matters to YOUR tech stack** (Python, Node, Go, etc.)  
✅ **How much time it could save** (estimated impact)  
✅ **Links to official documentation**  

## Example Report Output

```markdown
# Copilot Changelog Update - my-project

**Most important Copilot updates in the last 7 days** | Generated: 2026-04-05 10:59 UTC

## Summary
Found **5 important updates** that could improve your workflow.
Below are the most impactful changes, ranked by how much they can benefit YOUR codebase.

## Top Recommendations
1. Release 1.464.0
2. Release 1.463.0
... (continues with detailed analysis)
```

## PowerShell Alternative (Windows/macOS/Linux)

Requires PowerShell 7+:

```powershell
./changelog-skill.ps1 -Days 7 -Repo . -Output markdown
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Python not found` | Install Python 3.9+ from python.org |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `No releases found` | Check internet connection; GitHub API may be down |
| `Empty report` | Releases fetched but have no detailed notes; this is a GitHub API limitation |

## What It Does (5 Steps)

1. **Fetches** recent Copilot releases from GitHub
2. **Analyzes** your repo (tech stack, languages, recent commits)
3. **Scores** each release by how useful it is for YOUR workflow
4. **Generates** actionable explanations grounded in your codebase
5. **Outputs** a focused report (top 5 only, not overwhelming)

## Performance

- Typical execution: **5-15 seconds**
- Network I/O: ~2 API calls
- No external accounts or API keys needed

## For More Details

- See **README.md** for full documentation
- See **IMPLEMENTATION.md** for technical deep-dive
- Run `python3 src/main.py --help` for command help

---

**Ready to use!** Start with `python3 src/main.py --days 7` in your favorite repo.
