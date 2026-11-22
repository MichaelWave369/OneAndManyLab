# Part IX: matched expected budgets, unreliable feedback, and causal intervention

**Date:** November 21, 2026  
**Repository:** MichaelWave369/OneAndManyLab  
**Status:** Executed synthetic experiment; formulas and code tested. Not peer-reviewed research.

## Question

Under the same *expected* number of data **plus** control transmissions, does adaptive selective retransmission outperform blindly scheduling an additional copy? How does losing the feedback message change the answer?

## Model

Each independent synthetic episode has two true binary feature bits. Each is sensed once with probability `q` of flipping. A data packet is independently erased with probability `e`. The receiver identifies both features correctly only if both final answers match the true bits. A missing bit is guessed by a fair coin.

- **One-shot:** one data packet per feature.
- **Blind repeat, cost-matched:** send an initial data packet; send a second with probability `p=e(2-f)`, independent of actual loss.
- **Feedback retry:** send an initial data packet; if lost, the receiver sends one NACK; NACK is itself erased with probability `f`. Only if the NACK arrives does the sender retry the data once. Both NACK and retry count as transmissions.
- **Two-copy and three-copy baselines:** always send two or three data attempts, respectively.

The receiver is assumed to recognize initial packet erasure perfectly and issue exactly one NACK when a packet is lost. This is an *idealization*. There is no ACK overhead for successful packets and no retransmission timeout. Feedback and data packets have equal unit cost for this model, although real systems need not.

All strategies receive the same generated true bits, noisy sensory observations, and first/second packet-erasure draws per episode. Paired contrast uncertainty uses per-episode differences, not the standard error from independently pretending the protocols were sampled on different episodes.

## Analytical predictions

Let `T` be the probability one feature's sensed bit reaches the receiver:

| Strategy | Delivery probability `T` | Expected messages per feature | Maximum per feature |
|---|---|---:|---:|
| One-shot | `1-e` | `1` | 1 |
| Blind repeat | `1-e+p*e*(1-e)` | `1+p` | 2 |
| Feedback retry | `1-e+e*(1-f)*(1-e)` | `1+e*(2-f)` | 3 |
| Two-copy | `1-e²` | `2` | 2 |
| Three-copy | `1-e³` | `3` | 3 |

We require `p = e(2-f) <= 1`, making blind repetition and feedback exactly equal **in expected total transmission count**, but *not* in per-episode packet count or maximum latency. The allowed parameter grid meets this constraint.

Given one noisy observation reused on duplicates, the expected accuracy of a single feature is

`a = (1-q)*T + 0.5*(1-T) = 0.5 + (0.5-q)*T`.

Because the two features are independent, expected full-binding accuracy is `a²`.

The difference in delivery probabilities between feedback and blind repetition is

`ΔT = e*(1-e)*((1-f) - e*(2-f))`.

For `e > 0`, feedback has the advantage when `(1-f) > e*(2-f)`, equivalent to `f < (1-2e)/(1-e)` when `e < 1`. At `e=.35`, the crossover threshold is `f≈.4615` (46.15% NACK loss). This is an exact analytical property of *this protocol model*, not of biological feedback generally.

## Execution

Run:

```bash
python -m unittest discover -s research -p 'test_*.py' -v
python research/budgeted_feedback.py --trials 20000 --seed 369 --output public/data/part9.json --csv public/data/part9.csv
```

- 27 conditions: sensor noise `q` in {0%,10%,25%}, data erasure `e` in {0%,15%,35%}, NACK erasure `f` in {0%,20%,60%}.
- 20,000 synthetic episodes per strategy per condition, five strategies: **2,700,000 evaluated strategy-episodes**.
- Additional 60,000 paired intervention episodes for `do(f=0)` against `do(f=.6)` with shared exogenous random draws.
- Reproducibility: seed 369; Python standard library only.

### Illustrative results: q=10%, e=35%

| NACK loss | Blind repeat | Feedback retry | Paired feedback advantage | Analytical advantage |
|---|---:|---:|---:|---:|
| 0% | 67.95% | 72.35% | +4.40 percentage points | +4.57 pp |
| 20% | 67.30% | 69.64% | +2.34 pp | +2.55 pp |
| 60% | 63.93% | 62.56% | -1.37 pp | -1.31 pp |

The 95% paired intervals from the generated data exclude zero for these three contrasts. These are Monte Carlo uncertainty intervals, not uncertainty about whether the toy assumptions hold in nature.

### Causal intervention

Holding other randomness fixed while replacing the NACK-erasure rule changes full binding accuracy:

- `do(f=0)`: **72.41167%**, mean **3.39293** total messages.
- `do(f=.6)`: **63.44167%**, mean **2.97405** total messages.
- Paired effect: **+8.970 percentage points** for the reliable-return condition (predicted **+8.9948 pp**).

This controlled `do` calculation isolates the effect of feedback-channel reliability within the *simulated model*. It does not establish causal claims about brains or conscious awareness.

## Limitations and nonclaims

1. Matching **expected communication cost** does not equate worst-case slots, latency, energy, data/control mix, or statistical feedback overhead. Feedback has a three-transmission worst case per feature; blind repetition has a two-transmission worst case.
2. Sensor noise is independent of network loss, all data erasures are independent, and retransmission repeats the **same noisy observation**. New sensing attempts or correlated packet failures would produce different results.
3. Exact selective feedback depends on ideal receiver knowledge of packet loss. Real protocols may require acknowledgments, timeouts, encoding and synchronization.
4. Two features are independent binary variables, and missing observations are guessed at random. There is no binding ambiguity across multiple objects.
5. The experimental design tests a narrowly specified packet-transfer mechanism. It does **not** calculate IIT Φ, implement a genuine Global Neuronal Workspace or biological recurrence, or measure subjective consciousness.
6. The simulations illustrate consequences of specified assumptions; they are not empirical neuroscience measurements.

## Interpretation

At equal *expected* transmission count, reliable feedback can allocate retransmissions more efficiently because it acts specifically on failures. When the return channel becomes unreliable, the control overhead consumes resources without providing useful retransmissions and blind repetition can overtake it. The crossover is predictable analytically and reproducible computationally. Do not generalize this beyond the toy model without examining further constraints.