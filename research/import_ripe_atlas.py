#!/usr/bin/env python3
"""Fetch public RIPE Atlas ping results and preserve RTT/timeout triplets only."""
import argparse,json,urllib.parse,urllib.request
from pathlib import Path

def fetch(msm,probe,start,stop):
    base='https://atlas.ripe.net/api/v2/measurements/'+str(msm)+'/results/'
    url=base+'?'+urllib.parse.urlencode({'start':start,'stop':stop,'probe_ids':probe})
    with urllib.request.urlopen(url,timeout=60) as r: raw=json.load(r)
    samples=[];skipped=0
    for row in sorted(raw,key=lambda x:x['timestamp']):
        p=row.get('result',[])
        if len(p)!=3 or row.get('sent')!=3 or row.get('prb_id')!=probe:skipped+=1;continue
        vals=[round(x['rtt'],3) if 'rtt' in x else None if x.get('x')=='*' else 'ERROR' for x in p]
        if 'ERROR' in vals:skipped+=1;continue
        samples.append([int(row['timestamp']),*vals])
    return {'measurement_id':msm,'probe_id':probe,'excluded_incomplete':skipped,'api_url':url,'samples':samples}

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--start',type=int,required=True);a.add_argument('--stop',type=int,required=True)
    a.add_argument('--pairs',default='1001:10006,1010:10006,1001:10070')
    a.add_argument('--output',type=Path,required=True)
    args=a.parse_args()
    traces=[fetch(*[int(x) for x in spec.split(':')],args.start,args.stop) for spec in args.pairs.split(',')]
    doc={'version':'part-xii-v1','source':'RIPE Atlas public built-in ping results','observed_start_unix':args.start,'observed_stop_unix':args.stop,'time_span_note':'Measurement groups are ~240 seconds apart','ethics':'IP addresses and location omitted','traces':traces}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    print('Saved',sum(len(t['samples']) for t in traces),'measured groups')
