# Copilot Changelog Digest

**name:** copilot-changelog-digest  
**description:** Smart changelog analyzer that ranks Copilot updates by workflow impact for your specific tech stack

Get **actionable insights** from Copilot's changelog, ranked by what matters most to *your* workflow.

## What It Does

This skill fetches the latest Copilot feature updates and surfaces the ones most relevant to your repository's tech stack and your work patterns. Instead of reading every changelog entry, you get a **personalized top-5** ranked by practical impact.

### Core Features

1. **Intelligent Ranking** — Uses a 3-dimensional scoring algorithm:
   - **Tech Stack Match** (30%): Does this feature target your languages/frameworks?
   - **Workflow Impact** (50%): Does it save time, prevent errors, or improve code quality?
   - **User Context** (20%): Does it align with your recent coding patterns?

2. **Automated Repository Analysis** — Detects:
   - Primary languages (Python, Node, Go, Rust, etc.)
   - Frameworks (React, Next.js, Vue, Django, etc.)
   - Development patterns (testing, debugging, refactoring focus)

3. **Customizable Time Windows** — Check changes from:
   - Last 7 days (default)
   - Last 30 days
   - Custom range (e.g., `--days 14`)

4. **Production-Ready Output** — Generates:
   - Markdown reports with scores and reasoning
   - Action-oriented descriptions with real code examples
   - Links to full Copilot documentation

## Quick Start

### Installation

```bash
git clone https://github.com/mabthew/copilot-changelog-digest.git
cd copilot-changelog-digest
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Usage

```bash
# Analyze your current repo for the last 7 days
python3 src/main.py --days 7 --repo .

# Analyze a different repo
python3 src/main.py --days 30 --repo ~/other-project

# Output to file
python3 src/main.py --days 7 --repo . --output report.md
```

### Example Output

```markdown
# Copilot Changelog Digest
Generated: 2026-04-05
Analyzed: /Users/you/my-project (Node.js + React)
Timeframe: Last 7 days

## Top Changes for You

### 1. Improved TypeScript Error Detection ⭐ 94/100
**Impact:** Catch type errors 3x faster during development
**Why It Matters:** Your repo uses TypeScript heavily (tsconfig.json detected)
**What Changed:** Copilot now understands complex union types and generics better...

### 2. React Hook Best Practices Guide ⭐ 89/100
**Impact:** Prevent runtime errors from hook misuse
**Why It Matters:** React is your primary framework (package.json)
**What Changed:** New guided suggestions when detecting useState/useEffect patterns...

[... more updates ranked by your workflow ...]
```

## How Scoring Works

The algorithm analyzes each changelog entry across three dimensions:

### 1. Tech Stack Match
- Scans your `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, etc.
- Extracts top 10 dependencies per language
- Scores features that mention your tech stack 0-100
- Example: If you use React, updates about React features score higher

### 2. Workflow Impact (Highest Weight: 50%)
- Looks for impact keywords: "faster", "debug", "refactor", "test", "security"
- Evaluates effort saved and error prevention
- Ranks by practical value, not just novelty
- Example: "Debug 2x faster" scores higher than "New telemetry option"

### 3. User Context Match
- Integrates with `/chronicle` if available (your recent workflow hints)
- Falls back gracefully if `/chronicle` is unavailable
- Matches your focus areas (testing, performance, refactoring, etc.)
- Example: If you've been debugging, debugging features score higher

### Final Score Formula

```
Score = (TechStackMatch × 0.30) + (WorkflowImpact × 0.50) + (UserContext × 0.20)
Range: 0-100 (higher = more relevant to you)
```

## Architecture

```
┌─────────────────────────────────────────┐
│   Phase 1: Parallel Data Gathering      │
│  (Changelog, Repo Analysis, Context)    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Phase 2: 3D Relevance Scoring        │
│  (Tech × Workflow × User Context)       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Phase 3: Use Case Generation          │
│  (Actionable Recommendations)           │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Phase 4: Report Generation            │
│  (Markdown output with top 5)           │
└─────────────────────────────────────────┘
```

## Requirements

- **Python:** 3.8+
- **System:** macOS, Linux, or Windows (with PowerShell 7+)
- **Internet:** GitHub API access (for changelog fetching)
- **Optional:** Copilot CLI (for enhanced context via `/chronicle`)

## Configuration

Create `.changelog.yaml` to customize behavior:

```yaml
scoring:
  tech_weight: 0.30
  workflow_weight: 0.50
  context_weight: 0.20

output:
  top_n: 5
  include_explanations: true
  markdown_format: true

github:
  # Optional: use personal token for higher API rate limits
  api_token: ghp_xxxxx
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No Python found" | Install Python 3.8+ or use your system's package manager |
| GitHub API rate limit | Optional: Set `GITHUB_TOKEN` environment variable with a personal access token |
| `/chronicle` unavailable | Skill degrades gracefully and uses neutral context scoring |
| Incorrect tech stack detection | Verify `package.json`, `requirements.txt`, or other manifest files exist in repo root |

## Contributing

Issues and PRs welcome! See `IMPLEMENTATION.md` for architecture details and future enhancement ideas.

## License

MIT — Free to use, modify, and distribute.

---

**Ready to use?**

```bash
npx skills add mabthew/copilot-changelog-digest
```

Then run:

```bash
copilot-changelog-digest --days 7 --repo .
```
