import React, { useEffect, useMemo, useState } from 'react';
import './partix.css';

const COLORS = {
  one_shot: '#7188a7',
  random_repeat_matched: '#8badeb',
  feedback_unreliable: '#74dec7',
  always_two: '#e4b869',
  always_three: '#bca4ef'
};
const LABELS = {
  one_shot: 'One-shot baseline',
  random_repeat_matched: 'Blind repeat · cost-matched',
  feedback_unreliable: 'Feedback · unreliable NACK',
  always_two: 'Always send two copies',
  always_three: 'Always send three copies'
};
const ORDER = ['one_shot','random_repeat_matched','feedback_unreliable','always_two','always_three'];
const pct = x => `${(x*100).toFixed(2)}%`;
const fixed = (x, n=2) => Number(x).toFixed(n);

function Trend({points}) {
  const w=550,h=230,pad={left:57,right:30,top:30,bottom:47};
  const min=-.075, max=.095;
  const xp=i => pad.left + i * (w-pad.left-pad.right)/(points.length-1 || 1);
  const yp=y => pad.top+(max-y)/(max-min)*(h-pad.top-pad.bottom);
  return <div className="p9-trend">
    <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Observed feedback advantage in binding accuracy versus return-channel loss">
      {[-.05,0,.05].map(x=><g key={x}><line x1={pad.left} y1={yp(x)} x2={w-pad.right} y2={yp(x)} stroke={x===0?'#e7b879':'#31445a'} strokeDasharray={x===0?'6 5':'2 5'} strokeWidth={x===0?1.7:1}/><text x={pad.left-12} y={yp(x)+4} fill="#8faabe" fontSize="13" textAnchor="end">{x>0?'+':''}{Math.round(x*100)}pp</text></g>)}
      <path fill="none" stroke="#7ee0cf" strokeWidth="3" strokeLinejoin="round" d={points.map((p,i)=>`${i?'L':'M'}${xp(i)},${yp(p.paired_feedback_minus_matched.observed_accuracy_difference)}`).join(' ')}/>
      {points.map((p,i)=><g key={p.feedback_loss}><circle cx={xp(i)} cy={yp(p.paired_feedback_minus_matched.observed_accuracy_difference)} r="6" fill="#79e6cf" stroke="#0d1b2a" strokeWidth="2"/><text x={xp(i)} y={h-17} textAnchor="middle" fontSize="13" fill="#a9c4d4">{Math.round(p.feedback_loss*100)}% NACK loss</text></g>)}
    </svg>
  </div>;
}

export default function PartIX() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [q, setQ] = useState(.1);
  const [e, setE] = useState(.35);
  const [f, setF] = useState(.2);
  useEffect(() => {
    const controller = new AbortController();
    fetch(import.meta.env.BASE_URL + 'data/part9.json', {signal: controller.signal})
      .then(res => { if(!res.ok) throw new Error('Part IX dataset unavailable'); return res.json();})
      .then(setData)
      .catch(err => {if (err.name !== 'AbortError') setError(String(err.message || err));});
    return () => controller.abort();
  },[]);
  const conditions = data?.conditions || [];
  const selected = useMemo(() => conditions.find(c => c.sensory_noise===q && c.data_loss===e && c.feedback_loss===f), [conditions,q,e,f]);
  const trends = useMemo(() => conditions.filter(c=>c.sensory_noise===q && c.data_loss===e).sort((a,b)=>a.feedback_loss-b.feedback_loss), [conditions,q,e]);
  const diff=selected?.paired_feedback_minus_matched;
  const intervention=data?.intervention;
  return <section className="p9-root" aria-label="Part IX research lab">
    <div className="section-heading"><span className="eyebrow">EXPERIMENT 03 / PART IX</span><h2>Does feedback still help<br/>when feedback can fail?</h2><p>Matched expected communication cost. Unreliable return channel. Paired Monte Carlo trials with analytical predictions and causal intervention.</p></div>
    <div className="p9-intro">
      <div><strong>27</strong><span>conditions</span></div>
      <div><strong>2.7M</strong><span>protocol-evaluations</span></div>
      <div><strong>5</strong><span>communication strategies</span></div>
      <div><strong>17</strong><span>automated tests across Parts VII–IX</span></div>
    </div>
    {error && <p role="alert" className="p9-error">{error}</p>}
    {!data && !error && <p className="loading">Loading verified Part IX observations…</p>}
    {selected && <>
      <div className="card p9-controls">
        <label>Sensor noise<select value={q} onChange={ev=>setQ(+ev.target.value)}>{[0,.1,.25].map(n=><option key={n} value={n}>{pct(n)}</option>)}</select></label>
        <label>Data packet loss<select value={e} onChange={ev=>setE(+ev.target.value)}>{[0,.15,.35].map(n=><option key={n} value={n}>{pct(n)}</option>)}</select></label>
        <label>Feedback (NACK) loss<select value={f} onChange={ev=>setF(+ev.target.value)}>{[0,.2,.6].map(n=><option key={n} value={n}>{pct(n)}</option>)}</select></label>
        <p>Recorded results, not an in-browser simulation. Each protocol uses the same underlying noisy inputs within an episode.</p>
      </div>
      <div className="p9-metrics">
        <div><span>Feedback accuracy</span><strong>{pct(selected.protocols.feedback_unreliable.both_features_accuracy)}</strong><small>Both features correct</small></div>
        <div><span>Blind repeat · same mean cost</span><strong>{pct(selected.protocols.random_repeat_matched.both_features_accuracy)}</strong><small>Same expected messages</small></div>
        <div><span>Paired accuracy difference</span><strong className={diff.observed_accuracy_difference>=0?'p9-positive':'p9-negative'}>{diff.observed_accuracy_difference>=0?'+':''}{fixed(diff.observed_accuracy_difference*100)} pp</strong><small>95% CI: {fixed(diff.ci95_low*100)} to {fixed(diff.ci95_high*100)} pp</small></div>
      </div>
      <div className="card p9-card">
        <div className="p9-head"><div><h3>Full-binding accuracy</h3><p>Correctly identify both independently sensed feature bits after packet loss.</p></div><span className="tag">{selected.trials_per_protocol.toLocaleString()} episodes per strategy</span></div>
        <div className="p9-bars">{ORDER.map(key=>{let r=selected.protocols[key];return <div className="p9-bar" key={key}><label>{LABELS[key]}</label><div className="p9-rail"><div style={{width:`${100*r.both_features_accuracy}%`,background:COLORS[key]}}/></div><strong>{pct(r.both_features_accuracy)}</strong></div>})}</div>
        <p className="p9-foot">Comparison is valid for this binary synthetic task only. Error bars and paired uncertainty are provided in the dataset. Performance does not measure subjective consciousness.</p>
      </div>
      <div className="p9-duo">
        <div className="card p9-card"><h3>Communication cost</h3><p>Average total data + control transmissions for both features.</p><div className="p9-message-rows">{ORDER.map(key=><div key={key}><span style={{color:COLORS[key]}}>{LABELS[key]}</span><b>{fixed(selected.protocols[key].mean_total_messages)}</b></div>)}</div><p className="p9-foot">Feedback uses up to six transmissions in an episode. The cost-matched blind repeat uses at most four. Only mean total messages are matched, not latency or worst-case budget.</p></div>
        <div className="card p9-card"><h3>When does feedback stop winning?</h3><p>Observed feedback minus cost-matched repetition, holding sensor and data loss fixed.</p><Trend points={trends}/><p className="p9-foot">The dashed horizontal line represents zero advantage. Above it, feedback wins; below it, blind repetition wins.</p></div>
      </div>
      <div className="card p9-card p9-intervention"><span className="eyebrow">PAIRED CAUSAL INTERVENTION</span><h3>We change the return channel, not the incoming data.</h3><p>Two counterfactual feedback runs share the same random sensory inputs, data losses, and random draws. Only the rule for NACK loss changes.</p>
        <div className="p9-metrics intervention-metrics"><div><span>do(NACK loss = 0%)</span><strong>{pct(intervention.no_loss_accuracy)}</strong><small>{fixed(intervention.no_loss_messages)} total messages</small></div><div><span>do(NACK loss = 60%)</span><strong>{pct(intervention.loss_accuracy)}</strong><small>{fixed(intervention.loss_messages)} total messages</small></div><div><span>Measured causal effect</span><strong className="p9-positive">+{fixed(intervention.observed_causal_accuracy_effect*100)} pp</strong><small>Predicted: +{fixed(intervention.predicted_causal_accuracy_effect*100)} pp</small></div></div>
        <p className="p9-foot">The intervention shows the modeled effect of return-channel reliability. This is a toy structural model, not an experimental intervention on a person or brain.</p>
      </div>
      <div className="p9-caveat"><strong>What we've actually learned</strong><p>Feedback selectively retransmits failures, which can beat blind repetition at equal <em>expected</em> transmission count when the control channel works. But lost feedback wastes control packets and prevents retries. The five strategies have different worst-case costs and assumptions; architecture alone is not isolated.</p></div>
      <div className="p9-downloads"><a href={import.meta.env.BASE_URL+'data/part9.json'} download>Download Part IX JSON</a><a href={import.meta.env.BASE_URL+'data/part9.csv'} download>Download Part IX CSV</a><a href="https://github.com/MichaelWave369/OneAndManyLab/blob/main/research/PART_IX_REPORT.md" target="_blank" rel="noreferrer">Full methods and limitations ↗</a></div>
    </>}
  </section>;
}