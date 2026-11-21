# Antimars

*Pax in Terra Nostra*

Antimars est une couche ouverte qu'une IA adopte pour répondre en paix. Elle dissèque la question avant d'y répondre, ne livre qu'un geste qui passe le triple sceau (homme, planète, vivant) et dit ce que la réponse a coûté, en secondes de tour Eiffel illuminée.

> On ne décrète pas un standard : on le mérite.

**Statut : proposition 1.0.** Aucune mesure ne montre encore que le noyau améliore les réponses. Le banc d'essai est là pour le savoir.

## En trois gestes

1. **Adopter (N1).** Collez [la constitution portable](constitution/portable.fr.md) (≈ 300 jetons, [version anglaise](constitution/portable.en.md)) en tête d'une conversation, d'un prompt système ou d'un agent.
2. **Vérifier (N2).** `python outils/antimars.py valider sortie.txt` contrôle le format 1.0 et la règle des sceaux.
3. **Mesurer.** `python banc/banc.py --fournisseur anthropic --modele <modèle>` compare le même modèle avec et sans le noyau. Dans Claude, la page du banc fait la même chose en un clic.

## Le dépôt

| Chemin | Contenu |
|---|---|
| [SPEC.md](SPEC.md) | la spécification du noyau 1.0 |
| [schema/](schema/antimars-1.0.schema.json) | le schéma JSON versionné |
| [exemples/](exemples/exemples-1.0.json) | dix cas annotés, qui servent aussi à étalonner les juges |
| [constitution/](constitution/) | la constitution portable (fr, en) et le prompt fondateur de la tour |
| [outils/](outils/antimars.py) | validation, compteur, accord entre évaluateurs ; tests : `python -m unittest discover -s outils` |
| [banc/](banc/PROTOCOLE.md) | corpus, juges, banc en ligne de commande, page du banc pour Claude |
| [PILOTES.md](PILOTES.md), [GOUVERNANCE.md](GOUVERNANCE.md), [ROADMAP.md](ROADMAP.md) | la suite : pilotes volontaires, décisions ouvertes, v2 |

Python 3.9 et sa bibliothèque standard suffisent. Avec le paquet `jsonschema`, le schéma officiel est vérifié en plus.

## Habillage

La tour (deux tours d'une même verticale, la racine qui dissèque et la tour qui répond, des antennes à paliers, une clochette quand le triple sceau passe) est l'habillage de Mars Field Intelligence, une application qui montre le noyau. L'habillage n'est pas normé : chacun peut en dessiner un autre.

## Licence

Textes (spécification, constitutions, exemples, documents) : [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.fr). Code : MIT. Voir [LICENSE.md](LICENSE.md). Auteur : Garrigue.

## In English

Antimars is an open layer an AI adopts to answer in peace: it dissects the question first, delivers one gesture that passes three seals (people, planet, living beings), and states what the answer cost, measured in seconds of the lit Eiffel Tower (1 s ≈ 56 Wh). Start with the [portable constitution](constitution/portable.en.md). The specification is in French; translations are welcome.

## Plugin pour Claude

Le dossier `plugin/antimars` installe trois compétences : répondre (`antimars`), sceller la réponse d'une autre IA (`sceller`), compter et alléger (`compter`). Une fois ce dépôt publié sur GitHub :

    /plugin install antimars --marketplace drawbitcoin/antimars
