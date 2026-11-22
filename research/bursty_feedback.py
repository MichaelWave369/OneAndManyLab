#!/usr/bin/env python3
"""Part X: correlated erasure pairs, imperfect loss detection, latency and energy.

A binary color/shape feature is sensed with flip probability q. Two attempts to
transport that same observation suffer marginal packet erasure e with a simple
sticky-pair model: first erasure L1~Bernoulli(e), and second L2=L1 with probability
rho, otherwise L2~Bernoulli(e). Therefore Corr(L1,L2)=rho for 0<e<1.

When the first packet is lost, receiver detects loss with sensitivity d; when it
arrives, receiver may falsely raise a NACK with probability a. NACK messages are
lost with probability f. A delivered NACK triggers one retry. NACKs consume
0.2 units energy, and require 1.4 time units of round-trip control overhead;
data uses 1 unit energy and one time unit per send. Retry delivery is at t=3.4,
blind repeat at t=2.0. All transmissions occur even after a chosen deadline;
deadline accuracy only evaluates which deliveries have arrived on time.

Random, nonresponsive repetition is matched to feedback either in *expected*
message count or *expected* energy (not both). The protocols do not share the
same worst-case budget, tail latency, or physical semantics. Every protocol
receives paired underlying noisy observations and packet-loss draws.

This is a small stochastic communication toy, not neural recurrence, network
hardware validation, IIT Phi, or a detector of subjective consciousness.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import random
from pathlib import Path

PROTOCOLS = ('one_shot', 'blind_message_matched', 'blind_energy_matched',
             'selective_feedback', 'always_two')
DATA_ENERGY = 1.0
CONTROL_ENERGY = 0.2
DATA_TIME = 1.0
CONTROL_DELAY = 1.4
RETRY_ARRIVAL = DATA_TIME + CONTROL_DELAY + DATA_TIME
BLIND_ARRIVAL = 2 * DATA_TIME


def validate(q: float, e: float, rho: float, detection: float, alarm: float,
             feedback_loss: float, deadline: float) -> None:
    if not 0 <= q <= 0.5:
        raise ValueError('sensory noise must be in [0, 0.5]')
    if not all(0 <= x <= 1 for x in (e, rho, detection, alarm, feedback_loss)):
        raise ValueError('probabilities must be in [0,1]')
    if deadline < DATA_TIME:
        raise ValueError('deadline must accommodate the initial data packet')
    if message_repeat_rate(e, detection, alarm, feedback_loss) > 1:
        raise ValueError('message matching exceeds one optional repetition')


def nack_rate(e: float, detection: float, alarm: float) -> float:
    return e * detection + (1 - e) * alarm


def message_repeat_rate(e: float, detection: float, alarm: float, feedback_loss: float) -> float:
    return nack_rate(e, detection, alarm) * (2 - feedback_loss)


def energy_repeat_rate(e: float, detection: float, alarm: float, feedback_loss: float) -> float:
    return nack_rate(e, detection, alarm) * (CONTROL_ENERGY + 1 - feedback_loss)


def expected(q: float, e: float, rho: float, detection: float, alarm: float,
             feedback_loss: float, deadline: float, protocol: str) -> dict:
    validate(q, e, rho, detection, alarm, feedback_loss, deadline)
    if protocol not in PROTOCOLS:
        raise ValueError('Unknown protocol')
    s = nack_rate(e, detection, alarm)
    pm = message_repeat_rate(e, detection, alarm, feedback_loss)
    pe = energy_repeat_rate(e, detection, alarm, feedback_loss)
    rescue = e * (1 - rho) * (1 - e)
    if protocol == 'one_shot':
        t, messages, energy, latency = 1-e, 1, 1., 1.
    elif protocol == 'blind_message_matched':
        t = 1-e + (pm * rescue if deadline >= BLIND_ARRIVAL else 0)
        messages, energy, latency = 1+pm, 1+pm, 1+pm
    elif protocol == 'blind_energy_matched':
        t = 1-e + (pe * rescue if deadline >= BLIND_ARRIVAL else 0)
        messages, energy, latency = 1+pe, 1+pe, 1+pe
    elif protocol == 'selective_feedback':
        t = 1-e + (e * detection * (1-feedback_loss) * (1-rho) * (1-e)
                   if deadline >= RETRY_ARRIVAL else 0)
        messages = 1+s*(2-feedback_loss)
        energy = 1+s*(CONTROL_ENERGY+1-feedback_loss)
        latency = 1+s*CONTROL_DELAY+s*(1-feedback_loss)*DATA_TIME
    else:
        t = 1-e+(rescue if deadline >= BLIND_ARRIVAL else 0)
        messages, energy, latency = 2., 2., 2.
    single = .5+(.5-q)*t
    return {
        'delivery_by_deadline': round(t, 8),
        'single_feature_accuracy': round(single, 8),
        'both_features_accuracy': round(single**2, 8),
        'mean_total_messages': round(2*messages, 8),
        'mean_total_energy': round(2*energy, 8),
        'mean_per_feature_channel_time': round(latency, 8),
    }


def _trial(q: float, e: float, rho: float, detection: float, alarm: float,
           feedback_loss: float, deadline: float, rng: random.Random) -> tuple[dict,dict,dict,dict]:
    accuracy = {k: True for k in PROTOCOLS}
    msg = dict.fromkeys(PROTOCOLS, 0.)
    power = dict.fromkeys(PROTOCOLS, 0.)
    delay = dict.fromkeys(PROTOCOLS, 0.)
    pm = message_repeat_rate(e, detection, alarm, feedback_loss)
    pe = energy_repeat_rate(e, detection, alarm, feedback_loss)
    for _feature in range(2):
        truth = rng.randrange(2)
        sensed = truth ^ int(rng.random()<q)
        guess = rng.randrange(2)
        lost1 = rng.random()<e
        lost2 = lost1 if rng.random()<rho else rng.random()<e
        nack = rng.random() < (detection if lost1 else alarm)
        nack_survives = rng.random() >= feedback_loss
        blind_msg = rng.random() < pm
        blind_energy = rng.random() < pe
        resend = nack and nack_survives
        can_blind = deadline >= BLIND_ARRIVAL
        can_retry = deadline >= RETRY_ARRIVAL
        delivered = {
            'one_shot': not lost1,
            'blind_message_matched': not lost1 or (blind_msg and not lost2 and can_blind),
            'blind_energy_matched': not lost1 or (blind_energy and not lost2 and can_blind),
            'selective_feedback': not lost1 or (resend and not lost2 and can_retry),
            'always_two': not lost1 or (not lost2 and can_blind),
        }
        feature_cost = {
            'one_shot': (1., 1., 1.),
            'blind_message_matched': (1.+blind_msg, 1.+blind_msg, 1.+blind_msg),
            'blind_energy_matched': (1.+blind_energy, 1.+blind_energy, 1.+blind_energy),
            'selective_feedback': (1.+nack+resend, 1.+CONTROL_ENERGY*nack+resend,
                                   1.+CONTROL_DELAY*nack+DATA_TIME*resend),
            'always_two': (2., 2., 2.),
        }
        for k in PROTOCOLS:
            accuracy[k] &= (sensed if delivered[k] else guess)==truth
            m,p,l = feature_cost[k]
            msg[k] += m
            power[k] += p
            delay[k] += l/2
    return accuracy,msg,power,delay


def simulate(n: int, q: float, e: float, rho: float, detection: float,
             alarm: float, feedback_loss: float, deadline: float, seed: int) -> dict:
    validate(q,e,rho,detection,alarm,feedback_loss,deadline)
    if n < 1:
        raise ValueError('n must be positive')
    rng=random.Random(seed)
    totals={k:0 for k in PROTOCOLS}
    msg={k:0. for k in PROTOCOLS}
    energy={k:0. for k in PROTOCOLS}
    times={k:0. for k in PROTOCOLS}
    paired=paired_sq=0
    for _ in range(n):
        correct,m,p,l=_trial(q,e,rho,detection,alarm,feedback_loss,deadline,rng)
        for k in PROTOCOLS:
            totals[k]+=int(correct[k]);msg[k]+=m[k];energy[k]+=p[k];times[k]+=l[k]
        d=int(correct['selective_feedback'])-int(correct['blind_message_matched'])
        paired+=d; paired_sq+=d*d
    output={}
    for k in PROTOCOLS:
        a=totals[k]/n
        output[k]={
            'accuracy':round(a,7),
            'accuracy_standard_error':round(math.sqrt(a*(1-a)/n),7),
            'messages':round(msg[k]/n,7),
            'energy':round(energy[k]/n,7),
            'mean_channel_time':round(times[k]/n,7),
            'predicted':expected(q,e,rho,detection,alarm,feedback_loss,deadline,k),
        }
    delta=paired/n
    se=math.sqrt(max(0,paired_sq/n-delta*delta)/n)
    return {
        'noise':q,'erasure':e,'burst_correlation':rho,'detection_sensitivity':detection,
        'false_alarm':alarm,'feedback_erasure':feedback_loss,'deadline':deadline,
        'seed':seed,'trials_per_strategy':n,'strategies':output,
        'paired_difference':{'feedback_minus_message_matched':round(delta,7),
          'se':round(se,7),'ci95':[round(delta-1.96*se,7),round(delta+1.96*se,7)],
          'predicted_difference':round(output['selective_feedback']['predicted']['both_features_accuracy']-output['blind_message_matched']['predicted']['both_features_accuracy'],7)},
    }


def matrix(n:int=12_000,seed:int=369)->dict:
    conditions=[]
    for e in (.15,.35):
        for rho in (0.,.45,.85):
            for sensitivity in (.55,.95):
                for f in (.05,.4):
                    for deadline in (2.5,4.):
                        idx=len(conditions)
                        conditions.append(simulate(n,.1,e,rho,sensitivity,.08,f,deadline,seed+idx*173))
    return {'experiment':'Part X: correlated failures, imperfect detection and deadline budgets',
      'seed':seed,'model_version':'1.0','trials_per_strategy_per_condition':n,
      'protocol_evaluations':n*len(conditions)*len(PROTOCOLS),
      'conditions':conditions,
      'cost_model':{'data_energy':DATA_ENERGY,'nack_energy':CONTROL_ENERGY,
                    'data_time':DATA_TIME,'nack_roundtrip':CONTROL_DELAY,
                    'retry_delivery_time':RETRY_ARRIVAL,
                    'blind_repeat_delivery_time':BLIND_ARRIVAL},
      'limitations':[
       'The erasure process is a stylized sticky two-packet model, not a fitted network trace or full Gilbert-Elliott process.',
       'Failures are correlated within each feature only, not across both features.',
       'Message matching and energy matching are expectation-based; pathwise and worst-case costs are unequal.',
       'All retransmissions are attempted even if they will miss a deadline; results are evaluated at the deadline.',
       'A NACK is receiver-initiated using a stipulated detection sensitivity and false-alarm probability.',
       'Feedback control loss is independent of data-channel losses.',
       'Sensors, data timing, and synthetic guesses are deliberately simplified.',
       'This is not a real-network or neuroscience validation and does not measure consciousness.'
      ]}


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--trials',type=int,default=12000)
    a.add_argument('--seed',type=int,default=369)
    a.add_argument('--output',default='part10.json')
    args=a.parse_args()
    result=matrix(args.trials,args.seed)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    csvpath=path.with_suffix('.csv')
    fields=['noise','erasure','burst_correlation','detection_sensitivity','false_alarm','feedback_erasure','deadline','strategy','accuracy','accuracy_standard_error','messages','energy','mean_channel_time','expected_accuracy']
    with csvpath.open('w',encoding='utf-8',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader()
        for c in result['conditions']:
            for key,metrics in c['strategies'].items():
                writer.writerow({**{f:c[f] for f in fields[:7]},'strategy':key,
                  'accuracy':metrics['accuracy'],'accuracy_standard_error':metrics['accuracy_standard_error'],
                  'messages':metrics['messages'],'energy':metrics['energy'],
                  'mean_channel_time':metrics['mean_channel_time'],
                  'expected_accuracy':metrics['predicted']['both_features_accuracy']})
    print(f"{len(result['conditions'])} conditions; {result['protocol_evaluations']:,} evaluations; {path} and {csvpath}")


if __name__=='__main__':
    main()
