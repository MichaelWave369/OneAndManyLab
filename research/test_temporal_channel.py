import math
import random
import tempfile
import unittest
from pathlib import Path
from temporal_channel import (TRACE, POLICIES, read_trace, slots_for_bandwidth,
    states, run_policy, simulate, experiment, TICK_MS)

class TemporalChannelTests(unittest.TestCase):
    def setUp(self):
        self.trace=read_trace(TRACE)

    def test_measurement_has_real_sampling(self):
        self.assertEqual(len(self.trace),51)
        self.assertEqual(self.trace[0],0.0)
        self.assertEqual(self.trace[1],6.96)

    def test_capacity_is_integer_and_no_fraudulent_loss_assumption(self):
        self.assertEqual(slots_for_bandwidth(0),0)
        self.assertEqual(slots_for_bandwidth(2.4),1)
        self.assertEqual(slots_for_bandwidth(4.8),2)

    def test_negative_bandwidth_fails(self):
        with self.assertRaises(ValueError): slots_for_bandwidth(-1)

    def test_infinite_bandwidth_fails(self):
        with self.assertRaises(ValueError): slots_for_bandwidth(float('inf'))

    def test_bad_trace_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'x.csv'
            path.write_text('Timestamp (s),Bandwidth (Mbps)\n0,2\n0.1,3\n')
            with self.assertRaises(ValueError): read_trace(path)

    def test_negative_capacity_fails(self):
        with self.assertRaises(ValueError):
            run_policy('one_shot',2,4,(-1,2,2,2),[[False]*2]*4,(0,0),(0,0),(0,0),[(0,0)]*2,[1,1])

    def test_invalid_policy_fails(self):
        with self.assertRaises(ValueError):
            run_policy('unknown',2,4,(2,2,2,2),[[False]*2]*4,(0,0),(0,0),(0,0),[(0,0)]*2,[1,1])

    def test_zero_energy_transmits_nothing(self):
        got=run_policy('blind_twice',0,4,(2,2,2,2),[[False]*2]*4,(0,0),(0,0),(1,1),[(0,0)]*2,[1,1])
        self.assertEqual(got.packets,0)
        self.assertFalse(got.all_delivered)
        self.assertFalse(got.correct)

    def test_no_loss_and_two_slots_are_sufficient(self):
        for policy in POLICIES:
            with self.subTest(policy=policy):
                got=run_policy(policy,4.5,9,(2,)*9,[[False]*2 for _ in range(9)],(0,1),(0,1),(1,0),[(1,1)]*2,[1,1])
                self.assertTrue(got.correct)
                self.assertTrue(got.all_delivered)

    def test_energy_caps_enforced_for_all_protocols(self):
        for cap in (0,1,2,3.25,4.5):
            data=simulate(180,369,12,cap,'markov','measured',self.trace)
            for result in data['policies'].values():
                self.assertLessEqual(result['mean_energy'],cap+1e-6)

    def test_simulation_deterministic(self):
        a=simulate(120,369,9,3.25,'iid','measured',self.trace)
        b=simulate(120,369,9,3.25,'iid','measured',self.trace)
        self.assertEqual(a,b)

    def test_trace_v_flat_distinguished(self):
        a=simulate(250,369,9,4.5,'iid','measured',self.trace)
        b=simulate(250,369,9,4.5,'iid','flat',self.trace)
        self.assertNotEqual(a['policies'],b['policies'])

    def test_markov_state_runs_have_persistence(self):
        st=states(random.Random(369),5000,'markov')
        same=sum(a==b for a,b in zip(st,st[1:]))/4999
        self.assertGreater(same,.65)

    def test_strict_budget_boundary_after_nack(self):
        # All data first packets fail, feedback is generated, but 2.3 energy
        # cannot buy a whole second packet after two initial packets + NACKs.
        got=run_policy('selective_feedback',2.3,8,(2,)*8,[[True]*2]*8,
                       (0,0),(0,0),(1,1),[(0,0)]*2,[1,1])
        self.assertEqual(got.packets,2)
        self.assertLessEqual(got.energy,2.3)

    def test_deadline_aware_switches_to_blind_under_tight_deadline(self):
        cap=(2,)*5
        noise=[[True,True]]+[[False,False] for _ in range(4)]
        args=(4.5,5,cap,noise,(0,0),(0,0),(1,1),[(0,0)]*2,[1,1])
        self.assertEqual(run_policy('deadline_adaptive',*args),run_policy('blind_twice',*args))

    def test_deadline_aware_switches_to_feedback_when_time_allows(self):
        cap=(2,)*9;noise=[[True,True]]+[[False,False] for _ in range(8)]
        args=(4.5,9,cap,noise,(0,0),(0,0),(1,1),[(0,0)]*2,[1,1])
        self.assertEqual(run_policy('deadline_adaptive',*args),run_policy('selective_feedback',*args))

    def test_confidence_difference_is_finite(self):
        d=simulate(200,1,9,4.5,'markov','measured',self.trace)
        self.assertTrue(math.isfinite(d['paired_difference_se']))
        self.assertGreaterEqual(d['paired_difference_se'],0)

    def test_episode_deadline_is_hard(self):
        d=simulate(130,1,5,4.5,'markov','flat',self.trace)
        for p in d['policies'].values(): self.assertLessEqual(p['mean_completion_ms'],5*TICK_MS)

if __name__=='__main__':unittest.main()
