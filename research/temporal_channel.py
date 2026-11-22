#!/usr/bin/env python3
"""Part XI: discrete-time service replay plus strictly bounded sender energy.

Measured trace: Chorus airport cellular *bandwidth*, not recorded packet loss.
Loss state, observations, return-channel feedback and policies are simulated.
No future-state oracle, queues shared within a policy, or consciousness claims.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

TICK_MS = 200
PACKET_BYTES = 60000
DATA_COST = 1.0
NACK_COST = 0.15
FEEDBACK_DELAY_TICKS = 3
LOSS_GOOD = 0.04
LOSS_BAD = 0.72
GOOD_TO_BAD = 0.08
BAD_TO_GOOD = 0.25
DETECTION = 0.90
FALSE_ALARM = 0.08
RETURN_LOSS = 0.10
POLICIES = ('one_shot','blind_twice','selective_feedback','deadline_adaptive')
TRACE = Path(__file__).parent/'traces'/'chorus_cellular_airport_excerpt.csv'


def read_trace(path: Path) -> tuple[float, ...]:
    values=[]
    with Path(path).open(newline='',encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            try:
                t=float(row['Timestamp (s)'])
                bw=float(row['Bandwidth (Mbps)'])
            except (KeyError,TypeError,ValueError) as exc:
                raise ValueError('CSV requires numeric Timestamp (s),Bandwidth (Mbps)') from exc
            if not math.isfinite(t) or not math.isfinite(bw) or bw<0 or (values and t<=values[-1][0]):
                raise ValueError('Trace must have increasing finite timestamps and nonnegative rates')
            values.append((t,bw))
    if len(values)<2:
        raise ValueError('Trace requires multiple samples')
    if any(abs(values[i][0]-values[i-1][0]-TICK_MS/1000)>1e-6 for i in range(1,len(values))):
        raise ValueError('Samples must be evenly spaced at 200 milliseconds')
    return tuple(bw for _,bw in values)


def slots_for_bandwidth(bandwidth_mbps:float) -> int:
    """Integer 60-kB payload opportunities in one 200-ms slot, no carryover."""
    if not math.isfinite(bandwidth_mbps) or bandwidth_mbps<0:
        raise ValueError('Invalid bandwidth')
    return math.floor(bandwidth_mbps*1_000_000*(TICK_MS/1000)/(8*PACKET_BYTES)+1e-10)


def states(rng:random.Random, ticks:int, regime:str) -> list[bool]:
    """True = bad link state. Bursty uses Markov transitions, iid same marginal."""
    if regime not in ('iid','markov'):
        raise ValueError('Unknown state regime')
    bad_fraction=GOOD_TO_BAD/(GOOD_TO_BAD+BAD_TO_GOOD)
    bad=rng.random()<bad_fraction
    out=[]
    for _ in range(ticks):
        if regime=='iid':
            bad=rng.random()<bad_fraction
        else:
            if bad:
                bad=not (rng.random()<BAD_TO_GOOD)
            else:
                bad=rng.random()<GOOD_TO_BAD
        out.append(bad)
    return out


@dataclass(frozen=True)
class Episode:
    correct:bool
    all_delivered:bool
    energy:float
    packets:int
    nacks:int
    completion_ms:int
    budget_exhausted:bool


def run_policy(policy:str, cap:float, horizon:int, capacities:tuple[int,...],
               losses:list[list[bool]], sensed:tuple[int,int], truth:tuple[int,int],
               guess:tuple[int,int], detection_draw:list[tuple[float,float]],
               feedback_draw:list[float]) -> Episode:
    if policy not in POLICIES: raise ValueError('Unknown policy')
    if not math.isfinite(cap) or cap<0: raise ValueError('Energy budget must be finite and >=0')
    if horizon<1 or len(capacities)<horizon or len(losses)<horizon:
        raise ValueError('Insufficient schedule for requested deadline')
    if any(c<0 for c in capacities): raise ValueError('Negative capacity')
    use_blind=(policy=='blind_twice' or (policy=='deadline_adaptive' and horizon<=FEEDBACK_DELAY_TICKS+2))
    use_feedback=(policy=='selective_feedback' or (policy=='deadline_adaptive' and not use_blind))
    queue=[0,1]+([0,1] if use_blind else [])
    pending=[] # (feedback arrival slot, feature)
    seen=[False,False]
    first_received=[None,None]
    attempts=[0,0]
    energy=0.0; nacks=0; packets=0; rejected=False
    for tick in range(horizon):
        due=[feature for when,feature in pending if when==tick]
        if due:
            queue.extend(due)
        allowed=capacities[tick]
        for slot in range(allowed):
            if not queue: break
            feature=queue.pop(0)
            if energy+DATA_COST>cap+1e-9:
                rejected=True
                continue
            energy+=DATA_COST
            packets+=1
            attempts[feature]+=1
            loss=losses[tick][slot] if slot<len(losses[tick]) else True
            if not loss:
                seen[feature]=True
                if first_received[feature] is None: first_received[feature]=tick
            # Reverse-channel feedback occurs after a first attempt. It is charged
            # independently of the data channel, and arrives with a fixed delay.
            if use_feedback and attempts[feature]==1:
                detect_u,alarm_u=detection_draw[feature]
                request=(detect_u<DETECTION if loss else alarm_u<FALSE_ALARM)
                if request and energy+NACK_COST<=cap+1e-9:
                    energy+=NACK_COST
                    nacks+=1
                    if feedback_draw[feature]>=RETURN_LOSS:
                        pending.append((tick+FEEDBACK_DELAY_TICKS,feature))
        if not queue and not any(when>tick for when,_ in pending):
            break
    received_values=tuple(sensed[i] if seen[i] else guess[i] for i in range(2))
    complete=max(x for x in first_received if x is not None)+1 if any(x is not None for x in first_received) else horizon
    if not all(seen): complete=horizon
    return Episode(received_values==truth,all(seen),round(energy,6),packets,nacks,complete*TICK_MS,rejected)


def simulate(trials:int, seed:int, horizon:int, cap:float, regime:str,
             capacity_source:str, trace:tuple[float,...]) -> dict:
    if trials<1: raise ValueError('trials must be positive')
    if horizon<1 or horizon>len(trace): raise ValueError('invalid horizon')
    if capacity_source not in ('measured','flat'): raise ValueError('invalid source')
    if regime not in ('iid','markov'): raise ValueError('invalid regime')
    rng=random.Random(seed)
    sums={p:{'correct':0,'all_delivered':0,'energy':0.,'packets':0,'nacks':0,'completion_ms':0.,'budget_exhausted':0} for p in POLICIES}
    pairs=0
    pair_sq=0
    for _ in range(trials):
        start=rng.randrange(len(trace)-horizon+1)
        bws=trace[start:start+horizon] if capacity_source=='measured' else (4.50,)*horizon
        capacities=tuple(slots_for_bandwidth(x) for x in bws)
        truth=tuple(rng.randrange(2) for i in range(2))
        sensed=tuple(truth[i]^int(rng.random()<0.1) for i in range(2))
        guess=tuple(rng.randrange(2) for i in range(2))
        path=states(rng,horizon,regime)
        noise_draws=[[rng.random()< (LOSS_BAD if path[t] else LOSS_GOOD) for slot in range(capacities[t])] for t in range(horizon)]
        detection_draw=[(rng.random(),rng.random()) for i in range(2)]
        feedback_draw=[rng.random() for i in range(2)]
        outcomes={}
        for p in POLICIES:
            outcomes[p]=run_policy(p,cap,horizon,capacities,noise_draws,sensed,truth,guess,detection_draw,feedback_draw)
            o=outcomes[p]
            acc=sums[p]
            for field in acc:
                acc[field]+=getattr(o,field)
            if o.energy>cap+1e-8: raise AssertionError('Hard energy budget exceeded')
        delta=int(outcomes['deadline_adaptive'].correct)-int(outcomes['selective_feedback'].correct)
        pairs+=delta
        pair_sq+=delta**2
    results={}
    for p in POLICIES:
        v=sums[p]
        accuracy=v['correct']/trials
        results[p]={
            'accuracy':round(accuracy,6),'accuracy_se':round(math.sqrt(accuracy*(1-accuracy)/trials),6),
            'fully_delivered':round(v['all_delivered']/trials,6),
            'mean_energy':round(v['energy']/trials,6),'mean_packets':round(v['packets']/trials,6),
            'mean_nacks':round(v['nacks']/trials,6),'mean_completion_ms':round(v['completion_ms']/trials,3),
            'budget_exhaustion_rate':round(v['budget_exhausted']/trials,6)}
    return {'capacity_source':capacity_source,'loss_regime':regime,'deadline_ms':horizon*TICK_MS,
      'energy_cap':cap,'trials_per_policy':trials,'policies':results,
      'paired_adaptive_minus_feedback':round(pairs/trials,6),
      'paired_difference_se':round(math.sqrt(max(0,pair_sq/trials-(pairs/trials)**2)/trials),6)}


def experiment(trace_path:Path=TRACE,trials:int=5000,seed:int=369) -> dict:
    trace=read_trace(trace_path)
    conditions=[]
    for source in ('measured','flat'):
      for regime in ('iid','markov'):
       for horizon in (5,9,12):
        for cap in (2.0,3.25,4.5):
            conditions.append(simulate(trials,seed,horizon,cap,regime,source,trace))
    return {'version':'part-xi-v1','method':'Discrete-time replay, separate synthetic Markov erasure, hard per-episode sender+NACK energy cap',
      'trace':{'source':'Chorus MobiCom 2024 (Lv et al.)','url':'https://github.com/GreenLv/Chorus/blob/main/bw_traces/downlink-cellular_airport.csv','license':'CC BY 4.0',
       'kind':'measured bandwidth only (packet loss is simulated)','samples':len(trace),'bandwidth_mbps':list(trace),'window_seconds':[0,(len(trace)-1)*TICK_MS/1000]},
      'constants':{'tick_ms':TICK_MS,'packet_bytes':PACKET_BYTES,'feedback_delay_ticks':FEEDBACK_DELAY_TICKS,
       'data_energy':DATA_COST,'nack_energy':NACK_COST,'packet_loss_good':LOSS_GOOD,'packet_loss_bad':LOSS_BAD,
       'good_to_bad':GOOD_TO_BAD,'bad_to_good':BAD_TO_GOOD,'detection':DETECTION,'false_alarm':FALSE_ALARM,'return_channel_loss':RETURN_LOSS},
      'conditions':conditions,'protocol_evaluations':len(conditions)*len(POLICIES)*trials,'seed':seed}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--trace',type=Path,default=TRACE)
    parser.add_argument('--trials',type=int,default=5000)
    parser.add_argument('--seed',type=int,default=369)
    parser.add_argument('--output',type=Path,default=Path('part11.json'))
    args=parser.parse_args()
    result=experiment(args.trace,args.trials,args.seed)
    args.output.parent.mkdir(exist_ok=True,parents=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    csv_path=args.output.with_suffix('.csv')
    with csv_path.open('w',newline='',encoding='utf-8') as f:
        names=['capacity_source','loss_regime','deadline_ms','energy_cap','protocol','accuracy','accuracy_se','fully_delivered','mean_energy','mean_packets','mean_nacks','mean_completion_ms','budget_exhaustion_rate']
        writer=csv.DictWriter(f,fieldnames=names);writer.writeheader()
        for condition in result['conditions']:
            for policy,metrics in condition['policies'].items():
                writer.writerow({**{name:condition[name] for name in names[:4]},'protocol':policy,**metrics})
    print(f"Part XI: {len(result['conditions'])} conditions / {result['protocol_evaluations']:,} evaluations → {args.output}")

if __name__=='__main__': main()
