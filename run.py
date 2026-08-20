#!/usr/bin/env python3
"""Local orchestrator for the Dentist Directory — runs everything on YOUR
computer (no GitHub Actions needed).

  python run.py scrape --allow-bare-ip          # scrape from your IP (ban risk!)
  python run.py scrape --proxy http://user:pass@host:port   # safer
  python run.py scrape --proxy-file proxies.txt --headful   # watch it
  python run.py content                         # generate city/category copy (GROQ_API_KEY)
  python run.py guides                          # generate the guide articles
  python run.py clean                           # drop junk / dupes
  python run.py serve                           # run the website -> http://127.0.0.1:5000
  python run.py export                          # dump data/listings.csv + .json
  python run.py deploy                          # vercel deploy --prod (needs vercel CLI)

The scraper is resumable: progress is tracked in data/.offset, so you can stop
(Ctrl+C) and re-run `scrape` to pick up where you left off. Dedup means nothing
is scraped twice.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scraper"))
PY = sys.executable
OFFSET_FILE = ROOT / "data" / ".offset"


def _run(cmd, env=None):
    print("»", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, env=env or os.environ.copy()).returncode


def cmd_scrape(rest):
    import targets
    total = sum(1 for _ in targets.jobs())
    batch = int(os.environ.get("BATCH", "40"))
    maxr = os.environ.get("MAX_RESULTS", "30")
    OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    offset = int(OFFSET_FILE.read_text().strip()) if OFFSET_FILE.exists() else 0
    print(f"Scraping {total} jobs in batches of {batch}, starting at offset {offset}.")
    print("Stop anytime with Ctrl+C — progress is saved.\n")
    while offset < total:
        rc = _run([PY, str(ROOT / "scraper" / "scrape.py"),
                   "--offset", str(offset), "--limit", str(batch),
                   "--max-results", str(maxr), *rest])
        if rc != 0:
            print(f"\nScraper exited ({rc}). Fix the issue and re-run `scrape` "
                  "to resume from the same offset.")
            return rc
        _run([PY, str(ROOT / "scraper" / "clean.py")])
        offset += batch
        OFFSET_FILE.write_text(str(offset))
        print(f"--- progress: {min(offset, total)}/{total} jobs ---\n")
    print("Scrape complete.")
    return 0


def cmd_content(rest):
    return _run([PY, str(ROOT / "web" / "gen_content.py"), "--kind", "category"]) \
        or _run([PY, str(ROOT / "web" / "gen_content.py"), "--kind", "city", *rest])


def cmd_guides(rest):
    return _run([PY, str(ROOT / "web" / "gen_guides.py"), *rest])


def cmd_clean(rest):
    return _run([PY, str(ROOT / "scraper" / "clean.py")])


def cmd_export(rest):
    return _run([PY, str(ROOT / "scraper" / "export.py")])


def cmd_serve(rest):
    return _run([PY, str(ROOT / "web" / "app.py")])


def cmd_deploy(rest):
    return _run(["vercel", "deploy", "--prod", "--yes", *rest])


CMDS = {"scrape": cmd_scrape, "content": cmd_content, "guides": cmd_guides,
        "clean": cmd_clean, "export": cmd_export, "serve": cmd_serve,
        "deploy": cmd_deploy}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__)
        sys.exit(1)
    sys.exit(CMDS[sys.argv[1]](sys.argv[2:]) or 0)
