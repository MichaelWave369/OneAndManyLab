#!/usr/bin/env python3
"""Controlled toy feature-binding / observability experiment (stdlib only).

This evaluates packet-transfer protocols, not brains, subjective experience,
IIT Phi, or a faithful implementation of Global Neuronal Workspace Theory.

Shared task: At t=0 there are two objects (locations 0,1), each with a color
bit and shape bit. Independent sensory errors may flip the observed bits.
At t=1 a target location cue arrives. Two feature specialists must deliver
both observed feature bits to a readout, which reports the target pair.
Packets can be erased. Missing features are guessed with a fair coin.
The same precomputed noisy sensations and target cue are used by every protocol.

Protocols:
- feedforward: each specialist sends its two-bit packet once; readout caches it
  until cue arrives.
- workspace: each specialist publishes once to a shared cache; the cache answers
  when the cue arrives. On this one-query task, same information/budget as FF.
- recurrent_retry: on erasure, readout sends a reliable NACK and specialist
  retransmits once. Both data and NACK packets are counted. This is an
  intentionally simplified feedback protocol, not a neural recurrent network.
- feedforward_redundant: sends both packets twice without feedback, to control
  for the benefit of an additional opportunity for delivery.

All protocols receive equal initial sensory inputs; budgets and reliability
mechanisms intentionally differ and are measured, not silently equated.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import random
from pathlib import Path

PROTOCOLS = ("feedforward", "workspace", "recurrent_retry", "feedforward_redundant")


def probability_feature_success(sensory_noise: float, erasure: float, protocol: str) -> float:
    if protocol not in PROTOCOLS:
        raise ValueError(protocol)
    final_erasure = erasure if protocol in ("feedforward", "workspace") else erasure ** 2
    return (1.0 - final_erasure) * (1.0 - sensory_noise) + 0.5 * final_erasure


def theoretical_metrics(sensory_noise: float, erasure: float, protocol: str) -> dict:
    per_feature = probability_feature_success(sensory_noise, erasure, protocol)
    if protocol in ("feedforward", "workspace"):
        data_packets, control_packets = 2.0, 0.0
    elif protocol == "recurrent_retry":
        data_packets, control_packets = 2.0 + 2 * erasure, 2 * erasure
    else:
        data_packets, control_packets = 4.0, 0.0
    return {
        "single_feature_accuracy": round(per_feature, 6),
        "both_features_accuracy": round(per_feature**2, 6),
        "mean_data_packets": round(data_packets, 6),
        "mean_control_packets": round(control_packets, 6),
        "mean_total_packets": round(data_packets + control_packets, 6),
    }


def _deliver(protocol: str, erasure: float, rng: random.Random) -> tuple[bool, int, int]:
    if protocol in ("feedforward", "workspace"):
        return rng.random() >= erasure, 1, 0
    if protocol == "feedforward_redundant":
        a = rng.random() >= erasure
        b = rng.random() >= erasure
        return a or b, 2, 0
    if protocol == "recurrent_retry":
        first = rng.random() >= erasure
        if first:
            return True, 1, 0
        # Reliable NACK control channel, explicitly counted; second data attempt.
        return rng.random() >= erasure, 2, 1
    raise ValueError(protocol)


def _noisy_bit(b: int, flip_p: float, rng: random.Random) -> int:
    return b ^ int(rng.random() < flip_p)


def simulate_condition(n: int, sensory_noise: float, erasure: float, seed: int) -> dict:
    if n <= 0 or not (0 <= sensory_noise <= 0.5) or not (0 <= erasure <= 1):
        raise ValueError("n > 0, sensory_noise in [0,0.5], erasure in [0,1] required")
    rng = random.Random(seed)
    stats = {p: {"both_correct": 0, "correct_features": 0, "data_packets": 0,
                 "control_packets": 0, "received_packets": 0} for p in PROTOCOLS}

    for _ in range(n):
        truth = ((rng.randrange(2), rng.randrange(2)),
                 (rng.randrange(2), rng.randrange(2)))  # (color at loc0/1, shape at loc0/1)
        noisy = tuple(tuple(_noisy_bit(bit, sensory_noise, rng) for bit in feature)
                      for feature in truth)
        cue = rng.randrange(2)
        for protocol in PROTOCOLS:
            correct = 0
            s = stats[protocol]
            for feature_index in range(2):
                received, data, control = _deliver(protocol, erasure, rng)
                s["data_packets"] += data
                s["control_packets"] += control
                s["received_packets"] += int(received)
                response = noisy[feature_index][cue] if received else rng.randrange(2)
                correct += int(response == truth[feature_index][cue])
            s["correct_features"] += correct
            s["both_correct"] += int(correct == 2)

    results = {}
    for protocol, s in stats.items():
        accuracy = s["both_correct"] / n
        results[protocol] = {
            "both_features_accuracy": round(accuracy, 6),
            "both_features_standard_error": round(math.sqrt(accuracy * (1 - accuracy) / n), 6),
            "single_feature_accuracy": round(s["correct_features"] / (2 * n), 6),
            "mean_data_packets": round(s["data_packets"] / n, 6),
            "mean_control_packets": round(s["control_packets"] / n, 6),
            "mean_total_packets": round((s["data_packets"] + s["control_packets"]) / n, 6),
            "mean_received_packets": round(s["received_packets"] / n, 6),
            "analytical": theoretical_metrics(sensory_noise, erasure, protocol),
        }
    return {"trials_per_protocol": n, "sensory_noise": sensory_noise,
            "packet_erasure": erasure, "seed": seed, "protocols": results}


def causal_common_cause_test(n: int = 100_000, sensor_noise: float = 0.1,
                             transmission_noise: float = 0.1, seed: int = 369) -> dict:
    """High observational correlation needn't imply causal A->B.

    In a shared-cause setup: latent Z -> A and latent Z -> B. The hypothetical
    intervention do(A=0) vs do(A=1) leaves B unchanged under fixed exogenous
    randomness. In a directed A->B setup, B = A XOR transmission noise, and
    the intervention changes its probability of taking value 1.
    """
    if n <= 0 or not (0 <= sensor_noise <= .5) or not (0 <= transmission_noise <= .5):
        raise ValueError("Invalid causal test arguments")
    rng = random.Random(seed)
    agree = 0
    a_ones = b_ones = both_ones = 0
    directed_one_do0 = directed_one_do1 = 0
    common_diff_count = 0
    for _ in range(n):
        z = rng.randrange(2)
        a = z ^ int(rng.random() < sensor_noise)
        b = z ^ int(rng.random() < sensor_noise)
        agree += int(a == b)
        a_ones += a
        b_ones += b
        both_ones += int(a == 1 and b == 1)
        # Under do(A=0) or do(A=1), B still uses the same Z and noise.
        b_under_do0 = b_under_do1 = b
        common_diff_count += int(b_under_do0 != b_under_do1)
        transmitted_noise_bit = int(rng.random() < transmission_noise)
        directed_one_do0 += transmitted_noise_bit          # 0 XOR noise
        directed_one_do1 += 1 - transmitted_noise_bit      # 1 XOR noise
    mean_a, mean_b = a_ones / n, b_ones / n
    variance_product = mean_a * (1 - mean_a) * mean_b * (1 - mean_b)
    corr = ((both_ones / n - mean_a * mean_b) / math.sqrt(variance_product)
            if variance_product else None)
    return {
        "n": n,
        "shared_cause": {
            "observed_agreement_rate": round(agree / n, 6),
            "observed_pearson_r": None if corr is None else round(corr, 6),
            "theoretical_pearson_r": round((1 - 2 * sensor_noise)**2, 6),
            "interventional_effect_do_A1_minus_do_A0": 0.0,
            "paired_intervention_difference_count": common_diff_count,
        },
        "directed_A_to_B": {
            "interventional_effect_do_A1_minus_do_A0": round((directed_one_do1 - directed_one_do0) / n, 6),
            "theoretical_effect": round(1 - 2 * transmission_noise, 6),
        },
        "interpretation": "Shared causes generate correlation without A causing B. The second model has an explicit A->B channel.",
    }


def run_matrix(n: int = 50_000, seed: int = 369) -> dict:
    conditions = []
    for sensory_noise in (0.0, 0.1, 0.25):
        for erasure in (0.0, 0.15, 0.35):
            cond_seed = seed + len(conditions) * 101
            conditions.append(simulate_condition(n, sensory_noise, erasure, cond_seed))
    return {
        "experiment": "Distributed color-and-shape feature binding under noise and channel erasure",
        "method": "Paired synthetic episodes; identical initial sensory samples and target cues; differing packet-transfer protocols",
        "status": "Model comparison; not IIT/GNWT implementation or consciousness measurement",
        "seed": seed,
        "trials_per_condition_per_protocol": n,
        "total_trials_per_protocol": len(conditions)*n,
        "conditions": conditions,
        "causal_control": causal_common_cause_test(seed=seed + 999),
        "limitations": [
            "Protocols deliberately use different data/control message budgets; advantages cannot be attributed to topology alone.",
            "A simplified shared cache called 'workspace' is not a faithful Global Neuronal Workspace Theory implementation.",
            "A feedback retry protocol is not a faithful biological recurrent neural network.",
            "Each packet carries two bits from one feature specialist. Packets erase independently; control NACKs are reliable and counted.",
            "Receiver uses an unbiased random guess for missing data, and only one target cue arrives after sensing.",
            "Sensory noise is independent by feature/location and shared across the four protocol comparisons within an episode.",
            "No formal IIT integrated-information quantity or phenomenal experience is measured.",
        ],
    }


def write_summary_csv(report: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sensory_noise", "packet_erasure", "architecture", "both_correct",
                         "standard_error", "analytical_both_correct", "single_feature_correct",
                         "data_packets", "control_packets", "total_packets"])
        for cond in report["conditions"]:
            for protocol, r in cond["protocols"].items():
                writer.writerow([cond["sensory_noise"], cond["packet_erasure"], protocol,
                                 r["both_features_accuracy"], r["both_features_standard_error"],
                                 r["analytical"]["both_features_accuracy"],
                                 r["single_feature_accuracy"], r["mean_data_packets"],
                                 r["mean_control_packets"], r["mean_total_packets"]])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=50_000, help="Trials per condition and protocol")
    parser.add_argument("--seed", type=int, default=369)
    parser.add_argument("--output", type=Path, default=Path("binding_results.json"))
    args = parser.parse_args()
    report = run_matrix(n=args.trials, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_summary_csv(report, args.output.with_suffix(".csv"))
    print(f"Wrote {args.output} and {args.output.with_suffix('.csv')}.")
    example = next(c for c in report['conditions'] if c['sensory_noise'] == .1 and c['packet_erasure'] == .35)
    print('At 10% sensory noise / 35% packet erasure:')
    for name, entry in example['protocols'].items():
        print(f"  {name:24s} {entry['both_features_accuracy']:.3%} correct, {entry['mean_total_packets']:.3f} total packets")
    print('Shared-cause observational correlation:', report['causal_control']['shared_cause']['observed_pearson_r'])
    print('Shared-cause intervention effect:', report['causal_control']['shared_cause']['interventional_effect_do_A1_minus_do_A0'])


if __name__ == "__main__":
    main()