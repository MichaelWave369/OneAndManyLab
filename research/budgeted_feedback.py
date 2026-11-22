#!/usr/bin/env python3
"""Part IX: matched expected budgets and an unreliable feedback channel.

Synthetic binary feature-binding task. Two independent feature bits (color and
shape) are sensed once, with independent bit-flip noise q. Independent data
packet erasure has probability e. Missing bits are replaced by independent
fair guesses. The task is correct only when *both* features are correct.

Two primary strategies have the same *expected total transmission count*:
  - random_repeat_matched: first packet always; second packet with probability
    p=e*(2-f), chosen without knowing whether the first was lost.
  - feedback_unreliable: first data packet always; on loss, send a NACK through
    a channel with erasure f; on successful NACK, retry data once. The NACK
    itself and the data retry are counted as transmissions.

The strategies do NOT have the same maximum number of attempted transmissions,
latency, or data/control mix. We also compare one-shot, two-copy and three-copy
feedforward baselines. This is not a faithful neural network, a brain model,
IIT Phi, GNWT, or a test of subjective consciousness.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from pathlib import Path

PROTOCOLS = (
    "one_shot", "random_repeat_matched", "feedback_unreliable",
    "always_two", "always_three",
)


def repeat_probability(erasure: float, feedback_loss: float) -> float:
    if not (0 <= erasure <= 1 and 0 <= feedback_loss <= 1):
        raise ValueError("Probabilities must be in [0, 1]")
    p = erasure * (2 - feedback_loss)
    if p > 1:
        raise ValueError("Expected-cost match requires e*(2-f) <= 1")
    return p


def delivery_probability(erasure: float, feedback_loss: float, protocol: str) -> float:
    p = repeat_probability(erasure, feedback_loss)
    if protocol == "one_shot":
        return 1 - erasure
    if protocol == "random_repeat_matched":
        return 1 - erasure + p * erasure * (1 - erasure)
    if protocol == "feedback_unreliable":
        return 1 - erasure + erasure * (1 - feedback_loss) * (1 - erasure)
    if protocol == "always_two":
        return 1 - erasure**2
    if protocol == "always_three":
        return 1 - erasure**3
    raise ValueError(protocol)


def expected_metrics(q: float, e: float, f: float, protocol: str) -> dict:
    if not 0 <= q <= .5:
        raise ValueError("Sensory noise must be in [0, .5]")
    t = delivery_probability(e, f, protocol)
    single_accuracy = .5 + (.5 - q) * t
    if protocol == "one_shot":
        messages = 1.
        max_messages = 1
    elif protocol == "random_repeat_matched":
        messages = 1 + repeat_probability(e, f)
        max_messages = 2
    elif protocol == "feedback_unreliable":
        messages = 1 + e * (2 - f)
        max_messages = 3
    elif protocol == "always_two":
        messages = 2.
        max_messages = 2
    else:
        messages = 3.
        max_messages = 3
    # Features are independent by construction.
    return {
        "delivery_probability": round(t, 7),
        "single_feature_accuracy": round(single_accuracy, 7),
        "both_features_accuracy": round(single_accuracy ** 2, 7),
        "mean_total_messages": round(2 * messages, 7),
        "max_total_messages": 2 * max_messages,
    }


def _episode(q: float, e: float, f: float, rng: random.Random) -> tuple[dict, dict]:
    correct = {name: True for name in PROTOCOLS}
    costs = {name: 0 for name in PROTOCOLS}
    p = repeat_probability(e, f)
    for _feature in range(2):
        truth = rng.randrange(2)
        observation = truth ^ int(rng.random() < q)
        guess = rng.randrange(2)
        first_lost = rng.random() < e
        second_lost = rng.random() < e
        third_lost = rng.random() < e
        nack_lost = rng.random() < f
        scheduled_repeat = rng.random() < p

        delivered = {
            "one_shot": not first_lost,
            "random_repeat_matched": not first_lost or (scheduled_repeat and not second_lost),
            "feedback_unreliable": not first_lost or (not nack_lost and not second_lost),
            "always_two": not first_lost or not second_lost,
            "always_three": not first_lost or not second_lost or not third_lost,
        }
        retry = first_lost and not nack_lost
        costs["one_shot"] += 1
        costs["random_repeat_matched"] += 1 + int(scheduled_repeat)
        costs["feedback_unreliable"] += 1 + int(first_lost) + int(retry)
        costs["always_two"] += 2
        costs["always_three"] += 3
        for name in PROTOCOLS:
            output = observation if delivered[name] else guess
            correct[name] &= output == truth
    return correct, costs


def simulate_condition(n: int, q: float, e: float, f: float, seed: int) -> dict:
    if n < 1 or not 0 <= q <= .5:
        raise ValueError("n must be positive and q must be in [0,.5]")
    repeat_probability(e, f)  # Validate matching rule.
    rng = random.Random(seed)
    correct_count = dict.fromkeys(PROTOCOLS, 0)
    cost_sum = dict.fromkeys(PROTOCOLS, 0)
    paired_sum = 0
    paired_sumsq = 0
    for _ in range(n):
        outcomes, costs = _episode(q, e, f, rng)
        for name in PROTOCOLS:
            correct_count[name] += int(outcomes[name])
            cost_sum[name] += costs[name]
        diff = int(outcomes["feedback_unreliable"]) - int(outcomes["random_repeat_matched"])
        paired_sum += diff
        paired_sumsq += diff * diff
    protocols = {}
    for name in PROTOCOLS:
        a = correct_count[name] / n
        protocols[name] = {
            "both_features_accuracy": round(a, 7),
            "standard_error": round(math.sqrt(a * (1-a) / n), 7),
            "mean_total_messages": round(cost_sum[name] / n, 7),
            "expected": expected_metrics(q, e, f, name),
        }
    delta = paired_sum/n
    paired_se = math.sqrt(max(0, paired_sumsq/n-delta*delta)/n)
    return {
        "sensory_noise": q, "data_loss": e, "feedback_loss": f, "seed": seed,
        "trials_per_protocol": n,
        "matched_repeat_probability": round(repeat_probability(e, f), 7),
        "protocols": protocols,
        "paired_feedback_minus_matched": {
            "observed_accuracy_difference": round(delta, 7),
            "standard_error": round(paired_se, 7),
            "ci95_low": round(delta - 1.96*paired_se, 7),
            "ci95_high": round(delta + 1.96*paired_se, 7),
            "predicted_accuracy_difference": round(
                expected_metrics(q, e, f, "feedback_unreliable")["both_features_accuracy"] -
                expected_metrics(q, e, f, "random_repeat_matched")["both_features_accuracy"], 7),
        },
    }


def feedback_intervention(n: int = 60_000, seed: int = 369,
                          q: float = .1, e: float = .35, treatment_loss: float = .6) -> dict:
    """Paired do(feedback_loss = 0) vs do(feedback_loss = treatment_loss).

    The exogenous first/second data erasures, observations, and NACK uniform
    draws are fixed across arms. We intervene on the NACK-channel loss rule.
    """
    if n < 1 or not 0 <= q <= .5:
        raise ValueError("n and q invalid")
    repeat_probability(e, treatment_loss)
    rng = random.Random(seed)
    counts = [0, 0]
    messages = [0, 0]
    paired_diff_sum = paired_diff_sq = 0
    for _ in range(n):
        successes = [True, True]
        per_arm_cost = [0, 0]
        for _ in range(2):
            truth = rng.randrange(2)
            observed = truth ^ int(rng.random() < q)
            guess = rng.randrange(2)
            first_lost = rng.random() < e
            second_lost = rng.random() < e
            nack_draw = rng.random()
            for j, nack_loss in enumerate((0., treatment_loss)):
                nack_delivered = nack_draw >= nack_loss
                received = not first_lost or (nack_delivered and not second_lost)
                per_arm_cost[j] += 1 + int(first_lost) + int(first_lost and nack_delivered)
                successes[j] &= (observed if received else guess) == truth
        for j in (0, 1):
            counts[j] += int(successes[j])
            messages[j] += per_arm_cost[j]
        d = int(successes[0]) - int(successes[1])
        paired_diff_sum += d
        paired_diff_sq += d * d
    delta = paired_diff_sum/n
    se = math.sqrt(max(0., paired_diff_sq/n - delta**2)/n)
    predicted = (expected_metrics(q, e, 0, "feedback_unreliable")["both_features_accuracy"] -
                 expected_metrics(q, e, treatment_loss, "feedback_unreliable")["both_features_accuracy"])
    return {
        "intervention": "do(feedback_loss=0) vs do(feedback_loss=treatment_loss)",
        "shared_exogenous_randomness": True,
        "trials": n, "sensory_noise": q, "data_loss": e,
        "control_feedback_loss": 0., "treatment_feedback_loss": treatment_loss,
        "no_loss_accuracy": round(counts[0]/n, 7),
        "loss_accuracy": round(counts[1]/n, 7),
        "no_loss_messages": round(messages[0]/n, 7),
        "loss_messages": round(messages[1]/n, 7),
        "observed_causal_accuracy_effect": round(delta, 7),
        "predicted_causal_accuracy_effect": round(predicted, 7),
        "effect_standard_error": round(se, 7),
        "effect_ci95": [round(delta-1.96*se, 7), round(delta+1.96*se, 7)],
    }


def run_matrix(n: int = 20_000, seed: int = 369) -> dict:
    conditions = []
    for q in (0., .1, .25):
        for e in (0., .15, .35):
            for f in (0., .2, .6):
                conditions.append(simulate_condition(n, q, e, f, seed + 113*len(conditions)))
    return {
        "experiment": "Part IX — budget-matched communication with unreliable feedback",
        "version": "1.0", "seed": seed,
        "conditions": conditions,
        "trials_per_condition_per_protocol": n,
        "total_episode_protocol_evaluations": len(conditions)*n*len(PROTOCOLS),
        "intervention": feedback_intervention(seed=seed+8001),
        "limitations": [
            "Equal *expected* total messages, not equal worst-case slots, latency, energy per packet or data/control composition.",
            "The feedback receiver perfectly detects each initial erasure and sends a NACK only on loss.",
            "NACK delivery is unreliable, while the initial data and retry erasures are independent.",
            "A single sensory observation is reused on repetitions; transmission repetition cannot repair sensory noise.",
            "The feedforward random-repeat schedule is not allowed to inspect erasure events.",
            "The two feature bits are independent; missing observations are replaced by fair random guesses.",
            "These are information-theoretic toy protocols, not biological recurrent systems, IIT Φ, GNWT or consciousness tests.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trials", type=int, default=20_000)
    ap.add_argument("--seed", type=int, default=369)
    ap.add_argument("--output", default="part9.json")
    ap.add_argument("--csv", default="part9.csv")
    args = ap.parse_args()
    result = run_matrix(args.trials, args.seed)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    with Path(args.csv).open("w", newline="", encoding="utf-8") as output:
        w = csv.writer(output)
        w.writerow(["sensory_noise", "data_loss", "feedback_loss", "protocol",
                    "accuracy", "mean_messages", "predicted_accuracy", "predicted_messages"])
        for c in result["conditions"]:
            for name, val in c["protocols"].items():
                w.writerow([c["sensory_noise"],c["data_loss"],c["feedback_loss"],name,
                            val["both_features_accuracy"],val["mean_total_messages"],
                            val["expected"]["both_features_accuracy"],
                            val["expected"]["mean_total_messages"]])
    print(f"wrote {target}, {args.csv}; {len(result['conditions'])} conditions; "
          f"{result['total_episode_protocol_evaluations']:,} protocol-evaluations")


if __name__ == "__main__":
    main()