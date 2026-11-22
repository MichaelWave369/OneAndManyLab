"""Checks for the Part VIII synthetic binding and causal-inference lab."""
import unittest

from binding_architectures import (
    PROTOCOLS, causal_common_cause_test, probability_feature_success,
    simulate_condition, theoretical_metrics,
)


class TestBindingArchitectures(unittest.TestCase):
    def test_zero_noise_and_erasure_all_perfect(self):
        result = simulate_condition(1500, 0, 0, 4)
        for name in PROTOCOLS:
            self.assertEqual(result['protocols'][name]['both_features_accuracy'], 1.0)

    def test_expected_analytical_identity(self):
        for q in (0, .1, .25):
            for p in (0, .15, .35):
                self.assertEqual(theoretical_metrics(q, p, 'feedforward'),
                                 theoretical_metrics(q, p, 'workspace'))
                self.assertAlmostEqual(
                    probability_feature_success(q, p, 'recurrent_retry'),
                    probability_feature_success(q, p, 'feedforward_redundant'))

    def test_retries_and_redundancy_help_when_erasures_present(self):
        result = simulate_condition(12000, .1, .35, 369)
        ff = result['protocols']['feedforward']['both_features_accuracy']
        workspace = result['protocols']['workspace']['both_features_accuracy']
        retry = result['protocols']['recurrent_retry']['both_features_accuracy']
        redundant = result['protocols']['feedforward_redundant']['both_features_accuracy']
        self.assertAlmostEqual(ff, workspace, delta=.025)
        self.assertGreater(retry - ff, .1)
        self.assertAlmostEqual(retry, redundant, delta=.025)
        self.assertGreater(result['protocols']['feedforward_redundant']['mean_total_packets'],
                           result['protocols']['recurrent_retry']['mean_total_packets'])

    def test_shared_cause_is_not_causal_link(self):
        result = causal_common_cause_test(n=30000, seed=4)
        shared = result['shared_cause']
        direct = result['directed_A_to_B']
        self.assertAlmostEqual(shared['observed_pearson_r'], .64, delta=.02)
        self.assertEqual(shared['interventional_effect_do_A1_minus_do_A0'], 0)
        self.assertEqual(shared['paired_intervention_difference_count'], 0)
        self.assertAlmostEqual(direct['interventional_effect_do_A1_minus_do_A0'], .8, delta=.02)

    def test_fixed_seed_is_reproducible(self):
        self.assertEqual(simulate_condition(250, .1, .2, 16), simulate_condition(250, .1, .2, 16))

    def test_parameter_validation(self):
        for n, q, p in ((0, .1, .1), (100, -.01, .1), (100, .51, .1), (100, .1, 1.01)):
            with self.assertRaises(ValueError):
                simulate_condition(n, q, p, 3)


if __name__ == '__main__':
    unittest.main()