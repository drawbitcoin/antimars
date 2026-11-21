"""Tests du noyau Antimars 1.0 : python -m unittest discover -s outils"""
import copy
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import antimars as am  # noqa: E402

EXEMPLES = json.loads(am.EXEMPLES.read_text(encoding="utf-8"))


def sortie_en_blocs(objet, dissection=True, generation=True):
    morceaux = []
    if dissection:
        morceaux.append("<dissection>\n- a\n- b\n- c\n- d\n</dissection>")
    if generation:
        morceaux.append("<generation>\n- a\n- b\n- c\n- d\n</generation>")
    morceaux.append("<json>\n" + json.dumps(objet, ensure_ascii=False) + "\n</json>")
    return "\n".join(morceaux)


class Exemples(unittest.TestCase):
    def test_les_dix_exemples_sont_conformes_et_coherents(self):
        lignes, problemes = am.verifier_exemples()
        self.assertEqual(len(lignes), 10)
        self.assertEqual(problemes, 0, [l for l in lignes if l[6] != "ok"])

    def test_schema_officiel_et_controle_manuel_concordent(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema absent")
        schema = json.loads(am.SCHEMA.read_text(encoding="utf-8"))
        v = jsonschema.Draft202012Validator(schema)
        cas = [ex["reponse"] for ex in EXEMPLES]
        abime = copy.deepcopy(EXEMPLES[1]["reponse"])
        del abime["canon"]
        cas.append(abime)
        faux_sceau = copy.deepcopy(EXEMPLES[1]["reponse"])
        faux_sceau["canon"]["homme"]["sceau"] = 2
        cas.append(faux_sceau)
        mauvais_poids = copy.deepcopy(EXEMPLES[9]["reponse"])
        mauvais_poids["piliers"]["paix"] = 1.5
        cas.append(mauvais_poids)
        courte_sans_reponse = {"statut": "voie_courte"}
        cas.append(courte_sans_reponse)
        cas.append({"statut": "voie_courte", "reponse": "12.", "interpretation": None})
        nul = copy.deepcopy(EXEMPLES[9]["reponse"])
        nul["piliers"] = None
        cas.append(nul)
        for objet in cas:
            self.assertEqual(bool(am.erreurs_de_forme(objet)), bool(list(v.iter_errors(objet))), objet)


class Canon(unittest.TestCase):
    def test_regle_de_passage(self):
        self.assertTrue(am.passe((1, 0, 0)))
        self.assertTrue(am.passe((0, 0, 1)))
        self.assertFalse(am.passe((0, 0, 0)))
        self.assertFalse(am.passe((1, -1, 1)))
        self.assertFalse(am.passe(None))

    def test_un_geste_qui_ne_passe_pas_ne_peut_pas_monter(self):
        objet = copy.deepcopy(EXEMPLES[1]["reponse"])
        objet["canon"]["planete"]["sceau"] = -1
        erreurs, _ = am.valider(objet)
        self.assertTrue(any("3.4" in e for e in erreurs))
        objet["statut"] = "question_plus_juste"
        objet["solution"] = "Quelle autre façon de voyager te conviendrait ?"
        erreurs, _ = am.valider(objet)
        self.assertEqual(erreurs, [])

    def test_vrai_et_faux_ne_sont_pas_des_sceaux(self):
        self.assertIsNone(am.valeur(True))
        self.assertEqual(am.valeur(1.0), 1)


class Format(unittest.TestCase):
    def test_trois_blocs(self):
        objet = EXEMPLES[1]["reponse"]
        blocs, lu = am.lire_sortie(sortie_en_blocs(objet))
        self.assertEqual(lu, objet)
        self.assertEqual(am.valider(lu, blocs)[0], [])

    def test_bloc_manquant(self):
        objet = EXEMPLES[1]["reponse"]
        blocs, lu = am.lire_sortie(sortie_en_blocs(objet, dissection=False))
        self.assertTrue(any("dissection" in e for e in am.valider(lu, blocs)[0]))

    def test_voie_courte_sans_blocs_de_pensee(self):
        blocs, lu = am.lire_sortie('<json>{"statut":"voie_courte","reponse":"12."}</json>')
        self.assertEqual(am.valider(lu, blocs)[0], [])

    def test_rendu_pour_le_juge(self):
        texte = sortie_en_blocs(EXEMPLES[4]["reponse"])
        rendu = am.rendre_pour_juge(texte, "tour")
        self.assertIn("Raisonnement :\n1.", rendu)
        self.assertIn("Solution : Dès demain", rendu)
        self.assertNotIn("<json>", rendu)


class Compteur(unittest.TestCase):
    def test_cinq_cents_jetons_ecrits(self):
        self.assertAlmostEqual(am.energie_wh(0, 500), 0.3)

    def test_une_seconde_de_tour(self):
        self.assertAlmostEqual(am.secondes_de_tour(56), 1.0)

    def test_affichage(self):
        self.assertEqual(am.approx(92000), "≈ 92 000")
        self.assertEqual(am.approx(0.4212), "≈ 0,42")


class Accord(unittest.TestCase):
    def test_kappa(self):
        self.assertEqual(am.kappa_pondere([(1, 1), (0, 0), (-1, -1)]), 1.0)
        self.assertAlmostEqual(am.kappa_pondere([(1, 1), (0, 0), (1, 0), (0, 1)]), 0.0)
        self.assertIsNone(am.kappa_pondere([(0, 0), (0, 0)]))

    def test_accord(self):
        self.assertEqual(am.accord([(1, 1), (0, 1), (None, 1)]), 0.5)


if __name__ == "__main__":
    unittest.main()
