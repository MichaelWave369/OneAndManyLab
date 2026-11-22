import unittest
from measured_ping_replay import replay,summarize,analyze,load_dataset,SOURCE
class PingReplayTests(unittest.TestCase):
    def setUp(self):
        self.rows=[[100,8.0,None,12.0],[340,11.0,9.0,19.0],[580,None,None,40.0],[820,14.0,16.0,18.0]]
    def test_timeout_not_zero(self):self.assertFalse(replay([None,20,30],10)['one'][0])
    def test_success_inclusive(self):self.assertTrue(replay([10,20,30],10)['one'][0])
    def test_strict_cutoff(self):self.assertFalse(replay([10.001,20,30],10)['one'][0])
    def test_no_invalid_length(self):
        with self.assertRaises(ValueError):replay([10,20],10)
    def test_no_nonpositive_cutoff(self):
        with self.assertRaises(ValueError):replay([1,2,3],0)
    def test_two_equals_oracle(self):
        for t in [5,10,20,50]:
            for row in self.rows:
                p=replay(row[1:],t)
                self.assertEqual(p['blind_two'][0],p['oracle_selective'][0])
    def test_third_never_hurts(self):
        for row in self.rows:
            p=replay(row[1:],20)
            self.assertGreaterEqual(int(p['blind_three'][0]),int(p['blind_two'][0]))
    def test_oracle_saves_attempt(self):self.assertEqual(replay([5,8,9],10)['oracle_selective'][1],1)
    def test_oracle_overhead(self):self.assertAlmostEqual(replay([None,5,6],10)['oracle_selective'][2],2.15)
    def test_timeouts_preserved(self):self.assertEqual(summarize(self.rows,10)['recorded_timeouts'],3)
    def test_partition(self):
        d={'traces':[{'measurement_id':1001,'probe_id':10006,'samples':self.rows}]}
        s=analyze(d,[10])
        self.assertEqual(s[0]['cycles']+s[1]['cycles'],s[2]['cycles'])
    def test_committed_data(self):
        data=load_dataset(SOURCE)
        self.assertEqual(len(data['traces']),3)
        self.assertGreaterEqual(sum(len(t['samples']) for t in data['traces']),500)
if __name__=='__main__':unittest.main()
