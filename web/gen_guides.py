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
    # --- expanded library: high-demand informational queries ---
    ("how-long-do-dental-implants-last", "How Long Do Dental Implants Last?", "Oral Surgeon"),
    ("is-a-root-canal-painful", "Is a Root Canal Painful? What to Expect", "Endodontist"),
    ("how-much-do-veneers-cost", "How Much Do Veneers Cost?", "Cosmetic Dentist"),
    ("how-much-do-dentures-cost", "How Much Do Dentures Cost?", "General Dentist"),
    ("how-much-does-a-dental-crown-cost", "How Much Does a Dental Crown Cost?", "General Dentist"),
    ("how-much-does-invisalign-cost", "How Much Does Invisalign Cost?", "Orthodontist"),
    ("how-much-do-braces-cost", "How Much Do Braces Cost?", "Orthodontist"),
    ("how-to-get-rid-of-a-toothache-fast", "How to Get Rid of a Toothache Fast", "Emergency Dentist"),
    ("why-are-my-gums-bleeding", "Why Are My Gums Bleeding?", "Periodontist"),
    ("what-causes-tooth-sensitivity", "What Causes Tooth Sensitivity?", "General Dentist"),
    ("signs-of-a-tooth-abscess", "Signs of a Tooth Abscess", "Emergency Dentist"),
    ("wisdom-teeth-removal-recovery", "Wisdom Teeth Removal Recovery: What to Expect", "Oral Surgeon"),
    ("dental-implants-vs-dentures", "Dental Implants vs Dentures: Which Is Better?", "Oral Surgeon"),
    ("what-is-a-deep-cleaning", "What Is a Deep Cleaning at the Dentist?", "Periodontist"),
    ("how-much-does-wisdom-teeth-removal-cost", "How Much Does Wisdom Teeth Removal Cost?", "Oral Surgeon"),
    ("how-to-fix-a-chipped-tooth", "How to Fix a Chipped Tooth", "Cosmetic Dentist"),
    ("how-often-should-kids-see-the-dentist", "How Often Should Kids See the Dentist?", "Pediatric Dentist"),
    ("what-to-do-if-you-knock-out-a-tooth", "What to Do If You Knock Out a Tooth", "Emergency Dentist"),
    ("does-insurance-cover-dental-implants", "Does Insurance Cover Dental Implants?", "Oral Surgeon"),
    ("how-to-stop-grinding-teeth-at-night", "How to Stop Grinding Your Teeth at Night", "General Dentist"),
    ("what-is-dry-socket", "What Is Dry Socket and How to Prevent It", "Oral Surgeon"),
    ("how-much-does-a-tooth-extraction-cost", "How Much Does a Tooth Extraction Cost?", "General Dentist"),
    ("root-canal-vs-extraction", "Root Canal vs Extraction: Which Is Better?", "Endodontist"),
    ("how-long-does-a-dental-cleaning-take", "How Long Does a Dental Cleaning Take?", "General Dentist"),
    ("teeth-whitening-vs-veneers", "Teeth Whitening vs Veneers: Which Should You Choose?", "Cosmetic Dentist"),
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
