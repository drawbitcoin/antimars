#!/usr/bin/env python3
"""Construit la page Banc, un seul fichier HTML, à partir des fichiers du dépôt.

    python banc/page/construire.py [--signature signature.svg] [--sortie banc.html]

La page ne tourne que dans Claude : elle demande les réponses au modèle de la
personne qui l'ouvre (capacité `sample`) et garde les bancs dans la mémoire de
l'artefact (capacité `db`). Corpus, constitutions, juges et exemples viennent du
dépôt : la page et banc/banc.py posent exactement les mêmes questions.
"""
import argparse
import json
import pathlib
import sys

ICI = pathlib.Path(__file__).resolve().parent
BANC = ICI.parent
RACINE = BANC.parent
sys.path.insert(0, str(RACINE / "outils"))
sys.path.insert(0, str(BANC))
import antimars as am  # noqa: E402
from banc import bloc_cas  # noqa: E402


def donnees():
    exemples = json.loads(am.EXEMPLES.read_text(encoding="utf-8"))
    return {
        "corpus": json.loads((BANC / "corpus.json").read_text(encoding="utf-8")),
        "portable": am.extraire_constitution((RACINE / "constitution" / "portable.fr.md").read_text(encoding="utf-8")),
        "tour": (RACINE / "constitution" / "tour.fr.md").read_text(encoding="utf-8"),
        "juges": {k: (BANC / "juges" / f"{k}.txt").read_text(encoding="utf-8") for k in ("neutre", "canon", "etalon")},
        "cas": bloc_cas(exemples),
        "or": {ex["id"]: [ex["annotation"]["sceaux"][s]["valeur"] for s in am.SCEAUX]
               for ex in exemples if ex["annotation"].get("sceaux")},
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--signature", help="SVG de signature à placer en pied de page")
    p.add_argument("--sortie", default=str(ICI / "banc.html"))
    a = p.parse_args()
    page = (ICI / "banc.src.html").read_text(encoding="utf-8")
    signature = ('<span class="sig-txt">garrigue</span>' if not a.signature
                 else pathlib.Path(a.signature).read_text(encoding="utf-8").strip())
    blob = json.dumps(donnees(), ensure_ascii=False).replace("</", "<\\/")
    for marque, valeur in (("__SIGNATURE__", signature), ("__DONNEES__", blob)):
        if page.count(marque) != 1:
            sys.exit(f"marque {marque} introuvable ou en double")
        page = page.replace(marque, valeur)
    pathlib.Path(a.sortie).write_text(page, encoding="utf-8")
    print(f"{a.sortie} · {len(page.encode('utf-8')) // 1024} Ko")


if __name__ == "__main__":
    main()
