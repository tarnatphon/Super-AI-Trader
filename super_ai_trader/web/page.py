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
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='24' fill='%2329c484'/><path d='M22 66 L42 50 L58 58 L78 34' fill='none' stroke='white' stroke-width='7' stroke-linecap='round' stroke-linejoin='round'/><circle cx='78' cy='34' r='6' fill='white'/></svg>">
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
  .regime-on{display:inline-block;margin-top:10px;padding:8px 14px;border-radius:999px;font-weight:700;font-size:15px;
    background:rgba(41,196,132,.15);border:1px solid rgba(41,196,132,.45);color:#9af0cd}
  .regime-off{display:inline-block;margin-top:10px;padding:8px 14px;border-radius:999px;font-weight:700;font-size:15px;
    background:rgba(255,193,77,.15);border:1px solid rgba(255,193,77,.45);color:#ffe2a8}
  .modal{position:fixed;inset:0;background:rgba(4,8,14,.86);display:none;align-items:center;justify-content:center;z-index:50;padding:20px}
  .modal.show{display:flex}
  .modal .box{background:var(--card);border:1px solid var(--line);border-radius:20px;max-width:560px;width:100%;padding:24px;max-height:88vh;overflow:auto}
  .pick{padding:12px 14px;margin:8px 0;border-radius:12px;background:var(--card2);border:2px solid var(--line);cursor:pointer}
  .pick:hover{border-color:var(--accent)} .pick.sel{border-color:var(--green)}
  @media(max-width:560px){.metrics{grid-template-columns:1fr}.row{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
<div class="modal" id="aiModal">
  <div class="box">
    <h2 style="margin-top:0">&#x1F9E0; Choose your local AI</h2>
    <p class="help">First thing: pick the AI brain. It runs only on this computer (no cloud). You can
      change it later in <b>Local AI brain</b>. No local model? Use the built-in AI.</p>
    <div id="modal_models"><div class="fine">Checking&#8230;</div></div>
    <div class="pick sel" data-model="">
      <b>&#x26A1; Built-in AI (no download)</b>
      <div class="fine">Simple rule-based understanding &#8212; works offline immediately. Pick this if unsure.</div>
    </div>
    <button class="btn btn-green" style="margin-top:14px" onclick="confirmAIPicker()">Continue with selected &rarr;</button>
  </div>
</div>
  <header>
    <div class="logo">Super <span class="ai">AI</span> Trader</div>
    <div class="tag">Buy low · Sell high · The safe way. Plain words, simple buttons.</div>
    <div class="shield"><span class="lock">🔒</span> Safety Shield ON — your keys stay on your computer, money cannot be withdrawn</div>
    <div id="startupNotice" style="display:none;margin-top:12px;border-radius:12px;padding:12px 16px;font-size:16px"></div>
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

  <!-- QUICK START -->
  <div class="card">
    <h2>&#x1F680; Quick start (5 steps)</h2>
    <ol style="margin:6px 0;padding-left:22px;line-height:1.7">
      <li><b>Test connection</b> (&#x1F50C; on the Live Market card) &mdash; checks live data works.</li>
      <li><b>Practice:</b> in <b>Multi-coin grids</b>, press <b>Start grids</b> (practice money) and watch BNB/SOL/ETH.</li>
      <li>Or just press <b>&#x25B6; Start a quick demo</b> (one BNB practice grid):</li>
    </ol>
    <button class="btn btn-green" style="margin-top:4px;width:auto;padding:12px 20px"
      onclick="quickDemo()">&#x25B6;&#xFE0F; Start a quick demo (practice BNB)</button>
    <ol style="margin-top:8px;padding-left:22px;line-height:1.7" hidden>
      <li><b>Watch the shields</b> &mdash; Grid &#x23F8; pauses in a crash; smart exit &#x1F512; locks profit; alerts pop up.</li>
      <li><b>Time Machine</b> replays real history so you can learn safely.</li>
      <li><b>Going real (later):</b> save a trade-only key (withdrawals OFF), run the <b>&#x2705; safety checklist</b>, use a tiny cap, then ARM.</li>
    </ol>
    <div class="fine">Tip: keep it in <b>paper/practice</b> until you&#39;ve seen many rounds. Alerts can go to your phone/email in <b>Get alerts</b>.</div>
  </div>

  <!-- LIVE MARKET CHART -->
  <div class="card">
    <h2>📈 Live market</h2>
    <p class="help">Real Binance/Gate.io prices with EMA 7 / 25 / 99 (like your trading app).
      Shows practice data here if the live feed isn't connected.</p>
    <div class="row">
      <div><label>Exchange</label>
        <select id="mk_exchange" onchange="loadMarket()">
          <option value="binance">Binance</option>
          <option value="gateio">Gate.io</option>
        </select>
      </div>
      <div><label>Coin</label>
        <select id="mk_coin" onchange="loadMarket()">
          <option>BTC</option><option>ETH</option><option selected>BNB</option><option>SOL</option><option>DOGE</option>
        </select>
      </div>
      <div><label>Timeframe</label>
        <select id="mk_tf" onchange="loadMarket()">
          <option value="15m">15m</option><option value="1h" selected>1h</option>
          <option value="4h">4h</option><option value="1d">1d</option>
        </select>
      </div>
    </div>
    <div class="fine" id="mk_src" style="margin:8px 0"></div>
    <button class="btn btn-gray" style="margin:6px 0" onclick="testConnection()">🔌 Test connection to Binance / Gate</button>
    <div id="connTests" style="margin:10px 0"></div>
    <div class="big" id="mk_price" style="font-size:28px">–</div>
    <svg id="marketChart" viewBox="0 0 600 220"></svg>
    <div class="fine" id="mk_pressure"></div>
    <label style="margin-top:12px;display:flex;gap:8px;align-items:center;font-weight:700">
      <input type="checkbox" id="mk_grid_on" checked onchange="loadMarket()" style="width:auto">
      Show the robot’s buy/sell grid on the chart
    </label>
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

    <label>Timeframe (like your trading app)</label>
    <select id="timeframe">
      <option value="15m">15 minutes</option>
      <option value="1h" selected>1 hour</option>
      <option value="4h">4 hours</option>
      <option value="1d">1 day</option>
    </select>

    <div style="display:flex;gap:8px;align-items:flex-end;margin-top:12px;flex-wrap:wrap">
      <div style="flex:1;min-width:140px">
        <label>Save these settings as</label>
        <input id="presetName" placeholder="my safe BTC grid" style="padding:12px 14px;font-size:16px">
      </div>
      <button class="btn btn-gray" style="width:auto;margin-top:0;padding:12px 16px" onclick="savePreset()">💾 Save preset</button>
      <select id="presetList" style="width:auto;min-width:160px" onchange="loadPreset()">
        <option value="">— load a saved preset —</option>
      </select>
      <button class="btn btn-gray" style="width:auto;margin-top:0;padding:12px 14px" title="Delete selected preset" onclick="deletePreset()">🗑️</button>
    </div>

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
    <button class="btn" style="background:#2a3f66;color:#bcd6ff;margin-top:10px"
      onclick="autoTune()">🧠 Auto-tune best exit for this coin</button>
    <div id="tuneBox" class="autosay" style="display:none"></div>
    <button class="btn btn-gray" style="margin-top:10px" onclick="botDetails()">🤖 Show Bot Details (running summary)</button>
    <div id="autosay" class="autosay" style="display:none"></div>
  </div>

  <!-- BOT DETAILS (running summary) -->
  <div class="card" id="botCard" style="display:none">
    <h2>🤖 Bot Details — how your robot is doing</h2>
    <div class="metrics">
      <div class="metric"><div class="k">ROI</div><div class="v" id="b_roi"></div></div>
      <div class="metric"><div class="k">Profit (practice)</div><div class="v" id="b_pnl"></div></div>
      <div class="metric"><div class="k">Buy/Sell fills</div><div class="v" id="b_trades"></div></div>
      <div class="metric"><div class="k">Profit per grid</div><div class="v" id="b_ppg"></div></div>
    </div>
    <label style="margin-top:16px">📈 Profit over time</label>
    <svg id="profitChart" viewBox="0 0 600 140" preserveAspectRatio="none"></svg>
    <label style="margin-top:10px">🗺️ Bot preview — green buys below, red sells above (EMA 7/25/99)</label>
    <svg id="previewChart" viewBox="0 0 600 220"></svg>
    <div id="trailBadge" style="margin-top:8px;font-weight:800;font-size:17px"></div>
    <label style="margin-top:10px">🏃 Smart exit — lets winners run, locks profit if they reverse</label>
    <svg id="trailChart" viewBox="0 0 600 180"></svg>
    <div class="fine" id="trailNote"></div>
    <div class="fine" id="b_info"></div>
  </div>

  <!-- MULTI-COIN GRIDS -->
  <div class="card">
    <h2>&#x1F916; Multi-coin grids (practice money)</h2>
    <div class="row">
      <div>
        <label>Exchange</label>
        <select id="mg_exchange" onchange="multiSummary()">
          <option value="binance">Binance (lower fees, deep liquidity)</option>
          <option value="gateio">Gate.io (more coins / fallback)</option>
        </select>
      </div>
      <div></div>
    </div>
    <p class="help">Start safe paper grids on several coins at once. Each one reads the real price,
      pauses in a crash, trails winners, and shows alerts below. No real orders.</p>
    <div class="row">
      <div>
        <label>Coins (comma separated)</label>
        <input id="mg_coins" value="BNB,SOL,ETH">
      </div>
      <div><label>Money each (USDT)</label><input id="mg_inv" type="number" value="1000"></div>
    </div>
    <div class="row">
      <div><label>Range width %</label><input id="mg_range" type="number" value="12"></div>
      <div><label>Grid lines</label><input id="mg_grids" type="number" value="25"></div>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:6px">
      <button class="btn btn-green" style="width:auto;flex:1;min-width:160px" onclick="multiStart()">&#x25B6;&#xFE0F; Start grids</button>
      <button class="btn" style="width:auto;flex:1;min-width:160px;background:#3a2030;color:#ffb3b3" onclick="multiStop()">&#x23F9;&#xFE0F; Stop all grids (safe)</button>
      <button class="btn btn-gray" style="width:auto;flex:1;min-width:160px" onclick="multiRefresh()">&#x1F504; Refresh</button>
    </div>
    <div id="mg_msg" class="fine" style="margin-top:8px"></div>
    <button class="btn btn-gray" style="margin-top:8px;border-color:#ffc14d;color:#ffe2a8"
      onclick="multiRetune()">&#x1F9E0; Auto-tune exits for all running coins</button>
    <div id="mg_tune" class="fine" style="margin-top:8px"></div>
    <div id="mg_daily" class="fine" style="margin-top:6px"></div>
    <div id="mg_summary" class="metrics" style="margin-top:14px"></div>
    <div id="mg_rows" style="margin-top:12px"></div>
    <div id="mg_events" style="margin-top:10px"></div>
  </div>

  <!-- LIVE TRADING PANEL -->
  <div class="card">
    <h2>📡 Live — watch the robot trade real prices</h2>
    <p class="help">Connects to the real exchange price (Binance / Gate.io). In <b>practice</b> mode it
      uses practice money and sends <b>no real orders</b> — but every number is live. Use Preview first
      to see the past result, then Start to watch it live.</p>
    <div class="row">
      <div><label>Exchange</label>
        <select id="lv_ex"><option value="binance">Binance</option><option value="gateio">Gate.io</option></select>
      </div>
      <div><label>Coin</label>
        <select id="lv_coin"><option>SOL</option><option>BTC</option><option>ETH</option><option>BNB</option></select>
      </div>
    </div>
    <div class="row">
      <div><label>Money (practice USDT)</label><input id="lv_amt" type="number" value="1000" min="50"></div>
      <div><label>Range width</label><input id="lv_range" type="number" value="12"></div>
    </div>
    <div class="row">
      <button class="btn btn-gray" style="width:auto" onclick="preview()">🕘 Preview — show PAST result</button>
      <button class="btn btn-green" style="margin-top:18px" onclick="liveStart()">▶️ START LIVE (practice)</button>
    </div>
    <button class="btn btn-blue" style="margin-top:10px" onclick="replayStart()">⏪ TIME MACHINE — replay real past candles</button>
    <div id="replayBox" style="display:none;margin-top:14px">
      <div class="fine" id="rp_source"></div>
      <div class="metrics">
        <div class="metric"><div class="k">Replay price</div><div class="v" id="rp_price">–</div></div>
        <div class="metric"><div class="k">ROI so far</div><div class="v" id="rp_roi">–</div></div>
        <div class="metric"><div class="k">Buys / Sells</div><div class="v" id="rp_fills">–</div></div>
        <div class="metric"><div class="k">Progress</div><div class="v" id="rp_prog">–</div></div>
      </div>
      <svg id="replayChart" viewBox="0 0 600 140" preserveAspectRatio="none"></svg>
      <div style="display:flex;gap:10px;margin-top:10px;flex-wrap:wrap">
        <button class="chip" onclick="replayStep(1)">▶ Step 1</button>
        <button class="chip" onclick="replayStep(25)">⏩ +25</button>
        <button class="chip" onclick="replayStep(120)">⏩ +120</button>
        <button class="chip" onclick="replayPlay()">⏯ Auto-play</button>
      </div>
    </div>
    <button class="btn" style="background:#3a2030;color:#ffb3b3;margin-top:10px;display:none" id="stopBtn" onclick="liveStop()">⏹️ STOP the robot</button>
    <button class="btn" style="background:#2b3a52;color:#cfe0ff;margin-top:10px"
      onclick="safeStopAll()">&#x1F6D1; SAFE STOP — cancel all orders before leaving/restarting</button>
    <div id="safeStopNote" class="fine"></div>
    <div id="liveStatus" class="fine"></div>
    <div id="regimeBadge" class="regime-on" style="display:none"></div>
    <div id="liveBox" style="display:none">
      <div class="metrics">
        <div class="metric"><div class="k">Live price</div><div class="v" id="lv_price">–</div></div>
        <div class="metric"><div class="k">ROI (live)</div><div class="v" id="lv_roi">–</div></div>
        <div class="metric"><div class="k">Equity</div><div class="v" id="lv_equity">–</div></div>
        <div class="metric"><div class="k">Buys / Sells</div><div class="v" id="lv_fills">–</div></div>
      </div>
      <div id="liveTrailBadge" style="margin-top:10px;font-weight:800;font-size:16px"></div>
      <label style="margin-top:12px">💰 Live profit curve</label>
      <svg id="liveChart" viewBox="0 0 600 140" preserveAspectRatio="none"></svg>
      <div class="fine" id="lv_behavior"></div>
      <label style="margin-top:10px;display:flex;gap:8px;align-items:center;font-weight:700">
        <input type="checkbox" id="notifyOn" style="width:auto"> Notify me (browser alerts on lock/pause)
      </label>
      <div id="lv_events" style="margin-top:8px"></div>
    </div>
    <div id="prevNote" class="fine"></div>
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

  <!-- LOCAL AI LIBRARY -->
  <div class="card">
    <h2>&#x1F9E0; Local AI brain</h2>
    <p class="help">The AI runs entirely on THIS computer &mdash; no cloud. Pick a small model.
      Need Ollama? Get it free at <span style="color:var(--accent)">https://ollama.com</span> then restart the app.</p>
    <div class="fine" id="ai_status" style="margin:6px 0">Checking local AI…</div>
    <div id="ai_models"></div>
  </div>

    <div style="margin-top:18px;border-top:1px dashed var(--line);padding-top:14px">
      <h2 style="color:#ffc7c7;font-size:19px">&#x1F534; REAL-MONEY multi-coin grids</h2>
      <button class="btn btn-gray" style="margin:6px 0" onclick="livePreflight()">&#x2705; Run safety checklist before starting</button>
      <div id="lg_checks" style="margin:6px 0 10px"></div>
      <p class="help">This places REAL orders using your unlocked trade-only key. Withdrawals stay OFF
        and total buys are capped. Steps: build &rarr; review &rarr; type I AGREE &rarr; arm.</p>
      <div class="row">
        <div><label>Saved key name</label><input id="lg_name" value="my-binance"></div>
        <div><label>Vault password</label><input id="lg_pw" type="password" placeholder="unlock key"></div>
      </div>
      <div class="row">
        <div><label>Coins</label><input id="lg_coins" value="BNB"></div>
        <div><label>Max spend per coin (USDT)</label><input id="lg_cap" type="number" value="50"></div>
      </div>
      <div class="row">
        <div><label>Range %</label><input id="lg_range" type="number" value="12"></div>
        <div><label>Grids</label><input id="lg_grids" type="number" value="25"></div>
      </div>
      <button class="btn btn-gray" style="border-color:#ffc14d;color:#ffe2a8" onclick="liveGridPrepare()">1&#xFE0F;&#x20E3; Build real grids (no orders yet)</button>
      <div id="lg_review" class="fine"></div>
      <label style="margin-top:8px">Type <b>I AGREE</b> to place real orders up to the cap:</label>
      <input id="lg_agree" placeholder="I AGREE">
      <button class="btn" style="background:#5a1f1f;color:#ffb3b3" onclick="liveGridArm()">2&#xFE0F;&#x20E3; ARM REAL GRIDS</button>
      <button class="btn btn-gray" style="margin-top:8px" onclick="liveGridStop()">Stop &amp; cancel all real orders</button>
      <div id="lg_status" class="fine"></div>
    </div>
  </div>

  <!-- NOTIFICATIONS -->
  <div class="card">
    <h2>&#x1F4EC; Get alerts on your phone / email</h2>
    <p class="help">Optional. The AI emails/Telegrams you when it <b>pauses in a crash</b> or
      <b>locks profit</b>. Stored locally; email uses a Gmail <i>App Password</i> (not your login).</p>
    <div class="row">
      <div><label>&#x1F4E7; Email (Gmail)</label><input id="nt_user" placeholder="you@gmail.com"></div>
      <div><label>App Password</label><input id="nt_pass" type="password" placeholder="16-char app password"></div>
    </div>
    <div class="row">
      <div><label>Send alerts to (blank = same)</label><input id="nt_to" placeholder="you@gmail.com"></div>
      <div>
        <label style="display:flex;gap:8px;align-items:center;margin-top:28px">
          <input type="checkbox" id="nt_email_on" style="width:auto"> Enable email alerts
        </label>
      </div>
    </div>
    <div class="fine">Make a Gmail App Password: Google Account &#8594; Security &#8594; 2-Step Verification &#8594; App passwords.</div>
    <hr style="border-color:var(--line);margin:14px 0">
    <div class="row">
      <div><label>Telegram bot token</label><input id="nt_tg_tok" placeholder="from @BotFather"></div>
      <div><label>Your chat id</label><input id="nt_tg_chat" placeholder="e.g. 123456789"></div>
    </div>
    <label style="display:flex;gap:8px;align-items:center">
      <input type="checkbox" id="nt_tg_on" style="width:auto"> Enable Telegram alerts
    </label>
    <div style="display:flex;gap:10px;margin-top:12px;flex-wrap:wrap">
      <button class="btn btn-green" style="width:auto;flex:1;min-width:150px" onclick="saveNotify()">&#x1F4BE; Save alerts</button>
      <button class="btn btn-gray" style="width:auto;flex:1;min-width:150px" onclick="testNotify()">&#x2709; Send test</button>
    </div>
    <div id="nt_result" class="fine"></div>
  </div>

  <!-- HISTORY -->
  <div class="card">
    <h2>&#x1F5C2;&#xFE0F; History</h2>
    <p class="help">A private, on-your-computer record of runs (like "Historical Profits"). It
      survives restarts; nothing is sent anywhere.</p>
    <div class="metrics">
      <div class="metric"><div class="k">Runs</div><div class="v" id="jh_runs">0</div></div>
      <div class="metric"><div class="k">Total P/L (practice)</div><div class="v" id="jh_pnl">0</div></div>
      <div class="metric"><div class="k">Winning runs</div><div class="v" id="jh_wins">0</div></div>
      <div class="metric"><div class="k">Grid round-trips</div><div class="v" id="jh_rt">0</div></div>
    </div>
    <button class="btn btn-gray" style="margin-top:12px" onclick="loadHistory()">&#x1F504; Refresh history</button>
    <div id="jh_list" style="margin-top:12px"></div>
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

    <div style="margin-top:18px;border-top:1px dashed var(--line);padding-top:14px">
      <h2 style="font-size:19px;color:#ffc7c7">⚠️ Switch to REAL money (optional)</h2>
      <p class="help">Paper trading uses practice money and sends no orders. Real trading uses your
        actual exchange balance. <b>Withdrawals must be OFF</b>, and the robot can never spend more
        than the cap you set.</p>
      <label>Saved key name</label>
      <input id="rl_name" value="my-binance">
      <div class="row">
        <div><label>Vault password</label><input id="rl_pw" type="password" placeholder="to unlock your key"></div>
        <div><label>Hard max spend (USDT)</label><input id="rl_cap" type="number" value="100"></div>
      </div>
      <button class="btn btn-gray" style="border-color:#ffc14d;color:#ffe2a8" onclick="realPrepare()">1️⃣ Check key (read-only)</button>
      <div id="rl_prepare" class="fine"></div>
      <label style="margin-top:8px">Type <b>I AGREE</b> to arm live trading:</label>
      <input id="rl_agree" placeholder="I AGREE">
      <button class="btn" style="background:#5a1f1f;color:#ffb3b3" onclick="realArm()">2️⃣ ARM REAL TRADING</button>
      <div id="rl_result" class="fine"></div>
      <button class="btn btn-gray" style="border-color:#ffc14d;color:#ffe2a8;margin-top:14px"
        onclick="realCancelAll()">🧹 Cancel ALL my orders on the exchange (after power cut / before starting)</button>
      <div id="rl_cancel" class="fine"></div>
      <div class="fine">Cancelling resting orders removes stray buys/sells left behind — it never sells the coins you already hold.</div>
    </div>
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
    timeframe: document.getElementById('timeframe').value,
    days: 600
  };
}
async function refreshPresets(){
  const r=await (await fetch(_auth('/api/preset/list'))).json();
  const sel=document.getElementById('presetList');
  sel.innerHTML='<option value="">— load a saved preset —</option>'+
    (r.presets||[]).map(p=>`<option value="${p.name}">💾 ${p.name}</option>`).join('');
}
async function savePreset(){
  const name=(document.getElementById('presetName').value||'').trim();
  if(!name){ alert('Give your preset a name.'); return; }
  const v=vals();
  await post('/api/preset/save', Object.assign({name}, v));
  await refreshPresets();
  document.getElementById('presetList').value=name;
}
async function loadPreset(){
  const name=document.getElementById('presetList').value;
  if(!name) return;
  const r=await (await fetch(_auth('/api/preset/load?name='+encodeURIComponent(name)))).json();
  const s=r.settings; if(!s) return;
  if(s.ticker) document.getElementById('ticker').value=s.ticker;
  if(s.investment) document.getElementById('investment').value=s.investment;
  if(s.range_pct) document.getElementById('range_pct').value=s.range_pct;
  if(s.grids) document.getElementById('grids').value=s.grids;
  if(s.mode) document.getElementById('mode').value=s.mode;
  if(s.fee) document.getElementById('fee').value=s.fee;
  if(s.timeframe) document.getElementById('timeframe').value=s.timeframe;
}
function fmt(n){return Number(n).toLocaleString(undefined,{maximumFractionDigits:2});}
async function deletePreset(){
  const name=document.getElementById('presetList').value;
  if(!name){ alert('Pick a preset to delete.'); return; }
  if(!confirm('Delete preset "'+name+'"?')) return;
  await post('/api/preset/delete',{name});
  document.getElementById('presetList').value='';
  await refreshPresets();
}
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
let liveTimer=null;
function lvPayload(){
  return {ticker:document.getElementById('lv_coin').value,
          exchange:document.getElementById('lv_ex').value,
          investment:parseFloat(document.getElementById('lv_amt').value||1000),
          range_pct:parseFloat(document.getElementById('lv_range').value||12),
          grids:parseInt(document.getElementById('grids').value||25),
          mode:document.getElementById('mode').value, poll:5};
}
async function liveStart(){
  const r=await post('/api/live/start',lvPayload());
  const st=document.getElementById('liveStatus');
  if(!r.ok){ st.style.color='#ffc7c7'; st.textContent='⚠️ '+r.error; return; }
  st.style.color='#9af0cd'; st.textContent='✅ '+r.message;
  document.getElementById('liveBox').style.display='block';
  document.getElementById('stopBtn').style.display='block';
  if(liveTimer)clearInterval(liveTimer);
  liveTimer=setInterval(livePoll,5000); livePoll();
}
function showRegime(r){
  const b=document.getElementById('regimeBadge');
  if(!r.regime){ b.style.display='none'; }
  else {
    const g=r.regime;
    b.style.display='inline-block';
    b.className = g.active ? 'regime-on' : 'regime-off';
    b.textContent = g.active ? '✅ Grid ON — '+g.reason : '⏸️ Grid PAUSED — '+g.reason;
  }
  // trailing smart-exit badge (works for both live and replay status objects)
  const t=r.trail, el=document.getElementById('liveTrailBadge');
  if(el){
    if(!t){ el.innerHTML=''; }
    else if(t.state==='locked'){
      el.innerHTML='<span class="up">🔒 Smart exit LOCKED +'+t.locked_gain_pct+'% profit</span>';
    } else if(t.state==='holding'){
      el.innerHTML='<span style="color:#ffd54a">🟢 HOLDING for more — '+(t.current_gain_pct>=0?'+':'')+t.current_gain_pct+'% up (sells if it falls back '+(t.giveback_pct||1)+'% from peak)</span>';
    } else {
      el.innerHTML='<span class="flat">👀 Smart exit armed at +'+(t.arm_pct||5)+'% — protecting with stop until then</span>';
    }
  }
}
async function livePoll(){
  const r=await (await fetch(_auth('/api/live/status'))).json();
  showRegime(r);
  if(!r.running){ if(liveTimer){clearInterval(liveTimer);liveTimer=null;}
    document.getElementById('stopBtn').style.display='none';
    if(r.killed){document.getElementById('liveStatus').textContent='🛑 Safety stop triggered — robot stopped.';}
    return; }
  document.getElementById('lv_price').textContent=r.price;
  document.getElementById('lv_roi').innerHTML=(r.roi_pct>=0?'<span class="up">+':'<span class="down">')+r.roi_pct+'%</span>';
  document.getElementById('lv_equity').textContent=fmt(r.equity)+' / '+fmt(r.investment);
  document.getElementById('lv_fills').textContent=r.matched_buys+' / '+r.matched_sells+' ('+r.round_trips+' round-trips)';
  drawProfitAt('liveChart',r.profit_curve.length>1?r.profit_curve:[r.investment,r.equity]);
  renderEvents(r.events);
  if(r.behavior){
    const b=r.behavior;
    document.getElementById('lv_behavior').textContent=
      'Live humans: '+b.pressure+' · '+Math.round((b.buy_ratio||0.5)*100)+'% buy vs '+
      Math.round((b.sell_ratio||0.5)*100)+'% sell ('+(b.source||'')+')';
  }
}
async function liveStop(){
  const r=await (await fetch(_auth('/api/live/stop'))).json();
  document.getElementById('stopBtn').style.display='none';
  document.getElementById('liveStatus').textContent=r.message||'Stopped.';
  if(liveTimer){clearInterval(liveTimer);liveTimer=null;}
}
async function preview(){
  const r=await post('/api/preview',lvPayload());
  document.getElementById('prevNote').textContent='🕘 Past preview: ROI '+r.roi_pct+'% over '+
    r.matched_trades_total+' matched fills ('+r.data_source+'). Tap "Show Bot Details" for the chart.';
  botDetailsData(r);
}
let replayTimer=null;
async function replayStart(){
  const r=await post('/api/replay/start',lvPayload());
  if(!r.ok && r.error){ document.getElementById('liveStatus').textContent='⚠️ '+r.error; return; }
  document.getElementById('replayBox').style.display='block';
  document.getElementById('rp_source').textContent='Time machine: '+r.data_source+
    ' · '+r.symbol+' · '+r.grid_mode+' · '+r.grids+' grids · range '+r.lower+'–'+r.upper;
  replayRender(r);
}
function replayRender(r){
  document.getElementById('rp_price').textContent=r.price;
  document.getElementById('rp_roi').innerHTML=(r.roi_pct>=0?'<span class="up">+':'<span class="down">')+r.roi_pct+'%</span>';
  document.getElementById('rp_fills').textContent=r.matched_buys+' / '+r.matched_sells+' ('+r.round_trips+' round-trips)';
  document.getElementById('rp_prog').textContent=r.progress_pct+'%';
  const curve=r.profit_curve.length>1?r.profit_curve:[r.investment, r.equity||r.investment];
  drawProfitAt('replayChart',curve);
  showRegime(r);
  if(r.finished){ if(replayTimer){clearInterval(replayTimer);replayTimer=null;}
    document.getElementById('rp_source').textContent+='  ✅ Replay finished.'; }
}
async function replayStep(n){
  const r=await post('/api/replay/advance',{steps:n});
  if(r.ok) replayRender(r);
}
function replayPlay(){
  if(replayTimer){ clearInterval(replayTimer); replayTimer=null; return; }
  replayTimer=setInterval(()=>replayStep(8),350);
}
function drawProfitAt(id,pts){
  const svg=document.getElementById(id); if(!svg)return; svg.innerHTML='';
  if(!pts||pts.length<2)pts=[pts[0]||0,(pts[0]||0)];
  const W=600,H=130,pad=8,min=Math.min(...pts),max=Math.max(...pts),rng=(max-min)||1;
  const xy=pts.map((p,i)=>[pad+i*(W-2*pad)/(pts.length-1),H-pad-(p-min)/rng*(H-2*pad)]);
  const d=xy.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ');
  const col=pts[pts.length-1]>=pts[0]?'#29c484':'#ff6b6b';
  svg.innerHTML=`<path d="${d} L${W-pad} ${H-pad} L${pad} ${H-pad} Z" fill="${col}" opacity="0.12"/><path d="${d}" fill="none" stroke="${col}" stroke-width="2.5"/>`;
}
function _tok(){ return localStorage.getItem('sat_token') || ''; }
function _auth(path){ const t=_tok(); if(!t) return path; return path+(path.includes('?')?'&':'?')+'token='+encodeURIComponent(t); }
async function post(path,body){
  const r=await fetch(_auth(path),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
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
async function botDetails(){
  const b=await post('/api/botdetails',vals());
  botDetailsData(b);
}
function botDetailsData(b){
  document.getElementById('botCard').style.display='block';
  document.getElementById('b_roi').innerHTML = (b.roi_pct>=0?'<span class="up">':'<span class="down">')+b.roi_pct+'%</span>';
  document.getElementById('b_pnl').innerHTML = (b.pnl>=0?'<span class="up">+':'<span class="down">')+fmt(b.pnl)+'</span>';
  document.getElementById('b_trades').textContent = b.matched_trades_total+' matched';
  document.getElementById('b_ppg').textContent = b.profit_per_grid_pct+'%';
  const src=b.data_source?(' · '+b.data_source):'';
  document.getElementById('b_info').textContent =
    `${b.symbol} · ${b.mode} · ${b.grids} grids · range ${b.lower}–${b.upper} · fees ${fmt(b.fees)}${src} · `+
    (b.stopped?'safety stop triggered':'still running safely');
  drawProfit(b.profit_curve);
  drawPreview(b.preview);
  drawTrail(b.trail);
  document.getElementById('botCard').scrollIntoView({behavior:'smooth'});
}
function drawTrail(t){
  if(!t) return;
  const badge=document.getElementById('trailBadge');
  const note=document.getElementById('trailNote');
  const price=t.price, exit=t.exit_line;
  if(t.state==='locked'){
    badge.innerHTML='<span class="up">🔒 LOCKED PROFIT at +'+t.locked_gain_pct+'%</span>';
    note.textContent='Price ran up, then pulled back '+t.giveback_pct+'% from its peak — sold to bank the gain.';
  } else if(t.state==='holding'){
    badge.innerHTML='<span style="color:#ffd54a">🟢 HOLDING for more… '+t.current_gain_pct+'% up (exit trail at +'+t.giveback_pct+'% from peak)</span>';
    note.textContent='Arm at +'+t.arm_pct+'% then ride the move; sells only if price falls back '+t.giveback_pct+'% from the highest point.';
  } else {
    badge.innerHTML='<span class="flat">👀 Watching — trail arms once price is +'+t.arm_pct+'%</span>';
    note.textContent='Below +'+t.arm_pct+'% the smart exit stays off; normal stop protects the position.';
  }
  const svg=document.getElementById('trailChart'); svg.innerHTML='';
  const W=600,H=170,pad=26;
  const vals=price.concat(exit.filter(x=>x!=null)).concat([t.armed_at,t.entry]);
  const min=Math.min(...vals),max=Math.max(...vals),rng=(max-min)||1;
  const X=i=>pad+i*(W-2*pad)/Math.max(1,price.length-1);
  const Y=v=>H-pad-(v-min)/rng*(H-2*pad);
  let d=''; price.forEach((v,i)=>{ d+=(i?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)+' '; });
  let de=''; let started=false;
  exit.forEach((v,i)=>{ if(v==null){started=false;return;} de+=(started?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)+' '; started=true; });
  // arm line
  svg.innerHTML=
    `<line x1="${pad}" y1="${Y(t.armed_at)}" x2="${W-pad}" y2="${Y(t.armed_at)}" stroke="#ffd54a" stroke-dasharray="5 5" stroke-width="1" opacity="0.6"/>`+
    `<text x="${W-pad-150}" y="${Y(t.armed_at)-4}" fill="#ffd54a" font-size="12">arm +${t.arm_pct}%</text>`+
    `<path d="${de}" fill="none" stroke="#ff9f43" stroke-width="2.5" stroke-dasharray="2 3"/>`+
    `<path d="${d}" fill="none" stroke="#29c484" stroke-width="2.6"/>`+
    `<circle cx="${X(price.length-1)}" cy="${Y(price[price.length-1])}" r="4" fill="#29c484"/>`+
    (t.state==='locked'?`<text x="${pad+6}" y="${pad+14}" fill="#29c484" font-size="14" font-weight="800">🔒 locked</text>`:'');
}
function drawProfit(pts){
  const svg=document.getElementById('profitChart'); svg.innerHTML='';
  if(!pts||pts.length<2)return;
  const W=600,H=130,pad=8,min=Math.min(...pts),max=Math.max(...pts),rng=(max-min)||1;
  const xy=pts.map((p,i)=>[pad+i*(W-2*pad)/(pts.length-1),H-pad-(p-min)/rng*(H-2*pad)]);
  const d=xy.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ');
  const col=pts[pts.length-1]>=pts[0]?'#29c484':'#ff6b6b';
  const area=d+` L${W-pad} ${H-pad} L${pad} ${H-pad} Z`;
  svg.innerHTML=`<path d="${area}" fill="${col}" opacity="0.12"/><path d="${d}" fill="none" stroke="${col}" stroke-width="2.5"/>`;
}
function drawPreview(pv){
  const svg=document.getElementById('previewChart'); svg.innerHTML='';
  const W=600,H=210,pad=24;
  const price=pv.price.filter(x=>x!=null);
  const all=[...price,...(pv.buy_levels||[]),...(pv.sell_levels||[]),
    ...pv.ema7.filter(x=>x!=null),...pv.ema25.filter(x=>x!=null),...pv.ema99.filter(x=>x!=null)];
  const min=Math.min(...all),max=Math.max(...all),rng=(max-min)||1;
  const X=i=>pad+i*(W-2*pad)/(Math.max(1,pv.price.length-1));
  const Y=v=>H-pad-(v-min)/rng*(H-2*pad);
  function line(arr,col,w){
    let d='',started=false;
    arr.forEach((v,i)=>{ if(v==null)return; d+=(started?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)+' '; started=true;});
    return `<path d="${d}" fill="none" stroke="${col}" stroke-width="${w}" stroke-linejoin="round"/>`;
  }
  let html='';
  // grid ladder: buy lines (green, below price) and sell lines (red, above)
  (pv.buy_levels||[]).forEach(v=>{ html+=`<line x1="${pad}" y1="${Y(v)}" x2="${W-pad}" y2="${Y(v)}" stroke="#29c484" stroke-width="1.4" opacity="0.55"/>`;});
  (pv.sell_levels||[]).forEach(v=>{ html+=`<line x1="${pad}" y1="${Y(v)}" x2="${W-pad}" y2="${Y(v)}" stroke="#ff6b6b" stroke-width="1.4" opacity="0.55"/>`;});
  html+=line(pv.price,'#cfe0ff',2.2);
  html+=line(pv.ema7,'#ffd54a',1.4);
  html+=line(pv.ema25,'#ff4dd2',1.4);
  html+=line(pv.ema99,'#b48cff',1.4);
  svg.innerHTML=html;
}
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
async function autoTune(){
  const box=document.getElementById('tuneBox'); box.style.display='block';
  box.textContent='🧠 Thinking — testing many trailing settings…';
  const r=await post('/api/autotune',{ticker:document.getElementById('ticker').value});
  if(!r.ok){ box.textContent='⚠️ Could not tune.'; return; }
  const b=r.best;
  box.innerHTML='<b>🧠 Best smart-exit I found for '+r.ticker+':</b><br>• '
    +r.explanation.split('\n').join('<br>• ')
    +'<br><br><b>Apply it?</b> Arm after <b>'+b.arm_pct+'%</b>, give back <b>'
    +b.giveback_pct+'%</b> from the peak. (You can still use --trail-arm / --trail-giveback.)';
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
function rlBody(){
  return {name:document.getElementById('rl_name').value,
    password:document.getElementById('rl_pw').value,
    max_spend:parseFloat(document.getElementById('rl_cap').value||0)};
}
async function realPrepare(){
  const r=await post('/api/real/prepare',rlBody());
  const el=document.getElementById('rl_prepare');
  if(!r.ok){ el.style.color='#ffc7c7'; el.textContent='⚠️ '+r.error; return; }
  el.style.color='#9af0cd';
  el.innerHTML=`✅ Key OK on ${r.exchange} (${r.key_fingerprint}). Free USDT shown by exchange: ${r.free_usdt}. `+
    `If armed, the robot may place buy orders totalling up to <b>${r.max_spend_requested} USDT</b> — never withdrawals. `+
    `<br><b>Type "I AGREE" and press ARM.</b> ${r.note}`;
}
async function realArm(){
  const body=Object.assign(rlBody(),{confirm:document.getElementById('rl_agree').value});
  const r=await post('/api/real/arm',body);
  const el=document.getElementById('rl_result');
  el.style.color = r.ok ? '#9af0cd' : '#ffc7c7';
  el.textContent = r.ok ? ('🔴 LIVE ARMED — '+r.message) : ('⚠️ '+r.error);
}
async function loadChecklist(){
  const r=await (await fetch(_auth('/api/checklist'))).json();
  document.getElementById('checklist').innerHTML = r.checklist.map(c=>
    `<li><span class="tick">✔</span><span>${c.title}${c.must?'<span class="must">IMPORTANT</span>':''}
     <div class="fine">${c.detail}</div></span></li>`).join('');
}
(function(){const q=new URLSearchParams(location.search);const t=q.get('token');if(t){localStorage.setItem('sat_token',t);}})();
loadChecklist();
refreshPresets();
loadMarket();
loadHistory();
loadAILibrary();
loadNotify();
showAIStartPicker();
startupCheck();

async function loadMarket(){
  const body={exchange:(document.getElementById('mk_exchange')?document.getElementById('mk_exchange').value:'binance'), ticker:document.getElementById('mk_coin').value,
    timeframe:document.getElementById('mk_tf').value, limit:400,
    show_grid:document.getElementById('mk_grid_on')?.checked !== false,
    range_pct: parseFloat(document.getElementById('range_pct')?.value||12),
    grids: parseInt(document.getElementById('grids')?.value||25),
    mode: document.getElementById('mode')?.value||'geometric'};
  const m=await post('/api/market', body);
  document.getElementById('mk_src').textContent='Source: '+m.source;
  const chg=m.change_pct;
  document.getElementById('mk_price').innerHTML = m.last+'  '
    +`<span class="${chg>=0?'up':'down'}" style="font-size:20px">${chg>=0?'+':''}${chg}%</span>`;
  drawMarket(m);
  document.getElementById('mk_pressure').textContent = m.pressure
    ? `Live humans: ${m.pressure} · ${Math.round((m.buy_ratio||0.5)*100)}% buying vs ${Math.round((m.sell_ratio||0.5)*100)}% selling`
    : '';
}
function drawMarket(m){
  const svg=document.getElementById('marketChart'); svg.innerHTML='';
  const W=600,H=210,pad=30;
  let all=m.closes.concat(m.ema7).concat(m.ema25).concat(m.ema99).filter(x=>x!=null);
  if(m.grid){ const gv=(m.grid.buy_levels||[]).concat(m.grid.sell_levels||[]);
    if(gv.length){all=all.concat(gv);} }
  const min=Math.min(...all),max=Math.max(...all),rng=(max-min)||1;
  const N=m.closes.length;
  const X=i=>pad+i*(W-2*pad)/Math.max(1,N-1);
  const Y=v=>H-pad-(v-min)/rng*(H-2*pad);
  function line(arr,col,w){
    let d='',started=false;
    arr.forEach((v,i)=>{ if(v==null)return; d+=(started?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)+' '; started=true; });
    return `<path d="${d}" fill="none" stroke="${col}" stroke-width="${w}"/>`;
  }
  let html='';
  if(m.grid){
    (m.grid.buy_levels||[]).forEach(v=>{ html+=`<line x1="${pad}" y1="${Y(v)}" x2="${W-pad}" y2="${Y(v)}" stroke="#29c484" stroke-width="1.2" opacity="0.5"/>`; });
    (m.grid.sell_levels||[]).forEach(v=>{ html+=`<line x1="${pad}" y1="${Y(v)}" x2="${W-pad}" y2="${Y(v)}" stroke="#ff6b6b" stroke-width="1.2" opacity="0.5"/>`; });
    html+=`<line x1="${pad}" y1="${Y(m.last)}" x2="${W-pad}" y2="${Y(m.last)}" stroke="#ffd54a" stroke-dasharray="4 4" stroke-width="1" opacity="0.7"/>`;
  }
  html += line(m.ema99,'#b48cff',1.4)+line(m.ema25,'#ff4dd2',1.6)+line(m.ema7,'#ffd54a',1.8)+line(m.closes,'#7fd3ff',2.4);
  html += `<text x="${pad}" y="16" fill="#ffd54a" font-size="12">EMA7</text>`+
          `<text x="${pad+62}" y="16" fill="#ff4dd2" font-size="12">EMA25</text>`+
          `<text x="${pad+136}" y="16" fill="#b48cff" font-size="12">EMA99</text>`+
          `<text x="${W-pad-150}" y="16" fill="#29c484" font-size="12">● buy</text>`+
          `<text x="${W-pad-80}" y="16" fill="#ff6b6b" font-size="12">● sell</text>`;
  svg.innerHTML=html;
}
async function testConnection(){
  const box=document.getElementById('connTests');
  box.innerHTML='<div class="fine">Checking… (this may take a moment)</div>';
  const body={exchange:(document.getElementById('mk_exchange')?document.getElementById('mk_exchange').value:'binance'), ticker:document.getElementById('mk_coin').value};
  const r=await post('/api/connection-test', body);
  box.innerHTML=(r.checks||[]).map(c=>
    `<div style="margin:6px 0;padding:8px 12px;border-radius:10px;`+
    `background:var(--card2);border:1px solid var(--line)">`+
    `<b>${c.ok?'<span class="up">✔</span>':'<span class="down">✖</span>'} ${c.name}</b>`+
    `<div class="fine">${c.detail||''}</div></div>`).join('');
  if(!r.ok){
    box.innerHTML+='<div class="fine" style="color:#ffc7c7">Some checks failed. Install ccxt (`pip3 install ccxt`) or check internet for live prices. '+
      'Paper trading and practice still work without it.</div>';
  } else {
    box.innerHTML+='<div class="fine" style="color:#9af0cd">All checks passed — live data is working.</div>';
  }
}

async function loadHistory(){
  const r=await post('/api/journal',{});
  const st=r.stats||{};
  document.getElementById('jh_runs').textContent=st.runs||0;
  const pnl=st.total_pnl||0;
  document.getElementById('jh_pnl').innerHTML='<span class="'+(pnl>=0?'up':'down')+'">'+(pnl>=0?'+':'')+fmt(pnl)+'</span>';
  document.getElementById('jh_wins').textContent=st.wins||0;
  document.getElementById('jh_rt').textContent=st.round_trips||0;
  const rows=(r.history||[]).slice().reverse().map(e=>{
    const d=e.data||{};
    const when=new Date(e.ts*1000).toLocaleString();
    let line;
    if(e.kind==='grid'||e.kind==='replay'||e.kind==='paper'){
      const roi=d.roi_pct!=null?(' '+d.roi_pct+'%'):'';
      line=`${(d.ticker||'').toUpperCase()} ${e.kind} ${d.source||''} &mdash; P/L ${fmt(d.pnl||0)}${roi}, ${d.round_trips||0} round-trips`;
    } else {
      line=`${d.label||e.kind} ${d.ticker||''}`;
    }
    return `<div style="padding:7px 10px;margin:5px 0;border-radius:8px;background:var(--card2);border:1px solid var(--line)" class="fine">${when}<br>${line}</div>`;
  }).join('');
  document.getElementById('jh_list').innerHTML=rows||'<div class="fine">No runs recorded yet — try Time Machine or a grid.</div>';
}

async function loadAILibrary(){
  let d;
  try { d=await post('/api/ai/library',{}); } catch(e){ return; }
  const st=document.getElementById('ai_status');
  if(!d.ollama_installed){
    st.innerHTML='<span class="flat">No Ollama yet &mdash; install from ollama.com and restart to add a local brain. The app still works with its built-in simple parser.</span>';
  } else if(!d.ollama_running){
    st.innerHTML='<span class="flat">Ollama installed but not running &mdash; start Ollama, then install a model below.</span>';
  } else {
    st.innerHTML='<span class="up">&#x2714; Local AI running.</span> Active model: '+(d.active||'none yet');
  }
  document.getElementById('ai_models').innerHTML=(d.models||[]).map(m=>{
    const tag=m.installed?'<span class="up">&#x2714; installed</span>':('<span class="flat">not installed</span>');
    const btn=m.installed? '' :
      `<button class="chip" style="border-color:#ffc14d;color:#ffe2a8" onclick="installModel('${m.id}')">Download &amp; restart</button>`;
    return `<div style="padding:10px 12px;margin:6px 0;border-radius:10px;background:var(--card2);border:1px solid var(--line)">
      <b>${m.name}</b> <span class="fine">(${m.device}, ~${m.size_gb}GB) ${tag}</b><br>
      <span class="fine">${m.note}</span> ${btn}</div>`;
  }).join('');
}
async function installModel(id){
  const box=document.getElementById('ai_status');
  box.style.color='#ffe2a8';
  box.textContent='Downloading '+id+' from Ollama… this can take a few minutes. The app will restart when it finishes.';
  const r=await post('/api/ai/install',{action:'pull_model',target:id,restart:true});
  if(r.ok){
    box.textContent='&#x2714; '+id+' ready — safely stopping the bot before restart…';
    setTimeout(async ()=>{
      try{
        const r=await (await fetch(_auth('/api/restart'),{method:'POST'})).json();
        if(r.ok){ box.textContent='&#x2705; '+r.message; setTimeout(()=>location.reload(),4000); }
        else { box.style.color='#ffc7c7'; box.textContent='&#x26A0;&#xFE0F; '+r.message; }
      }catch(e){ box.style.color='#ffc7c7'; box.textContent='Could not restart safely; please use Safe Stop then restart.'; }
    }, 1500);
  } else {
    box.style.color='#ffc7c7'; box.textContent=r.status||'Install failed.';
  }
}

let pickedModel='';
async function showAIStartPicker(){
  let d; try{ d=await post('/api/ai/library',{});}catch(e){return;}
  if(!d.needs_selection) return;
  pickedModel='';
  const box=document.getElementById('modal_models');
  box.innerHTML=(d.models||[]).map(m=>{
    const here=m.installed?' <span class="up">&#x2714; ready</span>':'';
    return '<div class="pick" data-model="'+m.id+'"><b>'+m.name+'</b>'+here+' <span class="fine">('+m.device+', ~'+m.size_gb+'GB)</span><div class="fine">'+m.note+'</div></div>';
  }).join('');
  document.querySelectorAll('#aiModal .pick').forEach(el=>{
    el.onclick=()=>{
      document.querySelectorAll('#aiModal .pick').forEach(x=>x.classList.remove('sel'));
      el.classList.add('sel'); pickedModel=el.getAttribute('data-model');
    };
  });
  document.getElementById('aiModal').classList.add('show');
}
async function confirmAIPicker(){
  await post('/api/ai/select',{model: pickedModel||''});
  document.getElementById('aiModal').classList.remove('show');
  loadAILibrary(); loadMarket();
}

async function safeStopAll(){
  const n=document.getElementById('safeStopNote');
  n.style.color='#ffe2a8'; n.textContent='Stopping the bot and cancelling every open order…';
  const r=await (await fetch(_auth('/api/safe-stop'),{method:'POST'})).json();
  if(r.safe_to_restart){ n.style.color='#9af0cd'; }
  else { n.style.color='#ffc7c7'; }
  n.textContent=r.message+' (orders '+r.open_orders_before+' -> '+r.open_orders_after+')';
}

async function startupCheck(){
  try{
    const r=await post('/api/startup',{});
    const el=document.getElementById('startupNotice');
    if(r.clean_shutdown) return;
    el.style.display='block';
    el.style.background='rgba(255,193,77,.12)';
    el.style.border='1px solid rgba(255,193,77,.45)';
    el.style.color='#ffe2a8';
    el.innerHTML='&#x26A0;&#xFE0F; <b>Last session did not close cleanly</b> (possible power cut / app closed). '+
      'Before trading, the AI checked and cancelled any leftover orders ('+
      (r.leftover_orders_cancelled||0)+' found). The bot stays stopped until you press start. '+(r.note||'');
    await post('/api/startup/ack',{});
  }catch(e){}
}

async function realCancelAll(){
  const el=document.getElementById('rl_cancel');
  el.style.color='#ffe2a8'; el.textContent='Connecting and cancelling open orders on the exchange…';
  const r=await post('/api/real/cancel-all',{name:document.getElementById('rl_name').value,
    password:document.getElementById('rl_pw').value,
    symbol:document.getElementById('ex').value==='gateio'?(document.getElementById('cname').value):null});
  el.style.color = r.ok?'#9af0cd':'#ffc7c7';
  el.textContent = r.ok ? ('&#x2705; '+r.message) : ('&#x26A0;&#xFE0F; '+r.error);
}

let _seenEvents=new Set();
function colorSpan(c){ return c==='green'?'var(--green)':c==='amber'?'#ffd54a':c==='red'?'var(--red)':'var(--muted)'; }
function toast(text,color){
  const t=document.createElement('div');
  t.textContent=text;
  t.style.cssText='position:fixed;top:18px;left:50%;transform:translateX(-50%);background:#161f2e;border:1px solid '+colorSpan(color||'green')+';color:'+colorSpan(color||'green')+';padding:12px 18px;border-radius:12px;z-index:60;font-weight:700;box-shadow:0 8px 24px rgba(0,0,0,.4);max-width:90vw';
  document.body.appendChild(t);
  setTimeout(()=>t.remove(),6000);
}
function renderEvents(events){
  const box=document.getElementById('lv_events');
  if(!box||!events) return;
  box.innerHTML=events.slice().reverse().map(e=>
    `<div style="padding:7px 10px;margin:5px 0;border-radius:8px;background:var(--card2);border:1px solid var(--line);color:${colorSpan(e.color)};font-size:15px">${new Date(e.ts*1000).toLocaleTimeString()} · ${e.text}</div>`
  ).join('');
  // new-event toasts + browser notifications (important kinds only)
  events.forEach(e=>{
    const key=e.ts+'|'+e.text;
    if(!_seenEvents.has(key)){
      _seenEvents.add(key);
      if(e.kind && e.kind!=='info' && _seenEvents.size>0){
        toast(e.text, e.color);
        if(document.getElementById('notifyOn')&&document.getElementById('notifyOn').checked && e.kind!=='roundtrip'){
          try{
            if(Notification&&Notification.permission==='granted'){ new Notification('Super-AI-Trader',{body:e.text}); }
            else if(Notification&&Notification.permission!=='denied'){ Notification.requestPermission(); }
          }catch(_){}
        }
      }
    }
  });
}

let _mgSeen=new Set();
async function multiStart(){
  const msg=document.getElementById('mg_msg');
  msg.style.color='#ffe2a8'; msg.textContent='Starting paper grids (connecting to live prices)…';
  const r=await post('/api/multigrid/start',{
    exchange:document.getElementById('mg_exchange')?document.getElementById('mg_exchange').value:'binance',
    coins:document.getElementById('mg_coins').value,
    investment:parseFloat(document.getElementById('mg_inv').value||1000),
    range_pct:parseFloat(document.getElementById('mg_range').value||12),
    grids:parseInt(document.getElementById('mg_grids').value||25)
  });
  msg.style.color = r.ok ? '#9af0cd':'#ffc7c7';
  const ok=(r.started||[]).filter(x=>x.ok).length;
  const bad=(r.started||[]).filter(x=>!x.ok);
  msg.innerHTML = r.ok ? ('&#x2705; Started '+ok+' grid(s) '+
      (bad.length?('<br>failed: '+bad.map(b=>b.coin+' ('+b.error.slice(0,40)+')').join(', ')):''))
    : ('&#x26A0;&#xFE0F; Could not start grids. Install ccxt and check internet, then Test connection.');
  if(r.ok){ multiRefresh(); multiSummary(); }
}
async function multiStop(){
  const msg=document.getElementById('mg_msg');
  msg.style.color='#ffe2a8'; msg.textContent='Safely cancelling all grid orders…';
  const r=await post('/api/multigrid/stop',{});
  msg.style.color='#9af0cd'; msg.textContent='&#x23F9; Stopped '+r.stopped+' grid(s), all orders cancelled.';
  multiRefresh();
}
async function multiRefresh(){
  let r; try{ r=await apiGet('/api/multigrid/status?exchange='+mgEx()); }catch(e){ return; }
  if(!r||r.count==null) return;
  document.getElementById('mg_rows').innerHTML = (r.coins||[]).map(c=>{
    const roi=c.roi_pct||0;
    const reg = c.paused ? '<span style="color:#ffd54a">&#x23F8; paused</span>' : '<span class="up">&#x2705; on</span>';
    return `<div style="padding:10px 12px;margin:6px 0;border-radius:10px;background:var(--card2);border:1px solid var(--line)">
      <b>${c.coin}</b> &nbsp; price ${c.price} &nbsp; P/L <span class="${roi>=0?'up':'down'}">${roi>=0?'+':''}${roi}%</span>
      &nbsp; buys ${c.buys||0} / sells ${c.sells||0} &nbsp; ${reg}
      <div class="fine">${(c.events||[]).slice(-2).map(e=>e.text).join(' · ')}</div></div>`;
  }).join('') || '<div class="fine">No grids running. Press Start.</div>';
  // global alert toasts
  (r.coins||[]).forEach(c=>(c.events||[]).forEach(e=>{
    const key=c.coin+'|'+e.ts+'|'+e.text;
    if(!_mgSeen.has(key)){ _mgSeen.add(key); toast(c.coin+': '+e.text, e.color); }
  }));
}
setInterval(()=>{ try{ if(document.getElementById('mg_rows')){ multiRefresh(); multiSummary(); } }catch(e){} }, 6000);

async function loadNotify(){
  try{
    const n=await post('/api/notify/get',{});
    document.getElementById('nt_user').value=n.smtp_user||'';
    document.getElementById('nt_to').value=n.email_to||'';
    document.getElementById('nt_email_on').checked=!!n.email_enabled;
    document.getElementById('nt_tg_tok').value=n.tg_token||'';
    document.getElementById('nt_tg_chat').value=n.tg_chat||'';
    document.getElementById('nt_tg_on').checked=!!n.telegram_enabled;
  }catch(e){}
}
function notifyBody(){
  return {
    smtp_user:document.getElementById('nt_user').value,
    smtp_pass:document.getElementById('nt_pass').value,
    email_to:document.getElementById('nt_to').value,
    email_enabled:document.getElementById('nt_email_on').checked,
    tg_token:document.getElementById('nt_tg_tok').value,
    tg_chat:document.getElementById('nt_tg_chat').value,
    telegram_enabled:document.getElementById('nt_tg_on').checked
  };
}
async function saveNotify(){
  const r=await post('/api/notify/save',notifyBody());
  const el=document.getElementById('nt_result');
  el.style.color='#9af0cd'; el.textContent='Saved (password stored encrypted/locally).';
}
async function testNotify(){
  const el=document.getElementById('nt_result');
  el.style.color='#ffe2a8'; el.textContent='Sending test alert…';
  const r=await post('/api/notify/test',notifyBody());
  if(r.sent){ el.style.color='#9af0cd'; el.textContent='&#x2705; Test sent — check your email/Telegram.'; }
  else { el.style.color='#ffc7c7'; el.textContent='Not sent yet — check the App Password/token or enable a channel.'; }
}

async function multiSummary(){
  let r; try{ r=await apiGet('/api/multigrid/summary?exchange='+mgEx()); }catch(e){ return; }
  if(!r) return;
  const pnl=r.total_pnl||0;
  document.getElementById('mg_summary').innerHTML = `
    <div class="metric"><div class="k">Grids running</div><div class="v">${r.count||0}</div></div>
    <div class="metric"><div class="k">Total P/L</div><div class="v"><span class="${pnl>=0?'up':'down'}">${pnl>=0?'+':''}${fmt(pnl)}</span> <span style="font-size:14px">(${r.total_pnl_pct||0}%)</span></div></div>
    <div class="metric"><div class="k">Round-trips</div><div class="v">${r.total_round_trips||0}</div></div>
    <div class="metric"><div class="k">Paused / Active</div><div class="v">${(r.paused_coins||[]).length} / ${(r.active_coins||[]).length}</div></div>`;
  // combined event feed (most recent first)
  const tun=(r.tuning||[]).filter(Boolean);
  if(tun.length && document.getElementById('mg_tune')){
    document.getElementById('mg_tune').innerHTML='&#x1F9E0; Last tuned: '+
      tun.map(t=>`<span class="up">${t.coin} (${t.note})</span>`).join(' &middot; ');
  }
  const evs=(r.recent_events||[]).slice().reverse();
  document.getElementById('mg_events').innerHTML = evs.length?
    evs.map(e=>`<div style="padding:6px 10px;margin:4px 0;border-radius:8px;background:var(--card2);border:1px solid var(--line);font-size:14px;color:${e.color==='green'?'var(--green)':e.color==='amber'?'#ffd54a':e.color==='red'?'var(--red)':'var(--muted)'}"><b>${e.coin}</b> · ${e.text}</div>`).join('')
    : '<div class="fine">No alerts yet.</div>';
}

async function multiRetune(){
  const el=document.getElementById('mg_tune');
  el.style.color='#ffe2a8'; el.textContent='&#x1F9E0; Learning best exit settings for each coin… (this can take a minute)';
  const coins=document.getElementById('mg_coins').value;
  const ex=document.getElementById('mg_exchange')?document.getElementById('mg_exchange').value:'binance';
  const r=await post('/api/multigrid/retune',{coins, exchange:ex});
  const rows=(r.results||[]).map(x=> x.error
    ? `<span style="color:#ffc7c7">${x.coin}: ${x.error}</span>`
    : `<span class="up">&#x2713; ${x.coin}</span>: ${x.note}`);
  el.style.color='#9af0cd';
  el.innerHTML='<b>Tuned today:</b> '+rows.join(' &middot; ');
  multiSummary();
}

async function maybeDailyRetune(){
  try{
    const r=await post('/api/multigrid/daily-retune',{exchange:mgEx()});
    const el=document.getElementById('mg_daily');
    if(!el) return;
    if(r.ran){
      const n=(r.results||[]).length;
      el.style.color='#9af0cd';
      el.textContent='&#x1F9E0; AI tuned itself today ✅ ('+n+' coin(s) checked).';
      toast('AI auto-tuned '+n+' coin(s) today','green');
    }
  }catch(e){}
}
setTimeout(maybeDailyRetune, 4000);
setInterval(maybeDailyRetune, 6*60*60*1000); // re-check daily

async function liveGridPrepare(){
  const el=document.getElementById('lg_review');
  el.style.color='#ffe2a8'; el.textContent='Building guarded grids (read-only check)…';
  const r=await post('/api/livegrid/prepare',{
    name:document.getElementById('lg_name').value,
    password:document.getElementById('lg_pw').value,
    coins:document.getElementById('lg_coins').value,
    range_pct:parseFloat(document.getElementById('lg_range').value||12),
    grids:parseInt(document.getElementById('lg_grids').value||25),
    max_spend:parseFloat(document.getElementById('lg_cap').value||50)});
  if(!r.ok){ el.style.color='#ffc7c7'; el.textContent='&#x26A0;&#xFE0F; '+r.error; return; }
  el.style.color='#ffe2a8';
  el.innerHTML='&#x2713; Ready on '+r.exchange+' ('+r.key_fingerprint+'), '+r.coins_ready+' coin(s), total cap <b>'+r.total_cap+' USDT</b>. '+
    (r.details||[]).filter(d=>d.ok).map(d=>d.coin+' @ '+d.price).join(', ')+'. <b>Review, then type I AGREE to arm.</b> '+r.note;
}
async function liveGridArm(){
  const el=document.getElementById('lg_status');
  const r=await post('/api/livegrid/arm',{confirm:document.getElementById('lg_agree').value});
  el.style.color = r.ok ? '#9af0cd' : '#ffc7c7';
  el.innerHTML = r.ok
    ? ('&#x1F534; LIVE: '+r.armed_coins+' grid(s) armed — real orders placed within cap.')
    : ('&#x26A0;&#xFE0F; '+(r.errors&&r.errors.join('; ')||r.error||'Not armed. Type I AGREE.'));
}
async function liveGridStop(){
  const el=document.getElementById('lg_status');
  const r=await post('/api/livegrid/stop',{});
  el.style.color='#9af0cd';
  el.textContent='&#x23F9; Stopped; real orders cancelled.';
}

async function livePreflight(){
  const box=document.getElementById('lg_checks');
  box.innerHTML='<div class="fine">Checking safety preconditions…</div>';
  const r=await post('/api/livegrid/preflight',{
    name:document.getElementById('lg_name').value,
    password:document.getElementById('lg_pw').value,
    max_spend:document.getElementById('lg_cap').value,
    confirm:document.getElementById('lg_agree').value});
  const rows=(r.steps||[]).map(st=>
    `<div style="padding:7px 10px;margin:4px 0;border-radius:8px;background:var(--card2);border:1px solid var(--line)">`+
    `<b>${st.ok?'<span class="up">&#x2714;</span>':'<span style="color:#ffd54a">&#x25CB;</span>'} ${st.label}</b>`+
    (st.ok?'':`<div class="fine">&#x2192; ${st.fix}</div>`)+`</div>`).join('');
  box.innerHTML=rows+
    (r.ready
      ? '<div style="color:#9af0cd;font-weight:700;margin-top:6px">All checks passed — ready to Build then Arm.</div>'
      : '<div style="color:#ffd54a;font-weight:700;margin-top:6px">Finish the items above before going live.</div>');
}

async function quickDemo(){
  // fill sensible demo values and start one practice grid
  document.getElementById('mg_coins').value='BNB';
  if(document.getElementById('mg_exchange') && document.getElementById('mk_exchange')){
    document.getElementById('mg_exchange').value=document.getElementById('mk_exchange').value;
  }
  document.getElementById('mg_inv').value='1000';
  document.getElementById('mg_range').value='12';
  document.getElementById('mg_grids').value='25';
  toast('Starting practice BNB grid…','green');
  await multiStart();
  // scroll to the multi-grid card
  document.getElementById('mg_rows').scrollIntoView({behavior:'smooth',block:'center'});
}

function mgEx(){ return document.getElementById('mg_exchange')?document.getElementById('mg_exchange').value:'binance'; }

</script>
</body>
</html>
"""
