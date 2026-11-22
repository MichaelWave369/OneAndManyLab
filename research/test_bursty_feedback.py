"""Part X analytical and simulation regression tests."""
import unittest
from bursty_feedback import (
    PROTOCOLS, BLIND_ARRIVAL, RETRY_ARRIVAL, expected, simulate, matrix,
    message_repeat_rate, energy_repeat_rate, nack_rate, validate,
)

PARAM = dict(q=.1,e=.35,rho=.45,detection=.95,alarm=.08,feedback_loss=.05,deadline=4.)
class PartXTests(unittest.TestCase):
    def test_invalid_probability(self):
        with self.assertRaises(ValueError): expected(**{**PARAM,'rho':1.1},protocol='one_shot')
        with self.assertRaises(ValueError): expected(**{**PARAM,'deadline':.5},protocol='one_shot')
    def test_invalid_unknown_protocol(self):
        with self.assertRaises(ValueError): expected(**PARAM,protocol='unknown')
    def test_repeat_rate_bounds(self):
        self.assertAlmostEqual(message_repeat_rate(.35,.95,.08,.05),nack_rate(.35,.95,.08)*1.95)
        self.assertLess(energy_repeat_rate(.35,.95,.08,.05),message_repeat_rate(.35,.95,.08,.05))
    def test_matched_messages_analytic(self):
        fb=expected(**PARAM,protocol='selective_feedback')
        blind=expected(**PARAM,protocol='blind_message_matched')
        self.assertAlmostEqual(fb['mean_total_messages'],blind['mean_total_messages'],places=7)
    def test_matched_energy_analytic(self):
        fb=expected(**PARAM,protocol='selective_feedback')
        blind=expected(**PARAM,protocol='blind_energy_matched')
        self.assertAlmostEqual(fb['mean_total_energy'],blind['mean_total_energy'],places=7)
    def test_zero_erasure_all_equal_accuracy(self):
        p={**PARAM,'e':0.}
        for k in PROTOCOLS:
            self.assertAlmostEqual(expected(**p,protocol=k)['both_features_accuracy'],.81,places=6)
    def test_full_correlation_removes_rescue(self):
        p={**PARAM,'rho':1.}
        one=expected(**p,protocol='one_shot')['both_features_accuracy']
        for k in PROTOCOLS:
            self.assertAlmostEqual(expected(**p,protocol=k)['both_features_accuracy'],one)
    def test_short_deadline_feedback_not_delivered(self):
        p={**PARAM,'deadline':2.5}
        self.assertLess(BLIND_ARRIVAL, p['deadline'])
        self.assertGreater(RETRY_ARRIVAL, p['deadline'])
        self.assertEqual(expected(**p,protocol='one_shot')['both_features_accuracy'],
                         expected(**p,protocol='selective_feedback')['both_features_accuracy'])
    def test_perfect_detector_improves_long_deadline(self):
        p={**PARAM,'detection':1.,'alarm':0.,'feedback_loss':0.,'rho':0.}
        self.assertGreater(expected(**p,protocol='selective_feedback')['both_features_accuracy'],
                           expected(**p,protocol='one_shot')['both_features_accuracy'])
    def test_false_alarm_increases_cost_not_success(self):
        low={**PARAM,'alarm':0.}
        high={**PARAM,'alarm':.2}
        self.assertEqual(expected(**low,protocol='selective_feedback')['delivery_by_deadline'],
                         expected(**high,protocol='selective_feedback')['delivery_by_deadline'])
        self.assertGreater(expected(**high,protocol='selective_feedback')['mean_total_messages'],
                           expected(**low,protocol='selective_feedback')['mean_total_messages'])
    def test_burst_reduces_rescue(self):
        low=expected(**{**PARAM,'rho':0.},protocol='selective_feedback')['both_features_accuracy']
        high=expected(**{**PARAM,'rho':.85},protocol='selective_feedback')['both_features_accuracy']
        self.assertGreater(low,high)
    def test_feedback_latency_exceeds_blind(self):
        fb=expected(**PARAM,protocol='selective_feedback')
        blind=expected(**PARAM,protocol='blind_message_matched')
        self.assertGreater(fb['mean_per_feature_channel_time'],blind['mean_per_feature_channel_time'])
    def test_reproducibility(self):
        a=simulate(500,seed=123,**PARAM)
        self.assertEqual(a,simulate(500,seed=123,**PARAM))
        self.assertNotEqual(a,simulate(500,seed=124,**PARAM))
    def test_simulation_matches_predictions(self):
        v=simulate(20000,seed=369,**PARAM)
        for key in PROTOCOLS:
            got=v['strategies'][key]
            self.assertLess(abs(got['accuracy']-got['predicted']['both_features_accuracy']),.018,key)
            self.assertLess(abs(got['messages']-got['predicted']['mean_total_messages']),.04,key)
            self.assertLess(abs(got['energy']-got['predicted']['mean_total_energy']),.04,key)
    def test_matrix_dimensions(self):
        r=matrix(5,seed=369)
        self.assertEqual(len(r['conditions']),48)
        self.assertEqual(r['protocol_evaluations'],48*5*5)
    def test_paired_ci_brackets_prediction_usually(self):
        v=simulate(70000,seed=369,**PARAM)
        ci=v['paired_difference']['ci95']; theory=v['paired_difference']['predicted_difference']
        self.assertLessEqual(ci[0]-.002,theory)
        self.assertGreaterEqual(ci[1]+.002,theory)

if __name__=='__main__':unittest.main()
