# x-report-reminder

Track X (Twitter) accounts, auto-summarise their article links with Claude, and save the summaries as Obsidian notes.

## Setup

### 1. Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 2. Configure

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required values:
| Variable | Description |
|---|---|
| `X_USERNAME` | Your X account username |
| `X_PASSWORD` | Your X account password |
| `X_EMAIL` | Email address linked to your X account |
| `X_EMAIL_PASSWORD` | Email password (for auto-fetching verification codes) |
| `ANTHROPIC_API_KEY` | Claude API key from console.anthropic.com |
| `OBSIDIAN_VAULT_PATH` | Path to your Obsidian vault folder |

> `.env` is gitignored — your credentials will never be committed.

### 3. Login to X (one time)

```bash
xreminder init-scraper
```

This logs in via twscrape and saves session cookies. You may be prompted to enter a verification code sent to your email.

## Usage

```bash
# Add accounts to track
xreminder add-account stratechery
xreminder add-account benedictevans

# List tracked accounts
xreminder list-accounts

# Fetch new articles, summarise, save to Obsidian
xreminder fetch

# Fetch just one account
xreminder fetch --account stratechery

# Preview what would be fetched (no writes)
xreminder fetch --dry-run

# Remove an account
xreminder remove-account stratechery
```

## How it works

1. **Fetch** — twscrape logs in to X with your credentials and reads recent tweets from tracked accounts
2. **Extract** — External URLs from tweets are identified (t.co and twitter.com links are filtered out)
3. **Summarise** — Each article is fetched via httpx, text is extracted with trafilatura, then Claude Haiku generates a structured summary
4. **Save** — Notes are written to your Obsidian vault as `.md` files with YAML frontmatter

Processed articles are stored in SQLite (`~/.local/share/xreminder/`) — re-running `fetch` skips already-seen URLs.

## Obsidian note format

Each saved note includes:
- YAML frontmatter: title, author (@handle), source_url, date, tags
- **TL;DR** — 2-3 sentence summary
- **Key Points** — bullet list of concrete findings
- **Why It Matters** — significance and implications
- **Notable Quotes** — direct quotes (when available)
