#!/usr/bin/env python3
"""Builds the Bench page, a single HTML file, from the repository files.

    python bench/page/build.py [--signature signature.svg] [--out bench.html]

The page only runs inside Claude: it asks the model of the person who opens it
for the answers (`sample` capability) and keeps the benches in the artifact's
storage (`db` capability). Corpus, constitutions, judges and examples come from
the repository: the page and bench/bench.py ask exactly the same questions.
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BENCH = HERE.parent
ROOT = BENCH.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(BENCH))
import antimars as am  # noqa: E402
from bench import cases_block  # noqa: E402


def data():
    examples = json.loads(am.EXAMPLES.read_text(encoding="utf-8"))
    return {
        "corpus": json.loads((BENCH / "corpus.json").read_text(encoding="utf-8")),
        "portable": am.extract_constitution((ROOT / "constitution" / "portable.en.md").read_text(encoding="utf-8")),
        "tower": (ROOT / "constitution" / "tower.en.md").read_text(encoding="utf-8"),
        "judges": {k: (BENCH / "judges" / f"{k}.txt").read_text(encoding="utf-8") for k in ("neutral", "canon", "calibration")},
        "cases": cases_block(examples),
        "gold": {ex["id"]: [ex["annotation"]["seals"][s]["value"] for s in am.ANNOTATION_SEALS]
                 for ex in examples if ex["annotation"].get("seals")},
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--signature", help="signature SVG placed in the footer")
    p.add_argument("--out", default=str(HERE / "bench.html"))
    a = p.parse_args()
    page = (HERE / "bench.src.html").read_text(encoding="utf-8")
    signature = ('<span class="sig-txt">garrigue</span>' if not a.signature
                 else pathlib.Path(a.signature).read_text(encoding="utf-8").strip())
    blob = json.dumps(data(), ensure_ascii=False).replace("</", "<\\/")
    for mark, value in (("__SIGNATURE__", signature), ("__DATA__", blob)):
        if page.count(mark) != 1:
            sys.exit(f"mark {mark} missing or repeated")
        page = page.replace(mark, value)
    pathlib.Path(a.out).write_text(page, encoding="utf-8")
    print(f"{a.out} · {len(page.encode('utf-8')) // 1024} KB")


if __name__ == "__main__":
    main()
