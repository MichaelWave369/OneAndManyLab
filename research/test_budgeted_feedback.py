"""Checks for Part IX formulae, budget matching and interventions."""
import math
import unittest

from budgeted_feedback import (repeat_probability, delivery_probability,
                               expected_metrics, simulate_condition,
                               feedback_intervention, run_matrix)


class BudgetedFeedbackTests(unittest.TestCase):
    def test_matched_mean_total_messages(self):
        for e in (0, .15, .35):
            for f in (0, .2, .6):
                a = expected_metrics(.1, e, f, "feedback_unreliable")
                b = expected_metrics(.1, e, f, "random_repeat_matched")
                self.assertAlmostEqual(a["mean_total_messages"], b["mean_total_messages"])

    def test_boundary_zero_erasure(self):
        for protocol in ("one_shot", "feedback_unreliable", "always_three"):
            self.assertAlmostEqual(expected_metrics(.1, 0., .5, protocol)["both_features_accuracy"], .81)

    def test_delivery_likelihoods(self):
        self.assertAlmostEqual(delivery_probability(.35, 0, "feedback_unreliable"), 1 - .35**2)
        self.assertAlmostEqual(delivery_probability(.35, 1, "feedback_unreliable"), .65)
        self.assertAlmostEqual(delivery_probability(.35, .6, "always_three"), 1-.35**3)

    def test_invalid_matched_budget_rejected(self):
        with self.assertRaises(ValueError):
            repeat_probability(.9, .1)

    def test_monte_carlo_matches_predictions(self):
        c = simulate_condition(18_000, .1, .35, .2, 369)
        for p in c["protocols"].values():
            self.assertLess(abs(p["both_features_accuracy"]-p["expected"]["both_features_accuracy"]), .025)
            self.assertLess(abs(p["mean_total_messages"]-p["expected"]["mean_total_messages"]), .045)

    def test_feedback_advantage_targeting(self):
        # With e=.35 f=.2, feedback is more likely than a blind repeat to
        # allocate its second data packet to a genuinely failed first attempt.
        a = expected_metrics(.1, .35, .2, "feedback_unreliable")
        b = expected_metrics(.1, .35, .2, "random_repeat_matched")
        self.assertGreater(a["both_features_accuracy"], b["both_features_accuracy"])

    def test_feedback_is_not_better_than_two_repeats(self):
        a = expected_metrics(.1, .35, .2, "feedback_unreliable")
        b = expected_metrics(.1, .35, .2, "always_two")
        self.assertLess(a["both_features_accuracy"], b["both_features_accuracy"])

    def test_intervention_consistent(self):
        x = feedback_intervention(n=20_000, seed=369)
        self.assertGreater(x["observed_causal_accuracy_effect"], 0)
        self.assertLess(abs(x["observed_causal_accuracy_effect"]-x["predicted_causal_accuracy_effect"]), .025)
        self.assertGreater(x["no_loss_messages"], x["loss_messages"])

    def test_matrix_structure(self):
        x = run_matrix(n=10,seed=369)
        self.assertEqual(len(x["conditions"]),27)
        self.assertEqual(x["total_episode_protocol_evaluations"],1350)
        self.assertTrue(x["limitations"])


if __name__ == "__main__":
    unittest.main()