# Part XI — Temporal channel replay, constrained energy, and deadline-aware policies

## Research question

Does selective feedback outperform blind repetition after accounting for **a hard per-episode energy cap, time-varying measured service capacity, detection errors, and deadline pressure**?

## Data provenance

We extracted the first 51 rows (0–10 s, 0.2 s spacing, unchanged) from the open [Chorus cellular-airport downlink bandwidth trace](https://github.com/GreenLv/Chorus/blob/main/bw_traces/downlink-cellular_airport.csv), a measured trace used in Gerui Lv et al., *Chorus: Coordinating Mobile Multipath Scheduling and Adaptive Video Streaming*, ACM MobiCom 2024, DOI: 10.1145/3636534.3649359. The source dataset is published under CC BY 4.0. Attribution and license are in `research/traces/README.md`.

**The trace measures bandwidth, not packet loss.** This experiment replays the measured series as packet service capacity, then applies *synthetic* burst losses, sensor flips, NACK failures, and data decisions. Its outcomes should never be described as measured packet-loss performance in a real network.

## Model and controls

- Time discretization 200 ms per tick; fixed 60-kB packets. A slot permits `floor(Mbps * 1e6 * .2 / (8 * 60000))` transmissions, without carrying unused bandwidth over.
- Two binary feature observations are sensed with independent 10% bit-flip probability. Missing features default to a pre-sampled random guess.
- The loss model uses a hidden Good/Bad state with probabilities `P(G→B)=0.08`, `P(B→G)=0.25`, erasure `P(loss|G)=0.04`, and `P(loss|B)=0.72`. Independent control re-samples the state at each tick, matching the stationary fraction.
- The modeled return channel delivers detection-generated negative acknowledgements with 90% sensitivity, 8% false alarms, 10% return loss, and 3 ticks of delay. It is separate from the measured forward-capacity budget but NACKs cost 0.15 energy.
- Each data transmission costs 1.0 energy, and every trial has a **hard** cap of 2.0, 3.25, or 4.5 energy units.
- Deadlines are 1.0, 1.8, or 2.4 s; 4 policies: one-shot, blind two-copy, selective feedback, and a simple deadline-aware hybrid. The hybrid uses blind repetition if the horizon is short; otherwise it selects feedback. It is deliberately **not learned** and has no access to future channel states.
- Two capacity sources: a measured 10-second excerpt and synthetic constant 4.5 Mb/s. Both apply the same synthetic loss processes. 36 conditions × 4 policies × 8,000 seeded episodes = **1,152,000 protocol evaluations**.
- The simulator pairs truth, sensor observations, loss-state timelines, reverse-control draws, and time-slot outcomes across the four protocols within each episode, allowing meaningful comparisons without giving policies an oracle.

## Results and important caveats

The primary outputs are `public/data/part11.json` and `.csv`. Because redundancy consumes more energy, blind repetition may win on accuracy while selective feedback uses considerably less mean energy. Outcomes depend on both the **cap** and the **deadline**. A hybrid may tie one comparator exactly when its rule selects that comparator. It is not an optimized policy; do not interpret ties as scientific superiority.

The client reads *precomputed* results and provides four scenario controls. The dataset contains approximate 95% paired intervals for the adaptive-minus-selective-feedback gap, calculated from the outcomes of paired episodes. The experiment does **not** reproduce physical network hardware, congestion feedback, competing flows, end-to-end RTT distributions, transport-layer protocols, or neuronal processes. The measured capacity snippet is short and geographically unrepresentative. No neural consciousness or IIT Φ is calculated.

## Replication

```sh
python -m unittest discover -s research -p 'test_*.py' -v
python research/temporal_channel.py --trials 8000 --seed 369 --output public/data/part11.json
```

Python 3.10+ standard library only. The source accepts `--trace path/to/custom.csv` with exact header `Timestamp (s),Bandwidth (Mbps)`, an increasing uniform 0.2-second time grid, and nonnegative finite bandwidth.

## Next steps

Model finite queues and byte-level partial service; use longer traces from multiple environments; add RTT and loss measurements that are *actually recorded*; evaluate confidence intervals for full paired policy comparisons; investigate learned policies with out-of-sample validation and energy-deadline Pareto frontiers.
