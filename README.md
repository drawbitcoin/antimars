# Antimars

*Pax in Terra Nostra*

Antimars is an open layer an AI adopts to answer in peace. It dissects the question before answering, delivers only a gesture that passes the triple seal (human, planet, living) and states what the answer cost, in seconds of the lit Eiffel Tower.

> You don't decree a standard: you earn it.

**Status: proposal 1.0.** No measurement shows yet that the core improves answers. The test bench is there to find out.

## In three gestures

1. **Adopt (N1).** Paste [the portable constitution](constitution/portable.en.md) (≈ 300 tokens, [French version](constitution/portable.fr.md)) at the start of a conversation, a system prompt or an agent.
2. **Check (N2).** `python tools/antimars.py validate output.txt` checks format 1.0 and the seal rule.
3. **Measure.** `python bench/bench.py --provider anthropic --model <model>` compares the same model with and without the core. In Claude, the bench page does the same in one click.

## The repository

| Path | Content |
|---|---|
| [SPEC.md](SPEC.md) | the core 1.0 specification, with the glossary of the wire format |
| [schema/](schema/antimars-1.0.schema.json) | the versioned JSON schema |
| [examples/](examples/examples-1.0.json) | ten annotated cases, which also calibrate the judges |
| [constitution/](constitution/) | the portable constitution (en, fr) and the founding prompt of the tower (en, and the French original) |
| [tools/](tools/antimars.py) | validation, counter, agreement between raters, strip; tests: `python -m unittest discover -s tools` |
| [assets/](assets/bande-antimars.html) | the Antimars strip, drawn above every answer where the tower climbs |
| [bench/](bench/PROTOCOL.md) | corpus, judges, command-line bench, bench page for Claude |
| [PILOTS.md](PILOTS.md), [GOVERNANCE.md](GOVERNANCE.md), [ROADMAP.md](ROADMAP.md) | what comes next: volunteer pilots, open decisions, v2 |

Python 3.9 and its standard library are enough. With the `jsonschema` package, the official schema is checked as well.

## The Antimars strip

The plugin is French-native: the tower thinks in French. Above every answer where the tower climbs, it draws a thin strip of fixed height: a scrolling text banner on top, and under it the tower lying on the Earth line, drawn in face elevation after the 1889 plates (base 124.90 m, floors at 57.63, 115.73 and 276.13 m, the intermediate floor at 195.93 m, the campanile): the two towers stand foot to foot on four square concrete plinths, and their arches close into a circle on the Earth line. Under its floors, the keys A N fr T I M A xx R S choose a station: the two intermediate floors are translators, into French on the root side (fr, between N and T) and back into the language of the question on the tower side (xx, between A and R). Scrolling turns the tower; the pillar that comes to the top is elected and its letter (G R C P) shows on its plinth.

By default, the plugin shows a pictogram at the top of the answer, deliberately restrained: on the left the tower, after the same plates (the profile in one curve, the arch, the three floors as solid bars like the plinths, the antenna; the right tip turns gold when the triple seal passes), and on the right one line of Latin, the solution in synthesis, in a thin frame over an X lattice. There is no English or French in it; the written answer stays in the language of the question. Under it, three buttons go further, from the heaviest to the lightest: ANTIMARS TOWER (the full strip), ANTIMARS COUNTER (the detailed counter) and ANTIMARS TRADUCTEUR (the Latin line in the language of the question) (≈ 600 written tokens). The full strip comes on request (≈ 6,000 written tokens). Both are counted. Outside Claude, `python tools/antimars.py bande output.txt --question "…"` builds the strip as a page, and `--picto --latin "…"` the pictogram.

## Skin

The tower (two towers on one vertical, the root that dissects and the tower that answers, antennas with landings, a bell when the triple seal passes) is the skin of Mars Field Intelligence, an application that shows the core. The skin is not standardized: anyone can draw another.

## Licence

Text (specification, constitutions, examples, documents): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Code: MIT. See [LICENSE.md](LICENSE.md). Author: Garrigue.

## Format keys stay in French

The keys of the `<json>` block (`statut`, `interpretation`, `canon`, `sceau`, `reponse`…) are the 1.0 wire format and stay in French in every language; the values follow the language of the question. See the glossary in [SPEC.md](SPEC.md#41-glossary-of-the-wire-format).

## Plugin for Claude

The `plugin/antimars` folder is French-native and installs three skills: answer (`antimars`), seal another AI's answer (`sceller`), count and lighten (`compter`). In a Claude Code session:

    /plugin marketplace add drawbitcoin/antimars
    /plugin install antimars@antimars
