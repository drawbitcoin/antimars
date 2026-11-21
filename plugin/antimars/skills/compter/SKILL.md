---
name: compter
description: >
  This skill should be used when the user asks "combien ça coûte en jetons",
  "combien d'énergie", "compteur", "secondes de tour", "allège ce prompt",
  "optimise les jetons", or wants the cost of a prompt, a conversation or an answer
  in tokens, Wh and seconds of the lit Eiffel Tower, or a cheaper version of it.
metadata:
  version: "1.0.0"
  author: "Garrigue"
---

# Compter · la tour illuminée qui consomme

## Compter

1. **Jetons.** Use the API or tokenizer count when available and say so. Otherwise: characters ÷ 3.6 (French), ÷ 4 (English), ÷ 3 (code, JSON). Count **read** tokens (system prompt, history, documents, question) and **written** tokens separately. In a conversation the whole history is read again at every turn.
2. **Énergie.** ≈ 0.6 mWh per written token, ≈ 0.03 mWh per read token. 500 written tokens ≈ 0.3 Wh, the published order of magnitude for a common text query (Epoch AI 2025 ≈ 0.3 Wh; Google 2025 median 0.24 Wh). These vary widely with model, hardware and data center: always present them as estimates.
3. **Étalon.** Seconds of tower = Wh ÷ 56 (golden illumination ≈ 200 kW). One five-minute sparkle ≈ 4 kWh. For large scales (a million users, a year), convert into sparkles or nights of illumination (≈ 200 kWh per lit hour).
4. **Affichage.** `≈ N jetons · ≈ X Wh · ≈ Y s de tour`, two significant figures at most.
5. **Argent.** Never quote a per-token price from memory. Use the price the user gives, or look up the current one, or give the formula: cost = read × input price + written × output price.

With a shell, a file can be counted exactly the same way as the reference tool:

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/antimars/scripts/antimars.py" compter fichier.txt --lus 2100
```

## Optimiser : éteindre les projecteurs inutiles

Give the counter **before / after** and the rewritten prompt. Levers, most profitable first:
1. **Aiguillage** — short path for simple questions, the tower only for rich ones.
2. **Fix the output length** — written tokens cost ≈ 20 × read tokens: "in 3 lines", "one gesture".
3. **Do not paste long documents again** at each message: summarize once, then cite.
4. **New conversation** when the topic changes: history is re-read every turn.
5. **Prompt caching** for a long, repeated system prompt, where the API allows it — the tower's crystallized bars.
6. **Smaller model** or quick mode for sorting, summarizing, reformatting; the large model to judge.
7. **Group** several questions into one call.
8. **Prune the prompt** — politeness, repetitions, redundant examples; keep the constraints.

Never trade accuracy or the PAIX seal for savings: sobriety serves peace, it does not replace it.
