"""Generate long-form dental guides with Groq, stored in the `guides`
table. Top-of-funnel SEO content that pulls informational search traffic and
funnels readers to the directory listings.

    set GROQ_API_KEY=...
    python web/gen_guides.py            # generate all missing guides
    python web/gen_guides.py --force    # regenerate all
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scraper"))
sys.path.insert(0, str(ROOT / "web"))
import db as dbmod          # noqa: E402
import gen_content as gc    # noqa: E402  (reuse the LLM caller + backoff)

# (slug, title, related category) — high-volume informational queries.
TOPICS = [
    ("how-much-does-a-dental-implant-cost", "How Much Does a Dental Implant Cost?", "Oral Surgeon"),
    ("how-much-does-teeth-whitening-cost", "How Much Does Teeth Whitening Cost?", "Cosmetic Dentist"),
    ("signs-you-need-a-root-canal", "Signs You Need a Root Canal", "Endodontist"),
    ("how-to-find-a-good-dentist", "How to Find a Good Dentist", "General Dentist"),
    ("do-you-need-wisdom-teeth-removed", "Do You Need Your Wisdom Teeth Removed?", "Oral Surgeon"),
    ("how-often-should-you-visit-the-dentist", "How Often Should You Visit the Dentist?", "General Dentist"),
    ("braces-vs-invisalign", "Braces vs Invisalign: Which Is Right for You?", "Orthodontist"),
    ("what-to-do-in-a-dental-emergency", "What to Do in a Dental Emergency", "Emergency Dentist"),
    ("how-to-stop-tooth-pain", "How to Stop Tooth Pain", "General Dentist"),
    ("cosmetic-dentistry-options-explained", "Cosmetic Dentistry Options Explained", "Cosmetic Dentist"),
    ("how-to-choose-a-pediatric-dentist", "How to Choose a Pediatric Dentist", "Pediatric Dentist"),
    ("gum-disease-signs-and-treatment", "Gum Disease: Signs and Treatment", "Periodontist"),
    ("dental-insurance-what-is-covered", "Dental Insurance: What's Covered?", "General Dentist"),
    ("teeth-whitening-at-home", "How to Whiten Teeth at Home", "Cosmetic Dentist"),
    ("how-to-prevent-cavities", "How to Prevent Cavities", "General Dentist"),
]


def prompt(title):
    return (
        f"Write a helpful, accurate guide titled '{title}' for a dental "
        "directory that helps patients. Return JSON with keys: "
        "\"description\" (a 150-char meta description), "
        "\"intro\" (80-120 word opening paragraph), "
        "\"sections\" (4-6 items of {\"heading\":..., \"content\":<90-140 word "
        "paragraph>}), "
        "\"faq\" (3 items of {\"q\":..., \"a\":<40-70 words>}). "
        "Practical and specific. When professional help is warranted, say so "
        "plainly without naming any company or inventing prices/statistics.")


def run(force):
    conn = dbmod.connect()
    cur = conn.cursor()
    done = 0
    for slug, title, cat in TOPICS:
        if not force and cur.execute("SELECT 1 FROM guides WHERE slug=?",
                                     (slug,)).fetchone():
            print("skip", slug); continue
        try:
            data = gc.gemini(prompt(title))
            cur.execute(
                "INSERT OR REPLACE INTO guides(slug,title,description,category,"
                "body,generated_at) VALUES (?,?,?,?,?,datetime('now'))",
                (slug, title, data.get("description", ""), cat, json.dumps(data)))
            conn.commit()
            done += 1
            print("ok  ", slug)
        except Exception as e:
            print("FAIL", slug, e)
        time.sleep(1.0)
    print(f"\nGenerated {done} guides.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    run(ap.parse_args().force)
