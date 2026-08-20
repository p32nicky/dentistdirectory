# Dentist Directory

A nationwide dentist directory — scrape Google Maps → store in SQLite → render
thousands of SEO pages with Flask. **Runs entirely on your computer** (no
GitHub Actions required).

## Layout
```
dentists-directory/
├── run.py              ← local orchestrator (scrape / content / guides / serve / deploy)
├── scraper/            Google Maps scraper, DB, clean/dedupe, targets (8 dental specialties)
├── web/                Flask site, templates, static, content + guide generators
├── api/                Vercel serverless entrypoint (only if you deploy)
├── data/               dentists.db + us-cities.csv seed
└── config              vercel.json, Dockerfile, requirements*, tailwind.config.js
```

## 1. Setup (one time)
```bash
cd dentists-directory
python -m venv .venv
.venv\Scripts\activate                 # Windows  (source .venv/bin/activate elsewhere)
pip install -r requirements-scrape.txt  # scraper deps (Playwright)
pip install flask                       # website
python -m playwright install chromium
```

## 2. Scrape dentists (runs on YOUR machine)
The scraper is resumable — progress saved in `data/.offset`. Stop with Ctrl+C,
re-run to continue. Dedup means nothing is scraped twice.

```bash
# watch the first batch in a visible browser (recommended first run):
python run.py scrape --allow-bare-ip --headful

# full run through a proxy (protects your home IP from Google bans):
python run.py scrape --proxy http://user:pass@host:port
```

⚠️ **IP note:** scraping from your home IP risks a temporary Google block. Use a
**residential proxy** (`--proxy`) for large runs, or accept the risk with
`--allow-bare-ip`. Go slow; the scraper already paces itself.

Tuning (env vars): `BATCH=40 MAX_RESULTS=30 PCD_MAX_CITIES=300 python run.py scrape ...`

## 3. Generate SEO content (needs a free Groq key)
```bash
set GROQ_API_KEY=gsk_...                # console.groq.com/keys
python run.py content                   # unique copy for every city + specialty
python run.py guides                    # 15 dental guide articles
```

## 4. Run the website
```bash
python run.py serve                     # -> http://127.0.0.1:5000
```
Runs fully from the local `data/dentists.db`.

## 5. (Optional) Deploy
```bash
python run.py deploy                    # vercel deploy --prod  (needs vercel CLI + login)
```
Set a real `DOMAIN`, `GA_ID`, `ADSENSE_CLIENT`, `GSC_VERIFICATION` as Vercel env
vars for production. Everything is server-rendered and works read-only on Vercel.

## Specialties scraped
General Dentist · Cosmetic Dentist · Orthodontist · Pediatric Dentist ·
Oral Surgeon · Endodontist · Periodontist · Emergency Dentist

## Cities — nationwide
Top 1,000 US cities (`data/us-cities.csv`). 1,000 × 8 specialties = **8,000
search jobs** → tens of thousands of unique practices after dedup.

## Notes
Scraping Google Maps violates their ToS. Use rotating residential proxies, keep
concurrency low, and don't republish Google review *text* verbatim.
