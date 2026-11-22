#!/usr/bin/env python3
"""Reproduce a small, explicitly limited behavioral-equivalence demonstration.

Based on the construction in Wu & He (2026), arXiv:2611.08469, Section 3.
We independently implement the two-network, two-step I/O experiment, not IIT Phi.
All initial four-spin states are used with equal numbers of trials. State values
are +1/-1, and all noise sources are independent.

This demonstrates a difference in causal mechanisms and observability, not a
measurement of consciousness or subjective/phenomenal binding.
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
import random
from pathlib import Path

RECURRENT_RELIABILITIES = (0.78, 0.80, 0.83, 0.85)
A = math.prod(2.0 * p - 1.0 for p in RECURRENT_RELIABILITIES)
MATCH_PROBABILITY = (1.0 + A) / 2.0
CHAIN_RELIABILITY = (1.0 + math.sqrt(A)) / 2.0


def noise(rng: random.Random, reliability: float) -> int:
    return 1 if rng.random() < reliability else -1


def recurrent_trial(x: tuple[int, ...], rng: random.Random) -> tuple[int, int]:
    # All four units update with parity of the OTHER three units plus noise.
    t1 = tuple(
        math.prod(x[j] for j in range(4) if j != i) * noise(rng, RECURRENT_RELIABILITIES[i])
        for i in range(4)
    )
    # The specified output is unit 1 (zero-based index 0) at t+2.
    t2_output = math.prod(t1[j] for j in (1, 2, 3)) * noise(rng, RECURRENT_RELIABILITIES[0])
    # The internal probe is unit 2 (index 1) at t+1.
    return t2_output, t1[1]


def feedforward_trial(x: tuple[int, ...], rng: random.Random) -> tuple[int, int]:
    # We retain a four-unit chain, but only the first three units matter at the
    # declared horizon. t+1 unit 2 copies the external input with probability q,
    # and t+2 unit 3 copies unit 2 with the same probability.
    t1_unit2 = x[0] * noise(rng, CHAIN_RELIABILITY)
    t2_unit3 = t1_unit2 * noise(rng, CHAIN_RELIABILITY)
    return t2_unit3, t1_unit2


def run(trials_per_state: int, seed: int) -> dict:
    if trials_per_state < 1:
        raise ValueError('trials_per_state must be a positive integer')
    rng = random.Random(seed)
    states = list(itertools.product((-1, 1), repeat=4))
    totals = {name: {'io_match': 0, 'probe_match_input': 0, 'n': 0} for name in ('recurrent', 'feedforward')}
    for state in states:
        for _ in range(trials_per_state):
            for name, function in (('recurrent', recurrent_trial), ('feedforward', feedforward_trial)):
                output, probe = function(state, rng)
                bucket = totals[name]
                bucket['n'] += 1
                bucket['io_match'] += int(output == state[0])
                bucket['probe_match_input'] += int(probe == state[0])

    def summarize(name: str) -> dict:
        t = totals[name]
        n = t['n']
        p_io = t['io_match'] / n
        p_probe = t['probe_match_input'] / n
        return {
            'trials': n,
            'io_match_rate': round(p_io, 6),
            'io_standard_error': round(math.sqrt(p_io * (1 - p_io) / n), 6),
            'internal_probe_match_rate': round(p_probe, 6),
            'probe_standard_error': round(math.sqrt(p_probe * (1 - p_probe) / n), 6),
        }

    return {
        'experiment': 'Same external behavior, different internal causal organization',
        'reference': 'Wu and He (2026) arXiv:2611.08469 Section 3',
        'status': 'Independent minimal Monte Carlo implementation of selected construction; no IIT Phi calculation',
        'seed': seed,
        'initial_states': len(states),
        'trials_per_state_per_architecture': trials_per_state,
        'analytical': {
            'A': round(A, 6),
            'matching_input_output_probability_both': round(MATCH_PROBABILITY, 6),
            'recurrent_internal_probe_matching_input_probability': 0.5,
            'feedforward_internal_probe_matching_input_probability': round(CHAIN_RELIABILITY, 6),
            'phi_values_reported_in_paper_not_calculated_here': {'recurrent': 0.28, 'feedforward': 0.0},
        },
        'observed': {name: summarize(name) for name in totals},
        'limitations': [
            'Equivalence holds for the specified input, output and two-step horizon, not arbitrary tasks.',
            'The Monte Carlo trial noise is independent; initial four-bit states are balanced.',
            'Internal probe refers to one intermediate unit, not to consciousness.',
            'This implementation does not compute integrated information or establish which, if either, system experiences anything.'
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trials-per-state', type=int, default=5000)
    parser.add_argument('--seed', type=int, default=369)
    parser.add_argument('--output', type=Path, default=Path('results.json'))
    args = parser.parse_args()
    result = run(args.trials_per_state, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()