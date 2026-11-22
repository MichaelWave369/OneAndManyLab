# Part X: Bursty failures, imperfect loss detection, deadlines and energy

**Status:** Reproducible synthetic experiment. It does not study human or machine subjective experience or provide a realistic model of the Internet, neurons, or Integrated Information Theory.

## Question

How robust is selective retransmission once we introduce correlated packet loss, missed loss detections, false alarms, control-channel erasures, explicit latency and energy costs, and deadlines? Does an observed advantage persist if we compare against blind repetitions matched by *expected packet count* or *expected energy*, instead of comparing against a deliberately under-resourced baseline?

## Model, precisely

A trial has two independently sensed binary features. Each sensor bit is flipped with probability `q=0.1`. One data-packet erasure variable `L1` is Bernoulli(`e`). A possible second attempt has `L2=L1` with probability `rho`, otherwise it is an independently resampled Bernoulli(`e`). Thus both marginal losses are `e`, and `Corr(L1,L2)=rho` when `0<e<1`. This is a **sticky-pair correlation construction**, not a complete multi-state fading-channel simulation. The two features have independent channel draws.

The receiver sends a negative acknowledgement (NACK) after a missing first packet with detection sensitivity `d`; if the first packet arrived, it raises a false NACK with probability `a=0.08`. NACKs are independently erased with probability `f`. A delivered NACK triggers *one* data retry.

On each feature, the mean NACK probability is `s = e*d + (1-e)*a`. Expected feedback message count is `1 + s*(2-f)`. A random blind repetition with probability `p_message=s*(2-f)` matches that **expected message count**. A second blind baseline uses `p_energy=s*(0.2+1-f)`, matching **expected energy** when data costs 1 energy unit and a NACK 0.2. These are separate comparisons, not simultaneous matching of both budgets. Maximum expenditures differ.

The first data arrives at `t=1`; a blind second copy at `t=2`; the feedback retry arrives at `t=3.4` owing to `1.4` control roundtrip plus `1` retry. Results are measured at either `deadline=2.5` or `4.0`. The policies are *not* deadline-aware and may transmit useless late retries. If every copy of a feature is lost or late, its value is replaced by a fair random guess. **A success requires both feature values to be correct.** All strategies in a paired episode use the same noisy sensory values and possible first/second data erasures; optional scheduling and NACK draws are separate.

## Analytic predictions

Let `r = e*(1-rho)*(1-e)` denote the probability that a first packet is lost but a second, correlated attempt would succeed.

By a sufficiently long deadline:

- One-shot delivery: `1-e`
- Blind message-matched delivery: `1-e + p_message*r`
- Blind energy-matched delivery: `1-e + p_energy*r`
- Selective-feedback delivery: `1-e + e*d*(1-f)*(1-rho)*(1-e)`
- Always-two delivery: `1-e+r`

Terms involving the second packet vanish if its arrival time exceeds the deadline. With successful delivery probability `t`, one feature is correct with probability `0.5 + (0.5-q)*t`, and both independently sensed features are correct with its square.

## Experiment grid

48 conditions: `e ∈ {0.15, 0.35}`, `rho ∈ {0, 0.45, 0.85}`, `d ∈ {0.55, 0.95}`, `f ∈ {0.05, 0.4}`, `deadline ∈ {2.5, 4.0}`; `q=0.1`, `a=0.08`. **12,000 episodes per strategy and condition; 2,880,000 protocol evaluations.** Fixed master seed 369; unique derived seed for each condition. Five strategies per episode, with shared underlying random inputs. Exact Python standard-library implementation and expected metrics are in `bursty_feedback.py`.

## Key observations

Under `e=.35`, `d=.95`, `f=.05` and long deadline `4.0`:

| Pair correlation | Selective feedback | Blind message-matched | Paired gain |
|---|---:|---:|---:|
| 0.00 | 71.10% | 68.69% | +2.41 percentage points |
| 0.45 | 64.36% | 63.53% | +0.83 percentage points |
| 0.85 | 60.14% | 59.85% | +0.29 percentage points |

When the deadline is tightened to `2.5`, feedback retry delivery (t=3.4) becomes too late; at `rho=.45`, measured feedback falls to **57.38%**, while blind message-matched repetition reaches **63.30%**. This reversal is a consequence of the stipulated timing model, not a general measurement of network performance.

## Reproduce

```bash
python -m unittest discover -s research -p 'test_*.py' -v
python research/bursty_feedback.py --trials 12000 --seed 369 --output public/data/part10.json
npm install
npm run build
```

`part10.csv` is produced adjacent to the JSON. The website loads these committed results; it does not recompute simulations in a user's browser. The React controls select only actual stored conditions.

## Guardrails

- Burstiness is limited to two correlated attempted data packets within a single feature; failures are independent across features and control-message loss is independent of data loss.
- Energy and time values are illustrative arbitrary units, not hardware measurements. The short NACK is cheaper than data but incurs longer turnaround.
- The feedback scheme assumes an explicit missing-packet notification rule. Other real protocols use timeouts, ACKs, sequence numbers and different error detection.
- Match is on *expected* packet or energy budgets, not per-episode, tail latency, or worst-case resource availability.
- `12,000` Monte Carlo episodes per condition imply sampling uncertainty. The dataset contains both Monte Carlo outcomes, analytical expectations, and paired standard errors / 95% normal-approximation intervals.
- No discovery here demonstrates phenomenal binding, consciousness, universal mind, or the cosmologies of Plotinus or the Nag Hammadi writings.

## Next experiments

Model a genuine multi-state temporal erasure process across features; implement deadline-aware decision policies; compare under equal per-trial hard energy caps; and evaluate results against empirical network traces. These require additional design and data and are *not* claimed as completed.
