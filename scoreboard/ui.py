"""KOTH scoreboard UI theme (English). No emojis, no em-dashes."""

CSS = """<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#07090f;--surface:#0d1420;--surface2:#0a1018;--border:#1a2d45;--border2:#24405e;
--accent:#00e5ff;--accent2:#ff3c6e;--ok:#00e676;--warn:#ffa726;--text:#dbe7f2;--text-dim:#5b7da3;
--mono:'Share Tech Mono',ui-monospace,SFMono-Regular,monospace;
--sans:'Rajdhani','Segoe UI',system-ui,sans-serif;
--glow:0 0 16px rgba(0,229,255,.45);--glow-sm:0 0 8px rgba(0,229,255,.3)}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--text);margin:0;font-family:var(--sans);font-size:15px;min-height:100vh;
background-image:radial-gradient(1200px 420px at 50% -140px,rgba(0,229,255,.10),transparent 70%),
linear-gradient(rgba(26,45,69,.18) 1px,transparent 1px),
linear-gradient(90deg,rgba(26,45,69,.18) 1px,transparent 1px);
background-size:100% 100%,46px 46px,46px 46px;background-attachment:fixed}
.wrap{max-width:1120px;margin:0 auto;padding:24px 24px 64px}
header{display:flex;align-items:center;gap:20px;padding:14px 0 20px;margin-bottom:26px;position:relative}
header:after{content:"";position:absolute;left:0;right:0;bottom:0;height:1px;
background:linear-gradient(90deg,transparent,var(--accent),transparent);opacity:.5}
header img{height:74px;width:auto;filter:drop-shadow(0 0 12px rgba(0,229,255,.3))}
.brand{display:flex;flex-direction:column;gap:3px}
.brand b{font-family:var(--mono);font-weight:400;font-size:clamp(20px,3.4vw,32px);color:#fff;
letter-spacing:4px;text-shadow:var(--glow);line-height:1}
.brand span{font-family:var(--sans);font-size:13px;font-weight:600;color:var(--accent);
letter-spacing:3px;text-transform:uppercase}
.live{margin-left:auto;display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);
font-size:11px;color:var(--text-dim);text-transform:uppercase;letter-spacing:1.5px;
border:1px solid var(--border);border-radius:20px;padding:6px 13px;background:rgba(0,229,255,.03)}
.live i{width:7px;height:7px;border-radius:50%;background:var(--ok);box-shadow:0 0 8px var(--ok);animation:pulse 1.8s infinite}
.logout{display:inline-flex;align-items:center;font-family:var(--mono);font-size:11px;letter-spacing:1px;
text-transform:uppercase;color:var(--text-dim);text-decoration:none;border:1px solid var(--border);
border-radius:20px;padding:6px 13px;transition:color .15s,border-color .15s}
.logout:hover{color:var(--accent2);border-color:var(--accent2)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
.card{position:relative;background:linear-gradient(180deg,var(--surface),var(--surface2));
border:1px solid var(--border);border-radius:6px;padding:20px 22px;margin-bottom:20px;
box-shadow:0 0 0 1px rgba(0,229,255,.015),0 10px 34px -20px rgba(0,0,0,.85)}
.card>h2{margin:0 0 16px;font-family:var(--mono);font-size:12px;text-transform:uppercase;letter-spacing:2.5px;
color:var(--accent);text-shadow:var(--glow-sm);display:flex;align-items:center;gap:9px}
.card>h2:before{content:"";width:3px;height:13px;background:var(--accent);box-shadow:var(--glow-sm);border-radius:2px}
.grid{display:grid;grid-template-columns:1.4fr 1fr;gap:20px}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
table{border-collapse:collapse;width:100%}
th{text-align:left;font-family:var(--mono);font-size:10.5px;text-transform:uppercase;letter-spacing:1.5px;
color:var(--text-dim);font-weight:400;padding:0 12px 12px}
td{padding:12px;border-top:1px solid rgba(26,45,69,.7);vertical-align:middle}
tbody tr{transition:background .15s}
tbody tr:hover{background:rgba(0,229,255,.035)}
td.r,th.r{text-align:right}
#board tr:first-child td{border-top:none}
#board tr.you{background:linear-gradient(90deg,rgba(0,229,255,.09),transparent 72%)}
#board tr.you td:first-child{box-shadow:inset 2px 0 0 var(--accent)}
.rankb{display:inline-flex;align-items:center;justify-content:center;width:25px;height:25px;
border:1px solid var(--border2);border-radius:5px;font-family:var(--mono);font-size:12px;color:var(--text-dim)}
tr.you .rankb{border-color:var(--accent);color:var(--accent);box-shadow:var(--glow-sm)}
.youtag{font-family:var(--mono);font-size:9px;letter-spacing:1px;color:var(--accent);border:1px solid var(--accent);
border-radius:3px;padding:1px 5px;margin-left:8px;vertical-align:middle}
.team{font-weight:600;font-size:16px;letter-spacing:.3px}
.total{font-family:var(--mono);font-size:16px;color:var(--accent);text-shadow:var(--glow-sm)}
.num{font-family:var(--mono);color:var(--text-dim)}
.neg{color:var(--accent2)}
.pill{display:inline-flex;align-items:center;gap:7px;padding:4px 11px;border-radius:20px;
font-family:var(--mono);font-size:10.5px;letter-spacing:1px;text-transform:uppercase;border:1px solid transparent}
.pill:before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor;box-shadow:0 0 6px currentColor}
.OWNED{background:rgba(0,230,118,.1);color:var(--ok);border-color:rgba(0,230,118,.25)}
.NEUTRAL{background:rgba(91,125,163,.12);color:var(--text-dim);border-color:rgba(91,125,163,.2)}
.UNKNOWN{background:rgba(255,167,38,.1);color:var(--warn);border-color:rgba(255,167,38,.25)}
.SLA_DOWN,.NO_AGENT{background:rgba(255,60,110,.1);color:var(--accent2);border-color:rgba(255,60,110,.25)}
.PAUSED{background:rgba(0,229,255,.1);color:var(--accent);border-color:rgba(0,229,255,.25)}
.owner{font-family:var(--mono);color:var(--text)}
.hlink{color:var(--accent);text-decoration:none;border-bottom:1px dotted rgba(0,229,255,.45)}
.hlink:hover{text-shadow:var(--glow-sm);border-bottom-color:var(--accent)}
.log{font-family:var(--mono);font-size:12px;line-height:1.8;color:var(--text-dim);max-height:340px;overflow:auto;padding-right:4px}
.log::-webkit-scrollbar{width:8px}.log::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}
.log div{padding:3px 0}
.log b{color:var(--accent);font-weight:400}
label{display:block;font-family:var(--mono);font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-dim);margin-bottom:7px}
.field{margin-bottom:16px}
input{background:var(--surface2);color:var(--text);border:1px solid var(--border);border-radius:5px;
padding:11px 13px;width:100%;font-family:var(--mono);font-size:14px;transition:border-color .15s,box-shadow .15s}
input::placeholder{color:#3a5573}
input:focus{outline:none;border-color:var(--accent);box-shadow:var(--glow-sm)}
.actions{display:flex;gap:10px;flex-wrap:wrap}
button{background:transparent;color:var(--accent);border:1px solid var(--accent);border-radius:5px;
padding:10px 20px;font-family:var(--mono);font-size:12px;letter-spacing:1.5px;text-transform:uppercase;
cursor:pointer;transition:background .15s,box-shadow .15s}
button:hover{background:rgba(0,229,255,.12);box-shadow:var(--glow-sm)}
button.ghost{color:var(--text-dim);border-color:var(--border2)}
button.ghost:hover{color:var(--text);background:rgba(255,255,255,.03);box-shadow:none}
button.warn{color:var(--accent2);border-color:var(--accent2)}
button.warn:hover{background:rgba(255,60,110,.12);box-shadow:none}
button.block{width:100%;justify-content:center;padding:12px}
.row button{padding:6px 12px;font-size:11px}
.hint{font-size:14px;color:var(--text-dim);margin:0 0 16px;line-height:1.6}
.msg{font-size:13px;margin-top:12px;min-height:18px;font-family:var(--mono)}
.ok{color:var(--ok)}.err{color:var(--accent2)}
code{background:var(--surface2);border:1px solid var(--border);padding:2px 7px;border-radius:4px;font-family:var(--mono);font-size:13px;color:var(--accent)}
.codebox{background:var(--surface2);border:1px solid var(--border);border-radius:5px;padding:12px 14px;
font-family:var(--mono);font-size:14px;color:var(--accent);overflow-x:auto;word-break:break-all;user-select:all}
.rules .lead{color:var(--text-dim);line-height:1.65;margin:0 0 18px}
.rulecols{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
@media(max-width:700px){.rulecols{grid-template-columns:1fr}}
.rblock{background:var(--surface2);border:1px solid var(--border);border-left-width:3px;border-radius:5px;padding:13px 15px}
.rblock h4{margin:0 0 8px;font-family:var(--mono);font-size:11px;text-transform:uppercase;letter-spacing:1.5px}
.rblock ul{margin:0;padding-left:18px}.rblock li{margin:3px 0;color:var(--text-dim);font-size:14px}
.rblock p{margin:0;color:var(--text-dim);font-size:14px;line-height:1.55}
.rblock.allow{border-left-color:var(--ok)}.rblock.allow h4{color:var(--ok)}
.rblock.legal{border-left-color:var(--accent)}.rblock.legal h4{color:var(--accent)}
.rblock.illegal{border-left-color:var(--accent2)}.rblock.illegal h4{color:var(--accent2)}
.login-wrap{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px;text-align:center}
.login-wrap img{height:118px;filter:drop-shadow(0 0 18px rgba(0,229,255,.35));margin-bottom:22px}
.login-title{font-family:var(--mono);font-size:26px;letter-spacing:5px;color:#fff;text-shadow:var(--glow);margin-bottom:5px}
.login-sub{font-family:var(--sans);font-weight:600;font-size:13px;letter-spacing:3px;text-transform:uppercase;color:var(--accent);margin-bottom:26px}
.login-card{background:linear-gradient(180deg,var(--surface),var(--surface2));border:1px solid var(--border);
border-radius:8px;padding:26px;width:100%;max-width:360px;text-align:left;box-shadow:0 24px 70px -34px rgba(0,0,0,.9)}
</style>"""


def _page(title, subtitle, body, js, show_logout=True):
    scr = ("<script>" + js + "</script>") if js else ""
    logout = "<a class=logout id=logout href='/logout' style='display:none'>Log out</a>" if show_logout else ""
    who = ("<script>fetch('/whoami').then(function(r){return r.ok?r.json():null;}).then(function(j){"
           "if(j&&j.team){var l=document.getElementById('logout');l.textContent='Log out ('+j.team+')';l.style.display='';}});</script>"
           ) if show_logout else ""
    return ("<!doctype html><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>" + title + "</title>" + CSS +
            "<div class=wrap><header>"
            "<img src='/assets/logo.svg' alt='King of the Hill'>"
            "<div class=brand><b>KING OF THE HILL</b><span>" + subtitle + "</span></div>"
            "<div class=live><i></i>Live</div>" + logout +
            "</header>" + body + scr + who + "</div>")


DASH_BODY = """
<div class=card><h2>Your beacon</h2>
<p class=hint>You are logged in as your team. Plant this on a hill you control (as root) to claim it.</p>
<div class=field><label>Your token</label><div class=codebox id=mytoken>...</div></div>
<div class=field><label>Command (run as root on the hill)</label><div class=codebox id=mycmd>...</div></div>
<div class=actions><button onclick="dlking()">Download king.txt</button><button class=ghost onclick="cpcmd()">Copy command</button></div>
<div class=msg id=bmsg></div></div>
<div class=card><h2>Standings</h2>
<table><thead><tr><th style="width:38px">#</th><th>Team</th><th class=r>Hold</th><th class=r>Adjust</th><th class=r>Total</th></tr></thead>
<tbody id=board></tbody></table></div>
<div class=card><h2>Scoring</h2>
<p class=hint>Holding a hill scores <b style="color:var(--accent)">3 points every 7 seconds</b>. Overwriting another
team's beacon takes the hill. Flags are scored on the platform.</p>
<table><thead><tr><th>Hold time on one hill</th><th class=r>Points</th></tr></thead><tbody>
<tr><td>1 minute</td><td class="num r">~24</td></tr>
<tr><td>10 minutes</td><td class="num r">~255</td></tr>
<tr><td>30 minutes</td><td class="num r">~770</td></tr>
<tr><td>1 hour</td><td class="num r">~1540</td></tr>
<tr><td>Full event (2h), one hill</td><td class="num r">~3080</td></tr>
<tr><td>Full event (2h), all four hills</td><td class="total r">~12300</td></tr>
</tbody></table></div>
<div class="card rules"><h2>Rules of Engagement (ROE)</h2>
<p class=lead>King of the Hill. Break into a hill, get root, and plant your team beacon
(<code>echo 'TOKEN' &gt; /root/king.txt</code>) to hold it and score over time. Overwriting another
team's king.txt takes the hill. The entry vulnerability and privilege escalation are restored every
15 minutes, so a box cannot be locked down for good. Attack only the designated hill targets on their
game ports; everything else is out of scope. On every host you access you must identify your team as instructed in <code>TEAM-DECLARATION.md</code> on that host - operating without declaring is an ROE violation. Flags are submitted on the scoring platform.</p>
<div class=rulecols>
<div class="rblock allow"><h4>In scope</h4><ul><li>The four hill services on their game ports</li><li>Other teams' foothold on those hills</li></ul></div>
<div class="rblock illegal"><h4>Out of scope (do not touch)</h4><ul><li>Scoring / green-team server (scoreboard, port 8000)</li><li>Scoring agent (koth_agent.py) and reset service on the hills</li><li>Organizers' Jenkins / CI and management (SSH, port 22)</li><li>Other teams' own infrastructure and VPN</li></ul></div>
<div class="rblock legal"><h4>Penalties</h4><p>Every illegal or out-of-scope action costs your team points, up to 100 per action. Killing the scoring agent also triggers a forced revert.</p></div>
</div>
<div class=rulecols style="margin-top:14px">
<div class="rblock allow"><h4>Allowed defense</h4><ul><li>Active monitoring</li><li>Kicking other teams' sessions</li><li>Overwriting someone else's king.txt</li><li>Hardening the box</li><li>Revoking your own privileges (e.g. removing a sudoers entry), until the next reset</li></ul></div>
<div class="rblock illegal"><h4>Not allowed defense</h4><p>Removing the original point of entry. You may harden the box, but do not patch out or block the original vulnerability (it is restored every 15 minutes anyway).</p></div>
<div class="rblock illegal"><h4>Illegal</h4><p>DoS-ing other teams' infrastructure.</p></div>
</div></div>
<div class=grid>
<div class=card><h2>Hills</h2><table><thead><tr><th>Hill</th><th>Status</th><th>Owner</th></tr></thead>
<tbody id=hills></tbody></table></div>
<div class=card><h2>Event Log</h2><div class=log id=events></div></div>
</div>"""

DASH_JS = """
var MYTEAM=null;
fetch('/whoami').then(function(r){return r.ok?r.json():null;}).then(function(j){if(j)MYTEAM=j.team;});
async function tick(){
 const s=await(await fetch('/api/state')).json();
 document.getElementById('board').innerHTML=s.board.map(function(r,i){
  var me=r.team===MYTEAM;
  return '<tr class="'+(me?'you':'')+'"><td><span class=rankb>'+(i+1)+'</span></td>'
   +'<td class=team>'+r.team+(me?' <span class=youtag>YOU</span>':'')+'</td><td class="num r">'+r.ticks+'</td>'
   +'<td class="num neg r">'+r.adjust+'</td><td class="total r">'+r.total+'</td></tr>';}).join('');
 document.getElementById('hills').innerHTML=s.hills.map(function(h){
  var hn=h.url?'<a class=hlink href="'+h.url+'" target="_blank" rel="noopener">'+h.hill+'</a>':h.hill;
  return '<tr><td>'+hn+'</td><td><span class="pill '+h.status+'">'+h.status.replace('_',' ')
   +'</span></td><td class=owner>'+(h.owner||'-')+'</td></tr>';}).join('');
 document.getElementById('events').innerHTML=s.events.map(function(e){
  return '<div><b>'+e.type+'</b> '+e.hill+' '+(e.details||'')+' '+(e.points?('('+e.points+')'):'')+'</div>';}).join('');
}
function loadBeacon(){
 fetch('/mybeacon').then(function(r){return r.ok?r.text():null;}).then(function(t){
  if(!t)return; var tok=t.trim(); window.__kingcmd="echo '"+tok+"' > /root/king.txt";
  document.getElementById('mytoken').textContent=tok;
  document.getElementById('mycmd').textContent=window.__kingcmd;});
}
function dlking(){ window.location='/mybeacon'; }
function cpcmd(){ if(window.__kingcmd){navigator.clipboard.writeText(window.__kingcmd);
 var m=document.getElementById('bmsg');m.className='msg ok';m.textContent='Command copied.';} }
loadBeacon();tick();setInterval(tick,1000);"""

TEAM_BODY = """
<div class=card><h2>Get your beacon</h2>
<p class=hint>Enter your team access code to reveal your beacon command. Run it as root on a
hill you control to claim it (writes your team token to <code>/root/king.txt</code>).</p>
<div class=field><label>Team access code</label><input id=code placeholder="e.g. team1-xxxxxxxx"></div>
<div class=actions><button onclick="show()">Show beacon command</button></div>
<div id=result></div>
<div class=msg id=dlmsg></div></div>
<p class=hint>Flags are submitted on the scoring platform.</p>"""

TEAM_JS = """
function show(){
 var c=document.getElementById('code').value.trim(); if(!c)return;
 var m=document.getElementById('dlmsg'); var res=document.getElementById('result');
 res.innerHTML=''; m.textContent='';
 fetch('/beacon?code='+encodeURIComponent(c)).then(function(r){
  if(!r.ok){m.className='msg err';m.textContent='Invalid access code';return null;} return r.text();
 }).then(function(t){ if(!t)return; var tok=t.trim();
  window.__cmd="echo '"+tok+"' > /root/king.txt";
  res.innerHTML='<div class=field><label>Your team token</label><div class=codebox>'+tok+'</div></div>'
   +'<div class=field><label>Run as root on a hill you control</label><div class=codebox>'+window.__cmd+'</div></div>'
   +'<div class=actions><button onclick="cp()">Copy command</button></div>';
 });
}
function cp(){ navigator.clipboard.writeText(window.__cmd||'');
 var m=document.getElementById('dlmsg'); m.className='msg ok'; m.textContent='Command copied.'; }"""

ADMIN_LOGIN_BODY = """
<div class=card style="max-width:420px"><h2>Green Team Login</h2>
<div class=field><label>Admin key</label><input id=k type=password placeholder="admin key"></div>
<div class=actions><button class=block onclick="location.href='/admin?k='+encodeURIComponent(document.getElementById('k').value)">Enter</button></div></div>"""

ADMIN_BODY = """
<div class=grid>
<div class=card><h2>Hills control</h2><table><thead><tr><th>Hill</th><th>Status</th><th>Owner</th>
<th>Actions</th></tr></thead><tbody id=hills></tbody></table></div>
<div>
<div class=card><h2>Standings</h2><table><thead><tr><th>Team</th><th class=r>Total</th><th class=r>Adjust</th></tr></thead>
<tbody id=board></tbody></table></div>
<div class=card><h2>Manual adjustment</h2>
<div class=field><label>Team</label><input id=ateam placeholder="team name"></div>
<div class=field><label>Points (+ or -)</label><input id=apts placeholder="e.g. -30"></div>
<div class=actions><button onclick="adjust()">Apply</button></div></div>
</div></div>
<div class=card><h2>Audit Log</h2><div class=log id=events></div></div>"""

ADMIN_JS = """
var K=new URLSearchParams(location.search).get('k');
async function api(p,b){return (await fetch(p+'?k='+encodeURIComponent(K),{method:'POST',
 headers:{'Content-Type':'application/json'},body:JSON.stringify(b)})).json();}
async function tick(){
 var s=await(await fetch('/api/admin/state?k='+encodeURIComponent(K))).json();
 document.getElementById('hills').innerHTML=s.hills.map(function(h){
  var p=s.paused.indexOf(h.hill)>=0;
  return '<tr class=row><td>'+h.hill+'</td><td><span class="pill '+h.status+'">'+h.status.replace('_',' ')
   +'</span></td><td class=owner>'+(h.owner||'-')+'</td><td><div class=actions>'
   +'<button class=ghost onclick="pause(\\''+h.hill+'\\','+(!p)+')">'+(p?'Resume':'Pause')+'</button>'
   +'<button class=ghost onclick="rotate(\\''+h.hill+'\\')">Rotate key</button>'
   +'<button class=warn onclick="revert(\\''+h.hill+'\\')">Revert</button></div></td></tr>';}).join('');
 document.getElementById('board').innerHTML=s.board.map(function(r){
  return '<tr><td class=team>'+r.team+'</td><td class="total r">'+r.total+'</td><td class="num neg r">'+r.adjust+'</td></tr>';}).join('');
 document.getElementById('events').innerHTML=s.events.map(function(e){
  return '<div><b>'+e.type+'</b> '+e.hill+' '+(e.details||'')+' '+(e.points?('('+e.points+')'):'')+'</div>';}).join('');
}
async function pause(h,p){await api('/admin/pause',{hill_id:h,paused:p});tick();}
async function rotate(h){await api('/admin/rotate',{hill_id:h,new_key:'rot-'+Math.random().toString(36).slice(2,12)});tick();}
async function revert(h){if(confirm('Revert '+h+' ?')){await api('/admin/revert',{hill_id:h,reason:'green team'});tick();}}
async function adjust(){await api('/admin/adjust',{team:document.getElementById('ateam').value.trim(),
 points:parseInt(document.getElementById('apts').value)||0});tick();}
tick();setInterval(tick,1500);"""

LOGIN_PAGE = ("<!doctype html><meta charset=utf-8>"
              "<meta name=viewport content='width=device-width,initial-scale=1'>"
              "<title>King of the Hill - Login</title>" + CSS +
              "<div class=login-wrap>"
              "<img src='/assets/logo.svg' alt='King of the Hill'>"
              "<div class=login-title>KING OF THE HILL</div>"
              "<div class=login-sub>Scoreboard</div>"
              "<div class=login-card>"
              "<form method=post action=/login>"
              "<div class=field><label>Team</label><input name=team placeholder='team1' autofocus autocomplete=username></div>"
              "<div class=field><label>Password</label><input name=password type=password autocomplete=current-password></div>"
              "<div class=actions><button class=block type=submit>Enter</button></div>"
              "</form><div id=err class='msg err'></div></div>"
              "<script>if(location.search.indexOf('e=1')>=0){document.getElementById('err').textContent='Invalid team or password';}</script>"
              "</div>")

DASHBOARD = _page("King of the Hill - Scoreboard", "Scoreboard", DASH_BODY, DASH_JS)
TEAM_PAGE = _page("King of the Hill - Team Portal", "Team Portal", TEAM_BODY, TEAM_JS)
ADMIN_LOGIN = _page("King of the Hill - Green Team", "Green Team", ADMIN_LOGIN_BODY, "", show_logout=False)
ADMIN_PAGE = _page("King of the Hill - Green Team", "Green Team Control", ADMIN_BODY, ADMIN_JS, show_logout=False)
