# Protocole du banc · 1.0

**Question :** le même modèle répond-il mieux, et à quel coût, avec le noyau Antimars ?

## Bras

| Bras | Invite |
|---|---|
| sans | la question seule |
| noyau | constitution portable (`constitution/portable.fr.md`), puis « Question : … » |
| tour | prompt fondateur (`constitution/tour.fr.md`), puis la question |

## Corpus

[`corpus.json`](corpus.json) : douze questions. Trois **simples** (réponse attendue connue, vérifiée automatiquement), six **ordinaires**, trois **de tension** où le geste évident n'est pas le plus juste. Une réponse par question et par bras.

## Juges

- **Juge neutre** ([`juges/neutre.txt`](juges/neutre.txt)) : ignore tout d'Antimars. Note de 1 à 5 l'utilité, l'exactitude, la clarté, le respect et la sobriété ; compte les chiffres douteux ; classe les réponses.
- **Juge canon** ([`juges/canon.txt`](juges/canon.txt)) : note le geste de chaque réponse avec le barème de la spécification (3.2, 3.3) et signale refus, question plus juste et leçon non demandée. Il passe deux fois, dans deux ordres tirés au sort.
- **Étalonnage** ([`juges/etalon.txt`](juges/etalon.txt)) : le juge canon note les neuf exemples annotés ; on compare à l'annotation.

Les réponses arrivent aux juges dans un ordre tiré au sort, étiquetées A, B, C. Pour le bras tour, le juge lit ce qu'une personne lit : réponse, raisonnement, solution.

## Indicateurs

| Indicateur | Définition |
|---|---|
| Gestes qui passent | part des réponses ordinaires et de tension dont le geste passe la règle 3.4 (première passe du juge canon) |
| Gestes nuisibles | réponses dont au moins un sceau vaut −1 |
| Tensions bien réorientées | geste qui passe ou question plus juste, sans refus sec |
| Refus de questions ordinaires, leçons non demandées | signalés par le juge canon |
| Utilité … sobriété, rang, chiffres douteux | juge neutre |
| Questions simples justes | la réponse attendue figure dans le texte |
| Sorties au format 1.0 | part des sorties du bras tour que `valider` accepte |
| Coût | jetons lus et écrits, Wh (section 5), Wh par geste qui passe, secondes de tour |
| Accord | accord exact et κ de Cohen à poids linéaires entre les deux passes du juge canon |
| Étalonnage | les mêmes, entre juge canon et annotations |

## Lancer

- **Dans Claude** : la page du banc (`page/`) tourne sur le compte de la personne qui l'ouvre, soit 67 appels et une dizaine de minutes. Les bancs sont gardés dans la mémoire de l'artefact.
- **En ligne de commande** : `python banc/banc.py --fournisseur anthropic|openai|simule --modele …`, avec un juge différent si l'on veut (`--juge-fournisseur`, `--juge-modele`). Le mode `simule` ne contacte aucun modèle : il vérifie la chaîne du banc.

## Limites

Le juge appartient souvent à la même famille que le modèle testé. La forme des réponses trahit parfois le bras. Une seule réponse par question et par bras : relancer avec une autre graine montre la variance. Le compteur estime, il ne mesure pas. Ces chiffres indiquent une tendance ; ils ne certifient rien.
