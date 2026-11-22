import React, {useEffect,useMemo,useState} from 'react';
import './partxi.css';

const STRATEGIES=[
  ['one_shot','One-shot','#8ba9d5'],
  ['blind_twice','Blind repetition','#c9a7f3'],
  ['selective_feedback','Selective feedback','#67dbbc'],
  ['deadline_adaptive','Deadline-aware hybrid','#f2ba68'],
];
const pct=x=>(Number(x)*100).toFixed(2)+'%';
const fixed=(x,d=2)=>Number(x).toFixed(d);
const CHOICES=[
  ['capacity_source','Capacity trace',[['measured','Measured · airport'],['flat','Synthetic · flat']]],
  ['loss_regime','Loss pattern',[['markov','Bursty Markov'],['iid','Independent']]],
  ['deadline_ms','Deadline',[[1000,'1.0 seconds'],[1800,'1.8 seconds'],[2400,'2.4 seconds']]],
  ['energy_cap','Hard energy cap',[[2.0,'2.00 units'],[3.25,'3.25 units'],[4.5,'4.50 units']]],
];
function CapacityPlot({capacity}){
  let W=600,H=150;let x=i=>18+i*(W-34)/(capacity.length-1),y=v=>H-22-v/8*(H-40);
  return <svg className="p11-capacity-plot" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Measured cellular airport bandwidth fluctuates from 0 to about 7 megabits per second over the first 10 seconds">
    {[0,2,4,6,8].map(n=><g key={n}><line x1="18" x2="584" y1={y(n)} y2={y(n)} stroke="#45617a" opacity=".3"/><text x="4" y={y(n)+3} fill="#91a9bd" fontSize="9">{n}</text></g>)}
    <path d={`M${capacity.map((v,i)=>`${x(i)},${y(v)}`).join(' L')}`} fill="none" stroke="#68d7c5" strokeWidth="2.1"/>
    <text x="18" y="147" fill="#9ab1ca" fontSize="9">0 s</text><text x="564" y="147" fill="#9ab1ca" fontSize="9">10 s</text>
  </svg>
}
export default function PartXI(){
  const [data,setData]=useState(null),[error,setError]=useState('');
  const [selection,setSelection]=useState({capacity_source:'measured',loss_regime:'markov',deadline_ms:1000,energy_cap:4.5});
  useEffect(()=>{const controller=new AbortController();fetch(`${import.meta.env.BASE_URL}data/part11.json`,{signal:controller.signal}).then(r=>{if(!r.ok)throw Error('Part XI dataset unavailable');return r.json()}).then(setData).catch(e=>{if(e.name!=='AbortError')setError(String(e.message||e))});return ()=>controller.abort()},[]);
  const selected=useMemo(()=>data?.conditions.find(c=>Object.entries(selection).every(([k,v])=>c[k]===v)),[data,selection]);
  const choose=(key,value)=>setSelection(s=>({...s,[key]:['deadline_ms','energy_cap'].includes(key)?Number(value):value}));
  const series=selected?STRATEGIES.map(([id,label,color])=>({id,label,color,...selected.policies[id]})):[];
  const delta=selected?.paired_adaptive_minus_feedback || 0;
  const diffSe=selected?.paired_difference_se||0;
  return <section className="p11-root" aria-label="Part XI temporal channel lab">
    <div className="section-heading"><span className="eyebrow">EXPERIMENT 05 / PART XI</span><h2>When timing becomes<br/>part of the message.</h2><p>Replay measured cellular bandwidth alongside synthetic burst loss. Every retransmission now faces a deadline, a shared service schedule, and a strict episode-level energy cap.</p></div>
    <div className="p11-summary"><div><strong>36</strong><small>tested conditions</small></div><div><strong>{data?(data.protocol_evaluations/1e6).toFixed(2)+'M':'1.15M'}</strong><small>synthetic policy evaluations</small></div><div><strong>4</strong><small>transmission policies</small></div><div><strong>51</strong><small>Python tests passing locally</small></div></div>
    <div className="card p11-trace"><div className="p11-top"><div><h3>A measured input, not an invented network</h3><p>First 10 seconds of the Chorus cellular-airport downlink bandwidth trace. The observed rate limits how many 60-kB messages fit inside each 200-ms slot.</p></div><span className="tag">Measured capacity · CC BY 4.0</span></div>{data?.trace?.bandwidth_mbps && <CapacityPlot capacity={data.trace.bandwidth_mbps}/>}<div className="p11-source"><span>Measured bandwidth: Chorus / MobiCom 2024</span><a target="_blank" rel="noreferrer" href="https://github.com/GreenLv/Chorus/blob/main/bw_traces/downlink-cellular_airport.csv">View original trace ↗</a></div><p className="p11-note">The original trace is not a record of packet loss. Erasure states, feedback failures, sensory noise and decisions are deliberately simulated. A real capture does not magically turn the rest of the model into measured data.</p></div>
    {error&&<div className="p11-warning" role="alert">{error}</div>}
    <div className="card p11-controls"><div className="p11-top"><div><h3>Replay controls</h3><p>Switch between recorded experimental scenarios. These controls select previously generated data; they do not rerun Python in your browser.</p></div><span className="tag">Seed 369</span></div><div className="p11-control-grid">{CHOICES.map(([key,label,options])=><label key={key}>{label}<select value={selection[key]} onChange={e=>choose(key,e.target.value)}>{options.map(([value,text])=><option key={value} value={value}>{text}</option>)}</select></label>)}</div></div>
    {!selected&&!error&&<p className="loading">Loading recorded Part XI trials…</p>}
    {selected&&<>
      <div className="p11-metrics"><div><small>Deadline-aware accuracy</small><strong>{pct(selected.policies.deadline_adaptive.accuracy)}</strong><span>Both observed features correct</span></div><div><small>Feedback accuracy</small><strong>{pct(selected.policies.selective_feedback.accuracy)}</strong><span>Selective negative acknowledgements</span></div><div><small>Paired policy difference</small><strong className={delta>=0?'p11-positive':'p11-negative'}>{delta>=0?'+':''}{fixed(delta*100)} pp</strong><span>95% approximate CI: {fixed((delta-1.96*diffSe)*100)} to {fixed((delta+1.96*diffSe)*100)} pp</span></div></div>
      <div className="card p11-chart"><div className="p11-top"><div><h3>Do both features arrive correctly?</h3><p>{selected.trials_per_policy.toLocaleString()} paired episodes per policy, identical channel opportunities within each episode.</p></div><span className="tag">Monte Carlo</span></div><div className="p11-bars">{series.map(s=><div className="p11-bar" key={s.id}><span>{s.label}</span><div className="p11-rail"><div style={{width:`${100*s.accuracy}%`,background:s.color}}/></div><b>{pct(s.accuracy)}</b></div>)}</div><p className="p11-note">A protocol can obtain a correct answer by chance even if a feature never arrives; full-payload delivery is reported separately below. Small accuracy gaps may not exceed simulation uncertainty.</p></div>
      <div className="card p11-table"><h3>Performance under hard constraints</h3><div className="p11-scroll"><table><thead><tr><th>Policy</th><th>Full delivery</th><th>Energy used</th><th>Data packets</th><th>Time (ms)*</th><th>Budget blocked</th></tr></thead><tbody>{series.map(s=><tr key={s.id}><td><span className="p11-color" style={{background:s.color}}/>{s.label}</td><td>{pct(s.fully_delivered)}</td><td>{fixed(s.mean_energy)}</td><td>{fixed(s.mean_packets)}</td><td>{fixed(s.mean_completion_ms,0)}</td><td>{pct(s.budget_exhaustion_rate)}</td></tr>)}</tbody></table></div><p className="p11-note">*Completion time uses the deadline as a penalty for incomplete delivery. Each episode's data plus return-channel control costs are strictly limited by the selected cap, not just matched in expectation.</p></div>
      <div className="p11-insight"><b>Why the hybrid switches:</b> When the deadline is too tight to receive feedback and use a retry, it sends blind redundancy. With more time, it uses selective feedback. This is a predefined decision rule, not a learned optimal policy or an oracle that sees future channel states.</div>
      <div className="p11-links"><a href={`${import.meta.env.BASE_URL}data/part11.json`} download>Download JSON data</a><a href={`${import.meta.env.BASE_URL}data/part11.csv`} download>Download CSV data</a><a target="_blank" rel="noreferrer" href="https://github.com/MichaelWave369/OneAndManyLab/blob/main/research/PART_XI_REPORT.md">Read method & limitations ↗</a></div>
    </>}
  </section>
}
