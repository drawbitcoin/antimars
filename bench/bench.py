#!/usr/bin/env python3
"""Antimars test bench: the same model answers the same questions, with or without the constitution.

Three arms: without (the question alone), core (portable constitution), tower (founding prompt).
A neutral judge, who knows nothing of Antimars, scores what the answer brings the person.
A canon judge scores the three seals, twice and in two orders, to measure agreement.
Calibration compares the canon judge with the annotations of the examples.

    export ANTHROPIC_API_KEY=…
    python bench/bench.py --provider anthropic --model <model>

    export OPENAI_API_KEY=…         # or any compatible API: --base-url and --key-env
    python bench/bench.py --provider openai --model <model>

    python bench/bench.py --provider simulated      # no network: checks the bench pipeline

The judge can be another model: --judge-provider, --judge-model.
Results: bench/results/<timestamp>/ (generations.jsonl, judges.jsonl, summary.json, report.md).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import random
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import antimars as am  # noqa: E402

ARMS = ("without", "core", "tower")
LETTERS = "ABC"
CRITERIA = ("usefulness", "accuracy", "clarity", "respect", "sobriety")
JUDGE_SEALS = ("human", "planet", "living")  # same order as am.SEALS (homme, planete, vivant)


# --- providers -------------------------------------------------------------------

def _post(url, headers, body, attempts=4):
    data = json.dumps(body).encode("utf-8")
    for attempt in range(attempts):
        request = urllib.request.Request(url, data=data, headers={**headers, "content-type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=300) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and attempt < attempts - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}") from None
        except urllib.error.URLError:
            if attempt < attempts - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise


def _key(name):
    key = os.environ.get(name)
    if not key:
        sys.exit(f"Environment variable {name} is not set.")
    return key


class Anthropic:
    def __init__(self, model, key_env=None, base_url=None, max_tokens=None):
        self.model, self.max = model, max_tokens or 2000
        self.base = (base_url or "https://api.anthropic.com").rstrip("/")
        self.key = _key(key_env or "ANTHROPIC_API_KEY")

    def call(self, text):
        r = _post(f"{self.base}/v1/messages", {"x-api-key": self.key, "anthropic-version": "2023-06-01"},
                  {"model": self.model, "max_tokens": self.max, "messages": [{"role": "user", "content": text}]})
        output = "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")
        u = r.get("usage") or {}
        return {"text": output, "read": u.get("input_tokens"), "written": u.get("output_tokens")}


class OpenAICompatible:
    def __init__(self, model, key_env=None, base_url=None, max_tokens=None):
        self.model, self.max = model, max_tokens
        self.base = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.key = _key(key_env or "OPENAI_API_KEY")

    def call(self, text):
        body = {"model": self.model, "messages": [{"role": "user", "content": text}]}
        if self.max:
            body["max_tokens"] = self.max
        r = _post(f"{self.base}/chat/completions", {"authorization": f"Bearer {self.key}"}, body)
        output = (r["choices"][0]["message"].get("content") or "") if r.get("choices") else ""
        u = r.get("usage") or {}
        return {"text": output, "read": u.get("prompt_tokens"), "written": u.get("completion_tokens")}


class Simulated:
    """No network and deterministic: checks the bench pipeline, never a model."""

    SIMPLE_ANSWERS = {"17 × 23": "391.", "Australia": "Canberra.", "thank you": "Grazie."}

    def __init__(self, *_, **__):
        pass

    @staticmethod
    def _seals(n):
        return {"human": n % 3 - 1, "planet": (n // 3) % 3 - 1, "living": (n // 9) % 3 - 1}

    def call(self, text):
        h = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
        if "one entry per case" in text:
            ids = re.findall(r"### Case (ex\d+)", text)
            return self._json({i: self._seals(h >> (5 * k)) for k, i in enumerate(ids)})
        if "one entry per answer" in text:
            letters = re.findall(r"### Answer ([ABC])", text)
            if "find the main gesture" in text:
                return self._json({l: {"gesture": "a gesture", **self._seals(h >> (5 * k)), "refusal": False,
                                       "fairer_question": k == 0, "lecture": False}
                                   for k, l in enumerate(letters)})
            scores = {l: {c: 1 + (h >> (7 * k + j)) % 5 for j, c in enumerate(CRITERIA)} for k, l in enumerate(letters)}
            for k, l in enumerate(letters):
                scores[l]["dubious_figures"] = (h >> k) % 2
            ranking = sorted(letters, key=lambda l: -scores[l]["usefulness"])
            return self._json({**scores, "ranking": ranking, "why": "simulated"})
        for key, answer in self.SIMPLE_ANSWERS.items():
            if key in text.rsplit("Question:", 1)[-1][-200:]:
                return {"text": answer, "read": None, "written": None}
        if text.startswith("# MARS FIELD"):
            example = json.loads(am.EXAMPLES.read_text(encoding="utf-8"))[1 + h % 9]["response"]
            output = ("<dissection>\n- a\n- b\n- c\n- d\n</dissection>\n<generation>\n- a\n- b\n- c\n- d\n"
                      "</generation>\n<json>" + json.dumps(example, ensure_ascii=False) + "</json>")
            return {"text": output, "read": None, "written": None}
        if "Antimars · core" in text:
            return {"text": "Heard: …\nAt stake: …\nA simulated answer.\nGesture: a gesture.\n"
                            "Seals: human +1 · planet 0 · living 0", "read": None, "written": None}
        return {"text": "A simulated answer, without constitution.", "read": None, "written": None}

    @staticmethod
    def _json(obj):
        return {"text": json.dumps(obj, ensure_ascii=False), "read": None, "written": None}


PROVIDERS = {"anthropic": Anthropic, "openai": OpenAICompatible, "simulated": Simulated}


# --- prompts ---------------------------------------------------------------------

def load():
    corpus = json.loads((HERE / "corpus.json").read_text(encoding="utf-8"))
    portable = am.extract_constitution((ROOT / "constitution" / "portable.en.md").read_text(encoding="utf-8"))
    tower = (ROOT / "constitution" / "tower.en.md").read_text(encoding="utf-8")
    judges = {k: (HERE / "judges" / f"{k}.txt").read_text(encoding="utf-8") for k in ("neutral", "canon", "calibration")}
    examples = json.loads(am.EXAMPLES.read_text(encoding="utf-8"))
    return corpus, portable, tower, judges, examples


def prompt(arm, question, portable, tower):
    if arm == "without":
        return question
    if arm == "core":
        return f"{portable}\n\nQuestion: {question}"
    return tower + question


def order(seed, key):
    o = list(ARMS)
    random.Random(f"{seed}:{key}").shuffle(o)
    return o


def answers_block(o, rendered):
    return "\n\n".join(f"### Answer {LETTERS[i]}\n{rendered[a][:6000]}" for i, a in enumerate(o))


def cases_block(examples):
    parts = []
    for ex in examples:
        if ex["annotation"].get("seals"):
            resp = ex["response"]
            parts.append(f"### Case {ex['id']}\nQuestion: {ex['question']}\n"
                         f"Answer: {resp['reponse']}\nGesture: {resp.get('solution', '')}")
    return "\n\n".join(parts)


# --- measures ------------------------------------------------------------------------

def _integer(x):
    """A seal returned by a judge: 1, "+1", "−1"… brought back to -1, 0 or 1, otherwise None."""
    if isinstance(x, str):
        try:
            x = int(x.strip().replace("+", "").replace("−", "-"))
        except ValueError:
            return None
    return am.seal_value(x)


def _true(x):
    return x is True or (isinstance(x, str) and x.strip().lower() == "true")


def _number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _mean(xs):
    xs = [x for x in xs if _number(x)]
    return sum(xs) / len(xs) if xs else None


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def _verdict(judges, q, kind, arm):
    j = judges.get((q, kind))
    if not j or not isinstance(j.get("data"), dict):
        return None
    v = j["data"].get(LETTERS[j["order"].index(arm)])
    return v if isinstance(v, dict) else None


def _seals(v):
    vals = tuple(_integer(v.get(s)) for s in JUDGE_SEALS)
    return None if None in vals else vals


def measure(corpus, gens, judges, calibration, examples):
    rich = [c["id"] for c in corpus if c["type"] != "simple"]
    tensions = {c["id"] for c in corpus if c["type"] == "tension"}
    ordinary = {c["id"] for c in corpus if c["type"] == "ordinary"}
    simple = [c for c in corpus if c["type"] == "simple"]
    res = {}
    for a in ARMS:
        r = {}
        scored = []
        for q in rich:
            v = _verdict(judges, q, "canonA", a)
            s = _seals(v) if v else None
            if s:
                scored.append((q, v, s))
        passing = [q for q, _, s in scored if am.passes(s)]
        r["judged"] = len(scored)
        r["seal_ok"] = len(passing) / len(scored) if scored else None
        r["harmful"] = sum(1 for _, _, s in scored if min(s) < 0)
        for i, name in enumerate(JUDGE_SEALS):
            r["mean_" + name] = _mean([s[i] for _, _, s in scored])
        tv = [(v, s) for q, v, s in scored if q in tensions]
        good = [_true(v.get("fairer_question")) or am.passes(s) for v, s in tv]
        flat = [_true(v.get("refusal")) and not _true(v.get("fairer_question")) for v, _ in tv]
        r["tension_ok"] = sum(1 for x, y in zip(good, flat) if x and not y) / len(tv) if tv else None
        r["ordinary_refusals"] = sum(1 for q, v, _ in scored if q in ordinary and _true(v.get("refusal")))
        r["lectures"] = sum(1 for _, v, _ in scored if _true(v.get("lecture")))

        neutral = [v for v in (_verdict(judges, c["id"], "neutral", a) for c in corpus) if v]
        for crit in CRITERIA:
            r[crit] = _mean([v.get(crit) for v in neutral])
        r["dubious_figures"] = sum(v["dubious_figures"] for v in neutral if _number(v.get("dubious_figures")))
        ranks = []
        for c in corpus:
            j = judges.get((c["id"], "neutral"))
            if j and isinstance(j.get("data"), dict) and isinstance(j["data"].get("ranking"), list):
                ranking = [str(x).strip() for x in j["data"]["ranking"]]
                letter = LETTERS[j["order"].index(a)]
                if letter in ranking:
                    ranks.append(ranking.index(letter) + 1)
        r["rank"] = _mean(ranks)
        r["first"] = sum(1 for x in ranks if x == 1) / len(ranks) if ranks else None

        r["simple_exact"] = sum(1 for c in simple
                                if _norm(c["expected"]) in _norm(gens.get((c["id"], a), {}).get("text", "")))
        r["simple_tokens"] = _mean([gens[(c["id"], a)]["written"] for c in simple if (c["id"], a) in gens])
        r["relay_valid"] = None
        if a == "tower":
            valid = []
            for c in corpus:
                g = gens.get((c["id"], a))
                if g and g["text"]:
                    blocks, obj = am.read_output(g["text"])
                    valid.append(not am.validate(obj, blocks)[0])
            r["relay_valid"] = sum(valid) / len(valid) if valid else None

        ga = [gens[(c["id"], a)] for c in corpus if (c["id"], a) in gens]
        whs = [am.energy_wh(g["read"], g["written"]) for g in ga]
        r["read_tokens"] = _mean([g["read"] for g in ga])
        r["written_tokens"] = _mean([g["written"] for g in ga])
        r["wh"] = _mean(whs)
        r["wh_total"] = sum(whs)
        r["tower_seconds"] = am.tower_seconds(sum(whs))
        wh_rich = sum(am.energy_wh(gens[(q, a)]["read"], gens[(q, a)]["written"]) for q in rich if (q, a) in gens)
        r["wh_per_gesture"] = wh_rich / len(passing) if passing else None
        res[a] = r

    pairs = []
    for q in rich:
        for a in ARMS:
            x, y = _verdict(judges, q, "canonA", a), _verdict(judges, q, "canonB", a)
            sx, sy = (_seals(x) if x else None), (_seals(y) if y else None)
            if sx and sy:
                pairs += list(zip(sx, sy))
    pairs_c = []
    if isinstance(calibration, dict):
        for ex in examples:
            gold, j = ex["annotation"].get("seals"), calibration.get(ex["id"])
            sj = _seals(j) if isinstance(j, dict) else None
            if gold and sj:
                pairs_c += list(zip(sj, (gold[s]["value"] for s in am.ANNOTATION_SEALS)))
    return {
        "arms": res,
        "agreement": {"pairs": len(pairs), "exact": am.agreement(pairs), "kappa": am.weighted_kappa(pairs)},
        "calibration": {"pairs": len(pairs_c), "exact": am.agreement(pairs_c), "kappa": am.weighted_kappa(pairs_c)},
    }


# --- report --------------------------------------------------------------------------

# (key, label, format, direction): direction +1, higher is better; -1, lower is better.
ROWS = [
    ("seal_ok", "Gestures that pass the triple seal", "pct", 1),
    ("harmful", "Harmful gestures (a −1)", "n", -1),
    ("tension_ok", "Tensions well redirected", "pct", 1),
    ("ordinary_refusals", "Refusals of ordinary questions", "n", -1),
    ("lectures", "Unrequested lectures", "n", -1),
    ("usefulness", "Usefulness, 1 to 5", "f", 1),
    ("accuracy", "Accuracy, 1 to 5", "f", 1),
    ("clarity", "Clarity, 1 to 5", "f", 1),
    ("respect", "Respect, 1 to 5", "f", 1),
    ("sobriety", "Sobriety, 1 to 5", "f", 1),
    ("rank", "Mean rank with the neutral judge (1 = preferred)", "f", -1),
    ("dubious_figures", "Dubious figures", "n", -1),
    ("simple_exact", "Simple questions answered right", "n", 1),
    ("simple_tokens", "Written tokens, simple questions", "t", -1),
    ("relay_valid", "Outputs in format 1.0", "pct", 1),
    ("read_tokens", "Read tokens per answer", "t", -1),
    ("written_tokens", "Written tokens per answer", "t", -1),
    ("wh", "Wh per answer", "wh", -1),
    ("wh_per_gesture", "Wh per gesture that passes", "wh", -1),
    ("tower_seconds", "Seconds of tower, whole arm", "wh", -1),
]


def _fmt(x, kind):
    if x is None:
        return "—"
    if kind == "pct":
        return f"{round(100 * x)}%"
    if kind == "n":
        return str(int(x))
    if kind == "t":
        return str(round(x))
    if kind == "wh":
        return am.approx(x)
    return f"{x:.2f}"


def report(summary, config, corpus, judges):
    l = [f"# Antimars test bench · {config['date']}", "",
         f"Model tested: `{config['model']}` ({config['provider']}) · judge: `{config['judge_model']}` "
         f"({config['judge_provider']}) · {len(corpus)} questions · seed {config['seed']}", "",
         "| | Without | Core | Tower |", "|---|---|---|---|"]
    for key, label, kind, _ in ROWS:
        l.append(f"| {label} | " + " | ".join(_fmt(summary["arms"][a].get(key), kind) for a in ARMS) + " |")
    for name, title in (("agreement", "Agreement between the two passes of the canon judge"),
                        ("calibration", "Calibration of the canon judge on the annotated examples")):
        x = summary[name]
        kappa = "—" if x["kappa"] is None else f"{x['kappa']:.2f}"
        l += ["", f"**{title}**: {_fmt(x['exact'], 'pct')} exact agreement, weighted κ {kappa}, over {x['pairs']} seals."]
    l += ["", "## Seals per question (canon judge, first pass)", "", "| Question | Without | Core | Tower |", "|---|---|---|---|"]
    for c in corpus:
        if c["type"] == "simple":
            continue
        cells = []
        for a in ARMS:
            v = _verdict(judges, c["id"], "canonA", a)
            s = _seals(v) if v else None
            cells.append("—" if not s else am.format_seals(s) + (" ✓" if am.passes(s) else " ✗"))
        l.append(f"| {c['question']} | " + " | ".join(cells) + " |")
    l += ["", "The judge often belongs to the same family as the model tested, and the shape of the answers "
              "sometimes gives the arm away: these figures measure a trend, not a truth. "
              "One answer per question and per arm: run the bench again with another seed to see the variance."]
    return "\n".join(l) + "\n"


# --- run -----------------------------------------------------------------------------

def call_judge(provider, text, cost):
    try:
        r = provider.call(text)
    except Exception as e:  # noqa: BLE001: a failing judge must not stop the bench
        return None, str(e)
    read = r["read"] if r["read"] is not None else am.tokens(text)
    written = r["written"] if r["written"] is not None else am.tokens(r["text"])
    cost.append(am.energy_wh(read, written))
    obj = am.read_json(r["text"])
    return obj, (None if obj else "unreadable judge answer")


def main(argv=None):
    p = argparse.ArgumentParser(description="Antimars test bench: with or without the constitution.")
    p.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    p.add_argument("--model", default="simulated")
    p.add_argument("--base-url")
    p.add_argument("--key-env", help="environment variable that holds the key")
    p.add_argument("--max-tokens", type=int)
    p.add_argument("--judge-provider", choices=sorted(PROVIDERS))
    p.add_argument("--judge-model")
    p.add_argument("--judge-base-url")
    p.add_argument("--judge-key-env")
    p.add_argument("--questions", help="comma-separated identifiers, for example s1,r3,t2")
    p.add_argument("--seed", default="antimars-1.0")
    p.add_argument("--out", help="results folder")
    a = p.parse_args(argv)

    corpus, portable, tower, templates, examples = load()
    if a.questions:
        wanted = set(a.questions.split(","))
        corpus = [c for c in corpus if c["id"] in wanted]
    tested = PROVIDERS[a.provider](a.model, a.key_env, a.base_url, a.max_tokens)
    jp = a.judge_provider or a.provider
    judge = PROVIDERS[jp](a.judge_model or a.model, a.judge_key_env or a.key_env,
                          a.judge_base_url or a.base_url, None)
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    config = {"date": date, "provider": a.provider, "model": a.model, "judge_provider": jp,
              "judge_model": a.judge_model or a.model, "seed": a.seed, "core": "1.0"}
    folder = pathlib.Path(a.out) if a.out else HERE / "results" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    folder.mkdir(parents=True, exist_ok=True)

    gens, judges, judge_cost = {}, {}, []
    total = len(corpus) * len(ARMS)
    for i, c in enumerate(corpus):
        for k, arm in enumerate(ARMS):
            text_prompt = prompt(arm, c["question"], portable, tower)
            t0 = time.time()
            error = None
            try:
                r = tested.call(text_prompt)
            except Exception as e:  # noqa: BLE001
                r, error = {"text": "", "read": None, "written": None}, str(e)
            measured = r["read"] is not None and r["written"] is not None
            gens[(c["id"], arm)] = {
                "q": c["id"], "arm": arm, "text": r["text"], "measured": measured, "error": error,
                "read": r["read"] if measured else am.tokens(text_prompt),
                "written": r["written"] if measured else am.tokens(r["text"]),
                "seconds": round(time.time() - t0, 1),
            }
            print(f"[{i * len(ARMS) + k + 1}/{total}] {c['id']} · {arm}" + (f" · error: {error}" if error else ""))

    for c in corpus:
        rendered = {arm: am.render_for_judge(gens[(c["id"], arm)]["text"], arm) for arm in ARMS}
        kinds = ["neutral"] + (["canonA", "canonB"] if c["type"] != "simple" else [])
        for kind in kinds:
            o = order(a.seed, f"{c['id']}:{kind}")
            template = templates["neutral" if kind == "neutral" else "canon"]
            text_judge = template.replace("{QUESTION}", c["question"]).replace("{ANSWERS}", answers_block(o, rendered))
            data, error = call_judge(judge, text_judge, judge_cost)
            judges[(c["id"], kind)] = {"q": c["id"], "kind": kind, "order": o, "data": data, "error": error}
            print(f"judge {kind} · {c['id']}" + (f" · {error}" if error else ""))
    calibration, error = call_judge(judge, templates["calibration"].replace("{CASES}", cases_block(examples)), judge_cost)
    print("calibration" + (f" · {error}" if error else ""))

    summary = measure(corpus, gens, judges, calibration, examples)
    summary["judge_cost_wh"] = sum(judge_cost)
    summary["config"] = config
    with open(folder / "generations.jsonl", "w", encoding="utf-8") as f:
        for g in gens.values():
            f.write(json.dumps(g, ensure_ascii=False) + "\n")
    with open(folder / "judges.jsonl", "w", encoding="utf-8") as f:
        for j in judges.values():
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
        f.write(json.dumps({"kind": "calibration", "data": calibration}, ensure_ascii=False) + "\n")
    (folder / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "report.md").write_text(report(summary, config, corpus, judges), encoding="utf-8")
    print(f"Report: {folder / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
