"""The Super-AI-Trader dashboard page.

Original, simple design: big text, plain language, three big steps, and a
prominent green 'Safety Shield'. Practice mode first. Exchange secrets are never
shown or sent to the browser.
"""

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Super-AI-Trader</title>
<style>
  :root{
    --bg:#0e1420; --card:#161f2e; --card2:#1c2839; --line:#26324a;
    --green:#29c484; --green-d:#159a63; --red:#ff6b6b; --amber:#ffc14d;
    --text:#eef3fb; --muted:#9fb0c7; --accent:#4aa3ff;
    --radius:18px;
  }
  *{box-sizing:border-box}
  body{margin:0;background:linear-gradient(180deg,#0b111c,#0e1420);color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    font-size:18px;line-height:1.5;padding:0 0 60px}
  .wrap{max-width:920px;margin:0 auto;padding:0 18px}
  header{padding:26px 0 8px;text-align:center}
  .logo{font-size:30px;font-weight:800;letter-spacing:.5px}
  .logo .ai{color:var(--green)}
  .tag{color:var(--muted);font-size:17px;margin-top:4px}
  .shield{display:inline-flex;align-items:center;gap:10px;margin-top:14px;background:
    rgba(41,196,132,.12);border:1px solid rgba(41,196,132,.4);color:#9af0cd;
    padding:10px 18px;border-radius:999px;font-weight:700;font-size:17px}
  .shield .lock{font-size:20px}
  .mode{display:flex;justify-content:center;gap:12px;margin:22px 0 6px;flex-wrap:wrap}
  .mode button{font-size:18px;font-weight:700;padding:14px 26px;border-radius:14px;
    border:2px solid var(--line);background:var(--card);color:var(--muted);cursor:pointer}
  .mode button.active-practice{background:rgba(41,196,132,.18);border-color:var(--green);color:#bff3dd}
  .mode button.active-live{background:rgba(255,193,77,.12);border-color:var(--amber);color:#ffe2a8}
  .mode small{display:block;font-weight:500;font-size:14px;color:var(--muted)}
  .card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
    padding:22px;margin:18px 0;box-shadow:0 8px 24px rgba(0,0,0,.25)}
  .card h2{margin:0 0 6px;font-size:22px}
  .card p.help{color:var(--muted);margin:0 0 16px;font-size:17px}
  .steps{display:grid;grid-template-columns:1fr;gap:16px}
  label{display:block;font-weight:700;margin:14px 0 6px}
  input,select{width:100%;font-size:19px;padding:14px 16px;border-radius:12px;
    border:2px solid var(--line);background:var(--card2);color:var(--text)}
  input:focus,select:focus{outline:none;border-color:var(--accent)}
  .row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  .btn{display:inline-block;font-size:20px;font-weight:800;padding:16px 28px;border-radius:14px;
    border:none;cursor:pointer;margin-top:18px;width:100%}
  .btn-green{background:linear-gradient(180deg,var(--green),var(--green-d));color:#04231a}
  .btn-blue{background:linear-gradient(180deg,#4aa3ff,#2b7fd6);color:#031733}
  .btn-gray{background:var(--card2);color:var(--text);border:2px solid var(--line)}
  .autosay{background:rgba(74,163,255,.08);border:1px solid rgba(74,163,255,.3);border-radius:12px;
    padding:14px 16px;margin-top:14px;color:#cfe6ff;font-size:17px}
  .autosay li{margin:6px 0}
  .big{font-size:34px;font-weight:800}
  .up{color:var(--green)} .down{color:var(--red)} .flat{color:var(--muted)}
  .metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:14px}
  .metric{background:var(--card2);border:1px solid var(--line);border-radius:12px;padding:14px}
  .metric .k{color:var(--muted);font-size:15px}
  .metric .v{font-size:22px;font-weight:800;margin-top:2px}
  svg{width:100%;height:160px;margin-top:14px;background:var(--card2);border-radius:12px}
  .check li{list-style:none;margin:10px 0;display:flex;gap:10px;align-items:flex-start}
  .check .tick{color:var(--green);font-weight:900}
  .check .must{background:rgba(255,193,77,.15);color:#ffe2a8;border-radius:6px;padding:0 8px;
    font-size:13px;font-weight:700;margin-left:6px}
  .warn{background:rgba(255,107,107,.1);border:1px solid rgba(255,107,107,.4);color:#ffc7c7;
    border-radius:12px;padding:14px 16px;margin-top:14px;display:none}
  .fine{color:var(--muted);font-size:14px;margin-top:10px}
  .tab{cursor:pointer;text-decoration:underline;color:var(--accent)}
  footer{text-align:center;color:var(--muted);font-size:14px;margin-top:30px}
  .chip{background:var(--card2);border:1px solid var(--line);color:var(--text);border-radius:999px;
    padding:9px 14px;font-size:15px;cursor:pointer}
  .chip:hover{border-color:var(--accent)}
  .msg{border-radius:12px;padding:12px 16px;margin:10px 0;font-size:17px;line-height:1.5}
  .msg.you{background:rgba(74,163,255,.10);border:1px solid rgba(74,163,255,.3)}
  .msg.ai{background:rgba(41,196,132,.10);border:1px solid rgba(41,196,132,.35);white-space:pre-wrap}
  @media(max-width:560px){.metrics{grid-template-columns:1fr}.row{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">Super <span class="ai">AI</span> Trader</div>
    <div class="tag">Buy low · Sell high · The safe way. Plain words, simple buttons.</div>
    <div class="shield"><span class="lock">🔒</span> Safety Shield ON — your keys stay on your computer, money cannot be withdrawn</div>
  </header>

  <div class="mode">
    <button id="practiceBtn" class="active-practice" onclick="setMode('practice')">
      🧪 PRACTICE (safe) <small>pretend money · learn freely</small>
    </button>
    <button id="liveBtn" onclick="setMode('live')">
      🔗 CONNECT EXCHANGE <small>Binance / Gate.io · still no withdrawals</small>
    </button>
  </div>

  <!-- TALK TO YOUR AI -->
  <div class="card">
    <h2>💬 Tell your AI what you want</h2>
    <p class="help">Just type like you're talking to a person. The AI thinks, the robot does the
      work, and the Safety Shield protects you. Try one of these:</p>
    <div id="chips" style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">
      <button class="chip" onclick="quick('Set up a safe grid for Bitcoin with 1000 USDT')">Set up a safe Bitcoin grid</button>
      <button class="chip" onclick="quick('Analyze Ethereum — should I buy?')">Analyze Ethereum</button>
      <button class="chip" onclick="quick('Backtest the strategy on Bitcoin')">Backtest the strategy</button>
      <button class="chip" onclick="quick('Learn and predict Bitcoin')">Learn &amp; predict</button>
      <button class="chip" onclick="quick('Is my money safe?')">Is my money safe?</button>
    </div>
    <div style="display:flex;gap:10px">
      <input id="ask" placeholder="e.g. set up a safe grid for Bitcoin with 1000"
        onkeydown="if(event.key==='Enter')askAI()">
      <button class="btn btn-green" style="width:auto;margin-top:0;padding:14px 24px" onclick="askAI()">Ask ▶</button>
    </div>
    <div id="chat" style="margin-top:14px"></div>
  </div>

  <!-- STEP CARD -->
  <div class="card" id="setupCard">
    <h2>1️⃣ Pick your coin</h2>
    <p class="help">Choose what the little robot trades. Don't know? Use <b>BTC</b> (Bitcoin).</p>
    <label>Coin</label>
    <select id="ticker">
      <option value="BTC">BTC — Bitcoin (most popular)</option>
      <option value="ETH">ETH — Ethereum</option>
      <option value="BNB">BNB — Binance Coin</option>
      <option value="DOGE">DOGE — Dogecoin</option>
      <option value="DEMO">DEMO — practice coin</option>
    </select>

    <h2 style="margin-top:22px">2️⃣ Choose how much (practice money)</h2>
    <div class="row">
      <div>
        <label>Money to use (USDT)</label>
        <input id="investment" type="number" value="1000" min="50">
      </div>
      <div>
        <label>Price range width</label>
        <select id="range_pct">
          <option value="8">Narrow (calm market)</option>
          <option value="12" selected>Normal</option>
          <option value="20">Wide (bouncy market)</option>
        </select>
      </div>
    </div>
    <details style="margin-top:14px">
      <summary class="tab" style="cursor:pointer;font-size:16px">⚙️ Advanced (number of steps &amp; style) — you can skip this</summary>
      <div class="row">
        <div><label>Number of little steps</label><input id="grids" type="number" value="25" min="5" max="80"></div>
        <div><label>Step style</label>
          <select id="mode"><option value="geometric">Even % (recommended)</option><option value="arithmetic">Even price</option></select>
        </div>
      </div>
      <label>Fee per trade % (Binance 0.1 · Gate 0.1–0.2)</label>
      <input id="fee" type="number" value="0.1" step="0.01" min="0">
    </details>

    <button class="btn btn-blue" onclick="autoset()">✨ Auto-Set For Me (easiest)</button>
    <button class="btn btn-green" onclick="run()">▶️ Try It — Show My Results</button>
    <div id="autosay" class="autosay" style="display:none"></div>
  </div>

  <!-- RESULTS -->
  <div class="card" id="resultCard" style="display:none">
    <h2>📊 What happened</h2>
    <p class="help">A practice run over recent price moves. Green = made pretend money.</p>
    <div class="big" id="headline"></div>
    <svg id="chart" viewBox="0 0 600 160" preserveAspectRatio="none"></svg>
    <div class="metrics">
      <div class="metric"><div class="k">Money at the end</div><div class="v" id="m_end"></div></div>
      <div class="metric"><div class="k">Small wins collected</div><div class="v" id="m_trips"></div></div>
      <div class="metric"><div class="k">Profit from grid</div><div class="v" id="m_profit"></div></div>
      <div class="metric"><div class="k">Fees paid</div><div class="v" id="m_fees"></div></div>
    </div>
    <div class="fine" id="m_note"></div>
  </div>

  <!-- SAFETY -->
  <div class="card">
    <h2>🛡️ How we keep you safe</h2>
    <p class="help">Every box here is built into the app.</p>
    <ul class="check" id="checklist" style="padding:0"></ul>
    <div class="warn" id="liveWarn"></div>
  </div>

  <!-- CONNECT (hidden until live mode) -->
  <div class="card" id="connectCard" style="display:none">
    <h2>🔗 Connect an exchange (optional)</h2>
    <p class="help">Only needed for real trading. <b>Create a TRADE-ONLY key on the exchange and
      turn WITHDRAWALS OFF.</b> Your key is encrypted on this computer and never shown again.</p>
    <label>Exchange</label>
    <select id="ex"><option value="binance">Binance (recommended — lower fees, deep liquidity)</option>
      <option value="gateio">Gate.io (more coins)</option></select>
    <label>Save under name</label><input id="cname" value="my-binance">
    <label>API key</label><input id="apikey" type="password" placeholder="paste key">
    <label>API secret</label><input id="apisecret" type="password" placeholder="paste secret">
    <label>Make a vault password (to lock your keys)</label>
    <input id="vaultpw" type="password" placeholder="a strong password you will remember">
    <button class="btn btn-gray" onclick="connect()">🔒 Save &amp; Lock Key (this computer only)</button>
    <div id="cresult" class="fine"></div>
  </div>

  <footer>Educational software · not financial advice · runs on your own computer (127.0.0.1) · Super-AI-Trader</footer>
</div>

<script>
let MODE='practice';
function setMode(m){
  MODE=m;
  document.getElementById('practiceBtn').className = m==='practice' ? 'active-practice' : '';
  document.getElementById('liveBtn').className = m==='live' ? 'active-live' : '';
  document.getElementById('connectCard').style.display = m==='live' ? 'block' : 'none';
}
function vals(){
  return {
    ticker: document.getElementById('ticker').value,
    investment: parseFloat(document.getElementById('investment').value||1000),
    range_pct: parseFloat(document.getElementById('range_pct').value),
    grids: parseInt(document.getElementById('grids').value||25),
    mode: document.getElementById('mode').value,
    fee: parseFloat(document.getElementById('fee').value||0.1),
    days: 600
  };
}
function fmt(n){return Number(n).toLocaleString(undefined,{maximumFractionDigits:2});}
function drawChart(points){
  const svg=document.getElementById('chart'); svg.innerHTML='';
  if(!points||points.length<2) return;
  const min=Math.min(...points), max=Math.max(...points), rng=(max-min)||1;
  const W=600,H=150,pad=6;
  const xy=points.map((p,i)=>[pad+i*(W-2*pad)/(points.length-1), H-pad-(p-min)/rng*(H-2*pad)]);
  const d=xy.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ');
  const up=points[points.length-1]>=points[0];
  const col=up?'#29c484':'#ff6b6b';
  svg.innerHTML=`<path d="${d}" fill="none" stroke="${col}" stroke-width="3" stroke-linejoin="round"/>
    <line x1="${pad}" y1="${H-pad-(points[0]-min)/rng*(H-2*pad)}" x2="${W-pad}"
     y1="${H-pad-(points[0]-min)/rng*(H-2*pad)}" stroke="#445" stroke-dasharray="4 4"/>`;
}
function showResult(sim){
  document.getElementById('resultCard').style.display='block';
  const r=sim.return_pct;
  document.getElementById('headline').innerHTML =
    (r>=0?`<span class="up">+${r}%</span> made`:`<span class="down">${r}%</span>`) +
    ` in this practice run`;
  drawChart(sim.curve);
  document.getElementById('m_end').textContent = fmt(sim.final_equity)+' / '+fmt(sim.initial);
  document.getElementById('m_trips').textContent = sim.round_trips+' small wins';
  document.getElementById('m_profit').innerHTML =
    `<span class="${sim.grid_profit>=0?'up':'down'}">${sim.grid_profit>=0?'+':''}${fmt(sim.grid_profit)}</span>`;
  document.getElementById('m_fees').textContent = fmt(sim.fees);
  document.getElementById('m_note').textContent =
    `Robot buys below the price and sells above it across the range ${sim.lower}–${sim.upper}. `+
    (sim.unrealized<0? 'Note: some coins are still held and worth a bit less now — the stop-loss protects you in real use.':'');
  document.getElementById('resultCard').scrollIntoView({behavior:'smooth'});
}
async function post(path,body){
  const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  return r.json();
}
function addMsg(who,text){
  const div=document.createElement('div');
  div.className='msg '+(who==='you'?'you':'ai');
  div.textContent=(who==='you'?'🧑 ':'🤖 ')+text;
  document.getElementById('chat').appendChild(div);
  div.scrollIntoView({behavior:'smooth',block:'nearest'});
}
async function askAI(){
  const inp=document.getElementById('ask');
  const text=inp.value.trim(); if(!text)return;
  addMsg('you',text); inp.value='';
  const thinking=document.createElement('div');
  thinking.className='msg ai'; thinking.textContent='🤖 …';
  document.getElementById('chat').appendChild(thinking);
  const res=await post('/api/ask',{text});
  thinking.remove();
  addMsg('ai',res.reply.replace(/^🤖\s*/,''));
  // If it was a grid, also show the friendly result card.
  if(res.intent==='grid' && res.data && res.data.result){
    const g=res.data.result;
    drawChart(g.curve||[g.final_equity]);
  }
}
function quick(t){ document.getElementById('ask').value=t; askAI(); }
async function run(){ showResult(await post('/api/simulate', vals())); }
async function autoset(){
  const res=await post('/api/autoset', Object.assign(vals(),{risk_mode:'steady'}));
  document.getElementById('grids').value=res.grids;
  document.getElementById('mode').value=res.mode;
  document.getElementById('fee').value=res.fee;
  const box=document.getElementById('autosay'); box.style.display='block';
  box.innerHTML='<b>🤖 I picked safe settings for you:</b><ul>'+
    res.plain.map(l=>`<li>• ${l}</li>`).join('')+'</ul>';
  showResult(res.sim);
}
async function connect(){
  const body={exchange:document.getElementById('ex').value,name:document.getElementById('cname').value,
    api_key:document.getElementById('apikey').value,api_secret:document.getElementById('apisecret').value,
    password:document.getElementById('vaultpw').value};
  const res=await post('/api/connect',body);
  document.getElementById('cresult').textContent = res.ok
    ? `✅ Saved. Key saved as ${res.api_key_fp}. ${res.note}`
    : ('⚠️ '+res.error);
}
async function loadChecklist(){
  const r=await (await fetch('/api/checklist')).json();
  document.getElementById('checklist').innerHTML = r.checklist.map(c=>
    `<li><span class="tick">✔</span><span>${c.title}${c.must?'<span class="must">IMPORTANT</span>':''}
     <div class="fine">${c.detail}</div></span></li>`).join('');
}
loadChecklist();
</script>
</body>
</html>
"""
