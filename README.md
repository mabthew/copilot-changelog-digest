# Copilot Changelog Skill

A Copilot skill that analyzes GitHub Copilot's recent changelog updates and surfaces **the most important changes that could improve YOUR workflow** — grounded in your specific repository and tech stack.

## What It Does

This skill:

1. **Fetches** the latest Copilot changelog from GitHub (last N days)
2. **Analyzes** your repository (tech stack, dependencies, recent commits)
3. **Scans your code** for patterns (async issues, error handling, testing gaps, performance bottlenecks)
4. **Fetches your development patterns** via `/chronicle` (recent files, workflow patterns, error patterns)
5. **Scores** changelog items by workflow impact and relevance to YOUR code
6. **Generates** actionable use cases grounded in your actual codebase with concrete examples
7. **Outputs** a focused report with repository-specific recommendations and time savings estimates

## Quick Start

### Prerequisites

- Python 3.9+
- PowerShell 7+ (for the skill wrapper)
- A Git repository to analyze
- Internet connection (to fetch Copilot changelog from GitHub)

### Installation

```bash
# Clone or download the skill
cd copilot-changelog-skill

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Usage

#### Option 1: Direct Python (Recommended)

```bash
# Analyze current repo, last 7 days
python3 src/main.py --days 7 --repo .

# Analyze last 30 days
python3 src/main.py --days 30 --repo .

# Output as JSON instead of markdown
python3 src/main.py --days 7 --output json
```

#### Option 2: PowerShell Wrapper

```powershell
# Windows/macOS/Linux (requires PowerShell 7+)
./changelog-skill.ps1 -Days 7 -Repo . -Output markdown
```

### Example Output

The skill generates a focused markdown report with:

- **Summary**: Count of important updates found
- **Top Recommendations**: Prioritized list of impactful changes
- **Details for each**: 
  - How it helps YOUR workflow
  - Why it's relevant to your tech stack
  - Estimated impact (time saved, errors prevented, etc.)
  - Link to official release notes

## Architecture

### Phase 1: Parallel Data Retrieval (via `/fleet`)

Three independent tasks execute in parallel:

- **Task A**: Fetch Copilot changelog (GitHub API)
- **Task B**: Analyze repository (tech stack, dependencies, commits)
- **Task C**: Retrieve user context (via `/chronicle`)

Results are synced before proceeding.

### Phase 2: Ranking & Relevance Scoring

- Parse changelog into structured features
- Score each feature by:
  - Tech stack overlap (30% weight)
  - Workflow improvement potential (50% weight)
  - User context match (20% weight)
- Sort features by total workflow impact score

### Phase 3: Use Case Generation

- For top 5 features, generate "how this helps you" explanations
- Pull relevant code examples from the repo
- Estimate impact (time saved, errors prevented, etc.)
- Link to official documentation

### Phase 4: /Chronicle Integration & Repository-Grounded Personalization (NEW)

- **Code Analysis**: Scan your codebase for patterns (async/await issues, error handling gaps, testing coverage, performance bottlenecks)
- **Chronicle Integration**: Fetch your development patterns (recent files, workflow preferences, error patterns, focus areas)
- **Pattern Matching**: Link changelog features directly to specific files in YOUR repository
- **Personalized Impact**: Generate "Why This Matters To YOU" section with concrete examples and realistic time savings estimates
- **Next Steps**: Provide actionable next steps specific to your codebase

See [Phase 4 Documentation](./skills/copilot-changelog-digest/PHASE4_CHRONICLE.md) for details on repository-grounded personalization.

### Phase 5: Output Generation

- Generate focused markdown report (not all changes, just the important ones)
- Format for easy reading and sharing
- Include actionable next steps

## File Structure

```
copilot-changelog-skill/
├── src/
│   ├── main.py                         # Entry point
│   ├── fleet/
│   │   ├── orchestrator.py             # Manages parallel task execution
│   │   ├── task_changelog.py           # Fleet Task A
│   │   ├── task_repo_analyzer.py       # Fleet Task B
│   │   └── task_user_context.py        # Fleet Task C
│   ├── changelog/
│   │   ├── fetcher.py                  # GitHub API client
│   │   └── parser.py                   # Release notes parser
│   ├── repo_analyzer/
│   │   └── detector.py                 # Tech stack detection
│   ├── ranking/
│   │   └── scorer.py                   # Feature relevance scoring
│   ├── generation/
│   │   └── use_cases.py                # Use case generation
│   ├── output/
│   │   └── markdown.py                 # Markdown report generation
│   └── utils/
│       └── user_context.py             # User context retrieval
├── tests/                              # Unit and integration tests
├── changelog-skill.ps1                 # PowerShell wrapper
├── requirements.txt                    # Python dependencies
└── README.md                           # This file
```

## Configuration

### Command-line Arguments

```
--days <int>          Time window in days (default: 7)
--repo <path>         Repository path (default: current directory)
--output <format>     Output format: markdown | json (default: markdown)
```

### Environment Variables

Optional:

- `GITHUB_TOKEN`: GitHub API token for higher rate limits (default: unauthenticated)

## Performance

- **Typical runtime**: 5-15 seconds
- **Network I/O**: ~1-2 API calls to GitHub
- **Local analysis**: Scans recent commits and file structure

## Scoring Methodology

Features are scored on a 0-100 scale across three dimensions:

### 1. Tech Stack Match (30% weight)

- Does the feature mention your language/framework?
- Do the release notes include keywords relevant to your stack?
- Examples: "Python" score boost if you use Python

### 2. Workflow Impact (50% weight) — **Primary**

- What category is the feature? (performance, debugging, testing, etc.)
- Does it save time, prevent errors, or improve code quality?
- High-impact keywords: "performance", "debug", "faster", "security"

### 3. User Context Match (20% weight)

- Does the feature align with your recent activity?
- Does it match your development patterns (if available via `/chronicle`)?
- Fallback: neutral score if context unavailable

**Final Score** = (Tech Match × 0.30) + (Workflow Impact × 0.50) + (User Context × 0.20)

## Tech Stack Supported

The skill automatically detects and prioritizes:

- **Languages**: Python, JavaScript/TypeScript, Go, Rust, Java, C#, Ruby, PHP
- **Frameworks**: Node.js, React, Vue, Angular, Next.js, Django, FastAPI, Spring
- **Tools**: npm, pip, go.mod, gradle, cargo, composer, etc.

## Limitations & Known Issues

1. **Limited release notes**: GitHub API returns minimal release details. Full notes require parsing the HTML page.
2. **User context requires `/chronicle`**: Feature is optional; skill gracefully falls back to repo-only analysis.
3. **Code examples are templated**: Production version would extract real code snippets from the repo.
4. **No caching**: Each run fetches fresh data. Future versions will implement SQLite caching.

## Troubleshooting

### "Python not found"

Install Python 3.9+ from https://www.python.org/downloads/

### "Module not found" errors

Ensure you're running from the project root and virtual environment is activated:

```bash
source venv/bin/activate
python3 src/main.py
```

### "Failed to fetch releases"

Check internet connection and GitHub API availability. If using unauthenticated requests and hitting rate limits, set `GITHUB_TOKEN`:

```bash
export GITHUB_TOKEN="your_github_token"
python3 src/main.py
```

### Empty release notes

GitHub API provides minimal release details. The skill scores based on title and version; more detailed analysis would require fetching full HTML release pages.

## Future Enhancements

- [ ] SQLite caching to reduce API calls
- [ ] Integration with `/chronicle` for true user context personalization
- [ ] Real code snippet extraction from repo
- [ ] Interactive Q&A mode for deeper analysis
- [ ] Email digest export
- [ ] Integration with GitHub Issues/PRs
- [ ] Custom scoring rules per user

## Contributing

Found a bug or have a feature request? Open an issue or PR!

## License

MIT
