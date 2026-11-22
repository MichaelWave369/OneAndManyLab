# Experiment notes: The One and Many, Part VIII

**Run date:** 2026-11-21  
**Seed:** `369`  
**Software:** Python standard library only  
**Trials:** 9 experimental conditions × 50,000 episodes × 4 protocols = **1,800,000 protocol trials**, plus a separate 100,000-sample causal-control experiment.  
**Tests:** 8 passing tests (6 new, 2 carried forward from Part VII).

## Research question

When distinct feature-processing modules must jointly answer a location-cued query, what does packet feedback, a shared cache, or redundant feedforward communication change under sensory noise and channel erasures? Can observed correlation identify causal information transfer?

## Preregisterable toy predictions

1. **P1:** With no erasures, all four protocols tie in accuracy, because all use exactly the same sensory observations.
2. **P2:** With erasures, two transmission opportunities increase task accuracy compared with one opportunity.
3. **P3:** Adaptive retry and unconditional duplication have the same expected accuracy because both have final per-feature erasure probability `p²`, but differing average message costs.
4. **P4:** A cache/workspace provides no one-query accuracy benefit over an equally buffered feedforward readout when packet budgets and sensory inputs are held equal.
5. **P5:** A shared hidden cause can create strong observational correlation between A and B even when `do(A)` has zero causal effect on B.

These were analytically predictable from model design; the simulations are **sanity and reproducibility checks**, not independent empirical discoveries about consciousness.

## Protocol and outcome

Two objects have two binary features each. Noisy sensors observe both spatial values per feature at `t=0`. A target location cue arrives at `t=1`. The receiver must output both requested feature bits. Each protocol receives the same values and sensory bit flips on a given episode. Independent message erasures are applied according to each protocol. When no usable packet arrives, receiver chooses the missing bit uniformly at random.

Primary metric: joint probability both target bits are correct. Secondary: each feature accuracy, and mean data, reliable-control, and total messages per episode.

### Key condition: 10% sensory error, 35% packet erasure

| Protocol | Observed joint accuracy | Theoretical joint accuracy | Mean total messages |
|---|---:|---:|---:|
| One-send feedforward | 57.806% | 57.760% | 2.000 |
| One-send shared workspace | 57.758% | 57.760% | 2.000 |
| Feedback + one retry | 72.226% | 72.420% | 3.396 |
| Feedforward + fixed duplicate | 72.402% | 72.420% | 4.000 |

The sampled 0.18-percentage-point difference between retry and duplicate variants is small and consistent with random sampling. There is **no designed difference in their expected accuracies**.

### Three additional checks

- At `q=0, p=0`, all protocols obtained **100%** correct joint bindings.
- At `q=0.10, p=0`, all obtained **80.79%** in the same seeded condition, close to the exact expectation `(1-0.10)²=81%`.
- At `q=0.25, p=0`, all obtained **56.46%**, close to the exact expectation `(1-0.25)²=56.25%`.

These controls show why fixing transmission alone cannot repair already corrupted sensory evidence.

## What the causal control adds

The observed correlation between independent noisy descendants of a shared binary cause was `r=0.641913`, against theory `r=0.64`. The `do(A=1)` minus `do(A=0)` effect on B was **0** by model construction. In a separate explicit `A→B` mechanism with 10% transmission noise, the simulated difference in `P(B=1)` was **0.80012**, close to its theoretical value `0.8`.

**Interpretation:** Statistical dependence is not enough to justify a causal-arrow claim. Interventions or justified causal assumptions are needed.

## Conclusions and non-conclusions

**Supported within the model:**

- In the chosen loss model, feedback can save messages relative to unconditional duplication while retaining the same expected binding accuracy.
- A shared cache does not magically outperform an ordinary buffered downstream receiver on the same one-query task.
- A latent common cause can create correlated activity without direct causal influence.

**Not demonstrated:**

- That recurrence *per se* causes better binding, or is necessary for consciousness.
- That a shared cache correctly implements Global Neuronal Workspace Theory.
- That we measured IIT integrated information, phenomenal binding, awareness, or a spiritual property.
- That interpretations of Plato, Plotinus, or Nag Hammadi cosmology are established by the experiment.

## Experimental confounds and improvements

The feedback variant has a reliable control/NACK channel. Its advantage is partly extra transmissions, not solely its feedback structure; this is why an equal-success redundant feedforward comparison is included. A stricter comparison would match **total information transferred**, latency, memory capacity, and decoder complexity. Follow-up experiments should:

1. Introduce lossy feedback and account for control-channel reliability.
2. Match total data/control bit budgets and deadline constraints across protocols.
3. Include distractor-rich multi-object feature binding, temporal sequencing, and noisy cue reliability.
4. Compare **causal intervention responses**, not merely correlations or task accuracy.
5. Make formal a priori predictions for candidate architectures, and include architectures likely to falsify favored hypotheses.

## Ancient-philosophy connection: analogy, not evidence

The contrast between what a system reveals from outside and what its internal structure actually is parallels an epistemic theme in *Allogenes* and Plotinian reflection: representation is not identical to what is represented. Nothing in the code identifies a Demiurge, ultimate One, soul, consciousness, or cosmic source. The experiment is useful because it makes a **limited** claim falsifiable, not because it validates ancient metaphysics.

## Research references

- Wu & He (2026), arXiv:2611.08469: https://arxiv.org/abs/2611.08469
- Cogitate Consortium et al. (2025), *Nature* 642, 133–142: https://doi.org/10.1038/s41586-025-08888-1
- Percy & Agarwal (2026), *The phenomenal binding problem for neural networks*: https://pubmed.ncbi.nlm.nih.gov/41637896/