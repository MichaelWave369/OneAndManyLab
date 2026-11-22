"""Minimal standard-library checks for the demonstrator."""
import unittest
from causal_binding_probe import A, MATCH_PROBABILITY, CHAIN_RELIABILITY, run


class TestCausalBindingProbe(unittest.TestCase):
    def test_analytical_match(self):
        self.assertAlmostEqual(A, 0.155232, places=9)
        self.assertAlmostEqual(MATCH_PROBABILITY, CHAIN_RELIABILITY**2 + (1-CHAIN_RELIABILITY)**2, places=12)

    def test_both_mechanisms_match_externally_not_internally(self):
        result = run(trials_per_state=3000, seed=369)
        observed = result['observed']
        for name in ('recurrent', 'feedforward'):
            self.assertAlmostEqual(observed[name]['io_match_rate'], MATCH_PROBABILITY, delta=0.012)
        # Averaged over all balanced initial states, the recurrent unit-2 probe
        # loses the input bit; the chain's unit-2 probe retains it.
        self.assertAlmostEqual(observed['recurrent']['internal_probe_match_rate'], .5, delta=.012)
        self.assertAlmostEqual(observed['feedforward']['internal_probe_match_rate'], CHAIN_RELIABILITY, delta=.012)
        self.assertGreater(observed['feedforward']['internal_probe_match_rate'] - observed['recurrent']['internal_probe_match_rate'], .17)

if __name__ == '__main__':
    unittest.main()