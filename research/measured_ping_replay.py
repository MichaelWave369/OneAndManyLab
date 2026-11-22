#!/usr/bin/env python3
"""Part XII: observational (not causal) replay of actual RIPE Atlas ping triplets."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path

SOURCE=Path(__file__).parents[1]/'public'/'data'/'part12.json'
POLICIES=('one','blind_two','oracle_selective','blind_three')

def load_dataset(path=SOURCE):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('version')!='part-xii-v1' or not data.get('traces'):
        raise ValueError('Missing or unsupported data')
    for t in data['traces']:
        last=-1
        for stamp,a,b,c in t['samples']:
            if not isinstance(stamp,int) or stamp<=last:
                raise ValueError('Timestamps must increase')
            last=stamp
            for r in (a,b,c):
                if r is not None and (isinstance(r,bool) or not isinstance(r,(int,float)) or not math.isfinite(r) or r<0):
                    raise ValueError('Invalid RTT')
    return data

def replay(pings,threshold):
    if len(pings)!=3 or threshold<=0:raise ValueError('Invalid triplet or cutoff')
    good=[x is not None and x<=threshold for x in pings]
    n=1 if good[0] else 2
    return {'one':(good[0],1,1.),'blind_two':(any(good[:2]),2,2.),
      'oracle_selective':(any(good[:2]),n,float(n)+(0.15 if n==2 else 0)),
      'blind_three':(any(good),3,3.)}

def summarize(samples,threshold):
    if not samples:raise ValueError('Empty trace')
    n=len(samples)
    counts={k:[0,0,0.] for k in POLICIES}
    replies=sorted(x for row in samples for x in row[1:] if x is not None)
    for row in samples:
        for name,(good,tries,cost) in replay(row[1:],threshold).items():
            counts[name][0]+=bool(good);counts[name][1]+=tries;counts[name][2]+=cost
    return {'cycles':n,'recorded_timeouts':3*n-len(replies),
      'reply_median_ms':replies[math.ceil(len(replies)*0.5)-1] if replies else None,
      'reply_p95_ms':replies[math.ceil(len(replies)*0.95)-1] if replies else None,
      'policies':{k:{'successes':v[0],'accuracy':v[0]/n,'mean_attempts':v[1]/n,'mean_cost_proxy':v[2]/n} for k,v in counts.items()}}

def analyze(data,thresholds=(10,20,30,50)):
    out=[]
    for trace in data['traces']:
        rows=trace['samples'];m=len(rows)//2
        for split,portion in [('first_half',rows[:m]),('holdout',rows[m:]),('all',rows)]:
            for t in thresholds:
                out.append({'measurement_id':trace['measurement_id'],'probe_id':trace['probe_id'],'split':split,'threshold_ms':t,**summarize(portion,t)})
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,default=SOURCE)
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    rows=analyze(load_dataset(args.input))
    if args.output:
        args.output.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    print('Part XII:',len(rows),'measured-replay summaries')
