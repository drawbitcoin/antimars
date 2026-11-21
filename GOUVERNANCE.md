# Gouvernance

La spécification obéit à la règle qu'elle impose aux réponses : **un changement monte s'il passe le triple sceau et si le banc ne régresse pas.**

## Rôles

| Rôle | Qui | Ce qu'il fait |
|---|---|---|
| Mainteneur fondateur | Garrigue | tient la version 1.x et tranche en dernier ressort jusqu'à la 2.0 |
| Conseil des quatre piles | un siège par pilier | géométrie (sobriété, coût), rationalité (banc, preuves), créativité (forme, usages), paix (effets sur les personnes) |
| Siège du vivant | une personne qui parle pour ce qui ne parle pas : écologue, naturaliste, association | peut suspendre une décision qui ferait passer un −1 VIVANT ; la suspension renvoie la proposition au banc, elle ne l'enterre pas |
| Contributeurs | quiconque | ouvre une proposition, un banc, une traduction |

Avant la 2.0, au moins deux sièges du conseil sont tenus par des personnes extérieures au projet, sans lien d'intérêt avec le mainteneur.

## Proposer un changement

1. **Proposition PAX-n** : le problème, le changement, l'effet attendu, et les trois sceaux du changement lui-même.
2. **Discussion publique** : quatorze jours au moins.
3. **Banc** : même corpus, même protocole. Le changement ne doit pas réduire les gestes qui passent, ni augmenter les gestes nuisibles, ni baisser l'exactitude ou l'accord entre évaluateurs. Le coût en Wh n'augmente pas sans gain mesuré.
4. **Décision** : consensus du conseil ; à défaut, majorité des sièges. En 1.x, le mainteneur tranche si le conseil se partage.
5. **Publication** : nouveau numéro de version, journal des changements, rapport de banc joint.

## Révision périodique

Tous les six mois : relecture de la spécification, banc sur les modèles du moment, mise à jour des coefficients d'énergie quand des mesures publiées le permettent, publication des désaccords entre évaluateurs et des exemples qu'ils ont fait naître.

## Sortie

- **Pour chacun.** La licence permet de copier, modifier et partir. Rien n'oblige à rester.
- **Pour le projet.** Si deux bancs consécutifs ne montrent de gain sur aucun indicateur et un coût plus élevé, la spécification passe « en sommeil » et le dit en tête du README. Un standard peut grandir ou s'éteindre selon ses preuves.
- **Pour le fondateur.** À la 2.0, si au moins trois implémentations indépendantes existent, la gouvernance passe à une structure collective (association loi 1901 ou équivalent).

## Le nom et la conformité

Par convention du projet, une implémentation se dit « conforme Antimars N1, N2 ou N3 » quand elle publie le rapport de banc correspondant (SPEC.md, section 6). Une variante qui change le noyau est bienvenue sous un autre nom.

## Ce que la gouvernance ne fait pas

Elle ne certifie pas qu'une IA est « en paix ». Elle publie des mesures, leur méthode et leurs limites.
