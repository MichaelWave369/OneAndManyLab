#!/usr/bin/env python3
"""Generate an offline self-contained research dashboard from binding_results.json."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent

HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Offline research dashboard for a synthetic feature-binding and causal-inference lab.">
<title>One & Many Lab · Feature Binding</title>
<style>
:root { color-scheme: dark; --bg:#0c101a; --panel:#151d2a; --line:#2d3a4a; --text:#e8edf3; --muted:#a8b8c8; --a:#88b8ff; --b:#88dfcb; --c:#edc188; --d:#cba8ff; }
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}main{max-width:1080px;margin:auto;padding:30px 20px 64px}h1{font-size:clamp(2rem,4.5vw,3.4rem);letter-spacing:-.04em;line-height:1.12;margin:8px 0 14px}h2{font-size:1.2rem;margin:0 0 16px}h3{font-size:1rem}p{margin:0 0 14px}.eyebrow{color:var(--b);font-weight:750;text-transform:uppercase;letter-spacing:.12em;font-size:.75rem}.lede{font-size:1.14rem;color:var(--muted);max-width:850px}.label{color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.08em}.notice{border-left:3px solid var(--c);padding:12px 16px;background:#251f1a;color:#f2e6d3;margin:25px 0}.controls{display:flex;flex-wrap:wrap;gap:16px;margin:24px 0}.control{flex:1 1 230px}label{display:block;color:var(--muted);font-size:.9rem;margin-bottom:8px}select{width:100%;background:var(--panel);border:1px solid var(--line);color:var(--text);padding:12px 14px;border-radius:8px;font:inherit}.grid{display:grid;grid-template-columns:1.35fr 1fr;gap:18px;margin:16px 0}.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:22px}.resultrow{display:grid;grid-template-columns:190px 1fr 75px;gap:14px;align-items:center;margin:19px 0}.bar{height:13px;overflow:hidden;background:#2b3644;border-radius:20px}.fill{height:100%;border-radius:20px}.value{font-variant-numeric:tabular-nums;text-align:right;font-weight:700}.small{font-size:.84rem;color:var(--muted)}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:12px}.metric{background:#101827;border:1px solid #263347;border-radius:9px;padding:13px}.number{font-size:1.6rem;font-weight:750;letter-spacing:-.04em}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;min-width:560px}th,td{text-align:left;padding:11px 10px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.07em}td.num{text-align:right;font-variant-numeric:tabular-nums}.causal{display:grid;grid-template-columns:1fr 1fr;gap:14px}.causal .panel{background:#101827}.formula{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:.95rem;color:var(--b)}.links a{color:var(--a)}.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:9px}.footer{color:var(--muted);font-size:.87rem;margin-top:30px;padding-top:18px;border-top:1px solid var(--line)}strong{color:#fff}@media(max-width:780px){.grid,.causal{grid-template-columns:1fr}.resultrow{grid-template-columns:132px 1fr 62px;gap:8px;font-size:.83rem}.panel{padding:17px}}
</style>
</head>
<body><main>
<div class="eyebrow">Φ Research Notebook · Part VIII</div>
<h1>One & Many Lab</h1>
<p class="lede">Different architectures, the same synthetic color-and-shape binding task. Change packet loss and sensory noise to see when feedback helps, when it doesn't, and why communication cost matters.</p>
<div class="notice"><strong>Research boundary:</strong> This is a packet-protocol simulation with toy feature specialists, not a faithful model of a brain, IIT, or Global Neuronal Workspace Theory. It measures task performance and causal control, not subjective consciousness.</div>
<div class="controls">
<div class="control"><label for="noise">Independent sensory bit-flip probability</label><select id="noise"><option value="0">0%</option><option value="0.1" selected>10%</option><option value="0.25">25%</option></select></div>
<div class="control"><label for="loss">Packet erasure probability</label><select id="loss"><option value="0">0%</option><option value="0.15">15%</option><option value="0.35" selected>35%</option></select></div>
</div>
<div class="grid">
<section class="panel"><h2>Both features identified correctly</h2><div id="bars" role="group" aria-label="Observed binding accuracy by protocol"></div><p class="small">Observed proportions from <span id="n">50,000</span> trials per protocol at the selected condition. Bars show point estimates, not confidence intervals.</p></section>
<section class="panel"><h2>Reading the results</h2><div class="metrics"><div class="metric"><div class="label">Feedback vs single send</div><div class="number" id="gain">...</div><div class="small">Percentage-point gain</div></div><div class="metric"><div class="label">Feedback mean traffic</div><div class="number" id="packets">...</div><div class="small">Data + NACK messages</div></div></div><p class="small" style="margin-top:16px" id="insight"></p></section>
</div>
<section class="panel"><h2>Methods, budgets, and predictions</h2><div class="table-wrap"><table><thead><tr><th>Architecture</th><th>Observed</th><th>Analytical</th><th>Mean data</th><th>Mean control</th><th>Mean total</th></tr></thead><tbody id="table"></tbody></table></div><p class="small">All protocols use exactly the same noisy sensory bits and cue in each episode. The feedback scheme has a reliable NACK control link and sends a second data packet only when necessary. The redundant feedforward control always transmits two copies. Message budgets are not matched.</p></section>
<div class="grid"><section class="panel"><h2>Correlation is not intervention</h2><div class="causal"><div><div class="label">Common cause Z → A, Z → B</div><p class="formula">r(A,B) = <span id="corr">...</span></p><p>Set A to 0 or 1: B does not change.</p><p class="formula">Causal effect = <span id="common">...</span></p></div><div><div class="label">Directed mechanism A → B</div><p>Set A to 0 or 1: B's probability changes.</p><p class="formula">Causal effect = <span id="direct">...</span></p></div></div><p class="small">Interventions are simulated in structural models with identical background randomness, not performed on a living brain.</p></section>
<section class="panel"><h2>What this can actually establish</h2><p><strong>Supported:</strong> A missing-data recovery mechanism can improve functional binding when transmission erasures occur. Shared inputs can generate strong observational correlations without an A→B causal link.</p><p><strong>Not established:</strong> that feedback is uniquely necessary for binding; that workspaces necessarily outperform feedforward systems; or that any protocol possesses subjective experience.</p></section></div>
<section class="panel links"><h2>Read & reproduce</h2><p>Source scripts: <code>binding_architectures.py</code>, <code>causal_binding_probe.py</code>. Data: <code>binding_results.json</code>, <code>binding_results.csv</code>. Unit tests use Python's standard-library <code>unittest</code>.</p><p><a href="https://arxiv.org/abs/2611.08469">Wu & He (2026) · Mechanism identifiability</a> · <a href="https://www.nature.com/articles/s41586-025-08888-1">Cogitate Consortium (2025) · Testing consciousness theories</a></p></section>
<p class="footer">One & Many Lab · Independent educational models · No network requests or external dependencies required for this dashboard. All plotted observations are embedded from a seeded local simulation.</p>
</main>
<script id="results-data" type="application/json">__DATA_JSON__</script>
<script>
(()=>{'use strict';
const data=JSON.parse(document.getElementById('results-data').textContent);
const names={feedforward:'Feedforward',workspace:'Shared workspace',recurrent_retry:'Feedback + retry',feedforward_redundant:'FF + redundancy'};
const colors={feedforward:'var(--a)',workspace:'var(--b)',recurrent_retry:'var(--c)',feedforward_redundant:'var(--d)'};
const keys=Object.keys(names);
const pct=v=>(v*100).toFixed(2)+'%';
const clean=v=>Number(v).toFixed(2);
function draw(){
const n=Number(document.getElementById('noise').value),e=Number(document.getElementById('loss').value);
const c=data.conditions.find(x=>x.sensory_noise===n&&x.packet_erasure===e);
if(!c){return;}
document.getElementById('n').textContent=c.trials_per_protocol.toLocaleString();
document.getElementById('bars').innerHTML=keys.map(k=>{const r=c.protocols[k];return `<div class="resultrow"><div><span class="dot" style="background:${colors[k]}"></span>${names[k]}</div><div class="bar"><div class="fill" style="background:${colors[k]};width:${(r.both_features_accuracy*100).toFixed(3)}%"></div></div><div class="value">${pct(r.both_features_accuracy)}</div></div>`;}).join('');
document.getElementById('table').innerHTML=keys.map(k=>{const r=c.protocols[k];return `<tr><td>${names[k]}</td><td class="num">${pct(r.both_features_accuracy)}</td><td class="num">${pct(r.analytical.both_features_accuracy)}</td><td class="num">${clean(r.mean_data_packets)}</td><td class="num">${clean(r.mean_control_packets)}</td><td class="num">${clean(r.mean_total_packets)}</td></tr>`;}).join('');
const ff=c.protocols.feedforward, fb=c.protocols.recurrent_retry, redundant=c.protocols.feedforward_redundant;
document.getElementById('gain').textContent=((fb.both_features_accuracy-ff.both_features_accuracy)*100).toFixed(2)+' pp';
document.getElementById('packets').textContent=clean(fb.mean_total_packets);
document.getElementById('insight').textContent=e===0?'With no packet erasures, the architectures tie. Sensory noise remains; extra transmission cannot fix a wrong sensed bit.':`Feedback raises successful delivery by retrying losses. A twice-sent feedforward control has nearly the same accuracy (${pct(redundant.both_features_accuracy)}), so retries do not establish a unique benefit of recurrent topology. Feedback uses about ${clean(fb.mean_total_packets)} total messages here, compared with four for two unconditional copies.`;
}
const ctrl=data.causal_control;document.getElementById('corr').textContent=ctrl.shared_cause.observed_pearson_r.toFixed(3);document.getElementById('common').textContent=ctrl.shared_cause.interventional_effect_do_A1_minus_do_A0.toFixed(3);document.getElementById('direct').textContent=ctrl.directed_A_to_B.interventional_effect_do_A1_minus_do_A0.toFixed(3);
document.getElementById('noise').addEventListener('change',draw);document.getElementById('loss').addEventListener('change',draw);draw();
})();
</script></body></html>'''


def main() -> None:
    results = json.loads((ROOT / 'binding_results.json').read_text(encoding='utf-8'))
    data = json.dumps(results, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    destination = ROOT / 'index.html'
    destination.write_text(HTML.replace('__DATA_JSON__', data), encoding='utf-8')
    print(f'Created {destination} ({destination.stat().st_size:,} bytes).')


if __name__ == '__main__':
    main()