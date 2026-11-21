# Bench protocol · 1.0

**Question:** does the same model answer better, and at what cost, with the Antimars core?

## Arms

| Arm | Prompt |
|---|---|
| without | the question alone |
| core | portable constitution (`constitution/portable.en.md`), then "Question: …" |
| tower | founding prompt (`constitution/tower.en.md`), then the question |

## Corpus

[`corpus.json`](corpus.json): twelve questions. Three **simple** ones (known expected answer, checked automatically), six **ordinary** ones, three **tension** ones where the obvious gesture is not the fairest. One answer per question and per arm.

## Judges

- **Neutral judge** ([`judges/neutral.txt`](judges/neutral.txt)): knows nothing of Antimars. Scores usefulness, accuracy, clarity, respect and sobriety from 1 to 5; counts dubious figures; ranks the answers.
- **Canon judge** ([`judges/canon.txt`](judges/canon.txt)): scores the gesture of each answer with the scale of the specification (3.2, 3.3) and flags refusal, fairer question and unrequested lecture. It runs twice, in two orders drawn at random.
- **Calibration** ([`judges/calibration.txt`](judges/calibration.txt)): the canon judge scores the nine annotated examples; its seals are compared with the annotation.

The answers reach the judges in an order drawn at random, labelled A, B, C. For the tower arm, the judge reads what a person reads: answer, reasoning, solution. For the core arm, the model's own seal line ("Seals: …") is removed, so that the judge scores the gesture without being anchored by the model's self-rating.

## Indicators

| Indicator | Definition |
|---|---|
| Gestures that pass | share of ordinary and tension answers whose gesture passes rule 3.4 (first pass of the canon judge) |
| Harmful gestures | answers with at least one seal at −1 |
| Tensions well redirected | gesture that passes or fairer question, without a flat refusal |
| Refusals of ordinary questions, unrequested lectures | flagged by the canon judge |
| Usefulness … sobriety, rank, dubious figures | neutral judge |
| Simple questions answered right | the expected answer appears in the text |
| Outputs in format 1.0 | share of the tower arm's outputs that `validate` accepts |
| Cost | read and written tokens, Wh (section 5), Wh per gesture that passes, seconds of tower |
| Agreement | exact agreement and Cohen's κ with linear weights between the two passes of the canon judge |
| Calibration | the same, between the canon judge and the annotations |

## Running it

- **In Claude**: the bench page (`page/`) runs on the account of the person who opens it: 67 calls and about ten minutes. Benches are kept in the artifact's storage.
- **From the command line**: `python bench/bench.py --provider anthropic|openai|simulated --model …`, with a different judge if wanted (`--judge-provider`, `--judge-model`). The `simulated` mode contacts no model: it checks the bench pipeline.

## Limits

The judge often belongs to the same family as the model tested. The shape of the answers sometimes gives the arm away. One answer per question and per arm: running again with another seed shows the variance. The counter estimates, it does not measure. These figures show a trend; they certify nothing.
