#!/usr/bin/env python3
"""Antimars · noyau 1.0 · outils de référence.

    python outils/antimars.py valider sortie.txt           # format 1.0 et règles du canon
    python outils/antimars.py compter sortie.txt --lus 2100  # jetons, Wh, secondes de tour
    python outils/antimars.py exemples                     # vérifie les dix exemples annotés

Bibliothèque standard seulement. Si le paquet jsonschema est installé, le schéma
officiel est aussi vérifié.
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = RACINE / "schema" / "antimars-1.0.schema.json"
EXEMPLES = RACINE / "exemples" / "exemples-1.0.json"

SCEAUX = ("homme", "planete", "vivant")
STATUTS = ("monte", "question_plus_juste", "voie_courte")
FRAGMENTS = ("entendue", "energie", "pensee", "abstraction", "vivant", "enjeu")
MANQUE = object()  # distingue un champ absent d'un champ à null
GROUPES_DE_POIDS = {
    "poids": ("energie", "pensee", "abstraction", "vivant"),
    "piliers": ("geometrie", "rationalite", "creativite", "paix"),
    "echanges": ("geometrie_rationalite", "rationalite_creativite", "creativite_paix", "paix_geometrie"),
}

# Compteur : section 5 de la spécification.
WH_PAR_JETON_ECRIT = 0.0006
WH_PAR_JETON_LU = 0.00003
WH_PAR_SECONDE_DE_TOUR = 56.0
CARACTERES_PAR_JETON = {"fr": 3.6, "en": 4.0, "code": 3.0}


# --- lecture ----------------------------------------------------------------

def bloc(texte: str, nom: str):
    """Contenu du bloc <nom>…</nom>, ou None s'il manque. Un bloc non fermé court jusqu'à la fin."""
    debut = texte.find(f"<{nom}>")
    if debut < 0:
        return None
    debut += len(nom) + 2
    fin = texte.find(f"</{nom}>", debut)
    return (texte[debut:] if fin < 0 else texte[debut:fin]).strip()


def lire_json(texte):
    """Le premier objet JSON lisible d'un texte ; tolère les clôtures ``` et une phrase autour."""
    if not texte:
        return None
    texte = re.sub(r"```(?:json)?", "", texte)
    a, b = texte.find("{"), texte.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        objet = json.loads(texte[a:b + 1])
    except json.JSONDecodeError:
        return None
    return objet if isinstance(objet, dict) else None


def lire_sortie(texte: str):
    """Découpe une sortie Antimars en (blocs, objet du bloc json ou None)."""
    blocs = {nom: bloc(texte, nom) for nom in ("dissection", "generation", "json")}
    source = blocs["json"] if blocs["json"] is not None else texte
    return blocs, lire_json(source)


# --- canon ------------------------------------------------------------------

def valeur(x):
    """Un sceau : -1, 0 ou 1 ; None pour tout le reste (true et false ne sont pas des sceaux)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    return int(x) if x in (-1, 0, 1) else None


def sceaux_du_canon(canon):
    """(homme, planete, vivant) lus dans un canon, ou None s'il en manque un."""
    if not isinstance(canon, dict):
        return None
    valeurs = []
    for nom in SCEAUX:
        entree = canon.get(nom)
        v = valeur(entree.get("sceau")) if isinstance(entree, dict) else None
        if v is None:
            return None
        valeurs.append(v)
    return tuple(valeurs)


def passe(valeurs) -> bool:
    """Règle 3.4 : aucun −1 et au moins un +1."""
    return valeurs is not None and min(valeurs) >= 0 and max(valeurs) == 1


def statut(objet):
    return objet.get("statut", "monte") if isinstance(objet, dict) else None


def ecrire_sceaux(valeurs) -> str:
    if valeurs is None:
        return "—"
    return " ".join({1: "+1", 0: "0", -1: "−1"}[v] for v in valeurs)


# --- validation -------------------------------------------------------------

def _texte(x) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _poids(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and 0 <= x <= 1


def erreurs_de_forme(objet) -> list:
    """Ce qu'exige schema/antimars-1.0.schema.json, vérifié à la main."""
    if not isinstance(objet, dict):
        return ["le bloc json n'est pas un objet"]
    e = []
    st = objet.get("statut", "monte")
    if "statut" in objet and st not in STATUTS:
        e.append(f"statut inconnu : {st!r}")
    if "antimars" in objet and not (isinstance(objet["antimars"], str)
                                    and re.fullmatch(r"1\.[0-9]+", objet["antimars"])):
        e.append("antimars : version attendue de la forme 1.x")
    if not _texte(objet.get("reponse")):
        e.append("reponse manquante ou vide")
    requis = st != "voie_courte"

    it = objet.get("interpretation", MANQUE)
    if it is MANQUE:
        if requis:
            e.append("interpretation manquante")
    elif not isinstance(it, dict):
        e.append("interpretation doit être un objet")
    else:
        e += [f"interpretation.{k} manquant ou vide" for k in FRAGMENTS if not _texte(it.get(k))]
        e += _erreurs_poids(it.get("poids", MANQUE), "interpretation.poids", GROUPES_DE_POIDS["poids"])

    canon = objet.get("canon", MANQUE)
    if canon is MANQUE:
        if requis:
            e.append("canon manquant")
    elif not isinstance(canon, dict):
        e.append("canon doit être un objet")
    else:
        for nom in SCEAUX:
            entree = canon.get(nom)
            if not isinstance(entree, dict):
                e.append(f"canon.{nom} manquant")
                continue
            if valeur(entree.get("sceau")) is None:
                e.append(f"canon.{nom}.sceau doit valoir -1, 0 ou 1")
            if not isinstance(entree.get("pourquoi"), str):
                e.append(f"canon.{nom}.pourquoi manquant")
        if "note" in canon and not isinstance(canon["note"], str):
            e.append("canon.note doit être un texte")

    raisonnement = objet.get("raisonnement", MANQUE)
    if raisonnement is MANQUE:
        if requis:
            e.append("raisonnement manquant")
    elif not (isinstance(raisonnement, list) and raisonnement and all(_texte(x) for x in raisonnement)):
        e.append("raisonnement : liste d'étapes non vides attendue")

    if "solution" in objet:
        if not _texte(objet["solution"]):
            e.append("solution vide")
    elif requis:
        e.append("solution manquante")

    if "proto" in objet and not isinstance(objet["proto"], str):
        e.append("proto doit être un texte")
    if "code" in objet and not (isinstance(objet["code"], str) and not re.search(r"[\r\n]", objet["code"])):
        e.append("code : une seule ligne de texte")
    for groupe in ("piliers", "echanges"):
        e += _erreurs_poids(objet.get(groupe, MANQUE), groupe, GROUPES_DE_POIDS[groupe])
    return e


def _erreurs_poids(groupe, nom, cles) -> list:
    if groupe is MANQUE:
        return []
    if not isinstance(groupe, dict):
        return [f"{nom} doit être un objet"]
    return [f"{nom}.{k} : nombre de 0 à 1 attendu" for k in cles if k in groupe and not _poids(groupe[k])]


def erreurs_schema(objet) -> list:
    """Écarts au schéma officiel si le paquet jsonschema est installé ; sinon une liste vide."""
    try:
        import jsonschema
    except ImportError:
        return []
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validateur = jsonschema.Draft202012Validator(schema)
    return [f"schéma : {'/'.join(map(str, err.absolute_path)) or '(racine)'} : {err.message}"
            for err in validateur.iter_errors(objet)]


def compter_phrases(texte: str) -> int:
    """Nombre approximatif de phrases (sert aux avertissements seulement)."""
    texte = re.sub(r"\s+", " ", (texte or "").strip())
    if not texte:
        return 0
    return len(re.split(r"(?<=[.!?…])\s+(?=[A-ZÀ-ÖØ-Þ«\"0-9])", texte))


def valider(objet, blocs=None):
    """Vérifie une sortie : (erreurs, avertissements). Sans erreur, elle est conforme au format 1.0."""
    erreurs = erreurs_de_forme(objet)
    if not erreurs:
        erreurs = erreurs_schema(objet)
    avert = []
    st = statut(objet)
    if not erreurs:
        if st == "monte":
            vals = sceaux_du_canon(objet.get("canon"))
            if not passe(vals):
                erreurs.append("règle 3.4 : présenté comme solution, le geste ne passe pas "
                               f"le triple sceau ({ecrire_sceaux(vals)})")
        if st == "question_plus_juste" and "?" not in objet.get("solution", ""):
            avert.append("3.6 : la solution devrait être une question")
        if st != "voie_courte":
            n = len(objet.get("raisonnement", []))
            if not 2 <= n <= 4:
                avert.append(f"2.3 : {n} étape(s) de raisonnement, 2 à 4 attendues")
            p = compter_phrases(objet.get("reponse", ""))
            if not 2 <= p <= 3:
                avert.append(f"2.3 : environ {p} phrase(s) dans la réponse, 2 à 3 attendues")
        code = objet.get("code")
        if isinstance(code, str) and len(code) > 90:
            avert.append(f"4 : code de {len(code)} caractères, 90 au plus")
    if blocs and blocs.get("json") is not None:
        for nom, (bas, haut) in (("dissection", (4, 8)), ("generation", (4, 10))):
            t = blocs.get(nom)
            if t is None:
                if st != "voie_courte":
                    erreurs.append(f"4 : bloc <{nom}> manquant")
                continue
            lignes = [l for l in t.splitlines() if l.strip()]
            if not bas <= len(lignes) <= haut:
                avert.append(f"4 : {len(lignes)} ligne(s) dans <{nom}>, {bas} à {haut} attendues")
            if "{" in t or "}" in t:
                avert.append(f"4 : accolade dans le bloc <{nom}>")
    elif blocs and any(blocs.get(k) is not None for k in ("dissection", "generation")):
        erreurs.append("4 : bloc <json> manquant")
    return erreurs, avert


def rendre_pour_juge(texte: str, bras: str) -> str:
    """Ce qu'une personne lit. Pour la tour : réponse, raisonnement et solution ; sinon le texte tel quel."""
    if bras != "tour":
        return texte.strip()
    _, objet = lire_sortie(texte)
    if isinstance(objet, dict) and _texte(objet.get("reponse")):
        morceaux = [objet["reponse"].strip()]
        r = objet.get("raisonnement")
        if isinstance(r, list) and r:
            morceaux.append("Raisonnement :\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(r, 1)))
        if _texte(objet.get("solution")):
            morceaux.append("Solution : " + objet["solution"].strip())
        return "\n\n".join(morceaux)
    return re.sub(r"</?(dissection|generation|json)>", "", texte).strip()


def extraire_constitution(markdown: str) -> str:
    """Le premier bloc ```text d'un fichier de constitution."""
    m = re.search(r"```text\n(.*?)\n```", markdown, re.S)
    if not m:
        raise ValueError("aucun bloc ```text dans ce fichier")
    return m.group(1)


# --- compteur ---------------------------------------------------------------

def jetons(texte: str, sorte: str = "fr") -> int:
    """Estimation 5.2, quand l'API ne donne pas l'usage."""
    return round(len(texte or "") / CARACTERES_PAR_JETON[sorte])


def energie_wh(lus: float, ecrits: float) -> float:
    return lus * WH_PAR_JETON_LU + ecrits * WH_PAR_JETON_ECRIT


def secondes_de_tour(wh: float) -> float:
    return wh / WH_PAR_SECONDE_DE_TOUR


def approx(x: float, chiffres: int = 2) -> str:
    """« ≈ » et au plus deux chiffres significatifs, à la française (5.3)."""
    if x == 0:
        return "≈ 0"
    decimales = chiffres - 1 - math.floor(math.log10(abs(x)))
    v = round(x, decimales)
    if decimales > 0:
        return "≈ " + f"{v:.{decimales}f}".replace(".", ",")
    return "≈ " + f"{int(v):,}".replace(",", " ")


def compteur(lus: float, ecrits: float) -> str:
    wh = energie_wh(lus, ecrits)
    return f"{approx(lus + ecrits)} jetons · {approx(wh)} Wh · {approx(secondes_de_tour(wh))} s de tour"


# --- accord entre évaluateurs -------------------------------------------------

def accord(paires):
    """Part des paires identiques, ou None."""
    paires = [(a, b) for a, b in paires if a is not None and b is not None]
    return sum(a == b for a, b in paires) / len(paires) if paires else None


def kappa_pondere(paires):
    """Kappa de Cohen à poids linéaires sur l'échelle −1, 0, +1 ; None s'il n'est pas défini."""
    echelle = (-1, 0, 1)
    paires = [(a, b) for a, b in paires if a in echelle and b in echelle]
    n = len(paires)
    if not n:
        return None
    o = [[0] * 3 for _ in echelle]
    for a, b in paires:
        o[echelle.index(a)][echelle.index(b)] += 1
    lignes = [sum(r) for r in o]
    colonnes = [sum(o[i][j] for i in range(3)) for j in range(3)]
    observe = attendu = 0.0
    for i in range(3):
        for j in range(3):
            poids = abs(i - j) / 2
            observe += poids * o[i][j]
            attendu += poids * lignes[i] * colonnes[j] / n
    return None if attendu == 0 else 1 - observe / attendu


# --- exemples ---------------------------------------------------------------

def verifier_exemples(chemin=EXEMPLES):
    """Valide chaque exemple et la cohérence de son annotation : (lignes, nombre de problèmes)."""
    exemples = json.loads(pathlib.Path(chemin).read_text(encoding="utf-8"))
    lignes, problemes = [], 0
    for ex in exemples:
        rep, ann = ex["reponse"], ex["annotation"]
        erreurs, avert = valider(rep)
        gold = None
        if ann.get("sceaux"):
            gold = tuple(valeur(ann["sceaux"][s]["valeur"]) for s in SCEAUX)
        st, verdict = statut(rep), ann["verdict"]
        coherent = {
            "voie_courte": st == "voie_courte" and gold is None,
            "monte": st == "monte" and passe(gold),
            "ne_monte_pas": gold is not None and not passe(gold),
            "question_plus_juste": st == "question_plus_juste" and gold is not None,
        }.get(verdict, False)
        ok = not erreurs and coherent
        problemes += not ok
        etat = "ok" if ok else ("; ".join(erreurs) or "annotation incohérente")
        lignes.append((ex["id"], ex["titre"], st, ecrire_sceaux(sceaux_du_canon(rep.get("canon"))),
                       ecrire_sceaux(gold), verdict, etat, avert))
    return lignes, problemes


# --- ligne de commande --------------------------------------------------------

def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(prog="antimars", description="Outils de référence du noyau Antimars 1.0.")
    sous = p.add_subparsers(dest="commande", required=True)
    v = sous.add_parser("valider", help="vérifie une sortie : trois blocs, ou un objet JSON")
    v.add_argument("fichier")
    c = sous.add_parser("compter", help="jetons, Wh et secondes de tour d'une sortie")
    c.add_argument("fichier")
    c.add_argument("--lus", type=int, default=0, help="jetons lus (prompt et question), s'ils sont connus")
    c.add_argument("--sorte", choices=sorted(CARACTERES_PAR_JETON), default="fr")
    sous.add_parser("exemples", help="vérifie les exemples annotés")
    a = p.parse_args(argv)

    if a.commande == "valider":
        texte = pathlib.Path(a.fichier).read_text(encoding="utf-8")
        blocs, objet = lire_sortie(texte)
        erreurs, avert = valider(objet, blocs)
        if erreurs:
            print("non conforme au format 1.0")
            for x in erreurs:
                print("  erreur :", x)
        else:
            vals = sceaux_du_canon(objet.get("canon"))
            print(f"conforme au format 1.0 · statut {statut(objet)} · sceaux {ecrire_sceaux(vals)}"
                  + (" · passe" if passe(vals) else ""))
        for x in avert:
            print("  avertissement :", x)
        return 1 if erreurs else 0

    if a.commande == "compter":
        texte = pathlib.Path(a.fichier).read_text(encoding="utf-8")
        ecrits = jetons(texte, a.sorte)
        print(compteur(a.lus, ecrits))
        print(f"  jetons écrits estimés : {ecrits} ; jetons lus : {a.lus}")
        return 0

    lignes, problemes = verifier_exemples()
    for id_, titre, st, sceaux, gold, verdict, etat, avert in lignes:
        print(f"{id_}  {titre:<34} {st:<20} réponse {sceaux:<9} annotation {gold:<9} {verdict:<20} {etat}")
        for x in avert:
            print("      avertissement :", x)
    print(f"{len(lignes)} exemples, {problemes} problème(s)")
    return 1 if problemes else 0


if __name__ == "__main__":
    sys.exit(main())