"""Small dependency-free, loopback-only evidence browser."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
import json
import logging

from . import __version__
from .system import answer_question, ensure_index

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Evidence-backed local question answering for the Aegis Series-7 assessment corpus">
<title>Aegis Evidence Desk</title>
<style>
:root{color-scheme:dark;--bg:#101820;--panel:#182733;--line:#365266;--ink:#eef4f7;--muted:#afc1cc;--green:#83e0b0;--gold:#f1c778;--red:#ff9b91;--link:#9fd1ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,Segoe UI,sans-serif}main{max-width:920px;margin:0 auto;padding:36px 24px 72px}header{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:28px}h1{font-size:clamp(1.7rem,4vw,2.3rem);margin:0 0 6px;letter-spacing:-.025em}.sub{color:var(--muted);margin:0}.tag{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;color:var(--green);font-size:.78rem;padding:3px 10px;margin-top:12px}
form,.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px}.label{display:block;font-weight:650;margin-bottom:8px}textarea{display:block;width:100%;min-height:108px;resize:vertical;border:1px solid #526d80;border-radius:8px;padding:12px;background:#101a23;color:var(--ink);font:inherit}textarea:focus,button:focus-visible{outline:2px solid var(--link);outline-offset:2px}.row{display:flex;gap:12px;align-items:center;margin-top:12px;flex-wrap:wrap}button{border:0;border-radius:8px;padding:10px 18px;background:#a2d9f6;color:#10202b;font:650 1rem system-ui;cursor:pointer}button:disabled{opacity:.55;cursor:wait}.hint{color:var(--muted);font-size:.86rem}#result{margin-top:22px;display:grid;gap:14px}.panel h2{font-size:1.1rem;margin:0 0 10px}.status{font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em}.answered{color:var(--green)}.abstained,.insufficient_evidence{color:var(--gold)}.answer{font-size:1.06rem;margin:6px 0 0}.item{padding:12px 0;border-top:1px solid var(--line)}.item:first-of-type{border-top:0}.item p{margin:5px 0}.meta{color:var(--muted);font-size:.86rem}.quote{color:#e0eaf0}.source{color:var(--link);overflow-wrap:anywhere;font-size:.9rem}.claims{display:grid;grid-template-columns:1fr 2fr;gap:8px;margin:0}.claims dt{color:var(--muted)}.claims dd{margin:0;overflow-wrap:anywhere}footer{color:var(--muted);font-size:.83rem;margin-top:26px}
@media(max-width:600px){main{padding:24px 15px 48px}.claims{grid-template-columns:1fr;gap:2px}.claims dd{margin-bottom:9px}.panel,form{padding:16px}}
</style></head><body><main>
<header><h1>Aegis Evidence Desk</h1><p class="sub">Ask about the supplied Series-7 HCS documents. Each answer shows its claims, source locations, and uncertainty.</p><span class="tag">Local corpus · reviewed source excerpts · no external services</span></header>
<form id="ask" autocomplete="off"><label class="label" for="question">Your question</label><textarea id="question" name="question" maxlength="1200" required placeholder="For example: What changed at software revision 3.2?"></textarea><div class="row"><button id="submit" type="submit">Find an evidence-backed answer</button><span class="hint">Unknown values and unsupported assumptions receive an explicit abstention.</span></div></form>
<section id="result" aria-live="polite" aria-busy="false"></section><footer>Fictional assessment dataset · Screenshot numbers are historical image content, not live machine data · Corpus scope: 20 supplied source files · version __VERSION__</footer>
</main><script>
const form=document.querySelector('#ask'),result=document.querySelector('#result'),button=document.querySelector('#submit');
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n}
function panel(title){const box=el('section','panel');box.append(el('h2','',title));return box}
function render(data){result.replaceChildren();const status=panel('Answer');const mark=el('span','status '+data.status,data.status.replaceAll('_',' '));status.append(mark,el('p','answer',data.answer));if(data.route_id)status.append(el('p','meta','Evidence rule: '+data.route_id));result.append(status);
if(data.claims?.length){const box=panel('Structured claims');const dl=el('dl','claims');for(const claim of data.claims){dl.append(el('dt','',claim.subject+' · '+claim.predicate));let value=claim.value;if(value===null)value='Not specified in the supplied evidence';else if(Array.isArray(value))value=value.join('; ');else if(typeof value==='object')value=JSON.stringify(value);if(claim.unit)value+=' '+claim.unit;if(claim.scope&&Object.keys(claim.scope).length)value+=' · Scope: '+JSON.stringify(claim.scope);dl.append(el('dd','',value));}box.append(dl);result.append(box)}
if(data.resolved_entities?.length){const box=panel('Resolved identifiers');for(const item of data.resolved_entities)box.append(el('p','meta',item.matched_text+' → '+item.canonical_id+' ('+item.type+')'));result.append(box)}
if(data.evidence?.length){const box=panel('Evidence');for(const item of data.evidence){const article=el('article','item');article.append(el('p','source',item.source+' · '+item.locator));article.append(el('p','quote','“'+item.quote+'”'));article.append(el('p','meta','Extraction: '+(item.extraction_method||'indexed text')+' · Claim: '+(item.claim_id||'retrieved context')+' · Confidence: '+(item.confidence||'not scored')));box.append(article);}result.append(box)}
if(data.unresolved?.length){const box=panel('Unresolved points');for(const item of data.unresolved)box.append(el('p','',item));result.append(box)}if(data.limitations?.length){const box=panel('Scope');for(const item of data.limitations)box.append(el('p','meta',item));result.append(box)}}
form.addEventListener('submit',async event=>{event.preventDefault();button.disabled=true;result.replaceChildren(el('section','panel','Searching the local source index…'));result.setAttribute('aria-busy','true');try{const response=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:document.querySelector('#question').value})});const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed');render(data)}catch(error){result.replaceChildren(el('section','panel','Could not answer: '+error.message))}finally{button.disabled=false;result.setAttribute('aria-busy','false')}});
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "AegisEvidenceDesk/1.0"

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(data)

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")

    def do_GET(self) -> None:
        if self.path == "/health":
            try:
                report = ensure_index()
                self._json(200, {"status": "ok", "version": __version__, "indexed_files": report["dataset_file_count"], "segments": report["segment_count"]})
            except Exception as exc:
                logging.exception("health check failed")
                self._json(503, {"status": "error", "error": str(exc)})
            return
        if self.path not in {"/", "/index.html"}:
            self._json(404, {"error": "Not found"})
            return
        body = PAGE.replace("__VERSION__", __version__).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/api/ask":
            self._json(404, {"error": "Not found"})
            return
        length = self.headers.get("Content-Length", "")
        if not length.isdecimal() or int(length) > 16_384:
            self._json(413, {"error": "Request body must be valid and no larger than 16 KB."})
            return
        try:
            request = json.loads(self.rfile.read(int(length)))
            if not isinstance(request, dict) or not isinstance(request.get("question"), str):
                raise ValueError("Send a JSON object with a string field named question.")
            response = answer_question(request["question"])
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._json(400, {"error": str(exc)})
            return
        except Exception as exc:
            logging.exception("answer request failed")
            self._json(500, {"error": "The local evidence service could not process this question."})
            return
        self._json(200, response)

    def log_message(self, fmt: str, *args: Any) -> None:
        logging.info("%s - %s", self.address_string(), fmt % args)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("For local deployment, the server binds only to loopback. Configure an authenticated reverse proxy before exposing it to a network.")
    ensure_index()
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    logging.info("Aegis Evidence Desk listening on http://%s:%d", host, port)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        logging.info("Stopping Aegis Evidence Desk.")
    finally:
        server.server_close()
