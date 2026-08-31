"""The Super-AI-Trader dashboard page.

Original, simple design: big text, plain language, three big steps, and a
prominent green 'Safety Shield'. Practice mode first. Exchange secrets are never
shown or sent to the browser.
"""

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0e1420">
<title>Super-AI-Trader</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='24' fill='%2329c484'/><path d='M22 66 L42 50 L58 58 L78 34' fill='none' stroke='white' stroke-width='7' stroke-linecap='round' stroke-linejoin='round'/><circle cx='78' cy='34' r='6' fill='white'/></svg>">
<style>
  :root{
    --bg:#0a0e17; --panel:#101725; --card:#131c2e; --card2:#18233a; --elev:#1d2a44;
    --line:#243149; --line2:#2c3c5c;
    --green:#16c784; --green-d:#0e9f68; --red:#ea3943; --amber:#f0b90b; --accent:#4d8dff;
    --text:#eaf0fa; --muted:#8a99b5; --chip:#0e1626;
    --radius:14px;
    --shadow:0 8px 30px rgba(0,0,0,.35);
    --shadow-sm:0 2px 8px rgba(0,0,0,.3);
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;background:var(--bg);color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    font-size:15px;line-height:1.5;padding:0 0 70px;-webkit-font-smoothing:antialiased}
  .wrap{max-width:1080px;margin:0 auto;padding:0 20px}

  /* top bar */
  header{margin-bottom:18px}
  .app-shell{position:relative}
  .wrap.head{padding-top:14px;padding-bottom:12px;text-align:center}
  .logo{font-size:22px;font-weight:800;letter-spacing:.4px;display:flex;align-items:center;justify-content:center;gap:9px}
  .logo .mark{width:30px;height:30px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;
    background:linear-gradient(135deg,var(--green),var(--green-d));font-size:17px;box-shadow:var(--shadow-sm)}
  .logo .ai{color:var(--green)}
  .tag{color:var(--muted);font-size:13px;margin-top:2px;font-weight:500}

  .shield{display:inline-flex;align-items:center;gap:8px;margin-top:10px;
    background:rgba(22,199,132,.10);border:1px solid rgba(22,199,132,.35);color:#7fe3b8;
    padding:7px 14px;border-radius:999px;font-weight:600;font-size:13px}
  .shield .lock{font-size:15px}
  .mode{display:flex;justify-content:center;gap:8px;margin:12px 0 4px;flex-wrap:wrap}
  .mode button{font-size:14px;font-weight:700;padding:11px 22px;border-radius:11px;
    border:1px solid var(--line);background:var(--card);color:var(--muted);cursor:pointer;transition:.15s}
  .mode button:hover{border-color:var(--line2);color:var(--text)}
  .mode button.active-practice{background:rgba(22,199,132,.16);border-color:var(--green);color:#8fe9c2}
  .mode button.active-live{background:rgba(240,185,11,.12);border-color:var(--amber);color:#f5d479}

  /* cards */
  .card{background:linear-gradient(180deg,var(--card),var(--panel));border:1px solid var(--line);
    border-radius:var(--radius);padding:20px;margin:16px 0;box-shadow:var(--shadow-sm);transition:border-color .15s}
  .card:hover{border-color:var(--line2)}
  .card h2{margin:0 0 12px;font-size:17px;font-weight:700;letter-spacing:.2px;display:flex;align-items:center;gap:9px}
  .card p.help{color:var(--muted);font-size:13.5px;margin:0 0 14px}

  label{font-weight:600;font-size:13px;color:var(--muted);display:block;margin:14px 0 6px}
  input,select{width:100%;padding:11px 13px;border-radius:10px;border:1px solid var(--line2);
    background:var(--chip);color:var(--text);font-size:14px;outline:none;transition:.15s}
  input:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(77,141,255,.15)}
  .row{display:grid;grid-template-columns:1fr 1fr;gap:14px}

  .btn{display:inline-block;font-size:14px;font-weight:700;padding:12px 20px;border-radius:10px;border:none;
    background:linear-gradient(180deg,#1fcf8d,var(--green-d));color:#04130c;cursor:pointer;margin-top:12px;
    box-shadow:0 4px 14px rgba(22,199,132,.25);transition:.15s;width:100%}
  .btn:hover{filter:brightness(1.06)}
  .btn-blue{background:linear-gradient(180deg,#5b9bff,#3a76e0);color:#071224;box-shadow:0 4px 14px rgba(77,141,255,.25)}
  .btn-gray{background:var(--elev);color:var(--text);border:1px solid var(--line2);box-shadow:none}
  .btn-gray:hover{background:#223250}

  .big{font-size:26px;font-weight:800;font-variant-numeric:tabular-nums}
  .up{color:var(--green)} .down{color:var(--red)} .flat{color:var(--muted)}
  .metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}
  .metric{background:var(--card2);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
  .metric .k{color:var(--muted);font-size:11.5px;text-transform:uppercase;letter-spacing:.5px;font-weight:600}
  .metric .v{font-size:19px;font-weight:800;margin-top:3px;font-variant-numeric:tabular-nums}
  svg{width:100%;margin-top:12px;background:#0b1220;border:1px solid var(--line);border-radius:10px}
  .fine{color:var(--muted);font-size:12.5px;margin-top:6px}

  .chip{background:var(--chip);border:1px solid var(--line2);color:var(--text);border-radius:999px;
    padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;transition:.15s}
  .chip:hover{border-color:var(--accent);background:#13203a}
  .msg{border-radius:11px;padding:11px 15px;margin:9px 0;font-size:14px;line-height:1.5}
  .msg.you{background:rgba(77,141,255,.09);border:1px solid rgba(77,141,255,.28)}
  .msg.ai{background:rgba(22,199,132,.07);border:1px solid rgba(22,199,132,.28);white-space:pre-wrap}
  .regime-on,.regime-off{display:inline-block;margin-top:8px;padding:6px 13px;border-radius:999px;font-weight:700;font-size:12.5px}
  .regime-on{background:rgba(22,199,132,.13);border:1px solid rgba(22,199,132,.4);color:#7fe3b8}
  .regime-off{background:rgba(240,185,11,.13);border:1px solid rgba(240,185,11,.4);color:#f5d479}

  .modal{position:fixed;inset:0;background:rgba(4,8,15,.78);backdrop-filter:blur(3px);display:none;align-items:center;justify-content:center;z-index:60;padding:18px}
  .modal.show{display:flex}
  .modal .box{background:var(--card);border:1px solid var(--line2);border-radius:16px;max-width:560px;width:100%;padding:22px;max-height:88vh;overflow:auto;box-shadow:var(--shadow)}
  .pick{padding:12px 14px;margin:8px 0;border-radius:11px;background:var(--card2);border:1px solid var(--line);cursor:pointer}
  .pick:hover{border-color:var(--accent)} .pick.sel{border-color:var(--green)}
  .check li{list-style:none;margin:9px 0;display:flex;gap:9px;align-items:flex-start;font-size:14px}
  .check .tick{color:var(--green);font-weight:900}
  .check .must{background:rgba(240,185,11,.15);color:#f5d479;border-radius:6px;padding:0 7px;font-size:11.5px;font-weight:700;margin-left:6px}
  footer{text-align:center;color:var(--muted);font-size:12.5px;margin-top:34px}

  @media(max-width:820px){ .metrics{grid-template-columns:repeat(2,1fr)} .row{grid-template-columns:1fr} }
  /* Mobile / phone remote */
  @media(max-width:640px){
    body{font-size:14px;padding-bottom:90px} .wrap{padding:0 12px}
    .card{padding:16px;margin:12px 0}
    .logo{font-size:19px} .big{font-size:22px}
    .btn{font-size:16px;padding:15px 16px} .chip{font-size:14px;padding:10px 14px}
    input,select{font-size:16px;padding:13px} .metric .v{font-size:17px}
    .mode button{width:100%}
    #emergencyBtn{font-size:17px;padding:14px;position:sticky;bottom:10px;z-index:45;box-shadow:0 6px 22px rgba(234,57,67,.5)}
  }
  @media(max-width:380px){ .metrics{grid-template-columns:1fr} }

  /* ---- Sidebar layout ---- */
  .app-shell{display:grid;grid-template-columns:220px 1fr;gap:22px;align-items:start}
  .sidebar{position:sticky;top:12px;background:linear-gradient(180deg,var(--card),var(--panel));
    border:1px solid var(--line);border-radius:var(--radius);padding:16px 12px;display:flex;flex-direction:column;gap:4px;
    min-height:420px}
  .side-brand{font-size:16px;font-weight:800;padding:6px 8px 14px;display:flex;align-items:center;gap:8px}
  .logo-mark{width:28px;height:28px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;
    background:linear-gradient(135deg,var(--green),var(--green-d));font-size:15px}
  .navlink{display:flex;align-items:center;gap:10px;padding:11px 14px;border-radius:10px;color:var(--muted);
    cursor:pointer;font-weight:600;font-size:14px;text-decoration:none}
  .navlink:hover{background:var(--card2);color:var(--text)}
  .navlink.active{background:rgba(22,199,132,.15);color:#8fe9c2}
  .section{display:none} .section.show{display:block;animation:fade .18s ease}
  @keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
  @media(max-width:880px){
    .app-shell{grid-template-columns:1fr;gap:0}
    .sidebar{position:static;min-height:0;flex-direction:row;flex-wrap:wrap;gap:6px;padding:10px;margin-bottom:14px}
    .side-brand{width:100%} .sidebar #themeBtn{margin-top:0;margin-left:auto;width:auto}
  }

  /* ---- Light theme ---- */
  body.light{--bg:#eef2f8;--panel:#fff;--card:#fff;--card2:#f2f5fb;--elev:#e7ecf6;
    --line:#dbe2ee;--line2:#c7d1e3;--chip:#f6f8fc;--text:#14203a;--muted:#5b6a86;
    background:#eef2f8;text-shadow:none}
  body.light header{background:rgba(255,255,255,.85);border-bottom-color:#dbe2ee}
  body.light .modal{background:rgba(200,210,230,.7)}
  body.light .modal .box{background:#fff}
  body.light #candleChart,body.light #candleChartBig{background:#0b1220} /* keep chart dark */

  /* expandable bot rows */
  .botrow{cursor:pointer}
  .botdetail{display:none} .botdetail.open{display:block}

  .mobiletabs{display:none}
  @media(max-width:880px){
    .mobiletabs{display:flex;position:fixed;bottom:0;left:0;right:0;z-index:50;
      background:rgba(13,19,32,.94);backdrop-filter:blur(10px);border-top:1px solid var(--line);
      justify-content:space-around;padding:8px 6px calc(8px + env(safe-area-inset-bottom));}
    .mobiletabs a{flex:1;text-align:center;color:var(--muted);font-size:11px;font-weight:700;
      text-decoration:none;padding:6px 4px;border-radius:8px;cursor:pointer}
    .mobiletabs a span{display:block;font-size:20px;margin-bottom:2px}
    .mobiletabs a.active{color:#8fe9c2;background:rgba(22,199,132,.12)}
    body{padding-bottom:80px}
  }

  .monbar{grid-column:1/-1;display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
  .mon{background:var(--card2);border:1px solid var(--line);border-radius:10px;padding:8px 12px;display:flex;flex-direction:column;min-width:90px}
  .mon-k{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.5px}
  .mon b{font-size:16px;font-variant-numeric:tabular-nums}
  .mon-alert{flex:1;min-width:160px}
  .mon-alert span:last-child{font-weight:700;font-size:13px}
  @media(max-width:640px){.mon{min-width:0;flex:1}.mon b{font-size:14px}}
</style>
</head>
<body>
<div class="wrap">
<div class="app-shell">
  <div class="monbar" id="monBar">
    <div class="mon"><span class="mon-k">bots</span><b id="mon_bots">–</b></div>
    <div class="mon"><span class="mon-k">P/L</span><b id="mon_pnl">–</b></div>
    <div class="mon"><span class="mon-k">cash</span><b id="mon_cash">–</b></div>
    <div class="mon"><span class="mon-k">fills</span><b id="mon_fills">0</b></div>
    <div class="mon mon-alert" id="mon_alert"><span class="mon-k">status</span><span id="mon_status">idle</span></div>
  </div>
  <aside class="sidebar">
    <div class="side-brand"><span class="logo-mark">&#x1F4C8;</span> <b>Super&nbsp;<span style="color:var(--green)">AI</span>&nbsp;Trader</b></div>
    <nav>
      <a class="navlink active" data-nav="trade" onclick="showNav('trade')">&#x1F4C8; Trade</a>
      <a class="navlink" data-nav="bots" onclick="showNav('bots')">&#x1F916; Bots</a>
      <a class="navlink" data-nav="ai" onclick="showNav('ai')">&#x1F9E0; AI</a>
      <a class="navlink" data-nav="history" onclick="showNav('history')">&#x1F5C2;&#xFE0F; History</a>
      <a class="navlink" data-nav="settings" onclick="showNav('settings')">&#x2699;&#xFE0F; Settings</a>
    </nav>
    <button class="btn btn-gray" id="themeBtn" style="margin-top:auto" onclick="toggleTheme()">&#x1F317; Dark</button>
  </aside>
  <main class="content">

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
    <div class="logo"><span class="mark">&#x1F4C8;</span> Super <span class="ai">AI</span> Trader</div>
    <div class="tag">Buy low · Sell high · The safe way. Plain words, simple buttons.</div>
    <div class="shield"><span class="lock">🔒</span> Safety Shield ON — your keys stay on your computer, money cannot be withdrawn</div>
    <div id="startupNotice" style="display:none;margin-top:12px;border-radius:12px;padding:12px 16px;font-size:16px"></div>
    <button id="emergencyBtn" onclick="emergencyStop()"
      style="margin-top:14px;background:linear-gradient(180deg,#ff6b6b,#c0392b);color:white;
             border:none;border-radius:14px;padding:16px 26px;font-size:20px;font-weight:800;
             box-shadow:0 8px 20px rgba(0,0,0,.35);cursor:pointer;width:100%;max-width:560px">
      &#x1F6D1; EMERGENCY STOP &mdash; cancel ALL orders</button>
    <div id="emergencyNote" class="fine" style="margin-top:8px"></div>
    <div id="startupNotice" style="display:none;margin-top:12px;border-radius:12px;padding:12px 16px;font-size:16px"></div>
    <div id="healthBadge" style="margin-top:10px;display:inline-flex;align-items:center;gap:7px;font-size:13px;font-weight:700;padding:5px 12px;border-radius:999px;background:var(--card2);border:1px solid var(--line)">
      <span id="healthDot" style="width:9px;height:9px;border-radius:50%;background:var(--muted)"></span>
      <span id="healthText" class="fine">connecting…</span>
    </div>
    <div style="margin-top:12px">
      <label class="fine" for="langSel">&#x1F310; Language:</label>
      <select id="langSel" onchange="setLanguage(this.value)"
              style="width:auto;padding:8px 12px;font-size:15px;display:inline-block;margin-left:6px">
        <option value="en">English</option>
        <option value="th">ไทย</option>
        <option value="zh">中文</option>
        <option value="vi">Tiếng Việt</option>
        <option value="es">Español</option>
      </select>
    </div>
    <div style="margin-top:6px">
      <label class="fine" for="curSel">&#x1F4B1; Currency:</label>
      <select id="curSel" onchange="setCurrency(this.value)"
              style="width:auto;padding:6px 10px;font-size:14px;display:inline-block;margin-left:6px">
        <option value="USD">$ USD</option>
        <option value="THB">&#3647; THB</option>
        <option value="EUR">&euro; EUR</option>
        <option value="GBP">&pound; GBP</option>
        <option value="CNY">&yen; CNY</option>
      </select>
    </div>
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
  <div class="card section" data-section="ai">
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
  <div class="card section" data-section="trade">
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

  <!-- FIRST-RUN SETUP -->
  <div class="card section" data-section="trade" id="setupWizard" style="border-color:#ffc14d">
    <h2>&#x1F44B; First time here? 3 steps</h2>
    <p class="help">You are in safe PRACTICE mode. Tick these off as you go — this card hides itself when done.</p>
    <div id="wizardSteps" style="line-height:2">
      <div id="wiz_conn">&#x25CB; Tap <b>&#x1F50C; Test connection</b> on the Live Market card (needs live data).</div>
      <div id="wiz_demo">&#x25CB; Press <b>&#x25B6; Start a quick demo</b> to watch a practice BNB grid run.</div>
      <div id="wiz_grid">&#x25CB; Let it run a while, then check <b>&#x1F916; Multi-coin grids</b> &rarr; History for results.</div>
    </div>
    <button class="btn btn-gray" onclick="dismissWizard()" style="margin-top:10px">Done / hide this</button>
  </div>

  <!-- LIVE MARKET CHART -->
  <div class="card section" data-section="trade">
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
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <button class="btn btn-gray" style="width:auto;margin:0;padding:10px 16px" onclick="testConnection()">🔌 Test connection</button>
      <button class="btn btn-gray" style="width:auto;margin:0;padding:10px 16px" onclick="openChartModal()">⛶ Enlarge chart</button>
      <label class="fine" style="display:flex;gap:6px;align-items:center;margin-left:auto">
        <input type="checkbox" id="mk_grid_on" checked onchange="loadMarket()" style="width:auto"> grid
      </label>
    </div>
    <div id="connTests" style="margin:10px 0"></div>
    <div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin:6px 0">
      <div class="big" id="mk_price" style="font-size:30px;margin:0">–</div>
      <div class="fine" id="mk_pressure"></div>
    </div>
    <svg id="candleChart" viewBox="0 0 800 380" preserveAspectRatio="none"
         style="width:100%;height:380px;background:#0b111c;border:1px solid var(--line);border-radius:12px;margin-top:6px"></svg>
    <div class="fine" id="mk_legend" style="margin-top:6px"></div>
    <div class="fine" id="mk_ohlc" style="margin-top:2px;font-weight:700"></div>
  </div>

  <!-- ENLARGED CHART MODAL -->
  <div class="modal" id="chartModal">
    <div class="box" style="max-width:1000px">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
        <h2 id="cmTitle" style="margin:0">Chart</h2>
        <button class="btn btn-gray" style="width:auto;margin:0;padding:8px 14px" onclick="closeChartModal()">Close ✕</button>
      </div>
      <svg id="candleChartBig" viewBox="0 0 1000 560" preserveAspectRatio="none"
           style="width:100%;height:72vh;background:#0b111c;border:1px solid var(--line);border-radius:12px;margin-top:10px"></svg>
      <div class="fine" id="cm_legend"></div>
    </div>
  </div>

  <!-- STEP CARD -->
  <div class="card section" data-section="bots" id="setupCard">
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

  <!-- AI DAILY BRIEFING -->
  <div class="card section" data-section="trade" style="border-color:var(--green)">
    <h2>&#x1F4E3; AI briefing</h2>
    <div id="briefHeadline" style="font-size:18px;font-weight:800;margin-bottom:8px">&#8230;</div>
    <div id="briefLines" class="fine" style="font-size:14px;color:var(--text);line-height:1.7"></div>
    <div id="briefAlerts"></div>
    <div id="watchSummary" style="margin-top:10px"></div>
    <button class="btn btn-gray" style="width:auto;margin-top:10px" onclick="sendMorningBrief()">🌅 Email/message me this briefing</button>
    <label style="display:flex;gap:9px;align-items:center;margin-top:8px;color:var(--muted);font-weight:600">
      <input type="checkbox" id="morningAuto" style="width:auto" onchange="toggleMorningAuto()"> Auto-send this briefing once every morning (to email/Telegram)
    </label>
    <div id="morningStatus" class="fine"></div>
  </div>

  <!-- PORTFOLIO DASHBOARD -->
  <div class="card section" data-section="trade" id="portfolioCard">
    <h2>&#x1F4BC; Portfolio dashboard</h2>
    <p class="help">Total value of all your paper grids — cash + holdings. Like a real portfolio dashboard.</p>
    <div style="display:flex;gap:6px;margin:10px 0">
      <button class="chip pf-period" data-d="1" onclick="setPeriod(1)">1 day</button>
      <button class="chip pf-period active" data-d="7" onclick="setPeriod(7)">7 days</button>
      <button class="chip pf-period" data-d="30" onclick="setPeriod(30)">30 days</button>
      <button class="chip pf-period" data-d="0" onclick="setPeriod(0)">Total</button>
    </div>
    <div class="metrics" id="pfTiles" style="grid-template-columns:repeat(3,1fr)">
      <div class="metric"><div class="k">Total value</div><div class="v" id="pf_total">–</div></div>
      <div class="metric"><div class="k">P &amp; L (all)</div><div class="v" id="pf_pnl">–</div></div>
      <div class="metric"><div class="k">Cash (unallocated)</div><div class="v" id="pf_cash">–</div></div>
    </div>
    <div style="display:flex;gap:18px;flex-wrap:wrap;margin-top:14px;align-items:flex-start">
      <div>
        <div class="fine" style="margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px">Asset allocation</div>
        <svg id="pfDonut" viewBox="0 0 200 200" style="width:200px;height:200px;margin:0;background:transparent;border:none"></svg>
      </div>
      <div style="flex:2;min-width:240px">
        <div style="display:flex;gap:18px;flex-wrap:wrap">
          <div style="flex:1;min-width:150px">
            <div class="fine" style="text-transform:uppercase;letter-spacing:.5px">&#x1F7E2; Top winners</div>
            <div id="pf_winners" class="fine" style="color:var(--text)"></div>
          </div>
          <div style="flex:1;min-width:150px">
            <div class="fine" style="text-transform:uppercase;letter-spacing:.5px">&#x1F534; Biggest losers</div>
            <div id="pf_losers" class="fine" style="color:var(--text)"></div>
          </div>
        </div>
        <div id="pf_holdings" style="margin-top:10px"></div>
      </div>
    </div>
  </div>

  <!-- MULTI-COIN GRIDS -->
  <div class="card section" data-section="bots">
    <h2>&#x1F916; Multi-coin grids (practice money)</h2>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px">
      <button class="chip" onclick="setCoins('BTC,ETH,BNB')">Blue chips: BTC/ETH/BNB</button>
      <button class="chip" onclick="setCoins('BNB,SOL,ETH')">Momentum: BNB/SOL/ETH</button>
      <button class="chip" onclick="setCoins('BTC')">Single: BTC</button>
      <button class="chip" onclick="setCoins('SOL')">Single: SOL</button>
    </div>
    <div class="row">
      <div>
        <label>Exchange</label>
        <select id="mg_exchange" onchange="multiSummary()">
          <option value="binance">Binance</option>
          <option value="gateio">Gate.io</option>
          <option value="bybit">Bybit</option>
          <option value="okx">OKX</option>
          <option value="kucoin">KuCoin</option>
          <option value="kraken">Kraken</option>
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
    <div class="row">
      <div><label>Auto-stop if basket drops by % (0=off)</label>
        <input id="mg_dd" type="number" value="5"></div>
      <div class="fine" style="align-self:end">If total practice P/L falls this much, all grids stop automatically and you get an alert.</div>
    </div>
    <div class="row">
      <div><label>Max bots at once (1–12, keeps it light)</label>
        <input id="mg_maxbots" type="number" value="6" min="1" max="12"></div>
      <div><label>Total allowance across ALL bots (USDT, 0 = no extra cap)</label>
        <input id="mg_allowance" type="number" value="0"></div>
    </div>
    <div class="fine">The bot never runs more than 12 grids and never spends beyond the total allowance — per-bot amount is auto-reduced to stay inside it.</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0">
      <button class="chip" style="border-color:#29c484;color:#9af0cd" onclick="setStrategy('safe')">&#x1F6E1; Conservative</button>
      <button class="chip" style="border-color:#ffc14d;color:#ffe2a8" onclick="setStrategy('balanced')">&#x2696;&#xFE0F; Balanced</button>
      <button class="chip" style="border-color:#ff6b6b;color:#ffb3b3" onclick="setStrategy('aggressive')">&#x26A1; Aggressive</button>
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
    <div style="margin-top:14px;border-top:1px dashed var(--line);padding-top:12px">
      <label style="display:flex;gap:10px;align-items:center">
        <input type="checkbox" id="as_enabled" style="width:auto" onchange="autostartSave()">
        <b>&#x267B;&#xFE0F; Auto-start these grids when the app opens</b>
      </label>
      <div class="fine" style="margin-top:4px">Great for an always-on Mac: after a restart or power cut the bot starts in practice mode by itself (safety still applies).</div>
      <div id="as_status" class="fine"></div>
    </div>
    <div id="mg_daily" class="fine" style="margin-top:6px"></div>
    <div id="mg_summary" class="metrics" style="margin-top:14px"></div>
    <div id="mg_rows" style="margin-top:12px"></div>
    <div id="mg_events" style="margin-top:10px"></div>
  </div>

  <!-- DCA RECURRING BUYS -->
  <div class="card section" data-section="bots">
    <h2>&#x1F4B0; Recurring buys (DCA) &mdash; practice money</h2>
    <p class="help">Buy a fixed amount on a schedule (e.g. $25 of BTC every day). The most popular beginner/passive strategy &mdash; it averages your cost over time.</p>
    <div class="row">
      <div><label>Coins</label><input id="dca_coins" value="BTC,ETH"></div>
      <div><label>Buy each (USDT)</label><input id="dca_usd" type="number" value="25"></div>
    </div>
    <div class="row">
      <div><label>Every (hours) &mdash; use small value for demo</label><input id="dca_interval" type="number" value="24"></div>
      <div><label>Max buys (0 = until stopped)</label><input id="dca_max" type="number" value="0"></div>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap">
      <button class="btn" style="width:auto" onclick="dcaStart()">&#x25B6;&#xFE0F; Start recurring buys</button>
      <button class="btn btn-gray" style="width:auto" onclick="dcaStop('all')">Stop all</button>
      <button class="btn btn-gray" style="width:auto" onclick="dcaRefresh()">Refresh</button>
    </div>
    <div id="dca_rows" class="fine" style="margin-top:10px"></div>
  </div>

  <!-- LIVE TRADING PANEL -->
  <div class="card section" data-section="bots">
    <h2>📡 Live — watch the robot trade real prices</h2>
    <p class="help">Connects to the real exchange price (Binance / Gate.io). In <b>practice</b> mode it
      uses practice money and sends <b>no real orders</b> — but every number is live. Use Preview first
      to see the past result, then Start to watch it live.</p>
    <div class="row">
      <div><label>Exchange</label>
        <select id="lv_ex"><option value="binance">Binance</option><option value="gateio">Gate.io</option><option value="bybit">Bybit</option><option value="okx">OKX</option><option value="kucoin">KuCoin</option><option value="kraken">Kraken</option></select>
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
  <div class="card section" data-section="bots" id="resultCard" style="display:none">
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
  <div class="card section" data-section="ai">
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
      <button class="btn btn-gray" onclick="liveBalances()" style="border-color:#4aa3ff;color:#cfe6ff">&#x1F4B3; Check my exchange balance (read-only)</button>
      <div id="lg_bal" class="fine"></div>
      <button class="btn btn-gray" onclick="liveOrders()" style="border-color:#4aa3ff;color:#cfe6ff">&#x1F4CB; View open orders on exchange (read-only)</button>
      <div id="lg_orders" class="fine"></div>
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
  <div class="card section" data-section="settings">
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
  <div class="card section" data-section="history">
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
    <a class="btn btn-gray" style="margin-top:12px;text-align:center;text-decoration:none"
       href="/api/export.csv" download>&#x2B07;&#xFE0F; Download history as CSV</a>
    <div id="jh_list" style="margin-top:12px"></div>
  </div>

  <!-- SAFETY -->
  <div class="card section" data-section="settings">
    <h2>🛡️ How we keep you safe</h2>
    <p class="help">Every box here is built into the app.</p>
    <ul class="check" id="checklist" style="padding:0"></ul>
    <div class="warn" id="liveWarn"></div>
  </div>

  <!-- CONNECT (hidden until live mode) -->
  <div class="card section" data-section="settings" id="connectCard" style="display:none">
    <h2>🔗 Connect an exchange (optional)</h2>
    <p class="help">Only needed for real trading. <b>Create a TRADE-ONLY key on the exchange and
      turn WITHDRAWALS OFF.</b> Your key is encrypted on this computer and never shown again.</p>
    <label>Exchange</label>
    <select id="ex"><option value="binance">Binance</option>
      <option value="gateio">Gate.io</option>
      <option value="bybit">Bybit</option>
      <option value="okx">OKX</option>
      <option value="kucoin">KuCoin</option>
      <option value="kraken">Kraken</option></select>
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

  </main>
</div>
<!-- MOBILE BOTTOM TAB BAR -->
<nav class="mobiletabs">
  <a onclick="mobileTab('trade')"><span>&#x1F4C8;</span>Dashboard</a>
  <a onclick="mobileTab('bots')"><span>&#x1F50D;</span>Watchlist</a>
  <a onclick="mobileTab('history')"><span>&#x1F4CB;</span>Reports</a>
</nav>
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
  const realized=b.realized_pnl!==undefined?b.realized_pnl:(b.grid_profit||0);
  const unreal=b.unrealized!==undefined?b.unreal:0;
  const infoEl=document.getElementById('b_info');
  if(infoEl){
    infoEl.innerHTML =
      `<div style="margin-bottom:6px">`+
      `<b class="${realized>=0?'up':'down'}">Realized (completed trades): ${realized>=0?'+':''}${fmt(realized)}</b> &nbsp;·&nbsp; `+
      `<span class="${unreal>=0?'up':'down'}">Unrealized (holding value): ${unreal>=0?'+':''}${fmt(unreal)}</span></div>`;
  }
  if(infoEl){
    infoEl.innerHTML +=
      `<div class="fine">${b.symbol} · ${b.mode} · ${b.grids} grids · range ${b.lower}–${b.upper} · fees ${fmt(b.fees)}${src} · `+
      (b.stopped?'safety stop triggered':'still running safely')+`</div>`;
  }
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
  if(svg) svg.innerHTML=html;
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
autostartLoad().then(autostartApply);
showNav('trade');
loadBriefing();
loadWatcher();
loadPortfolio();
loadCurrency();
healthCheck();
liveMonitor();
(async()=>{try{const r=await post('/api/morning/status',{});const cb=document.getElementById('morningAuto');if(cb)cb.checked=!!r.enabled;}catch(e){}})();
const _savedLang=localStorage.getItem('lang')||'en'; loadLanguage(_savedLang).then(()=>{const ls=document.getElementById('langSel'); if(ls) ls.value=_savedLang;});
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
  // big candlestick view
  try{
    const cd=await post('/api/candles',{exchange:m._exchange||'binance',
      ticker:document.getElementById('mk_coin').value,
      timeframe:document.getElementById('mk_tf').value, limit:160,
      show_grid:document.getElementById('mk_grid_on')?document.getElementById('mk_grid_on').checked:true,
      range_pct: parseFloat(document.getElementById('range_pct')?document.getElementById('range_pct').value||12:12)});
    cd._exchange = body.exchange; _chartData=cd;
    renderCandles('candleChart', cd, false);
    document.getElementById('mk_legend').innerHTML =
      '<span style="color:#ffd54a">&#x25CF; EMA7</span> &nbsp;<span style="color:#ff4dd2">&#x25CF; EMA25</span> &nbsp;<span style="color:#b48cff">&#x25CF; EMA99</span> &nbsp;<span class="up">&#x25CF; buy grid</span> &nbsp;<span style="color:#ff6b6b">&#x25CF; sell grid</span> &middot; '+cd.source;
  }catch(e){}
  document.getElementById('mk_pressure').textContent = m.pressure
    ? `Live humans: ${m.pressure} · ${Math.round((m.buy_ratio||0.5)*100)}% buying vs ${Math.round((m.sell_ratio||0.5)*100)}% selling`
    : '';
}
function drawMarket(m){
  const svg=document.getElementById('marketChart'); if(svg) svg.innerHTML='';
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
  if(svg) svg.innerHTML=html;
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
    grids:parseInt(document.getElementById('mg_grids').value||25),
    max_drawdown_pct: -Math.abs(parseFloat(document.getElementById('mg_dd').value||0)),
    max_bots: parseInt(document.getElementById('mg_maxbots').value||6),
    max_allowance: parseFloat(document.getElementById('mg_allowance').value||0)||null
  });
  msg.style.color = r.ok ? '#9af0cd':'#ffc7c7';
  const ok=(r.started||[]).filter(x=>x.ok).length;
  const bad=(r.started||[]).filter(x=>!x.ok);
  const capNote = (r.note?('<br><span class="fine">'+r.note+' · per-bot '+fmt(r.per_bot||0)+'</span>'):'');
  msg.innerHTML = r.ok ? ('&#x2705; Started '+ok+' grid(s) '+capNote+
      (bad.length?('<br>failed: '+bad.map(b=>b.coin+' ('+b.error.slice(0,40)+')').join(', ')):''))
    : ('&#x26A0;&#xFE0F; Could not start grids. Install ccxt and check internet, then Test connection.');
  if(r.ok){ multiRefresh(); multiSummary(); loadBriefing(); localStorage.setItem('wiz_demo','1'); localStorage.setItem('wiz_grid','1'); refreshWizard(); }
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
    const tone=(c.status_note&&c.status_note.tone)||'muted';
    const toneColor = tone==='green'?'var(--green)':tone==='amber'?'#ffd54a':tone==='red'?'var(--red)':'var(--muted)';
    const reg = c.paused ? '<span style="color:#ffd54a">&#x23F8; paused</span>' : '<span class="up">&#x2705; on</span>';
    const note = c.status_note ? `<span style="color:${toneColor}"> &#x2014; ${c.status_note.label}</span>` : '';
    const spark = sparklineSvg(c.equity_curve||[], roi);
    const fills = (c.recent_fills||[]).slice().reverse().slice(0,6).map(f=>{
      const col=f.side==='buy'?'var(--green)':'var(--red)';
      const t=f.ts?new Date(f.ts*1000).toLocaleTimeString():'';
      return `<div style="color:${col};font-size:13px">${t} ${f.side} ${f.amount} @ ${f.price}</div>`;
    }).join('') || '<div class="fine">no fills yet</div>';
    return `<div class='botrow' style="padding:12px;margin:8px 0;border-radius:12px;background:var(--card2);border:1px solid var(--line)">
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <b style="font-size:18px">${c.coin}</b>
        <span class="fine">price</span> <b>${c.price}</b>
        <div style="display:flex;gap:14px;margin-left:auto;flex-wrap:wrap">
          <span class="fine">P/L&nbsp;<b class="${roi>=0?'up':'down'}" style="font-size:16px">${roi>=0?'+':''}${roi}%</b></span>
          <span class="fine">buys&nbsp;<b style="color:var(--green)">${c.buys||0}</b></span>
          <span class="fine">sells&nbsp;<b style="color:var(--red)">${c.sells||0}</b></span>
          <span>${reg}${note}</span>
        </div>
      </div>
      ${c.instruction?`<div style="margin-top:8px;padding:8px 10px;border-radius:8px;background:${c.instruction.tone==='amber'?'rgba(240,185,11,.1)':c.instruction.tone==='green'?'rgba(22,199,132,.09)':'#0e1626'};border:1px solid ${c.instruction.tone==='amber'?'rgba(240,185,11,.3)':'rgba(22,199,132,.25)'}">
        <b>&#x1F916; AI instruction [${c.instruction.action}]</b> &mdash; ${c.instruction.headline} <span class="fine">(auto-trading in paper; fills ${(c.buys||0)+(c.sells||0)})</span>
        ${c.instruction.next_buy?`<div class="fine">&#x1F4B9; next BUY LOW ~ <span class="up">${c.instruction.next_buy}</span> &middot; next SELL HIGH ~ <span style="color:var(--red)">${c.instruction.next_sell}</span></div>`:''}
      </div>`:''}
      <div style="display:flex;gap:12px;margin-top:8px;flex-wrap:wrap">
        <div style="flex:2;min-width:220px"><div class="fine">Equity</div>${spark}</div>
        <div style="flex:1;min-width:180px"><div class="fine">Recent fills (live)</div>${fills}</div>
      </div>
      <div class="fine" style="margin-top:6px"><b>&#x25B8; details</b> — ${(c.events||[]).slice(-2).map(e=>e.text).join(' · ')||'no alerts'}</div>
        <div class='botdetail' style="margin-top:8px;padding-top:8px;border-top:1px dashed var(--line)">
          ${(c.events||[]).slice().reverse().map(e=>`<div class='fine'>${new Date((e.ts||0)*1000).toLocaleTimeString()} · ${e.text}</div>`).join('')}
        </div>
    </div>`;
  }).join('') || '<div class="fine">No grids running. Press Start.</div>';
  // global alert toasts
  (r.coins||[]).forEach(c=>(c.events||[]).forEach(e=>{
    const key=c.coin+'|'+e.ts+'|'+e.text;
    if(!_mgSeen.has(key)){ _mgSeen.add(key); toast(c.coin+': '+e.text, e.color); }
  }));
}
setInterval(()=>{ try{
  if(document.getElementById('mg_rows')){ multiRefresh(); multiSummary(); checkDrawdown(); }
}catch(e){} }, 6000);
async function checkDrawdown(){
  const r=await post('/api/multigrid/drawdown',{exchange:mgEx()});
  if(r && r.tripped){
    toast('AUTO STOP: '+r.reason,'red');
    const el=document.getElementById('mg_msg');
    if(el){ el.style.color='#ffb3b3'; el.textContent='🛑 '+r.reason; }
    multiRefresh(); multiSummary();
  }
}

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
  const dp=r.daily_pnl||0;
  document.getElementById('mg_summary').innerHTML = `
    <div class="metric"><div class="k">Grids running</div><div class="v">${r.count||0}</div></div>
    <div class="metric"><div class="k">Today P/L</div><div class="v"><span class="${dp>=0?'up':'down'}">${dp>=0?'+':''}${fmt(dp)}</span> <span style="font-size:14px">(${r.daily_pnl_pct||0}%)</span></div></div>
    <div class="metric"><div class="k">Total P/L</div><div class="v"><span class="${pnl>=0?'up':'down'}">${pnl>=0?'+':''}${fmt(pnl)}</span> <span style="font-size:14px">(${r.total_pnl_pct||0}%)</span></div></div>
    <div class="metric"><div class="k">Round-trips / Paused</div><div class="v">${r.total_round_trips||0} · ${(r.paused_coins||[]).length}</div></div>`;
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
  if(r.ai_tuned){
    const tuned=Object.entries(r.ai_tuned).filter(([c,v])=>v.tuned)
      .map(([c,v])=>c+': '+v.note).join('; ');
    if(tuned){ el.innerHTML+='<br><span class="up">&#x1F9E0; Using AI-tuned exits:</span> '+tuned; }
  }
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


async function liveBalances(){
  const el=document.getElementById('lg_bal');
  el.style.color='#ffe2a8'; el.textContent='Reading balances (no orders placed)…';
  const r=await post('/api/live/balances',{
    name:document.getElementById('lg_name').value,
    password:document.getElementById('lg_pw').value,
    exchange:document.getElementById('ex')?document.getElementById('ex').value:'binance',
    coins:document.getElementById('lg_coins').value});
  if(!r.ok){ el.style.color='#ffc7c7'; el.textContent='&#x26A0;&#xFE0F; '+r.error; return; }
  el.style.color='#9af0cd';
  const rows=Object.entries(r.balances||{}).filter(([k])=>!k.startsWith('_'))
    .map(([k,v])=>k+': '+(v.free!=null?('free '+v.free):('total '+(v.total||0)))).join(' &middot; ');
  el.innerHTML='&#x2713; Available on '+r.exchange+': '+rows;
}

async function liveOrders(){
  const el=document.getElementById('lg_orders');
  el.style.color='#ffe2a8'; el.textContent='Reading resting orders…';
  const r=await post('/api/live/open-orders',{
    name:document.getElementById('lg_name').value,
    password:document.getElementById('lg_pw').value,
    exchange:document.getElementById('ex')?document.getElementById('ex').value:'binance',
    coin:(document.getElementById('lg_coins').value||'BNB').split(',')[0].trim()});
  if(!r.ok){ el.style.color='#ffc7c7'; el.textContent='&#x26A0;&#xFE0F; '+r.error; return; }
  const rows=(r.orders||[]).map(o=>`<div style="color:${o.side==='buy'?'var(--green)':'var(--red)'}">${o.side} ${o.amount||''} @ ${o.price||''} ${o.symbol||r.symbol}</div>`).join('');
  el.style.color='#9af0cd';
  el.innerHTML='Open orders ('+r.count+') on '+r.exchange+': '+
    (r.count? ('<div style="margin-top:4px">'+rows+'</div>') : '<span class="fine"> none for '+r.symbol+'</span>');
}

let _liveOrdersTimer=null;
async function maybeLiveOrders(){
  // Only auto-refresh if the user has a vault password present (likely armed).
  const pw=document.getElementById('lg_pw').value;
  if(!pw) return; // no key yet -> don't spam
  try{ await liveOrdersSilent(); }catch(e){}
}
async function liveOrdersSilent(){
  const r=await post('/api/live/open-orders',{
    name:document.getElementById('lg_name').value,
    password:document.getElementById('lg_pw').value,
    exchange:document.getElementById('ex')?document.getElementById('ex').value:'binance',
    coin:(document.getElementById('lg_coins').value||'BNB').split(',')[0].trim()});
  if(!r.ok) return;
  const el=document.getElementById('lg_orders');
  if(!el) return;
  const rows=(r.orders||[]).map(o=>`<div style="color:${o.side==='buy'?'var(--green)':'var(--red)'}">${o.side} ${o.amount||''} @ ${o.price||''} ${o.symbol||r.symbol}</div>`).join('');
  el.style.color='#9af0cd';
  el.innerHTML='Open orders ('+r.count+') on '+r.exchange+': '+
    (r.count? ('<div style="margin-top:4px">'+rows+'</div>') : '<span class="fine"> none for '+r.symbol+'</span>');
}
function startLiveOrdersTimer(){
  if(_liveOrdersTimer) return;
  _liveOrdersTimer=setInterval(maybeLiveOrders, 15000);
}
// ensure the timer exists after arming
const _origArm=liveGridArm;
liveGridArm=async function(){ await _origArm(); startLiveOrdersTimer(); };


async function emergencyStop(){
  if(!confirm('EMERGENCY STOP: stop every paper grid and cancel ALL orders. Proceed?')) return;
  const btn=document.getElementById('emergencyBtn'); btn.disabled=true; btn.textContent='Stopping…';
  const r=await post('/api/emergency-stop',{
    name:(document.getElementById('rl_name')||{}).value?document.getElementById('rl_name').value:'',
    password:(document.getElementById('rl_pw')||{}).value?document.getElementById('rl_pw').value:'',
    coins:(document.getElementById('lg_coins')||{}).value?document.getElementById('lg_coins').value:''});
  btn.disabled=false;
  btn.innerHTML='&#x1F6D1; EMERGENCY STOP &mdash; cancel ALL orders';
  const note=document.getElementById('emergencyNote');
  note.style.color='#9af0cd';
  note.textContent='✅ All paper grids stopped'+(r.live?('; cancelled '+r.live.cancelled+' real orders on '+r.live.exchange):' (real orders only if a vault password was entered).');
  toast('EMERGENCY STOP done — all orders cancelled','red');
}

function setCoins(list){
  const el=document.getElementById('mg_coins');
  if(el){ el.value=list; el.scrollIntoView({behavior:'smooth',block:'center'}); }
}

async function autostartLoad(){
  try{ const r=await post('/api/autostart/get',{});
    document.getElementById('as_enabled').checked=!!r.autostart_enabled;
    if(r.autostart_coins) document.getElementById('mg_coins').value=r.autostart_coins;
  }catch(e){}
}
async function autostartSave(){
  await post('/api/autostart/set',{
    autostart_enabled: document.getElementById('as_enabled').checked,
    autostart_coins: document.getElementById('mg_coins').value,
    autostart_exchange: mgEx(),
    autostart_investment: parseFloat(document.getElementById('mg_inv').value||1000),
    autostart_range: parseFloat(document.getElementById('mg_range').value||12),
    autostart_grid_count: parseInt(document.getElementById('mg_grids').value||25)
  });
}
async function autostartApply(){
  try{
    const r=await post('/api/autostart/apply',{});
    if(r.started && r.count!==0){
      toast('Auto-started '+r.count+' practice grids','green');
      multiRefresh(); multiSummary();
    }
  }catch(e){}
}

function markWiz(id, ok){
  const el=document.getElementById('wiz_'+id);
  if(!el) return;
  el.innerHTML = (ok?'<span class="up">&#x2705;</span>':'<span class="flat">&#x25CB;</span>') + ' ' +
    el.innerHTML.replace(/^[^<]*/,'');
  if(ok){
    el.style.opacity=0.65;
    if(!localStorage.getItem('wiz_'+id)) localStorage.setItem('wiz_'+id,'1');
  }
}
function refreshWizard(){
  ['conn','demo','grid'].forEach(id=>markWiz(id, !!localStorage.getItem('wiz_'+id)));
  const doneCount=['conn','demo','grid'].filter(id=>localStorage.getItem('wiz_'+id)).length;
  const card=document.getElementById('setupWizard');
  if(card && (localStorage.getItem('wiz_dismissed')||doneCount>=3)) card.style.display='none';
}
function dismissWizard(){
  localStorage.setItem('wiz_dismissed','1');
  const card=document.getElementById('setupWizard'); if(card) card.style.display='none';
}
// mark demo/grid when relevant flows succeed
const _origMultiStart=(typeof multiStart==='function')?multiStart:null;
window.addEventListener('DOMContentLoaded',refreshWizard);
refreshWizard();

// ---- Professional candlestick chart ----
function renderCandles(elId, m, big){
  const svg=document.getElementById(elId); if(!svg||!m||!m.candles) return;
  svg._m=m;
  const W=big?1000:800, H=big?560:380, padL=8,padR=62,padT=14,padB=22;
  const candles=m.candles;
  let lo=Infinity, hi=-Infinity;
  candles.forEach(k=>{ lo=Math.min(lo,k.l); hi=Math.max(hi,k.h); });
  (m.grid? m.grid.buy_levels.concat(m.grid.sell_levels):[]).forEach(v=>{lo=Math.min(lo,v);hi=Math.max(hi,v);});
  const span=(hi-lo)||1; lo-=span*0.03; hi+=span*0.03;
  const Y=v=>padT+(hi-v)/(hi-lo)*(H-padT-padB);
  const cw=(W-padL-padR)/candles.length;
  let h='';
  // grid lines (price scale)
  for(let g=0; g<=4; g++){ const pv=lo+(span*1.06)*(g/4); const y=Y(pv);
    h+=`<line x1="${padL}" y1="${y}" x2="${W-padR}" y2="${y}" stroke="#1c2839" stroke-width="1"/>`;
    h+=`<text x="${W-padR+4}" y="${y+3}" fill="#9fb0c7" font-size="11">${pv.toFixed(pv>1000?0:2)}</text>`; }
  // robot buy/sell grid ladders
  if(m.grid){
    m.grid.buy_levels.forEach(v=>{ const y=Y(v);
      h+=`<line x1="${padL}" y1="${y}" x2="${W-padR}" y2="${y}" stroke="#29c484" stroke-width="1" opacity="0.35"/>`; });
    m.grid.sell_levels.forEach(v=>{ const y=Y(v);
      h+=`<line x1="${padL}" y1="${y}" x2="${W-padR}" y2="${y}" stroke="#ff6b6b" stroke-width="1" opacity="0.35"/>`; });
  }
  // candles
  candles.forEach((k,i)=>{
    const up=k.c>=k.o, col=up?'#26c281':'#ef5350';
    const x=padL+i*cw, bw=Math.max(1.5,cw*0.6), cx=x+cw/2;
    h+=`<line x1="${cx}" y1="${Y(k.h)}" x2="${cx}" y2="${Y(k.l)}" stroke="${col}" stroke-width="1"/>`;
    const yO=Y(k.o), yC=Y(k.c);
    h+=`<rect x="${cx-bw/2}" y="${Math.min(yO,yC)}" width="${bw}" height="${Math.max(1,Math.abs(yC-yO))}" fill="${col}"/>`;
  });
  // volume bars (bottom strip)
  let vmax=0; candles.forEach(k=>{vmax=Math.max(vmax,k.v||0);});
  if(vmax>0){ const vh=(H-padB)*0.18, vbase=H-padB;
    candles.forEach((k,i)=>{ const x=padL+i*cw, bw=Math.max(1.5,cw*0.6);
      const up=k.c>=k.o; const hgt=(k.v/vmax)*vh;
      h+=`<rect x="${x+cw/2-bw/2}" y="${vbase-hgt}" width="${bw}" height="${hgt}" fill="${up?'#26c281':'#ef5350'}" opacity="0.28"/>`; });
  }
  // EMAs
  function ema(arr,col,w){
    let p=''; let started=false;
    arr.forEach((v,i)=>{ if(v==null) return; const x=padL+(i+0.5)*cw, y=Y(v);
      if(!started){p+=`M ${x} ${y}`;started=true;} else p+=` L ${x} ${y}`; });
    h+=`<path d="${p}" fill="none" stroke="${col}" stroke-width="${w}" opacity="0.9"/>`;
  }
  if(m.ema7) ema(m.ema7,'#ffd54a',1.6);
  if(m.ema25) ema(m.ema25,'#ff4dd2',1.4);
  if(m.ema99) ema(m.ema99,'#b48cff',1.4);
  // last price line
  if(m.last){ const y=Y(m.last);
    h+=`<line x1="${padL}" y1="${y}" x2="${W-padR}" y2="${y}" stroke="#7fd3ff" stroke-width="1" stroke-dasharray="4 3"/>`;
    // price label
    h+=`<rect x="${W-padR+2}" y="${y-9}" width="${padR-4}" height="18" rx="3" fill="#7fd3ff" opacity="0.18"/>`;
  }
  // AI next BUY-LOW / SELL-HIGH markers
  if(m.next_buy!=null){ const y=Y(m.next_buy);
    h+=`<line x1="${padL}" y1="${y}" x2="${W-padR}" y2="${y}" stroke="#29c484" stroke-width="1.6" stroke-dasharray="8 4"/>`;
    h+=`<polygon points="${W-padR-16},${y-6} ${W-padR-4},${y} ${W-padR-16},${y+6}" fill="#29c484"/>`;
    h+=`<text x="${padL+6}" y="${y-6}" fill="#8fe9c2" font-size="12" font-weight="700">BUY LOW ${m.next_buy}</text>`;
  }
  if(m.next_sell!=null){ const y=Y(m.next_sell);
    h+=`<line x1="${padL}" y1="${y}" x2="${W-padR}" y2="${y}" stroke="#ff6b6b" stroke-width="1.6" stroke-dasharray="8 4"/>`;
    h+=`<polygon points="${W-padR-16},${y-6} ${W-padR-4},${y} ${W-padR-16},${y+6}" fill="#ff6b6b"/>`;
    h+=`<text x="${padL+6}" y="${y+14}" fill="#ff9b9b" font-size="12" font-weight="700">SELL HIGH ${m.next_sell}</text>`;
  }
  svg.innerHTML=h;
}
let _chartData=null;
function openChartModal(){
  const c=document.getElementById('chartModal'); c.classList.add('show');
  document.getElementById('cmTitle').textContent=(_chartData?(_chartData.symbol+' '):'Chart')+(_chartData?(_chartData.source+' '+_chartData.timeframe):'');
  if(_chartData){ renderCandles('candleChartBig', _chartData, true);
    document.getElementById('cm_legend').textContent =
      (document.getElementById('mk_legend')?document.getElementById('mk_legend').textContent:''); }
}
function closeChartModal(){ document.getElementById('chartModal').classList.remove('show'); }

function sparklineSvg(vals, roi){
  if(!vals || vals.length<2) return '<span class="fine">waiting for data…</span>';
  const w=320,h=64,min=Math.min(...vals),max=Math.max(...vals),rng=(max-min)||1;
  const X=i=4+i*(w-12)/(vals.length-1), Y=v=4+(max-v)/rng*(h-12);
  let d=''; vals.forEach((v,i)=>{d+=(i?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1);});
  const col=roi>=0?'#26c281':'#ef5350';
  let area=d+` L ${X(vals.length-1).toFixed(1)} ${h} L 4 ${h} Z`;
  return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" style="width:100%;height:64px">
    <path d="${area}" fill="${col}" opacity="0.12"/>
    <path d="${d}" fill="none" stroke="${col}" stroke-width="2"/>
  </svg>`;
}

function setStrategy(kind){
  // range%, grid lines, drawdown%
  const map={safe:{range:8, grids:35, dd:3}, balanced:{range:12, grids:25, dd:5}, aggressive:{range:20, grids:18, dd:8}};
  const m=map[kind]||map.balanced;
  document.getElementById('mg_range').value=m.range;
  document.getElementById('mg_grids').value=m.grids;
  document.getElementById('mg_dd').value=m.dd;
  toast('Strategy: '+kind+' (range '+m.range+'%, grids '+m.grids+', auto-stop -'+m.dd+'%)',
        kind==='aggressive'?'red':'green');
}

// Candle crosshair + OHLC hover
function attachCandleCrosshair(big){
  const svg=document.getElementById(big?'candleChartBig':'candleChart');
  if(!svg||svg._cross) return; svg._cross=true;
  svg.addEventListener('mousemove',(ev)=>{
    const r=svg.getBoundingClientRect();
    const Wbig=svg.id==='candleChartBig'?1000:800;
    const padRbig=svg.id==='candleChartBig'?62:62;
    const x=(ev.clientX-r.left)/r.width*Wbig;
    const m=svg._m; if(!m||!m.candles) return;
    const padL=8,padR=62;
    const cw=(Wbig-padL-padR)/m.candles.length;
    const idx=Math.round((x-padL)/cw-0.5);
    const k=m.candles[Math.max(0,Math.min(m.candles.length-1,idx))];
    let info=document.getElementById(big?'cm_legend':'mk_ohlc');
    if(info) info.innerHTML='<b>OHLC</b> O '+k.o+'  H '+k.h+'  L '+k.l+'  C '+k.c;
  });
}
setTimeout(()=>{ attachCandleCrosshair(false); attachCandleCrosshair(true); },1500);

let _labels={};
function tr(k){ return _labels[k]||k; }
async function loadLanguage(lang){
  const r=await post('/api/language/set',{lang:lang||'en'});
  if(r && r.labels){ _labels=r.labels; applyLanguage(); }
}
async function setLanguage(lang){
  await loadLanguage(lang); localStorage.setItem('lang',lang);
}
function applyLanguage(){
  // static labeled elements
  const map=[
    ['practice','modePractice'],
    ['connect','modeLive']
  ];
  // dynamic labels used across feeds are looked up via tr() at render time;
  // re-run refreshers so the new labels appear.
  try{ multiRefresh(); multiSummary(); }catch(e){}
  const es=document.getElementById('emergencyBtn');
  if(es && tr('emergency')) es.innerHTML='&#x1F6D1; '+tr('emergency');
}
function _currentLang(){ return document.getElementById('langSel')?document.getElementById('langSel').value:'en'; }

function showNav(name){
  document.querySelectorAll('.navlink').forEach(a=>a.classList.toggle('active',a.dataset.nav===name));
  document.querySelectorAll('.section').forEach(el=>{
    el.classList.toggle('show', el.dataset.section===name);
  });
  if(name==='history' && typeof loadHistory==='function') loadHistory();
  window.scrollTo({top:0,behavior:'smooth'});
}
function toggleTheme(){
  document.body.classList.toggle('light');
  const light=document.body.classList.contains('light');
  localStorage.setItem('theme', light?'light':'dark');
  const b=document.getElementById('themeBtn'); if(b) b.innerHTML=light? '&#x2600;&#xFE0F; Light':'&#x1F317; Dark';
}
(function initTheme(){
  if(localStorage.getItem('theme')==='light') document.body.classList.add('light');
})();
// expand/collapse bot detail
document.addEventListener('click',(e)=>{
  const row=e.target.closest('.botrow');
  if(!row) return;
  const d=row.querySelector('.botdetail');
  if(d) d.classList.toggle('open');
});

async function dcaStart(){
  const r=await post('/api/dca/start',{
    coins:document.getElementById('dca_coins').value,
    usd:parseFloat(document.getElementById('dca_usd').value||25),
    interval_hours:parseFloat(document.getElementById('dca_interval').value||24),
    max_buys:parseInt(document.getElementById('dca_max').value||0)});
  toast('DCA started for '+(r.started||[]).filter(x=>x.ok).length+' coin(s)','green');
  dcaRefresh();
}
async function dcaRefresh(){
  let r; try{ r=await apiGet('/api/dca/status'); }catch(e){ return; }
  const rows=(r.plans||[]).map(p=>{
    const pnl=p.pnl||0;
    return `<div style="padding:10px 12px;margin:6px 0;border-radius:10px;background:var(--card2);border:1px solid var(--line)">
      <b>${p.coin}</b> &nbsp; ${p.buys_done} buys &nbsp; spent ${p.total_spent} &nbsp; held ${p.base_acquired}
      <span class="${pnl>=0?'up':'down'}" style="float:right">${pnl>=0?'+':''}${pnl}</span>
      <div class="fine">avg entry ${p.avg_entry} · current value ${p.current_value} · ${p.running?'running':'stopped'}
        <a class="tab" onclick="dcaStop('${p.coin}')">stop</a></div></div>`;
  }).join('') || '<div class="fine">No recurring buys yet.</div>';
  const el=document.getElementById('dca_rows'); if(el) el.innerHTML=rows;
}
async function dcaStop(coin){ await post('/api/dca/stop',{coin:coin||'all'}); dcaRefresh(); }
setInterval(()=>{ try{ if(document.getElementById('dca_rows')) dcaRefresh(); }catch(e){} }, 12000);

async function loadBriefing(){
  try{
    const r=await post('/api/briefing',{exchange:mgEx(),lang:(localStorage.getItem('lang')||'en')});
    const h=document.getElementById('briefHeadline');
    if(!h) return;
    const pos=(r.total_pnl||0)>=0?'up':'down';
    h.innerHTML=`<span class="${pos==='up'?'up':'down'}">${r.headline||''}</span>`;
    document.getElementById('briefLines').innerHTML =
      (r.lines||[]).map(l=>`<div>• ${l}</div>`).join('');
    const a=document.getElementById('briefAlerts');
    if(a) a.innerHTML=(r.alerts||[]).map(x=>
      `<div style="color:#f5d479;margin-top:8px">&#x26A0;&#xFE0F; ${x}</div>`).join('');
  }catch(e){}
}
setInterval(loadBriefing, 15000);

async function loadWatcher(){
  try{
    const r=await post('/api/watcher',{lang:(localStorage.getItem('lang')||'en')});
    const box=document.getElementById('watchSummary'); if(!box) return;
    const color={BEST_BUY:'var(--green)',BEST_SELL:'var(--red)',BANK:'var(--green)',PAUSE:'#ffd54a',GRID:'var(--muted)'};
    let html='<div class="fine" style="margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px">👁️ 24/7 watcher — best moments now</div>';
    (r.summary||[]).forEach(l=>{ html+=`<div style="margin:4px 0;font-weight:600">${l}</div>`; });
    html+='<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">';
    (r.ranked||[]).slice(0,8).forEach(v=>{
      html+=`<span class="chip" style="border-color:${color[v.state]}33;color:${color[v.state]}">${v.coin} · ${(v.state_label||v.state.replace(/_/g,' '))} · ${v.score}/100</span>`;
    });
    html+='</div>';
    box.innerHTML=html;
  }catch(e){}
}
setInterval(loadWatcher, 20000);

async function sendMorningBrief(){
  const btn=event&&event.target; if(btn){btn.textContent='Sending…';btn.disabled=true;}
  const r=await post('/api/morning-brief',{});
  if(btn){btn.disabled=false;btn.innerHTML='🌅 Email/message me this briefing';}
  toast(r.sent?'Morning briefing sent ✅':'Set up email/Telegram in Settings to receive it','green');
}

async function toggleMorningAuto(){
  const on=document.getElementById('morningAuto').checked;
  const r=await post('/api/morning/enable',{enabled:on});
  const el=document.getElementById('morningStatus');
  if(el){ el.style.color='#9af0cd';
    el.textContent= on ? '✅ Morning brief will auto-send once a day (needs email/Telegram set up).'
                       : 'Auto morning brief off.'; }
}
async function morningTick(){
  try{ await post('/api/morning/tick',{}); }catch(e){}
}
setInterval(morningTick, 60*60*1000);  // check hourly; server gates once/day

function donutSvg(items){
  const svg=document.getElementById('pfDonut'); if(!svg||!items.length) return;
  const R=70,cx=100,cy=100; let start=-Math.PI/2; let h='';
  const total=items.reduce((a,i)=>a+i.value,0)||1;
  items.forEach((it,i)=>{
    const frac=it.value/total; const ang=frac*2*Math.PI;
    const x1=cx+R*Math.cos(start), y1=cy+R*Math.sin(start);
    const x2=cx+R*Math.cos(start+ang), y2=cy+R*Math.sin(start+ang);
    const large=ang>Math.PI?1:0;
    h+=`<path data-donut="${it.label}" onclick="donutDrill('${it.label}')" style="cursor:pointer" d="M ${cx} ${cy} L ${x1.toFixed(1)} ${y1.toFixed(1)} A ${R} ${R} 0 ${large} 1 ${x2.toFixed(1)} ${y2.toFixed(1)} Z" fill="${it.color||'#666'}" opacity="0.9"><title>${it.label}</title></path>`;
    // label at mid
    const mid=start+ang/2; const lx=cx+(R*0.62)*Math.cos(mid), ly=cy+(R*0.62)*Math.sin(mid);
    if(frac>0.05) h+=`<text x="${lx}" y="${ly}" fill="#fff" font-size="9" text-anchor="middle">${it.label}</text>`;
    start+=ang;
  });
  h+=`<circle cx="${cx}" cy="${cy}" r="34" fill="#0b1220"/>`;
  h+=`<text x="${cx}" y="${cy-2}" fill="#9fb0c7" font-size="9" text-anchor="middle">${items.length}</text>`;
  h+=`<text x="${cx}" y="${cy+10}" fill="#eaf0fa" font-size="10" font-weight="700" text-anchor="middle">assets</text>`;
  svg.innerHTML=h;
}
async function loadPortfolio(){
  let r; try{ r=await apiGet('/api/portfolio?exchange='+mgEx()+'&period='+_period); }catch(e){ return; }
  if(!r) return;
  const set=(id,txt)=>{const el=document.getElementById(id); if(el) el.innerHTML=txt;};
  const pnl=r.total_pnl||0;
  set('pf_total','<b>'+fmt(r.total_value)+'</b>');
  const shownPnl=(r.period_days? r.period_pnl: r.total_pnl)||pnl;
  set('pf_pnl','<span class="'+(shownPnl>=0?'up':'down')+'">'+(shownPnl>=0?'+':'')+fmt(shownPnl)+'</span>');
  set('pf_cash','<b>'+fmt(r.cash)+'</b>');
  set('pf_winners',(r.winners||[]).map(w=>`<div>${w.coin}: <span class="up">+${w.roi_pct}%</span></div>`).join('')||'<span class=fine>none yet</span>');
  set('pf_losers',(r.losers||[]).map(w=>`<div>${w.coin}: <span class="down">${w.roi_pct}%</span></div>`).join('')||'<span class=fine>none yet</span>');
  const rows=(r.holdings||[]).filter(h=>h.amount>0||h.cash>0).map(h=>
    `<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--line)">
      <span>${h.coin} ${h.paused?'<span style="color:#ffd54a">⏸</span>':''}</span>
      <span class="fine">held ${h.amount} &asymp; <b>${fmt(h.value)}</b> &middot; <span class="${h.roi_pct>=0?'up':'down'}">${h.roi_pct>=0?'+':''}${h.roi_pct}%</span></span>
    </div>`).join('')||'<div class="fine">No holdings — start grids to build your portfolio.</div>';
  set('pf_holdings', rows);
  donutSvg(r.allocation||[]);
}
setInterval(loadPortfolio, 20000);


let _curRate=1, _curSym='$', _cur='USD';
async function loadCurrency(){
  try{ const r=await apiGet('/api/currency'); _cur=r.current||'USD';
    const sel=document.getElementById('curSel'); if(sel) sel.value=_cur;
  }catch(e){}
}
async function setCurrency(code){
  await post('/api/currency/set',{currency:code});
  localStorage.setItem('cur',code); _cur=code;
  try{ loadPortfolio(); }catch(e){}
}


let _period=7;
async function setPeriod(d){
  _period=d;
  document.querySelectorAll('.pf-period').forEach(b=>b.classList.toggle('active',+(b.dataset.d)===d));
  loadPortfolio();
}

function mobileTab(name){
  // reuse section navigation: Dashboard=trade, Watchlist=bots, Reports=history
  if(typeof showNav==='function') showNav(name);
  document.querySelectorAll('.mobiletabs a').forEach(a=>a.classList.remove('active'));
  event&&event.currentTarget&&event.currentTarget.classList.add('active');
  window.scrollTo({top:0,behavior:'smooth'});
}

function donutDrill(label){
  if(label==='USD (cash)'){ toast('Cash (unallocated USDT) — not a coin','green'); return; }
  toast('Selected '+label+' — opening bots view','green');
  if(typeof showNav==='function') showNav('bots');
  setTimeout(()=>{ window.scrollTo({top:0,behavior:'smooth'}); },150);
}

async function healthCheck(){
  try{
    const ex=(document.getElementById('mk_exchange')?document.getElementById('mk_exchange').value:'binance');
    const r=await post('/api/health',{exchange:ex,coin:(document.getElementById('mk_coin')?document.getElementById('mk_coin').value:'BTC')});
    const dot=document.getElementById('healthDot'), txt=document.getElementById('healthText'), bd=document.getElementById('healthBadge');
    if(!dot) return;
    if(r.ok){ dot.style.background='#16c784'; txt.textContent='Live · '+r.exchange+' · '+r.price; txt.style.color='#8fe9c2'; if(bd)bd.style.borderColor='rgba(22,199,132,.4)'; }
    else { dot.style.background='#ea3943'; txt.textContent=r.exchange+' offline (practice)'; txt.style.color='#ff9b9b'; }
  }catch(e){ const d=document.getElementById('healthDot'); if(d) d.style.background='#ea3943'; }
}
setInterval(healthCheck, 30000);

async function liveMonitor(){
  let r; try{ r=await apiGet('/api/portfolio?exchange='+mgEx()+'&period=7'); }catch(e){ return; }
  if(!r) return;
  const set=(id,t)=>{const el=document.getElementById(id); if(el) el.innerHTML=t;};
  set('mon_bots', r.count||0);
  const pnl=r.total_pnl||0;
  set('mon_pnl','<span class="'+(pnl>=0?'up':'down')+'">'+(pnl>=0?'+':'')+fmt(pnl)+'</span>');
  set('mon_cash', fmt(r.cash||0));
  let fills=0, paused=[], alerts=[];
  try{ const w=await post('/api/watcher',{lang:localStorage.getItem('lang')||'en'});
    (w.ranked||[]).forEach(v=>{ fills+=0; if(v.state==='PAUSE') paused.push(v.coin); });
    (w.summary||[]).forEach(x=>alerts.push(x));
    if(alerts[0]) set('mon_status', alerts[0]);
  }catch(e){}
  (r.holdings||[]).forEach(h=>fills+=0);
  set('mon_fills', (r.winners||[]).length+'▲ '+(r.losers||[]).length+'▼');
}
setInterval(liveMonitor, 15000);
</script>
</body>
</html>
"""
