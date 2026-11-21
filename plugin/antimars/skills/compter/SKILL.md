---
name: compter
description: >
  À utiliser quand l'utilisateur demande « combien ça coûte en jetons », « combien
  d'énergie », « compteur », « secondes de tour », « allège ce prompt », « optimise les
  jetons », « how many tokens », ou veut le coût d'un prompt, d'une conversation ou
  d'une réponse en jetons, Wh et secondes de tour Eiffel allumée, ou une version moins chère.
metadata:
  version: "1.1.0"
  author: "Garrigue"
---

# Compter · la tour allumée qui consomme

## Compter

1. **Jetons.** Prendre le compte de l'API ou d'un tokenizer s'il existe, et le dire. Sinon : caractères ÷ 3,6 (français), ÷ 4 (anglais), ÷ 3 (code, JSON). Compter à part les jetons **lus** (prompt système, historique, documents, question) et **écrits**. Dans une conversation, tout l'historique est relu à chaque tour.
2. **Énergie.** ≈ 0,6 mWh par jeton écrit, ≈ 0,03 mWh par jeton lu. 500 jetons écrits ≈ 0,3 Wh, l'ordre de grandeur publié pour une requête texte courante (Epoch AI 2025 ≈ 0,3 Wh ; Google 2025, médiane 0,24 Wh). Ces valeurs varient fortement selon le modèle, le matériel et le centre de données : toujours des estimations.
3. **Étalon.** Secondes de tour = Wh ÷ 56 (illumination dorée ≈ 200 kW). Un scintillement de cinq minutes ≈ 4 kWh. À grande échelle, convertir en scintillements ou en nuits d'illumination (≈ 200 kWh par heure allumée).
4. **Affichage.** `≈ N jetons · ≈ X Wh · ≈ Y s de tour`, deux chiffres significatifs au plus.
5. **Argent.** Jamais de prix par jeton de mémoire : prendre le tarif donné, le chercher, ou laisser la formule : coût = lus × prix d'entrée + écrits × prix de sortie.

Avec un terminal, un fichier se compte comme l'outil de référence :

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/antimars/scripts/antimars.py" count fichier.txt --read 2100 --kind fr
```

## Optimiser : éteindre les projecteurs inutiles

Donner le compteur **avant / après** et la réécriture. Leviers, du plus rentable au moins rentable :
1. **Aiguillage** : voie courte pour les questions simples, la tour pour les riches.
2. **Fixer la longueur de sortie** : un jeton écrit coûte ≈ 20 jetons lus.
3. **Ne pas recoller** de longs documents à chaque message : résumer une fois, citer ensuite.
4. **Nouvelle conversation** quand le sujet change : l'historique est relu à chaque tour.
5. **Mise en cache** d'un long prompt système répété : les barreaux cristallisés de la tour.
6. **Modèle plus petit** pour trier, résumer, reformater ; le grand modèle pour juger.
7. **Regrouper** plusieurs questions en un seul appel.
8. **Élaguer le prompt** : politesses, répétitions, exemples redondants ; garder les contraintes.
9. **Pictogramme plutôt que bandeau** : ≈ 2 000 jetons écrits contre ≈ 6 000 ; ni l'un ni l'autre quand la sobriété prime.

Ne jamais sacrifier la justesse ni le sceau PAIX pour économiser : la sobriété sert la paix, elle ne la remplace pas.
