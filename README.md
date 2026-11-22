# One & Many Lab

**Open computational experiments in feature binding, causal inference, feedback and the limits of observability.** A PHI369 Labs open research project.

Live React dashboard: **https://michaelwave369.github.io/OneAndManyLab/**

> **Scope:** Models of information processing, not measurements of subjective consciousness or evidence for ancient cosmologies. No IIT Φ is calculated.

## What's inside

- **React/Vite web app**: real dataset-backed binding comparisons, causal-control visualizations, linked evidence, responsive dark research UI.
- **`research/`**: original Part VII and VIII reproducible Python simulations and eight unit tests, plus a standalone archived offline dashboard.
- **`public/data/`**: seeded experimental results as JSON and CSV, served unmodified by GitHub Pages.
- **`.github/workflows/pages.yml`**: tests both experiments, compiles React with Vite, deploys with GitHub Pages Actions.

## Reproduce the simulations

Python 3.10 or later. No Python dependencies required.

```bash
cd research
python -m unittest discover -v
python binding_architectures.py --trials 50000 --seed 369 --output binding_results.json
python causal_binding_probe.py --trials-per-state 50000 --seed 369 --output results.json
```

## Run React locally

Node.js 22+.

```bash
npm install
npm run dev
npm run build
```

The deployed app loads the committed datasets under `public/data`. It does **not** run new simulations inside the browser. Controls select among nine previously simulated conditions. Python produces fresh datasets when run separately.

## Core observations

For 10% sensory noise and 35% packet-erasure probability (50,000 trials per protocol), we measured:

| Protocol | Full-binding accuracy | Mean total messages |
|---|---:|---:|
| Feedforward | 57.806% | 2.000 |
| Shared workspace | 57.758% | 2.000 |
| Feedback with retry | 72.226% | 3.396 |
| Redundant feedforward | 72.402% | 4.000 |

Feedback does not prove conscious integration. In this toy model, retry and fixed duplication have identical *expected* accuracy, because both provide two packet-delivery opportunities. Feedback uses a perfectly reliable NACK control channel, counted in message costs. See [research report](research/RESEARCH_REPORT.md) for detailed limitations.

## References

- Wu & He (2026), *Same Behavior, Different Mechanism* (preprint): https://arxiv.org/abs/2611.08469
- Cogitate Consortium et al. (2025), *Nature*: https://doi.org/10.1038/s41586-025-08888-1
- Percy & Agarwal (2026), *Phenomenal binding problem*: https://pubmed.ncbi.nlm.nih.gov/41637896/

## Deployment

Enable **Settings → Pages → Build and deployment → Source: GitHub Actions** once, then push to `main`. The Pages workflow validates the Python tests before publishing the React app. No secrets or external API keys are required.