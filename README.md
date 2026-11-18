# Scholarship AutoPilot

A standalone, no-ChatGPT-required scholarship discovery and application-preparation project. Python runs on GitHub Actions every Monday; a static dashboard is published on GitHub Pages. Email is optional.

**This is a working starter system, not an exhaustive scholarship search engine.** It starts with two directory links and zero individual verified awards. Add legitimate RSS/Atom feeds and/or manually curated award URLs. It does **not** scrape arbitrary scholarship sites, bypass anti-bot protections, fabricate eligibility, or submit applications.

## Quick start (about 20–30 minutes)

1. Create a **new GitHub repository** and upload the contents of this folder. Use the `main` branch. **Important:** GitHub Pages sites are public; never commit personal/financial information, transcripts, application essays or secrets. Public repos are simplest for free GitHub Pages. Review GitHub's current plan and Pages restrictions.
2. In repository **Settings → Actions → General**, allow GitHub Actions to run and ensure workflow permissions permit writing repository contents (the workflow declares `contents: write`, but organization policies can override this).
3. In **Settings → Pages → Build and deployment**, choose **GitHub Actions** as the source.
4. Open **Actions → Weekly scholarship discovery → Run workflow** to run once. The job writes `data/opportunities.json` and drafts (for individual candidates) and pushes changes.
5. Open **Actions → Publish dashboard → Run workflow**. Once published, the dashboard URL is shown in the Pages deployment. It will also update when the opportunity data changes.
6. Optionally set up SMTP email using repository **Settings → Secrets and variables → Actions → New repository secret**: `SMTP_HOST`, `SMTP_PORT` (usually `587`), `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO`, and optionally `EMAIL_FROM`. Use an app password or provider-issued SMTP credential; **never commit it**. Some mail providers disable password-based SMTP; use a supported transactional SMTP service instead.
7. Add sources in `config/sources.json`: RSS entries need a working HTTPS RSS/Atom URL and `enabled: true`. `links` entries are bookmarks to browse, **not** scraped scholarship records.
8. To add a specific award, run locally:

```bash
python -m pip install -r requirements.txt
python -m app.cli add --title "Example Engineering Award" --url "https://example.org/award" --source "Award provider" --deadline 2027-03-01 --eligibility "Canadian engineering students"
python -m app.core
python -m unittest discover -s tests
```

Replace the example with a **real verified award**. The `--verified` flag should only be used after checking the official rules yourself. To generate a draft for a particular ID: `python -m app.cli draft ID`.

## Weekly workflow

- Runs at **14:00 UTC every Monday** (GitHub Actions scheduled jobs can be delayed or skipped during load; scheduled workflows can be disabled after repository inactivity).
- Reads `config/sources.json`, fetches enabled HTTPS RSS feeds, extracts relevant award candidate links, and preserves existing manually added entries.
- Scores textual keyword matches using `config/profile.example.json` as a non-sensitive example profile. To customize matching in GitHub, edit the example profile or commit a **non-sensitive** `config/profile.json` only after changing `.gitignore`; do not store private data in a public repo.
- Generates draft templates for candidates (not directories). Existing drafts are **not overwritten**.
- Sends an email summary if SMTP secrets are configured.
- Updates `data/opportunities.json`, which GitHub Pages displays.

## Dashboard capabilities

Search, filter by listing type, track personal statuses, download a blank application template, and export/import local status backups. **Statuses and notes live only in the current browser's localStorage**. They are not synced across devices or backed up automatically. Use Export regularly. The site itself and its `data/opportunities.json` are public when deployed via GitHub Pages.

## Accuracy and safety

- Match scores are **keyword relevance only**, not eligibility determinations. Unknown deadlines and amounts remain unknown. Verify all award rules on the provider's official site.
- The app never auto-submits applications. Human review and official-site submission are mandatory.
- Don't put financial need evidence, citizenship documents, transcripts, GPA details, or sensitive essay content in public GitHub files or public Pages.
- Award funds may be restricted to tuition/educational expenses; do not assume they can be used for INSPIRE travel.
- Respect website terms and robots policies. RSS only; no generic crawler or form-submission bot.
- The default directories may change or disappear. GitHub Actions and GitHub Pages availability and pricing depend on your account and repository settings.

## Architecture

`app/core.py` — source ingestion, deduplication, matching, drafts, SMTP.
`app/cli.py` — add individual award candidates and create templates.
`site/index.html` — static dashboard.
`data/opportunities.json` — public listing data.
`drafts/` — generic templates; **never place real personal application answers here**.
`.github/workflows/weekly.yml` — scheduler.
`.github/workflows/pages.yml` — dashboard publishing.

## Possible next version

Add an authenticated private backend for cross-device tracking, official source-specific connectors, structured deadline extraction with review, and optional local LLM drafting. Those are **not** included in this starter version.
