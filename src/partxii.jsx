import React,{useEffect,useMemo,useState} from 'react';
import './partxii.css';

const strategies=[
 ['one','One observed ping','#82a9f1','First measured opportunity'],
 ['blind_two','Two observed pings','#ba9bea','Always count first two opportunities'],
 ['oracle_selective','Oracle-selective upper bound','#65dbbc','Hindsight only, not deployable'],
 ['blind_three','Three observed pings','#dcb265','All three recorded opportunities']
];
const pct=x=>(100*x).toFixed(2)+'%';
export function evaluatePartXII(trace,part,threshold){
  const n=trace.samples.length, samples=part==='first_half'?trace.samples.slice(0,Math.floor(n/2)):part==='holdout'?trace.samples.slice(Math.floor(n/2)):trace.samples;
  if(!samples.length)return null;
  const totals=Object.fromEntries(strategies.map(x=>[x[0],{success:0,attempts:0,cost:0}]));
  let timeouts=0;const replies=[];
  for(const [stamp,a,b,c] of samples){
    for(const t of [a,b,c]){if(t===null)timeouts++;else replies.push(t);}
    const passed=[a,b,c].map(v=>v!==null&&v<=threshold),attempt=passed[0]?1:2;
    const values={
      one:[passed[0],1,1],
      blind_two:[passed[0]||passed[1],2,2],
      oracle_selective:[passed[0]||passed[1],attempt,attempt+(attempt===2?0.15:0)],
      blind_three:[passed.some(Boolean),3,3]
    };
    for(const [key,[ok,tries,cost]] of Object.entries(values)){totals[key].success+=Number(ok);totals[key].attempts+=tries;totals[key].cost+=cost;}
  }
  replies.sort((a,b)=>a-b);
  return {samples,cycles:samples.length,timeouts,replies:replies.length,median:replies[Math.ceil(replies.length*0.5)-1]??null,p95:replies[Math.ceil(replies.length*0.95)-1]??null,
    policies:Object.fromEntries(strategies.map(x=>[x[0],{success:totals[x[0]].success,rate:totals[x[0]].success/samples.length,attempts:totals[x[0]].attempts/samples.length,cost:totals[x[0]].cost/samples.length}]))};
}
function PingPlot({rows,cutoff}){
 const dots=rows.slice(0,60).flatMap((row,i)=>row.slice(1).map((r,k)=>({r,i:i*3+k})));
 const W=700,H=175,pad=25,mx=Math.max(10,cutoff*1.1,...dots.filter(x=>x.r!==null).map(x=>x.r));
 const x=i=>pad+i*(W-2*pad)/Math.max(1,dots.length-1), y=v=>H-25-(v/mx)*(H-47);
 return <svg className="p12-plot" viewBox="0 0 700 175" role="img" aria-label="Actual recorded ping RTTs and timeout crosses">
   {[0,0.5,1].map(v=><g key={v}><line x1={pad} x2={W-pad} y1={y(mx*v)} y2={y(mx*v)} stroke="#476076" opacity=".5"/><text x="0" y={y(mx*v)+3} fill="#a3b6c9" fontSize="10">{Math.round(mx*v)}</text></g>)}
   <line x1={pad} x2={W-pad} y1={y(cutoff)} y2={y(cutoff)} stroke="#f1b870" strokeDasharray="6 4"/>
   {dots.map(({r,i})=>r===null?<g key={i}><path d={'M'+(x(i)-3)+' 147 l6 6 m-6 0 l6 -6'} stroke="#ef7585" strokeWidth="2"/></g>:<circle key={i} cx={x(i)} cy={y(r)} r="2.6" fill={r<=cutoff?'#68d6bd':'#f1ba6a'}/>)}
   <text x="26" y="171" fill="#9ab0c6" fontSize="9">First 60 measurement groups (not continuous seconds)</text>
 </svg>;
}
export default function PartXII(){
 const [data,setData]=useState(null),[error,setError]=useState('');
 const [traceIndex,setTraceIndex]=useState(0),[cutoff,setCutoff]=useState(20),[part,setPart]=useState('holdout');
 useEffect(()=>{const c=new AbortController();fetch(import.meta.env.BASE_URL+'data/part12.json',{signal:c.signal}).then(r=>{if(!r.ok)throw Error('Part XII data unavailable');return r.json()}).then(setData).catch(e=>{if(e.name!=='AbortError')setError(String(e.message||e))});return()=>c.abort()},[]);
 const trace=data?.traces?.[traceIndex];
 const result=useMemo(()=>trace?evaluatePartXII(trace,part,cutoff):null,[trace,part,cutoff]);
 return <section className="p12-root" aria-label="Part XII measured ping replay lab">
   <div className="section-heading"><span className="eyebrow">EXPERIMENT 06 / PART XII</span><h2>Observations are not<br/>counterfactuals.</h2><p>Actual recorded ping round-trip times and timeout markers. Compare reliability across observed packet opportunities without pretending they are measured outcomes of a new protocol.</p></div>
   <div className="p12-metrics"><div><strong>{data?data.traces.reduce((n,t)=>n+t.samples.length*3,0).toLocaleString():'—'}</strong><small>Recorded ping outcomes</small></div><div><strong>{data?.traces.length??'—'}</strong><small>Public measurement streams</small></div><div><strong>0</strong><small>Invented trace-loss events</small></div></div>
   <div className="card"><h3>What's actually measured?</h3><p>RIPE Atlas built-in IPv4 ICMP results contain per-ping RTT in milliseconds, or an explicit timeout marker. Three pings are recorded per measurement group, but groups are roughly 240 seconds apart. Source IPs and locations have been excluded.</p><p className="p12-warning"><b>Research boundary:</b> a high RTT is not recorded packet loss. The oracle-selective strategy knows hindsight and cannot be implemented with zero feedback delay. Replaying observations cannot establish causal deployment improvements, and these are not real-time network measurements by the browser.</p><a href="https://atlas.ripe.net/docs/apis/measurement-result-format/version-4750/" target="_blank" rel="noreferrer">See source field definitions ↗</a></div>
   {error&&<div role="alert" className="p12-warning">{error}</div>}
   <div className="card p12-controls"><h3>Explore the frozen trace</h3><div className="p12-selectors">
     <label>Measurement / probe<select value={traceIndex} onChange={e=>setTraceIndex(Number(e.target.value))}>{(data?.traces||[]).map((t,i)=><option key={i} value={i}>#{t.measurement_id} / probe #{t.probe_id}</option>)}</select></label>
     <label>Response RTT cutoff<select value={cutoff} onChange={e=>setCutoff(Number(e.target.value))}>{[10,20,30,50].map(x=><option key={x} value={x}>{x} ms</option>)}</select></label>
     <label>Chronological partition<select value={part} onChange={e=>setPart(e.target.value)}><option value="first_half">First half · exploratory</option><option value="holdout">Second half · holdout</option><option value="all">All observed groups</option></select></label>
   </div><p>Controls recalculate statistics from committed observations. No new packets are sent.</p></div>
   {!result&&!error&&<p>Loading measured evidence…</p>}
   {result&&<>
    <div className="p12-metrics"><div><strong>{result.cycles}</strong><small>Selected ping groups</small></div><div><strong>{result.timeouts}/{result.cycles*3}</strong><small>Explicit ping timeouts</small></div><div><strong>{result.median?.toFixed(2)??'—'} / {result.p95?.toFixed(2)??'—'} ms</strong><small>Reply median / p95</small></div></div>
    <div className="card"><h3>Measured RTT and timeout observations</h3><p>Green: returned before cutoff. Orange: returned after cutoff. Red crosses: actual recorded timeout.</p><PingPlot rows={result.samples} cutoff={cutoff}/></div>
    <div className="card"><h3>Observation-only replay success</h3><div className="p12-bars">{strategies.map(([key,label,color,explain])=><div className="p12-bar" key={key}><div><b>{label}</b><small>{explain}</small></div><div className="p12-track"><span style={{width:(100*result.policies[key].rate)+'%',background:color}}/></div><strong>{pct(result.policies[key].rate)}</strong></div>)}</div></div>
    <div className="card p12-table"><h3>Reliability and unitless cost proxies</h3><div className="p12-scroll"><table><thead><tr><th>Replay rule</th><th>Passing cycles</th><th>Mean attempts</th><th>Mean cost proxy</th></tr></thead><tbody>{strategies.map(([key,label])=><tr key={key}><td>{label}</td><td>{result.policies[key].success}/{result.cycles}</td><td>{result.policies[key].attempts.toFixed(2)}</td><td>{result.policies[key].cost.toFixed(2)}</td></tr>)}</tbody></table></div><p>Oracle decision overhead: assumed 0.15 units on retry, not measured energy or return-channel cost.</p></div>
    <div className="p12-links"><a href={import.meta.env.BASE_URL+'data/part12.json'} download>Download measured observations (JSON)</a><a target="_blank" rel="noreferrer" href="https://github.com/MichaelWave369/OneAndManyLab/blob/main/research/PART_XII_REPORT.md">Read detailed methods ↗</a></div>
   </>}
 </section>;
}