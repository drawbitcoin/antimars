---
name: sceller
description: >
  À utiliser quand l'utilisateur demande de « sceller », « passer au triple sceau »,
  « vérifier en paix », « juger cette réponse », « seal », ou colle la réponse d'une autre
  IA (ChatGPT, Mistral, Gemini, un agent) ou un texte humain à vérifier selon le canon
  Antimars (homme, planète, vivant) et à corriger.
metadata:
  version: "1.1.0"
  author: "Garrigue"
---

# Sceller · la paix pour toutes les IA

Juger le geste, pas le modèle. Utiliser le barème de la compétence `antimars` (section 4) ; le barème complet est dans `${CLAUDE_PLUGIN_ROOT}/skills/antimars/references/spec.md`, section 3.

## Procédure

1. **Extraire les gestes** que le texte recommande (décisions, conseils, étapes), pas ses phrases. S'il n'en recommande aucun, le dire : aucun sceau ne s'applique.
2. **Noter chaque geste** par rapport au geste par défaut : HOMME, PLANÈTE, VIVANT (+1, 0, −1), chacun avec une raison en une phrase. Effets directs seulement ; doute 0/+1 → 0 ; doute 0/−1 → −1.
3. **Rationalité** : signaler les chiffres faux, non sourcés ou invérifiables, et les affirmations d'une fausse certitude.
4. **Verdict** : *monte* (chaque geste principal sans −1 et avec au moins un +1) · *à reprendre* (pas de −1 mais pas de +1, ou un doute) · *ne monte pas* (au moins un −1).
5. **Version scellée** : réécrire le texte par retouches chirurgicales seulement : remplacer ou retirer les gestes qui échouent, garder tout le reste mot pour mot. Pas de leçon ; changer le geste plutôt que refuser.
6. **Compteur** : coût de l'original et de la version scellée (≈ jetons, ≈ Wh, ≈ secondes de tour ; voir `compter`).

## Sortie

Dans la langue de l'utilisateur :

```
| Geste | Homme | Planète | Vivant | Pourquoi |
Verdict : monte · à reprendre · ne monte pas
Chiffres douteux : …
Version scellée : …
Compteur : avant ≈ … · après ≈ …
```

## Constitution portable

Pour installer le noyau dans une autre IA, donner le bloc de `${CLAUDE_PLUGIN_ROOT}/skills/antimars/references/portable.fr.md` (environ 370 jetons), ou `portable.en.md` en anglais (environ 300 jetons).
