"""Tests of the Antimars 1.0 core: python -m unittest discover -s tools"""
import copy
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import antimars as am  # noqa: E402

EXAMPLES = json.loads(am.EXAMPLES.read_text(encoding="utf-8"))


def output_in_blocks(obj, dissection=True, generation=True):
    parts = []
    if dissection:
        parts.append("<dissection>\n- a\n- b\n- c\n- d\n</dissection>")
    if generation:
        parts.append("<generation>\n- a\n- b\n- c\n- d\n</generation>")
    parts.append("<json>\n" + json.dumps(obj, ensure_ascii=False) + "\n</json>")
    return "\n".join(parts)


class Examples(unittest.TestCase):
    def test_the_ten_examples_comply_and_are_consistent(self):
        rows, problems = am.check_examples()
        self.assertEqual(len(rows), 10)
        self.assertEqual(problems, 0, [r for r in rows if r[6] != "ok"])

    def test_official_schema_and_manual_check_agree(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not installed")
        schema = json.loads(am.SCHEMA.read_text(encoding="utf-8"))
        v = jsonschema.Draft202012Validator(schema)
        cases = [ex["response"] for ex in EXAMPLES]
        damaged = copy.deepcopy(EXAMPLES[1]["response"])
        del damaged["canon"]
        cases.append(damaged)
        bad_seal = copy.deepcopy(EXAMPLES[1]["response"])
        bad_seal["canon"]["homme"]["sceau"] = 2
        cases.append(bad_seal)
        bad_weight = copy.deepcopy(EXAMPLES[9]["response"])
        bad_weight["piliers"]["paix"] = 1.5
        cases.append(bad_weight)
        short_without_answer = {"statut": "voie_courte"}
        cases.append(short_without_answer)
        cases.append({"statut": "voie_courte", "reponse": "12.", "interpretation": None})
        null = copy.deepcopy(EXAMPLES[9]["response"])
        null["piliers"] = None
        cases.append(null)
        for obj in cases:
            self.assertEqual(bool(am.shape_errors(obj)), bool(list(v.iter_errors(obj))), obj)


class Canon(unittest.TestCase):
    def test_passage_rule(self):
        self.assertTrue(am.passes((1, 0, 0)))
        self.assertTrue(am.passes((0, 0, 1)))
        self.assertFalse(am.passes((0, 0, 0)))
        self.assertFalse(am.passes((1, -1, 1)))
        self.assertFalse(am.passes(None))

    def test_a_gesture_that_fails_cannot_rise(self):
        obj = copy.deepcopy(EXAMPLES[1]["response"])
        obj["canon"]["planete"]["sceau"] = -1
        errors, _ = am.validate(obj)
        self.assertTrue(any("3.4" in e for e in errors))
        obj["statut"] = "question_plus_juste"
        obj["solution"] = "What other way of travelling would suit you?"
        errors, _ = am.validate(obj)
        self.assertEqual(errors, [])

    def test_true_and_false_are_not_seals(self):
        self.assertIsNone(am.seal_value(True))
        self.assertEqual(am.seal_value(1.0), 1)


class Format(unittest.TestCase):
    def test_three_blocks(self):
        obj = EXAMPLES[1]["response"]
        blocks, read = am.read_output(output_in_blocks(obj))
        self.assertEqual(read, obj)
        self.assertEqual(am.validate(read, blocks)[0], [])

    def test_missing_block(self):
        obj = EXAMPLES[1]["response"]
        blocks, read = am.read_output(output_in_blocks(obj, dissection=False))
        self.assertTrue(any("dissection" in e for e in am.validate(read, blocks)[0]))

    def test_short_path_without_thinking_blocks(self):
        blocks, read = am.read_output('<json>{"statut":"voie_courte","reponse":"12."}</json>')
        self.assertEqual(am.validate(read, blocks)[0], [])

    def test_rendering_for_the_judge(self):
        text = output_in_blocks(EXAMPLES[4]["response"])
        rendered = am.render_for_judge(text, "tower")
        self.assertIn("Reasoning:\n1.", rendered)
        self.assertIn("Solution: From tomorrow", rendered)
        self.assertNotIn("<json>", rendered)

    def test_the_judge_does_not_see_the_self_rating(self):
        for seal_line in ("Seals: human +1 · planet 0 · living 0", "**Seals:** human +1",
                          "Sceaux : homme +1 · planète 0 · vivant 0"):
            text = f"Heard: x\nAt stake: y\nAn answer.\nGesture: walk.\n{seal_line}"
            rendered = am.render_for_judge(text, "core")
            self.assertIn("Gesture: walk.", rendered)
            self.assertNotIn("+1", rendered)
        self.assertIn("Seal the jar: tightly.", am.render_for_judge("Seal the jar: tightly.", "without"))


class Counter(unittest.TestCase):
    def test_five_hundred_written_tokens(self):
        self.assertAlmostEqual(am.energy_wh(0, 500), 0.3)

    def test_one_tower_second(self):
        self.assertAlmostEqual(am.tower_seconds(56), 1.0)

    def test_display(self):
        self.assertEqual(am.approx(92000), "≈ 92,000")
        self.assertEqual(am.approx(0.4212), "≈ 0.42")

    def test_display_never_shows_three_significant_figures(self):
        self.assertEqual(am.approx(0.0996), "≈ 0.10")
        self.assertEqual(am.approx(9.96), "≈ 10")
        self.assertEqual(am.approx(99.6), "≈ 100")


class Agreement(unittest.TestCase):
    def test_kappa(self):
        self.assertEqual(am.weighted_kappa([(1, 1), (0, 0), (-1, -1)]), 1.0)
        self.assertAlmostEqual(am.weighted_kappa([(1, 1), (0, 0), (1, 0), (0, 1)]), 0.0)
        self.assertIsNone(am.weighted_kappa([(0, 0), (0, 0)]))

    def test_agreement(self):
        self.assertEqual(am.agreement([(1, 1), (0, 1), (None, 1)]), 0.5)


class Bande(unittest.TestCase):
    def test_the_strip_has_one_data_mark(self):
        self.assertEqual(am.BANDE.read_text(encoding="utf-8").count(am.BANDE_MARK), 1)

    def test_the_strip_carries_the_ask_safely(self):
        obj = copy.deepcopy(EXAMPLES[9]["response"])
        obj["reponse"] += " </script><script>alert(1)</script>"
        data = am.ask_data(obj, "Why?", "en", 2000, 500, "Pourquoi ?", {"reponse": "a", "solution": "b"})
        html = am.bande_html(data)
        self.assertNotIn(am.BANDE_MARK, html)
        self.assertNotIn("</script><script>alert", html)
        got = json.loads(html.split('id="am-d">', 1)[1].split("</script>", 1)[0])
        self.assertEqual(got["sortie"], obj)
        self.assertEqual(got["question_fr"], "Pourquoi ?")
        self.assertEqual(got["traduction"]["solution"], "b")
        self.assertEqual(got["compteur"], {"lus": 2000, "ecrits": 500})

    def test_the_pictogram_is_restrained_to_one_line_of_latin(self):
        page = am.PICTO.read_text(encoding="utf-8")
        self.assertEqual(page.count(am.PICTO_LATIN), 1)
        self.assertEqual(page.count(am.PICTO_GOLD), 1)
        self.assertNotIn("<script", page)
        self.assertNotIn("<button", page)
        self.assertLess(len(page), 1200)  # about 400 tokens of template
        gold = am.picto_html("Pax  <tibi> & vobis", (1, 1, 0))
        self.assertIn('lang="la">Pax &lt;tibi&gt; &amp; vobis</p>', gold)
        self.assertIn('fill="#D4A72C"', gold)
        self.assertNotIn("__", gold)
        self.assertIn('fill="currentColor"/></svg>', am.picto_html("Quaere", (1, -1, 0)))
        self.assertIn('fill="currentColor"/></svg>', am.picto_html("Quaere", None))
        self.assertTrue(am.picto_html("Pax", (0, 0, 1), standalone=True).startswith('<!DOCTYPE html>\n<html lang="la">'))

    def test_the_layered_master_parses(self):
        import xml.dom.minidom
        doc = xml.dom.minidom.parse(str(pathlib.Path(__file__).resolve().parent.parent / "assets" / "picto-antimars.svg"))
        labels = [g.getAttribute("inkscape:label") for g in doc.getElementsByTagName("g") if g.getAttribute("inkscape:groupmode") == "layer"]
        self.assertEqual(labels, ["structure", "socles", "sceau (or si le triple sceau monte)"])

    def test_standalone_page(self):
        self.assertTrue(am.bande_html(am.ask_data(EXAMPLES[2]["response"]), standalone=True).startswith("<!DOCTYPE html>"))


class PluginCopies(unittest.TestCase):
    """The plugin carries copies of repository files: they must not drift apart."""

    def test_plugin_copies_match_the_repository(self):
        skill = am.ROOT / "plugin" / "antimars" / "skills" / "antimars"
        pairs = {
            "tools/antimars.py": "scripts/antimars.py",
            "SPEC.md": "references/spec.md",
            "schema/antimars-1.0.schema.json": "schema/antimars-1.0.schema.json",
            "examples/examples-1.0.json": "examples/examples-1.0.json",
            "constitution/portable.en.md": "references/portable.en.md",
            "constitution/portable.fr.md": "references/portable.fr.md",
            "constitution/tower.en.md": "references/tower.en.md",
            "constitution/tour.fr.md": "references/tour.fr.md",
            "assets/bande-antimars.html": "assets/bande-antimars.html",
            "assets/picto-antimars.html": "assets/picto-antimars.html",
        }
        for repo, copy_ in pairs.items():
            with self.subTest(repo=repo):
                self.assertEqual((am.ROOT / repo).read_bytes(), (skill / copy_).read_bytes())


if __name__ == "__main__":
    unittest.main()
