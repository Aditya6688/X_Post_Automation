# Ghostwriter — AI-Powered Twitter/X Content Drafting System

An automated system that fetches trending tech content from multiple sources, generates engaging tweet drafts using OpenAI, and saves them to a Notion database for review and publishing.

## Architecture

```
                         config.yaml
                             |
                             v
┌─────────────────────────────────────────────────────┐
│                     Engine (run)                     │
│  Reads config, selects source, orchestrates pipeline │
└──────┬──────────────────┬──────────────────┬────────┘
       │                  │                  │
       v                  v                  v
 ┌───────────┐    ┌──────────────┐    ┌────────────┐
 │  Fetchers │    │  Generation  │    │   Storage  │
 │  Module 1 │───>│   Module 2   │───>│  (Notion)  │
 └───────────┘    └──────────────┘    └────────────┘
  HackerNews       OpenAI API          Notion API
  GitHub           Persona-driven      Structured
  ArXiv            prompts             page creation
  Dev.to
```

### Design Decisions

**Why a config file instead of hardcoded values?**
Every tuneable knob — source URLs, weights, personas, model name, tweet rules, log level — lives in `config.yaml`. This means you can change the system's behaviour (swap models, disable a source, adjust tone) without touching Python code. It also makes the gap between "local dev" and "CI run" zero: same script, different config if needed.

**Why structured (JSON) logging?**
Print statements are fine for demos but useless when debugging a daily cron job that failed at 3 AM. Structured JSON logs give you machine-parseable records with timestamps, log levels, and attached data payloads. You can pipe them into any log aggregator (Datadog, CloudWatch, ELK) or just `jq` them locally. A `"text"` format option exists in config for local development readability.

**Why weighted random source selection?**
Not all sources are equal. GitHub repos tend to produce the most engaging developer content, so they get a 40% weight by default. Weights are configurable — if your audience shifts toward research, bump ArXiv's weight in config. The system picks one source per run to keep each draft focused.

**Why one draft per run?**
Quality over quantity. A single focused draft is easier to review and publish than a batch of five mediocre ones. The GitHub Actions cron triggers once daily, producing exactly one draft in Notion's review queue.

**Why a source registry pattern?**
Each fetcher is a standalone function with an identical signature `(cfg, log) -> list[dict]`. The engine maps config keys to fetchers via `SOURCE_REGISTRY`. To add a new source, you write one function and add one entry to the registry and config — no if/else chains to extend.

## Features

- **Multi-Source Fetching**: Pulls from GitHub Trending, HackerNews, Dev.to, and ArXiv
- **Persona-Driven Generation**: Different AI voices per content type (Engineer, Researcher, Mentor, Commentator)
- **Configurable via YAML**: Sources, weights, personas, model, tweet rules, logging — all in `config.yaml`
- **Structured Logging**: JSON log output with timestamps, levels, and data payloads
- **Notion Integration**: Saves drafts with full metadata (title, draft, source URL, type, status)
- **One Draft Per Run**: Focused, high-quality output

## Prerequisites

- Python 3.10+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Notion API token ([Create integration](https://www.notion.so/my-integrations))
- Notion database with properties:
  - `Name` (Title)
  - `Tweet Draft` (Rich Text)
  - `Source URL` (URL)
  - `Status` (Status) — with "Not started" option
  - `Type` (Select) — with options: Code, News, Research, Tutorial

## Installation

```bash
git clone https://github.com/Aditya6688/X_Post_Automation.git
cd X_Post_Automation
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-openai-api-key
NOTION_TOKEN=secret_your-notion-token
NOTION_DB_ID=your-notion-database-id
```

### System Configuration

All system behaviour is controlled by `config.yaml`. Key sections:

| Section | What it controls |
|---------|-----------------|
| `openai.model` | Which OpenAI model to use |
| `tweet.*` | Max length, tone, generation rules |
| `sources.*` | URLs, weights, enable/disable, max items per source |
| `personas.*` | AI role and instruction per content type |
| `logging.*` | Log level, format (`json`/`text`), optional file output |

Override the config path with the `GHOSTWRITER_CONFIG` env var:

```bash
GHOSTWRITER_CONFIG=config.prod.yaml python ghostwriter.py
```

## Usage

```bash
python ghostwriter.py
```

### Example Log Output (JSON mode)

```json
{"timestamp": "2026-04-02 09:00:01", "level": "INFO", "module": "ghostwriter", "message": "Pipeline started"}
{"timestamp": "2026-04-02 09:00:01", "level": "INFO", "module": "ghostwriter", "message": "Source selected", "data": {"source": "github_trending"}}
{"timestamp": "2026-04-02 09:00:02", "level": "INFO", "module": "ghostwriter", "message": "Fetching from GitHub Trending", "data": {"url": "https://github.com/trending/python?since=daily"}}
{"timestamp": "2026-04-02 09:00:03", "level": "INFO", "module": "ghostwriter", "message": "Draft saved to Notion successfully", "data": {"title": "Repo: user/project - desc", "source": "github_trending"}}
```

### Example Log Output (text mode)

```
2026-04-02 09:00:01 | INFO     | ghostwriter | Pipeline started
2026-04-02 09:00:01 | INFO     | ghostwriter | Source selected
```

## Project Structure

```
X_Post_Automation/
├── ghostwriter.py              # Main application
├── config.yaml                 # System configuration
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not committed)
├── .github/workflows/
│   └── daily_post.yml          # GitHub Actions cron job
└── README.md
```

## Extending

To add a new content source:

1. Write a fetcher function matching the signature `(cfg, log) -> list[dict]`
2. Add it to `SOURCE_REGISTRY` in `ghostwriter.py`
3. Add its config block under `sources:` in `config.yaml`
4. Add a persona entry under `personas:` if it needs a unique voice

## Troubleshooting

- **"Missing required environment variables"**: Check your `.env` file has all three keys
- **Notion errors**: Verify database properties match the expected names and types
- **Config errors**: Run `python -c "import yaml; yaml.safe_load(open('config.yaml'))"` to validate syntax
- **Log too noisy/quiet**: Change `logging.level` in `config.yaml` to `DEBUG` or `WARNING`

## License

This project is open source and available under the [MIT License].

## Disclaimer

This tool generates draft content. Always review and edit generated tweets before publishing.
