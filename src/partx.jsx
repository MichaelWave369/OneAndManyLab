import React, { useEffect, useMemo, useState } from 'react';
import './partx.css';

const STRATEGIES = [
  ['one_shot', 'One-shot', '#88a6c9'],
  ['blind_message_matched', 'Blind · messages matched', '#8db5ff'],
  ['blind_energy_matched', 'Blind · energy matched', '#c7a0f4'],
  ['selective_feedback', 'Selective feedback', '#67ddc8'],
  ['always_two', 'Always send twice', '#e8bd7b']
];
const pct = x => `${(100 * Number(x)).toFixed(2)}%`;
const fixed = (x,n=2) => Number(x).toFixed(n);
const fields = [
  ['erasure', 'Data packet loss', [0.15,0.35]],
  ['burst_correlation', 'Burst correlation', [0,0.45,0.85]],
  ['detection_sensitivity', 'Loss detection sensitivity', [0.55,0.95]],
  ['feedback_erasure', 'Feedback channel loss', [0.05,0.4]],
  ['deadline', 'Result deadline', [2.5,4.0]],
];

function MiniTrend({conditions,selection}) {
  const series = conditions.filter(c=>c.erasure===selection.erasure &&
    c.detection_sensitivity===selection.detection_sensitivity &&
    c.feedback_erasure===selection.feedback_erasure && c.deadline===selection.deadline)
    .sort((a,b)=>a.burst_correlation-b.burst_correlation);
  if (series.length!==3) return null;
  const values = series.map(c=>c.paired_difference.feedback_minus_message_matched*100);
  const extent = Math.max(2,Math.max(...values.map(x=>Math.abs(x)))*1.2);
  const x = i=>45+i*128, y = v=>100-v/extent*60;
  const points=values.map((v,i)=>`${x(i)},${y(v)}`).join(' ');
  return <div className="p10-trend" role="img" aria-label="Difference in percentage-point accuracy between feedback and blind repetition at three burst-correlation levels">
    <svg viewBox="0 0 365 165" preserveAspectRatio="xMidYMid meet">
      <line x1="32" y1="100" x2="329" y2="100" stroke="#a4b5c5" strokeDasharray="4 4" opacity=".7"/>
      <polyline points={points} stroke="#75e0ca" strokeWidth="3" strokeLinejoin="round" fill="none"/>
      {values.map((v,i)=><g key={i}><circle cx={x(i)} cy={y(v)} r="5" fill="#75e0ca"/><text x={x(i)} y={y(v)-13} fontSize="11" fill="#d9fff1" textAnchor="middle">{v>=0?'+':''}{fixed(v,1)}pp</text><text x={x(i)} y="148" fontSize="11" fill="#9db6c9" textAnchor="middle">{pct(series[i].burst_correlation)}</text></g>)}
    </svg>
    <div className="p10-chart-caption">Accuracy advantage against message-matched blind repetition · dashed line = no advantage</div>
  </div>;
}

export default function PartX(){
  const [dataset,setDataset] = useState(null);
  const [error,setError] = useState('');
  const [selection,setSelection]=useState({erasure:.35,burst_correlation:.45,detection_sensitivity:.95,feedback_erasure:.05,deadline:4});
  useEffect(()=>{
    const controller=new AbortController();
    fetch(`${import.meta.env.BASE_URL}data/part10.json`,{signal:controller.signal})
      .then(res=>{if(!res.ok)throw new Error('Part X dataset could not be loaded'); return res.json();})
      .then(setDataset)
      .catch(err=>{if(err.name!=='AbortError')setError(err.message||String(err));});
    return()=>controller.abort();
  },[]);
  const conditions=dataset?.conditions||[];
  const selected=useMemo(()=>conditions.find(c=>fields.every(([k])=>c[k]===selection[k])),[conditions,selection]);
  const choose=(key,value)=>setSelection(previous=>({...previous,[key]:Number(value)}));
  const diff=selected?.paired_difference;
  return <section className="p10-root" aria-label="Part X bursty feedback laboratory">
    <div className="section-heading"><span className="eyebrow">EXPERIMENT 04 / PART X</span><h2>When the channel breaks<br/>in bursts.</h2><p>Realistic complications, controlled one by one: correlated packet erasures, false loss alarms, missed feedback, energy expenditure, and deadlines.</p></div>
    <div className="p10-overview">
      <div><b>{conditions.length||48}</b><span>recorded conditions</span></div>
      <div><b>{dataset?(dataset.protocol_evaluations/1e6).toFixed(2)+'M':'2.88M'}</b><span>protocol evaluations</span></div>
      <div><b>5</b><span>transfer strategies</span></div>
      <div><b>33</b><span>full suite of Python tests</span></div>
    </div>
    {error&&<p className="p10-error" role="alert">{error}</p>}
    {!dataset&&!error&&<p className="loading">Loading Part X recorded results…</p>}
    {selected&&<>
      <div className="card p10-controls"><div className="p10-controls-head"><h3>Choose the experimental conditions</h3><span>Fixed: sensor noise 10% · false alarms 8%</span></div><div className="p10-control-grid">
        {fields.map(([key,label,options])=><label key={key}>{label}<select value={selection[key]} onChange={e=>choose(key,e.target.value)}>{options.map(v=><option key={v} value={v}>{key==='deadline'?`${v.toFixed(1)} time units`:pct(v)}</option>)}</select></label>)}
      </div></div>
      <div className="p10-top-metrics">
        <div><span>Selective feedback accuracy</span><strong>{pct(selected.strategies.selective_feedback.accuracy)}</strong><small>Both features correct by deadline</small></div>
        <div><span>Blind repeat · message matched</span><strong>{pct(selected.strategies.blind_message_matched.accuracy)}</strong><small>Same expected packet count</small></div>
        <div><span>Paired accuracy difference</span><strong className={diff.feedback_minus_message_matched>=0?'p10-up':'p10-down'}>{diff.feedback_minus_message_matched>=0?'+':''}{fixed(diff.feedback_minus_message_matched*100)} pp</strong><small>95% CI: {fixed(diff.ci95[0]*100)} to {fixed(diff.ci95[1]*100)} pp</small></div>
      </div>
      {selection.deadline<dataset.cost_model.retry_delivery_time&&<div className="p10-deadline"><strong>Deadline warning</strong> · A selective feedback retry arrives at t={fixed(dataset.cost_model.retry_delivery_time,1)}, after this deadline. Its retry cannot improve the on-time result, although it still consumes energy.</div>}
      <div className="card p10-card"><div className="p10-card-title"><div><h3>Who identifies both features?</h3><p>Measured accuracy, with a matched expected-cost comparison.</p></div><span className="tag">{selected.trials_per_strategy.toLocaleString()} episodes per strategy</span></div>
        <div className="p10-bars">{STRATEGIES.map(([key,label,color])=>{let s=selected.strategies[key];return <div className="p10-bar" key={key}><span>{label}</span><div className="p10-track"><div style={{width:`${s.accuracy*100}%`,background:color}}/></div><b>{pct(s.accuracy)}</b></div>})}</div>
        <p className="p10-subtext">The dashed scenario is synthetic. It does not recreate real packet traces or neural communication. The predicted probabilities and uncertainty estimates are preserved in the JSON dataset.</p>
      </div>
      <div className="p10-side-by-side">
        <div className="card p10-card"><h3>Count packets and energy separately</h3><p>One data packet costs 1 energy unit. NACK messages cost 0.2, but add a 1.4-unit control delay.</p>
          <div className="p10-table-scroll"><table><thead><tr><th>Strategy</th><th>Packets</th><th>Energy</th><th>Time*</th></tr></thead><tbody>{STRATEGIES.map(([key,label,color])=><tr key={key}><td><span className="p10-dot" style={{background:color}}/>{label}</td><td>{fixed(selected.strategies[key].messages)}</td><td>{fixed(selected.strategies[key].energy)}</td><td>{fixed(selected.strategies[key].mean_channel_time)}</td></tr>)}</tbody></table></div>
          <p className="p10-subtext">*Mean modeled channel time per feature; not measured internet latency. Packet and energy matching use expectations, never equal per-episode caps.</p>
        </div>
        <div className="card p10-card"><h3>Does burstiness erase the advantage?</h3><p>Hold detection, packet loss and deadline fixed while changing correlation between consecutive erasures.</p><MiniTrend conditions={conditions} selection={selection}/><p className="p10-subtext">At 100% sticky correlation, second packets would fail whenever first packets fail; retransmitting cannot rescue them.</p></div>
      </div>
      <div className="p10-reading"><strong>Interpret the result carefully.</strong><p>Reliable loss detection can make selective feedback valuable when there is time for a retry. Bursts make subsequent retries more likely to fail, false alarms waste messages, and deadlines can reverse the preferred strategy. A matched number of packets is not the same as matched energy, latency, or worst-case cost. No architecture is a universal winner.</p></div>
      <div className="p10-links"><a href={`${import.meta.env.BASE_URL}data/part10.json`} download>Download full JSON</a><a href={`${import.meta.env.BASE_URL}data/part10.csv`} download>Download CSV</a><a href="https://github.com/MichaelWave369/OneAndManyLab/blob/main/research/PART_X_REPORT.md" target="_blank" rel="noreferrer">Read the reproducibility report ↗</a></div>
    </>}
  </section>;
}
