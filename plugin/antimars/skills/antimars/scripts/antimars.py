#!/usr/bin/env python3
"""Antimars · core 1.0 · reference tools.

    python tools/antimars.py validate output.txt           # format 1.0 and canon rules
    python tools/antimars.py count output.txt --read 2100  # tokens, Wh, seconds of tower
    python tools/antimars.py examples                      # checks the ten annotated examples
    python tools/antimars.py bande sortie.txt --question "…"   # bandeau Antimars d'une question
    python tools/antimars.py bande sortie.txt --picto --latin "…"   # le pictogramme, une ligne latine

Standard library only. If the jsonschema package is installed, the official
schema is checked as well.

The keys and enum values of the JSON block (statut, interpretation, canon, sceau…)
are the wire format of core 1.0 and stay in French; see the glossary in SPEC.md.
"""
from __future__ import annotations

import html as _html
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema" / "antimars-1.0.schema.json"
EXAMPLES = ROOT / "examples" / "examples-1.0.json"
BANDE = ROOT / "assets" / "bande-antimars.html"
PICTO = ROOT / "assets" / "picto-antimars.html"
BANDE_MARK = "__ANTIMARS_WINDOW_DATA__"
PICTO_LATIN, PICTO_GOLD, GOLD = "__LATIN__", "__OR__", "#D4A72C"

# Wire format 1.0 (French keys, kept as is).
SEALS = ("homme", "planete", "vivant")                       # human, planet, living
STATUSES = ("monte", "question_plus_juste", "voie_courte")   # rises, fairer question, short path
FRAGMENTS = ("entendue", "energie", "pensee", "abstraction", "vivant", "enjeu")
MISSING = object()  # tells an absent field from a field set to null
WEIGHT_GROUPS = {
    "poids": ("energie", "pensee", "abstraction", "vivant"),
    "piliers": ("geometrie", "rationalite", "creativite", "paix"),
    "echanges": ("geometrie_rationalite", "rationalite_creativite", "creativite_paix", "paix_geometrie"),
}
# Annotation seals in examples/examples-1.0.json, in the same order as SEALS.
ANNOTATION_SEALS = ("human", "planet", "living")

# Counter: section 5 of the specification.
WH_PER_WRITTEN_TOKEN = 0.0006
WH_PER_READ_TOKEN = 0.00003
WH_PER_TOWER_SECOND = 56.0
CHARS_PER_TOKEN = {"fr": 3.6, "en": 4.0, "code": 3.0}


# --- reading ----------------------------------------------------------------

def block(text: str, name: str):
    """Content of the <name>…</name> block, or None if missing. An unclosed block runs to the end."""
    start = text.find(f"<{name}>")
    if start < 0:
        return None
    start += len(name) + 2
    end = text.find(f"</{name}>", start)
    return (text[start:] if end < 0 else text[start:end]).strip()


def read_json(text):
    """The first readable JSON object in a text; tolerates ``` fences and a sentence around it."""
    if not text:
        return None
    text = re.sub(r"```(?:json)?", "", text)
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        obj = json.loads(text[a:b + 1])
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def read_output(text: str):
    """Splits an Antimars output into (blocks, object of the json block or None)."""
    blocks = {name: block(text, name) for name in ("dissection", "generation", "json")}
    source = blocks["json"] if blocks["json"] is not None else text
    return blocks, read_json(source)


# --- canon ------------------------------------------------------------------

def seal_value(x):
    """A seal: -1, 0 or 1; None for anything else (true and false are not seals)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    return int(x) if x in (-1, 0, 1) else None


def canon_seals(canon):
    """(homme, planete, vivant) read from a canon, or None if one is missing."""
    if not isinstance(canon, dict):
        return None
    values = []
    for name in SEALS:
        entry = canon.get(name)
        v = seal_value(entry.get("sceau")) if isinstance(entry, dict) else None
        if v is None:
            return None
        values.append(v)
    return tuple(values)


def passes(values) -> bool:
    """Rule 3.4: no −1 and at least one +1."""
    return values is not None and min(values) >= 0 and max(values) == 1


def status(obj):
    return obj.get("statut", "monte") if isinstance(obj, dict) else None


def format_seals(values) -> str:
    if values is None:
        return "—"
    return " ".join({1: "+1", 0: "0", -1: "−1"}[v] for v in values)


# --- validation -------------------------------------------------------------

def _text(x) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _weight(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and 0 <= x <= 1


def shape_errors(obj) -> list:
    """What schema/antimars-1.0.schema.json requires, checked by hand."""
    if not isinstance(obj, dict):
        return ["the json block is not an object"]
    e = []
    st = obj.get("statut", "monte")
    if "statut" in obj and st not in STATUSES:
        e.append(f"unknown statut: {st!r}")
    if "antimars" in obj and not (isinstance(obj["antimars"], str)
                                  and re.fullmatch(r"1\.[0-9]+", obj["antimars"])):
        e.append("antimars: expected a version of the form 1.x")
    if not _text(obj.get("reponse")):
        e.append("reponse missing or empty")
    required = st != "voie_courte"

    it = obj.get("interpretation", MISSING)
    if it is MISSING:
        if required:
            e.append("interpretation missing")
    elif not isinstance(it, dict):
        e.append("interpretation must be an object")
    else:
        e += [f"interpretation.{k} missing or empty" for k in FRAGMENTS if not _text(it.get(k))]
        e += _weight_errors(it.get("poids", MISSING), "interpretation.poids", WEIGHT_GROUPS["poids"])

    canon = obj.get("canon", MISSING)
    if canon is MISSING:
        if required:
            e.append("canon missing")
    elif not isinstance(canon, dict):
        e.append("canon must be an object")
    else:
        for name in SEALS:
            entry = canon.get(name)
            if not isinstance(entry, dict):
                e.append(f"canon.{name} missing")
                continue
            if seal_value(entry.get("sceau")) is None:
                e.append(f"canon.{name}.sceau must be -1, 0 or 1")
            if not isinstance(entry.get("pourquoi"), str):
                e.append(f"canon.{name}.pourquoi missing")
        if "note" in canon and not isinstance(canon["note"], str):
            e.append("canon.note must be a text")

    reasoning = obj.get("raisonnement", MISSING)
    if reasoning is MISSING:
        if required:
            e.append("raisonnement missing")
    elif not (isinstance(reasoning, list) and reasoning and all(_text(x) for x in reasoning)):
        e.append("raisonnement: expected a list of non-empty steps")

    if "solution" in obj:
        if not _text(obj["solution"]):
            e.append("solution empty")
    elif required:
        e.append("solution missing")

    if "proto" in obj and not isinstance(obj["proto"], str):
        e.append("proto must be a text")
    if "code" in obj and not (isinstance(obj["code"], str) and not re.search(r"[\r\n]", obj["code"])):
        e.append("code: a single line of text")
    for group in ("piliers", "echanges"):
        e += _weight_errors(obj.get(group, MISSING), group, WEIGHT_GROUPS[group])
    return e


def _weight_errors(group, name, keys) -> list:
    if group is MISSING:
        return []
    if not isinstance(group, dict):
        return [f"{name} must be an object"]
    return [f"{name}.{k}: expected a number from 0 to 1" for k in keys if k in group and not _weight(group[k])]


def schema_errors(obj) -> list:
    """Departures from the official schema if the jsonschema package is installed; otherwise an empty list."""
    try:
        import jsonschema
    except ImportError:
        return []
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [f"schema: {'/'.join(map(str, err.absolute_path)) or '(root)'}: {err.message}"
            for err in validator.iter_errors(obj)]


def count_sentences(text: str) -> int:
    """Approximate number of sentences (used for warnings only)."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return 0
    return len(re.split(r"(?<=[.!?…])\s+(?=[A-ZÀ-ÖØ-Þ«\"“0-9])", text))


def validate(obj, blocks=None):
    """Checks an output: (errors, warnings). Without errors, it complies with format 1.0."""
    errors = shape_errors(obj)
    if not errors:
        errors = schema_errors(obj)
    warnings = []
    st = status(obj)
    if not errors:
        if st == "monte":
            vals = canon_seals(obj.get("canon"))
            if not passes(vals):
                errors.append("rule 3.4: presented as a solution, the gesture does not pass "
                              f"the triple seal ({format_seals(vals)})")
        if st == "question_plus_juste" and "?" not in obj.get("solution", ""):
            warnings.append("3.6: the solution should be a question")
        if st != "voie_courte":
            n = len(obj.get("raisonnement", []))
            if not 2 <= n <= 4:
                warnings.append(f"2.3: {n} reasoning step(s), 2 to 4 expected")
            p = count_sentences(obj.get("reponse", ""))
            if not 2 <= p <= 3:
                warnings.append(f"2.3: about {p} sentence(s) in the answer, 2 to 3 expected")
        code = obj.get("code")
        if isinstance(code, str) and len(code) > 90:
            warnings.append(f"4: code of {len(code)} characters, 90 at most")
    if blocks and blocks.get("json") is not None:
        for name, (low, high) in (("dissection", (4, 8)), ("generation", (4, 10))):
            t = blocks.get(name)
            if t is None:
                if st != "voie_courte":
                    errors.append(f"4: <{name}> block missing")
                continue
            lines = [l for l in t.splitlines() if l.strip()]
            if not low <= len(lines) <= high:
                warnings.append(f"4: {len(lines)} line(s) in <{name}>, {low} to {high} expected")
            if "{" in t or "}" in t:
                warnings.append(f"4: brace in the <{name}> block")
    elif blocks and any(blocks.get(k) is not None for k in ("dissection", "generation")):
        errors.append("4: <json> block missing")
    return errors, warnings


# A model's own seal line ("Seals: human +1 · …", or "Sceaux : homme +1 · …" in French):
# hidden from the judges so they score the gesture without being anchored by its self-rating.
SELF_SEAL_LINE = re.compile(r"^\W*(seals?|sceaux)\W*\s*:.*$", re.I | re.M)


def render_for_judge(text: str, arm: str) -> str:
    """What a person reads. For the tower: answer, reasoning and solution; otherwise the text as is,
    without the model's own seal line."""
    if arm != "tower":
        return re.sub(r"\n{3,}", "\n\n", SELF_SEAL_LINE.sub("", text)).strip()
    _, obj = read_output(text)
    if isinstance(obj, dict) and _text(obj.get("reponse")):
        parts = [obj["reponse"].strip()]
        r = obj.get("raisonnement")
        if isinstance(r, list) and r:
            parts.append("Reasoning:\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(r, 1)))
        if _text(obj.get("solution")):
            parts.append("Solution: " + obj["solution"].strip())
        return "\n\n".join(parts)
    return re.sub(r"</?(dissection|generation|json)>", "", text).strip()


def extract_constitution(markdown: str) -> str:
    """The first ```text block of a constitution file."""
    m = re.search(r"```text\n(.*?)\n```", markdown, re.S)
    if not m:
        raise ValueError("no ```text block in this file")
    return m.group(1)


# --- bandeau ------------------------------------------------------------------

def ask_data(obj, question: str = "", lang: str = "fr", read=None, written=None,
             question_fr: str = "", translation: dict = None) -> dict:
    """What the Antimars strip reads for one ask (French-native keys). The tower works in French:
    question_fr is the question translated at the root's intermediate floor, translation the
    answer and solution given back in the asker's language at the tower's intermediate floor."""
    data = {"langue": lang, "question": question, "sortie": obj}
    if question_fr:
        data["question_fr"] = question_fr
    if translation:
        data["traduction"] = translation
    if read is not None and written is not None:
        data["compteur"] = {"lus": read, "ecrits": written}
    return data


def bande_html(data: dict, standalone: bool = False, template=None) -> str:
    """assets/bande-antimars.html with one ask embedded. The fragment goes as is into an inline
    widget; standalone=True wraps it in a page that opens in any browser."""
    template = template or BANDE
    page = template.read_text(encoding="utf-8")
    if page.count(BANDE_MARK) != 1:
        raise ValueError(f"{BANDE_MARK} missing or repeated in {template.name}")
    page = page.replace(BANDE_MARK, json.dumps(data, ensure_ascii=False).replace("<", "\\u003c"))
    return _page(page, "Antimars · bandeau", "fr") if standalone else page


def picto_html(latin: str, seals, standalone: bool = False) -> str:
    """assets/picto-antimars.html, deliberately restrained: the tower on the left, one line of
    Latin on the right (the solution in synthesis, no English or French), the right tip gold
    when the triple seal passes."""
    page = PICTO.read_text(encoding="utf-8")
    for mark in (PICTO_LATIN, PICTO_GOLD):
        if page.count(mark) != 1:
            raise ValueError(f"{mark} missing or repeated in {PICTO.name}")
    page = page.replace(PICTO_LATIN, _html.escape(" ".join(latin.split()), quote=False))
    page = page.replace(PICTO_GOLD, GOLD if passes(seals) else "currentColor")
    return _page(page, "Antimars · pax", "la") if standalone else page


def _page(fragment: str, title: str, lang: str) -> str:
    """A fragment wrapped in a page that opens in any browser."""
    return (f'<!DOCTYPE html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{title}</title>\n</head>\n<body style="max-width:1000px;margin:24px auto;padding:0 16px">\n'
            + fragment + '</body>\n</html>\n')


# --- counter ----------------------------------------------------------------

def tokens(text: str, kind: str = "en") -> int:
    """Estimate 5.2, when the API does not report usage."""
    return round(len(text or "") / CHARS_PER_TOKEN[kind])


def energy_wh(read: float, written: float) -> float:
    return read * WH_PER_READ_TOKEN + written * WH_PER_WRITTEN_TOKEN


def tower_seconds(wh: float) -> float:
    return wh / WH_PER_TOWER_SECOND


def approx(x: float, digits: int = 2) -> str:
    """"≈" and at most two significant figures (5.3)."""
    if x == 0:
        return "≈ 0"
    decimals = digits - 1 - math.floor(math.log10(abs(x)))
    v = round(x, decimals)
    if v != 0:  # rounding can carry to the next power of ten (0.0996 → 0.10): count again
        decimals = digits - 1 - math.floor(math.log10(abs(v)))
        v = round(x, decimals)
    if decimals > 0:
        return "≈ " + f"{v:.{decimals}f}"
    return "≈ " + f"{int(v):,}"


def counter(read: float, written: float) -> str:
    wh = energy_wh(read, written)
    return f"{approx(read + written)} tokens · {approx(wh)} Wh · {approx(tower_seconds(wh))} s of tower"


# --- agreement between raters -------------------------------------------------

def agreement(pairs):
    """Share of identical pairs, or None."""
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    return sum(a == b for a, b in pairs) / len(pairs) if pairs else None


def weighted_kappa(pairs):
    """Cohen's kappa with linear weights on the −1, 0, +1 scale; None when undefined."""
    scale = (-1, 0, 1)
    pairs = [(a, b) for a, b in pairs if a in scale and b in scale]
    n = len(pairs)
    if not n:
        return None
    o = [[0] * 3 for _ in scale]
    for a, b in pairs:
        o[scale.index(a)][scale.index(b)] += 1
    rows = [sum(r) for r in o]
    cols = [sum(o[i][j] for i in range(3)) for j in range(3)]
    observed = expected = 0.0
    for i in range(3):
        for j in range(3):
            w = abs(i - j) / 2
            observed += w * o[i][j]
            expected += w * rows[i] * cols[j] / n
    return None if expected == 0 else 1 - observed / expected


# --- examples ---------------------------------------------------------------

def check_examples(path=EXAMPLES):
    """Validates each example and the consistency of its annotation: (rows, number of problems)."""
    examples = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    rows, problems = [], 0
    for ex in examples:
        resp, ann = ex["response"], ex["annotation"]
        errors, warnings = validate(resp)
        gold = None
        if ann.get("seals"):
            gold = tuple(seal_value(ann["seals"][s]["value"]) for s in ANNOTATION_SEALS)
        st, verdict = status(resp), ann["verdict"]
        consistent = {
            "short_path": st == "voie_courte" and gold is None,
            "rises": st == "monte" and passes(gold),
            "does_not_rise": gold is not None and not passes(gold),
            "fairer_question": st == "question_plus_juste" and gold is not None,
        }.get(verdict, False)
        ok = not errors and consistent
        problems += not ok
        state = "ok" if ok else ("; ".join(errors) or "inconsistent annotation")
        rows.append((ex["id"], ex["title"], st, format_seals(canon_seals(resp.get("canon"))),
                     format_seals(gold), verdict, state, warnings))
    return rows, problems


# --- command line -------------------------------------------------------------

def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(prog="antimars", description="Reference tools of the Antimars 1.0 core.")
    sub = p.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate", help="checks an output: three blocks, or a JSON object")
    v.add_argument("file")
    c = sub.add_parser("count", help="tokens, Wh and seconds of tower of an output")
    c.add_argument("file")
    c.add_argument("--read", type=int, default=0, help="read tokens (prompt and question), if known")
    c.add_argument("--kind", choices=sorted(CHARS_PER_TOKEN), default="en")
    sub.add_parser("examples", help="checks the annotated examples")
    w = sub.add_parser("bande", help="builds the Antimars strip of one output (an HTML page or fragment)")
    w.add_argument("file")
    w.add_argument("--question", default="", help="the question as asked")
    w.add_argument("--question-fr", default="", help="the question in French, when asked in another language")
    w.add_argument("--lang", default="fr", help="language of the question (fr, en, es…)")
    w.add_argument("--translation", help="JSON file {reponse, solution} in the language of the question")
    w.add_argument("--read", type=int, help="read tokens, to show the counter")
    w.add_argument("--kind", choices=sorted(CHARS_PER_TOKEN), default="fr")
    w.add_argument("--fragment", action="store_true", help="the bare fragment, for an inline widget")
    w.add_argument("--picto", action="store_true", help="the pictogram instead of the strip: the tower and one line of Latin")
    w.add_argument("--latin", default="", help="with --picto: the solution in one line of Latin")
    w.add_argument("--out")
    a = p.parse_args(argv)

    if a.command == "bande":
        text = pathlib.Path(a.file).read_text(encoding="utf-8")
        blocks, obj = read_output(text)
        errors, _ = validate(obj, blocks)
        if errors:
            print("does not comply with format 1.0: no strip")
            for x in errors:
                print("  error:", x)
            return 1
        if status(obj) == "voie_courte":
            print("short path: the tower does not climb, no strip")
            return 1
        if a.picto:
            if not a.latin.strip():
                print("the pictogram needs --latin: the solution in one line of Latin")
                return 1
            page = picto_html(a.latin, canon_seals(obj.get("canon")), standalone=not a.fragment)
            out = a.out or "picto-antimars.html"
            pathlib.Path(out).write_text(page, encoding="utf-8")
            print(f"{out} · {len(page.encode('utf-8'))} bytes")
            return 0
        tr = json.loads(pathlib.Path(a.translation).read_text(encoding="utf-8")) if a.translation else None
        written = tokens(text, a.kind) if a.read is not None else None
        data = ask_data(obj, a.question, a.lang, a.read, written, a.question_fr, tr)
        html = bande_html(data, standalone=not a.fragment)
        out = a.out or "bande-antimars.html"
        pathlib.Path(out).write_text(html, encoding="utf-8")
        print(f"{out} · {len(html.encode('utf-8')) // 1024} KB")
        return 0

    if a.command == "validate":
        text = pathlib.Path(a.file).read_text(encoding="utf-8")
        blocks, obj = read_output(text)
        errors, warnings = validate(obj, blocks)
        if errors:
            print("does not comply with format 1.0")
            for x in errors:
                print("  error:", x)
        else:
            vals = canon_seals(obj.get("canon"))
            print(f"complies with format 1.0 · statut {status(obj)} · seals {format_seals(vals)}"
                  + (" · passes" if passes(vals) else ""))
        for x in warnings:
            print("  warning:", x)
        return 1 if errors else 0

    if a.command == "count":
        text = pathlib.Path(a.file).read_text(encoding="utf-8")
        written = tokens(text, a.kind)
        print(counter(a.read, written))
        print(f"  estimated written tokens: {written}; read tokens: {a.read}")
        return 0

    rows, problems = check_examples()
    for id_, title, st, seals, gold, verdict, state, warnings in rows:
        print(f"{id_}  {title:<34} {st:<20} response {seals:<9} annotation {gold:<9} {verdict:<16} {state}")
        for x in warnings:
            print("      warning:", x)
    print(f"{len(rows)} examples, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
