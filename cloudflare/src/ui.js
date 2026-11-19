// Jednostavna chat stranica. Historija razgovora ostaje u pregledaču korisnika (localStorage), server je ne čuva.
export const PAGE = `<!DOCTYPE html>
<html lang="bs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Una# Asistent</title>
<style>
:root{--bg:#0d0d0d;--bg2:#161616;--line:#2a2a2a;--txt:#e0ddd5;--mut:#8a867e;--amb:#e8c84a;--ok:#4ae87a;--bad:#e84a4a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.5 system-ui,sans-serif;display:flex;flex-direction:column;height:100vh}
header{padding:14px 18px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:8px}
h1{margin:0;font-size:20px;letter-spacing:.1em;color:var(--amb)}small{color:var(--mut)}
#chat{flex:1;overflow-y:auto;padding:18px;max-width:860px;width:100%;margin:0 auto}
.m{margin:0 0 14px;padding:12px 14px;border-radius:6px;white-space:pre-wrap;word-wrap:break-word}
.u{background:#1f1c12;border-left:3px solid var(--amb)}.a{background:var(--bg2);border-left:3px solid var(--line)}
.meta{font-size:12px;color:var(--mut);margin-top:6px}.PASS{color:var(--ok)}.FAIL{color:var(--bad)}
form{display:flex;gap:8px;padding:12px 18px;border-top:1px solid var(--line);max-width:860px;width:100%;margin:0 auto}
textarea{flex:1;resize:none;height:56px;background:var(--bg2);color:var(--txt);border:1px solid var(--line);border-radius:6px;padding:10px;font:inherit}
button{background:transparent;color:var(--amb);border:1px solid var(--amb);border-radius:6px;padding:0 16px;cursor:pointer;font:inherit}
button:disabled{opacity:.4;cursor:wait}#clear{border-color:var(--line);color:var(--mut);padding:6px 10px}
</style></head><body>
<header><div><h1>UNA# ASISTENT</h1><small>Neprovjereno = NEMAM POTVRDU</small></div><button id="clear" type="button">Obriši historiju</button></header>
<div id="chat"></div>
<form id="f"><textarea id="q" placeholder="Postavi pitanje… (Enter šalje, Shift+Enter novi red)"></textarea><button id="send">Pošalji</button></form>
<script>
const KEY="una_history",chat=document.getElementById("chat"),q=document.getElementById("q"),send=document.getElementById("send");
const load=()=>{try{return JSON.parse(localStorage.getItem(KEY))||[]}catch{return[]}};
const save=h=>{try{localStorage.setItem(KEY,JSON.stringify(h.slice(-20)))}catch{}};
let history=load();
function add(cls,text,meta,verdict){const d=document.createElement("div");d.className="m "+cls;d.textContent=text;
 if(meta){const m=document.createElement("div");m.className="meta";if(verdict){const v=document.createElement("b");v.className=verdict;v.textContent=verdict+" ";m.appendChild(v)}
 m.appendChild(document.createTextNode(meta));d.appendChild(m)}chat.appendChild(d);chat.scrollTop=chat.scrollHeight;return d}
history.forEach(h=>{add("u",h.question);add("a",h.answer,"",h.verdict)});
document.getElementById("clear").onclick=()=>{history=[];save(history);chat.innerHTML=""};
q.addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();document.getElementById("f").requestSubmit()}});
document.getElementById("f").onsubmit=async e=>{e.preventDefault();const question=q.value.trim();if(!question)return;
 q.value="";add("u",question);send.disabled=true;const wait=add("a","Agenti rade, Đavolji advokat provjerava…");
 const headers={"content-type":"application/json"};const code=sessionStorage.getItem("una_code");if(code)headers["x-access-code"]=code;
 try{let r=await fetch("/api/ask",{method:"POST",headers,body:JSON.stringify({question,history:history.slice(-3)})});
  if(r.status===401){const c=prompt("Pristupni kod za beta:");if(c){sessionStorage.setItem("una_code",c);headers["x-access-code"]=c;
   r=await fetch("/api/ask",{method:"POST",headers,body:JSON.stringify({question,history:history.slice(-3)})})}}
  const d=await r.json();wait.remove();
  if(!r.ok){add("a","Greška: "+(d.error||r.status));return}
  const a=d.audit;add("a",d.answer,"tačnost "+a.accuracy+" · kompletnost "+a.completeness+" · sigurnost "+a.safety+" · popravki "+d.refinePasses+" · "+(d.durationMs/1000).toFixed(1)+"s",d.verdict);
  history.push({question,answer:d.answer,verdict:d.verdict});save(history);
 }catch(err){wait.remove();add("a","Greška mreže: "+err.message)}finally{send.disabled=false;q.focus()}};
</script></body></html>`;
