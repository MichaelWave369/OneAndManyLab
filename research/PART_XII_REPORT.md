# Part XII — RIPE Atlas measured ping replay

## Scope and primary evidence

This is an **observational replay**, not a causal evaluation of deployed retransmission policies. We use real ICMP ping results from RIPE Atlas built-in measurements, not synthetic loss markers. Original data source and documentation: https://atlas.ripe.net/docs/getting-started/built-in-measurements/ and https://atlas.ripe.net/docs/apis/measurement-result-format/version-4750/.

Source window: **2026-11-20 00:00–12:00 UTC**, Unix 1795132800–1795176000. Public measurement/probe pairs: **1001/10006** (k-root), **1010/10006** (b-root), **1001/10070** (k-root). Three selected series are a convenience sample, not representative of all networks. Original API URL for each appears in the frozen \`public/data/part12.json\`.

We retained **537 complete groups**, each consisting of three ordered ping results, for **1,611 actual ping observations** including **four explicit ICMP timeouts**. One incomplete group per series was excluded. Frozen data intentionally excludes source IP addresses, source locations, and unrelated personal metadata. Timeouts are stored as \`null\`; replies are recorded RTTs in milliseconds.

**Key sampling limitation:** Groups are about 240 seconds apart, NOT an uninterrupted second-by-second packet trace. The three results within each group are not guaranteed independent. We cannot measure transmission changes or feedback delays from these data.

## Predeclared replay rules

At a specified response RTT cutoff, a measured reply passes if RTT is at or below that cutoff. An RTT above it is still a successful reply, **not observed packet loss**.

- **One:** the first ping passes.
- **Blind two:** the first or second ping passes; always costs two hypothetical attempts.
- **Oracle-selective upper bound:** retry only when the *observed* first reply did not pass, so its success set necessarily equals blind two. This is hindsight: it is not a deployable instantaneous feedback mechanism. Its unitless modeled cost adds 0.15 if the oracle chooses a second attempt.
- **Blind three:** any of the three observed pings passes; always costs three hypothetical attempts.

The React dashboard computes outcomes directly from frozen raw observations. Choose source, RTT cutoff (10, 20, 30, 50 ms), and chronological exploratory/holdout/all splits. The Python companion implements the same deterministic rules and supports offline replay.

## Preliminary result and interpretation

The observed timeout incidence is just 4/1611 = about **0.25%** in these selected traces. Most differences under stricter thresholds result from *late replies*, not packet loss. In the second half of measurement 1001 / probe 10006, a 20 ms response cutoff produced 92.22% first-opportunity success; a second opportunity also produced 92.22%. That does **not** imply that duplicates never help elsewhere.

A comparison of observed ping opportunities is **not a causal estimate** of what would happen if a real sender used those policies. Adaptive sends change timing, load and link state; counterfactual outcomes were not recorded. The oracle has unrealizable perfect hindsight. There is no real radio-energy measurement, no real NACK feedback channel, and no controlled application deadline in this dataset. These observations cannot verify any claim about subjective consciousness or historical Gnostic cosmology.

## Reproduce

\`\`\`bash
python -m unittest discover -s research -p 'test_*.py' -v
python research/measured_ping_replay.py --input public/data/part12.json --output /tmp/part12_results.json
\`\`\`

Re-fetch the original observations from the public API using:

\`\`\`bash
python research/import_ripe_atlas.py --start 1795132800 --stop 1795176000 --pairs 1001:10006,1010:10006,1001:10070 --output public/data/part12.json
\`\`\`

Further work should randomize actual implemented policies on an instrumented path, recording packet send/receive times, NACK traffic, power and queue effects, with holdout paths selected before observing outcomes.
