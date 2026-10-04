"""Small dependency-free, loopback-only evidence browser."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from mimetypes import guess_type
from pathlib import Path, PurePosixPath
from typing import Any
from io import BytesIO
import json
import html as html_lib
import logging
import re
from urllib.parse import parse_qs, unquote, urlsplit
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

from . import __version__
from .system import DATASET_DIR, PROJECT_DIR, answer_question, ensure_index

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Evidence-backed local question answering for the Aegis Series-7 assessment corpus">
<title>Aegis — Evidence Desk</title>
<style>
:root{color-scheme:light;--paper:#f8f9f6;--white:#fff;--ink:#24342d;--muted:#78847d;--line:#e6eae4;--sage:#e8efe9;--green:#285c43;--green2:#3b7657;--mint:#f1f6f1;--amber:#9d6d23;--shadow:0 12px 34px rgba(34,53,42,.07)}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}button,textarea{font:inherit}button{cursor:pointer}button:focus-visible,textarea:focus-visible{outline:3px solid #a6c4af;outline-offset:2px}
/* Keep scroll interaction while omitting visible scrollbar tracks. */
html,body,*{scrollbar-width:none;-ms-overflow-style:none}
html::-webkit-scrollbar,body::-webkit-scrollbar,*::-webkit-scrollbar{display:none;width:0;height:0}
.app{min-height:100vh;display:grid;grid-template-columns:260px minmax(0,1fr)}.sidebar{height:100vh;position:sticky;top:0;padding:25px 17px 18px;background:#f0f3ef;border-right:1px solid var(--line);display:flex;flex-direction:column;gap:22px}.brand{display:flex;align-items:center;gap:11px;padding:3px 7px}.brand-mark{width:37px;height:37px;border-radius:12px;background:var(--green);display:grid;place-items:center;color:white;font-weight:750;font-size:18px;box-shadow:0 4px 10px #285c4324}.brand-name{font-size:16px;line-height:1.2;font-weight:720;letter-spacing:-.02em}.brand-caption{font-size:11px;color:var(--muted);margin-top:3px}.new-chat{width:100%;display:flex;align-items:center;gap:9px;text-align:left;border:1px solid #dce4dc;border-radius:11px;background:#fff;color:var(--ink);padding:11px 12px;font-weight:620;transition:.18s}.new-chat:hover,.history-item:hover{background:#e6eee7;border-color:#c8d8ca;color:var(--green)}.plus{font-size:19px;color:var(--green);line-height:1}.side-label{padding:0 9px;color:#89948c;font-size:10px;font-weight:750;text-transform:uppercase;letter-spacing:.12em}.history{min-height:0;overflow:auto;display:grid;align-content:start;gap:4px}.history-item{width:100%;padding:9px 10px;border:1px solid transparent;border-radius:9px;text-align:left;background:transparent;color:#5d6a62;font-size:12px;line-height:1.4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.history-item.active{background:#e5ede6;color:var(--green);font-weight:620}.sidebar-bottom{margin-top:auto}.local-note{border:1px solid #dfe6df;background:#f8faf7;border-radius:11px;padding:12px}.local-note strong{font-size:11px;display:flex;align-items:center;gap:7px}.dot{width:7px;height:7px;border-radius:50%;background:#60a573}.local-note p{margin:5px 0 0;color:var(--muted);font-size:10px;line-height:1.5}
.workspace{min-width:0;min-height:100vh;display:flex;flex-direction:column}.topbar{height:64px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 clamp(20px,4vw,56px);background:#ffffffb8}.top-title{font-size:12px;color:var(--muted)}.corpus-badge{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line);background:#fff;border-radius:999px;padding:6px 10px;color:#627068;font-size:10px}.corpus-badge .dot{width:6px;height:6px}.main{width:min(1080px,100%);margin:0 auto;padding:40px clamp(20px,5vw,70px) 24px;flex:1;display:flex;flex-direction:column}.welcome{margin:auto 0;display:grid;justify-items:center;text-align:center;padding:28px 0 44px}.eyebrow{color:var(--green2);text-transform:uppercase;letter-spacing:.16em;font-size:10px;font-weight:750}.welcome h1{font-size:clamp(32px,4vw,48px);line-height:1.14;letter-spacing:-.05em;font-weight:590;margin:15px 0 12px}.welcome h1 em{font-style:normal;color:var(--green2)}.welcome-copy{max-width:480px;color:var(--muted);margin:0 0 28px;font-size:14px}.suggestions{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin-top:15px;max-width:730px}.suggestion{border:1px solid #e2e8e1;border-radius:999px;background:#fff;color:#647169;padding:7px 12px;font-size:11px;transition:.18s}.suggestion:hover{border-color:#b8cebc;background:var(--mint);color:var(--green)}
.composer{width:min(760px,100%);margin:0 auto;border:1px solid #dfe5de;background:var(--white);border-radius:17px;padding:14px;box-shadow:var(--shadow);transition:.2s}.composer:focus-within{border-color:#b9cebc;box-shadow:0 12px 36px rgba(34,83,52,.1)}.composer textarea{width:100%;display:block;resize:vertical;min-height:62px;max-height:180px;padding:6px 7px;border:0;background:transparent;color:var(--ink);font-size:14px;line-height:1.6}.composer textarea:focus-visible{outline:0}.composer textarea::placeholder{color:#a4ada6}.composer-bottom{display:flex;align-items:center;justify-content:space-between;padding:6px 2px 0 7px}.composer-hint{font-size:10px;color:#9aa49c}.send{width:37px;height:37px;border:0;border-radius:11px;background:var(--green);color:white;display:grid;place-items:center;transition:.18s}.send:hover{background:#36734f;transform:translateY(-1px)}.send:disabled{opacity:.5;cursor:wait}.send svg{width:17px;height:17px}.privacy-line{text-align:center;font-size:10px;color:#99a39b;margin:12px auto 0}
.conversation{width:min(900px,100%);margin:0 auto;display:grid;gap:23px;padding-bottom:25px}.user-question{margin-left:auto;max-width:78%;padding:12px 16px;border-radius:15px 15px 4px 15px;background:#e9efe9;color:#34483b;font-size:13px;white-space:pre-wrap}.answer-layout{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:22px;align-items:start}.answer-column{min-width:0}.answer-card{padding:4px 0 16px}.answer-head{display:flex;align-items:center;gap:9px;margin-bottom:10px}.answer-symbol{width:27px;height:27px;border-radius:9px;background:#e6eee7;color:var(--green);display:grid;place-items:center;font-size:13px;font-weight:750}.answer-label{font-size:12px;font-weight:700}.status{margin-left:auto;border-radius:999px;padding:4px 8px;background:#edf5ed;color:#3f7750;font-size:9px;font-weight:750;text-transform:uppercase;letter-spacing:.06em}.status.abstained,.status.insufficient_evidence{background:#f8f1e5;color:var(--amber)}.answer-text{font-size:15px;line-height:1.8;white-space:pre-wrap;margin:0;color:#344139}.section{margin-top:15px}.section-title{font-size:10px;color:#879189;text-transform:uppercase;letter-spacing:.12em;font-weight:750;margin:0 0 8px}.claim-list{display:grid;gap:7px}.claim{display:grid;grid-template-columns:minmax(120px,.7fr) minmax(0,1.3fr);gap:10px;padding:10px 12px;border:1px solid #e8ece7;background:#fff;border-radius:10px;font-size:11px}.claim-name{color:#7b877e}.claim-value{color:#34483b;font-weight:620;overflow-wrap:anywhere}.claim-scope{grid-column:2;color:#89948b;font-size:10px}.source-list{display:grid;gap:6px}.source-link{display:flex;width:100%;align-items:center;gap:8px;padding:9px 10px;text-align:left;border:1px solid #e7ebe6;background:#fff;border-radius:9px;color:var(--green);font-size:10px;transition:.16s}.source-link:hover,.source-link[aria-expanded="true"]{background:#edf4ee;border-color:#cddbcf}.source-link span:last-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.source-number{flex:none;width:21px;height:21px;display:grid;place-items:center;background:#eef3ee;border-radius:6px;font-size:9px;font-weight:750}.source-detail{margin-top:9px;padding:13px;border:1px solid #dfe8df;background:#f7faf6;border-radius:10px}.source-path{font-size:10px;font-weight:650;color:var(--green);overflow-wrap:anywhere}.source-locator{font-size:10px;color:#879188;margin-top:2px}.source-quote{font-size:11px;color:#505d53;line-height:1.6;margin:9px 0 0;padding:0;border:0}.source-meta{font-size:9px;color:#9aa39b;margin-top:7px}.answer-side{border:1px solid #e5eae4;background:#fff;border-radius:13px;padding:14px;position:sticky;top:83px}.answer-side h2{font-size:12px;margin:0 0 11px}.entity-chip{display:inline-block;margin:0 4px 5px 0;padding:4px 7px;background:#edf3ed;border-radius:7px;color:#486851;font-size:9px}.side-copy{font-size:10px;color:#7f8b82;line-height:1.6;margin:9px 0 0}.limitation{font-size:10px;color:#7f8b82;padding-top:9px;margin-top:9px;border-top:1px solid var(--line)}.error{color:#8f4a3b;background:#fcf2ef;border:1px solid #f0ded9;border-radius:10px;padding:11px;font-size:12px}.footer{width:min(900px,100%);margin:0 auto;padding:10px 0 0;border-top:1px solid var(--line);color:#a0a9a1;font-size:9px}.hidden{display:none!important}
@media(max-width:800px){.app{grid-template-columns:210px minmax(0,1fr)}.answer-layout{grid-template-columns:minmax(0,1fr)}.answer-side{position:static;order:-1}.main{padding-top:25px}}
@media(max-width:600px){.app{display:block}.sidebar{position:fixed;z-index:5;left:0;top:0;bottom:0;width:270px;height:auto;transform:translateX(-101%);transition:transform .2s;box-shadow:var(--shadow)}.sidebar.open{transform:translateX(0)}.topbar{height:56px;padding:0 15px}.mobile-menu{display:grid!important}.main{min-height:calc(100vh - 56px);padding:15px 16px 20px}.welcome{padding:25px 0 30px}.welcome h1{font-size:34px}.welcome-copy{font-size:12px}.user-question{max-width:94%}.claim{grid-template-columns:1fr;gap:3px}.claim-scope{grid-column:1}.composer-hint{max-width:78%;font-size:9px}.suggestion{font-size:10px}.corpus-badge{font-size:0;padding:8px}.corpus-badge .dot{width:7px;height:7px}.mobile-menu{display:grid!important;width:34px;height:34px;place-items:center;border:1px solid var(--line);background:#fff;border-radius:9px;color:var(--green);margin-right:10px}.top-left{display:flex;align-items:center}.top-title{font-size:11px}}
.mobile-menu{display:none}
/* A restrained workspace: answer first, source links second, cited passage only on demand. */
:root{--paper:#fff;--ink:#242d27;--muted:#778078;--line:#e8ebe7;--green:#38664a;--green2:#38664a;--sage:#f2f5f1;--mint:#f2f5f1;--shadow:none}
.sidebar{background:#fafbf9;gap:17px;padding:20px 14px 16px}.brand{padding:2px 5px}.brand-mark{width:30px;height:30px;border-radius:8px;box-shadow:none;font-size:15px}.brand-caption,.sidebar-bottom,.corpus-badge,.eyebrow,.welcome-copy,.suggestions,.privacy-line,.footer,.answer-symbol,.answer-side,.claim-list{display:none!important}
.topbar{height:48px;justify-content:flex-start;padding:0 34px;background:#fff}.top-title{font-size:12px}.main{width:min(1080px,100%);padding:38px 36px 24px;min-height:calc(100vh - 48px)}.welcome{padding:0;margin:15vh 0 0;justify-items:stretch;text-align:left}.welcome h1{font-size:28px;letter-spacing:-.035em;font-weight:600;margin:0 0 18px}.welcome h1 em{color:var(--ink)}.composer-wrap{width:100%;max-width:740px!important}.composer{width:min(740px,100%);border-radius:10px;padding:10px 11px;box-shadow:none}.composer:focus-within{box-shadow:none}.composer textarea{min-height:54px;font-size:16px}.send{width:34px;height:34px;border-radius:7px}.composer-hint{font-size:12px}.conversation{width:100%;max-width:900px;gap:18px;flex:1}.user-question{padding:0;background:transparent;border-radius:0;color:#69736b;font-size:15px;max-width:100%;text-align:right}.answer-layout{display:block}.answer-card{padding:0}.answer-head{margin-bottom:7px}.answer-label{font-size:13px;color:var(--muted);font-weight:550}.status{margin-left:4px;background:transparent;padding:0;color:var(--muted);font-weight:550;font-size:11px}.status.abstained,.status.insufficient_evidence{background:transparent;color:var(--amber)}.answer-text{font-size:16px;line-height:1.75}.section{margin-top:17px}.section-title{display:block!important;margin-bottom:6px;font-size:12px;letter-spacing:0;text-transform:none;font-weight:550;color:#818a82}.source-list{display:flex;flex-wrap:wrap;gap:4px 16px}.source-link{display:inline-flex;width:auto;max-width:100%;padding:2px 0;border:0;border-radius:0;background:transparent;color:#426b50;text-decoration:underline;text-decoration-color:#b9c9bc;text-underline-offset:3px;font-size:13px}.source-link:hover,.source-link[aria-expanded="true"]{background:transparent;border-color:transparent;color:#254d33;text-decoration-color:#426b50}.source-link span:last-child{white-space:normal;text-align:left}.source-number{display:none}.answer-layout.source-open{display:grid;grid-template-columns:minmax(0,1fr) minmax(390px,48%);gap:28px;align-items:start}.answer-layout.source-open .source-viewer{display:block!important}.source-viewer{border-left:1px solid var(--line);padding:0 0 0 20px;position:sticky;top:62px;min-width:0}.viewer-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.viewer-file{font-size:13px;font-weight:550;overflow-wrap:anywhere}.viewer-location{font-size:12px;color:var(--muted);margin-top:3px}.viewer-close{flex:none;border:0;background:transparent;color:#7a847c;padding:0 3px;font-size:20px;line-height:1}.viewer-close:hover{color:var(--ink)}.viewer-label{font-size:11px;color:#8c958e;margin:14px 0 6px}.viewer-quote{margin:0;font-size:14px;line-height:1.8;color:#414a43}.viewer-quote mark{background:#e4f0c5;color:inherit;padding:1px 2px;box-decoration-break:clone;-webkit-box-decoration-break:clone}.viewer-meta{font-size:11px;color:#8e978f;margin-top:11px}.source-link[aria-expanded="true"]{font-weight:650}.viewer-frame{display:block;width:100%;height:min(68vh,720px);min-height:430px;border:1px solid var(--line);margin-top:12px;background:#f5f6f4}.viewer-image{display:block;max-width:100%;max-height:68vh;object-fit:contain;object-position:top left;margin-top:12px}.viewer-open-link{display:inline-block;margin-top:12px;font-size:13px;color:var(--green);text-underline-offset:3px}
@media(max-width:800px){.answer-layout.source-open{grid-template-columns:1fr}.source-viewer{position:static;border-left:0;border-top:1px solid var(--line);padding:13px 0 0}.main{padding-top:27px}.viewer-frame{height:62vh;min-height:360px}}
#followup{position:fixed;left:calc(260px + max(20px,(100vw - 260px - 740px)/2));bottom:16px;width:min(740px,calc(100vw - 300px));margin:0;z-index:5;background:#fff}
.conversation{padding-bottom:145px}
.answer-layout.source-open{grid-template-columns:minmax(0,1fr) minmax(480px,min(48vw,850px));gap:36px}.answer-layout.source-open .source-viewer{display:flex!important;position:sticky;z-index:2;top:64px;height:calc(100vh - 82px);padding:0 0 0 24px;background:transparent;border:0;border-left:1px solid var(--line);border-radius:0;box-shadow:none;flex-direction:column;overflow:hidden}.main:has(.source-open){width:100%;max-width:none;padding-left:34px;padding-right:34px}.main:has(.source-open) .conversation{max-width:none}.viewer-head{flex:none}.viewer-controls{display:flex;align-items:center;gap:8px;margin-top:12px;flex:none}.viewer-controls button{border:1px solid var(--line);background:#fff;border-radius:6px;padding:4px 10px;color:var(--ink)}.viewer-zoom{font-size:12px;color:var(--muted);min-width:48px;text-align:center}.viewer-frame{flex:1;min-height:0;height:auto;margin-top:12px}.viewer-image{max-width:100%;max-height:none;object-fit:contain;margin:12px auto;overflow:auto}.viewer-content{flex:1;min-height:0;width:100%;border:1px solid var(--line);margin-top:12px;background:#fff}.viewer-pdf-image{flex:none;max-width:none;max-height:none;margin:12px auto;transform-origin:top center}.viewer-body{flex:1;min-height:0;display:flex;flex-direction:column;overflow:auto}
@media(max-width:800px){#followup{left:230px;width:calc(100vw - 250px)}}
@media(max-width:1000px){.answer-layout.source-open{grid-template-columns:minmax(0,1fr) minmax(390px,46vw);gap:22px}.main:has(.source-open){padding-left:22px;padding-right:22px}}
@media(max-width:800px){.main:has(.source-open){width:100%;padding-left:18px;padding-right:18px}.answer-layout.source-open{grid-template-columns:1fr}.answer-layout.source-open .source-viewer{position:relative;top:auto;height:75vh;border-left:0;border-top:1px solid var(--line);padding:16px 0 0}}
@media(max-width:600px){.main{padding:26px 20px 20px}.topbar{padding:0 15px}.welcome{margin-top:16vh}.welcome h1{font-size:25px}.answer-layout.source-open{display:block}.mobile-menu{width:30px;height:30px;border:0;background:transparent;margin-right:8px}.source-link{font-size:13px}.viewer-frame{height:58vh;min-height:320px}#followup{left:16px;right:16px;width:auto;bottom:12px}.conversation{padding-bottom:150px}}
/* Warm neutral surfaces and one restrained persimmon accent, inspired by Pi's sparse site. */
:root{--paper:#faf9f7;--white:#fff;--ink:#272622;--muted:#77746d;--line:#e9e6e0;--sage:#f1efea;--green:#a64e32;--green2:#a64e32;--mint:#f7f1ed;--amber:#8a632d}
body{background:var(--paper);color:var(--ink)}.sidebar{background:#f5f3ef;border-color:#e8e5df}.brand-mark,.send{background:#30302d}.plus,.source-link,.viewer-open-link{color:#9f4d34}.history-item.active{background:#eae6df;color:#34322d}.history-item:hover,.new-chat:hover{background:#efede8;border-color:#dfdbd3;color:#34322d}.answer-text{color:#35332f}.user-question{color:#77746d}.source-link:hover,.source-link[aria-expanded="true"]{color:#813c29;text-decoration-color:#9f4d34}.viewer-quote mark,.viewer-content mark{background:rgba(244,212,90,.32);color:inherit;padding:1px 2px;border-radius:2px;text-decoration:underline;text-decoration-color:#b7831c;text-decoration-thickness:1px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.main.source-open{width:100%;max-width:none;display:grid;grid-template-columns:minmax(0,1fr) minmax(410px,42vw);gap:30px;align-items:start;padding-left:32px;padding-right:30px}.conversation-pane{min-width:0}.main.source-open .conversation{max-width:none}.source-dock{position:sticky;top:58px;height:calc(100vh - 76px);min-width:0;display:flex;flex-direction:column;border-left:1px solid var(--line);padding-left:20px}.dock-tabs{display:flex;gap:3px;overflow-x:auto;flex:none;border-bottom:1px solid var(--line);margin-bottom:12px}.dock-tab{display:flex;align-items:center;max-width:220px;border-bottom:2px solid transparent;color:var(--muted)}.dock-tab.active{border-bottom-color:#9f4d34;color:var(--ink)}.dock-tab-select,.dock-tab-close{border:0;background:transparent;color:inherit}.dock-tab-select{max-width:185px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding:8px 7px;font-size:12px}.dock-tab-close{font-size:16px;padding:4px 7px}.dock-tab-close:hover{color:#9f4d34}.dock-content{display:flex;flex:1;min-height:0;flex-direction:column;overflow:hidden}.dock-content .viewer-head{flex:none}.dock-content .viewer-body,.dock-content .viewer-content{flex:1;min-height:0}.dock-content .viewer-body{display:flex;flex-direction:column;overflow:auto}.dock-content .viewer-image{max-width:100%;max-height:none}.dock-content .viewer-pdf-image{flex:none;max-width:none;max-height:none;margin:12px auto}.dock-content .viewer-controls{flex:none}.dock-content .viewer-open-link,.dock-content .viewer-meta{flex:none}.dock-content .viewer-content{display:block;width:100%;border:1px solid var(--line);margin-top:12px;background:#fff}.dock-content .viewer-label{margin:12px 0 5px}
@media(max-width:1000px){.main.source-open{grid-template-columns:minmax(0,1fr) minmax(360px,45vw);gap:20px;padding-left:22px;padding-right:22px}.source-dock{padding-left:14px}}
@media(max-width:800px){.main.source-open{grid-template-columns:1fr}.source-dock{position:relative;top:auto;height:75vh;border-left:0;border-top:1px solid var(--line);padding:14px 0 0}.main.source-open .conversation{max-width:100%}}
.user-question{width:fit-content;max-width:82%;margin-left:auto;padding:10px 14px;background:#f0eee9;border:1px solid #e7e3dc;border-radius:14px 14px 3px 14px;color:#383630;text-align:left}
.sidebar-head{display:flex;align-items:center;justify-content:space-between;gap:5px}.sidebar-head .brand{min-width:0}.sidebar-toggle,.sidebar-restore{width:29px;height:29px;flex:none;border:1px solid transparent;border-radius:6px;background:transparent;color:#77746d;display:grid;place-items:center;padding:0}.sidebar-toggle:hover,.sidebar-restore:hover{background:#ebe8e2;color:#383630}.sidebar-toggle svg,.sidebar-restore svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.sidebar-restore{margin-right:12px;border-color:var(--line);background:white}
@media(max-width:800px){.user-question{max-width:92%}}
/* Keep the conversation and composer in separate layout rows, like a conventional chat view. */
.workspace{height:100vh;min-height:0;overflow:hidden}
.topbar{display:none}
.main{width:100%;max-width:none;height:100%;min-height:0;flex:1;display:grid;grid-template-columns:minmax(0,1fr);grid-template-rows:minmax(0,1fr) auto;gap:0;margin:0;padding:22px 34px 0;overflow:hidden}
.conversation-pane{grid-column:1;grid-row:1;min-width:0;min-height:0;overflow-y:auto;overscroll-behavior:contain;scrollbar-gutter:stable both-edges}
.conversation{flex:none;padding-bottom:24px}
#followup,.main.source-open #followup,.app.sidebar-collapsed .main #followup{position:static;grid-column:1;grid-row:2;left:auto;right:auto;bottom:auto;width:min(740px,100%);max-width:740px;margin:8px auto 12px;transform:none;z-index:auto}
.main.source-open{grid-template-columns:minmax(0,1fr) 8px minmax(360px,var(--dock-width,46vw));grid-template-rows:minmax(0,1fr) auto;gap:0;padding:22px 26px 0;align-items:stretch}
.main.source-open .conversation-pane{grid-column:1;grid-row:1}
.main.source-open .conversation-pane{align-self:stretch;height:100%;max-height:100%;min-height:0;overflow-x:hidden;overflow-y:auto;overscroll-behavior-y:contain}
.dock-resizer{grid-column:2;grid-row:1 / 3;align-self:stretch;position:relative;z-index:2;cursor:col-resize;touch-action:none;display:grid;place-items:center;outline:none}
.dock-resizer::after{content:"";width:4px;height:42px;border-radius:4px;background:#d9d4cb;transition:background .15s,width .15s,height .15s}
.dock-resizer:hover::after,.dock-resizer:focus-visible::after,.dock-resizer.dragging::after{width:5px;height:54px;background:#a64e32}
.main.source-open .source-dock{position:relative;grid-column:3;grid-row:1 / 3;top:auto;height:100%;min-height:0;overflow:hidden}
.viewer-controls{order:0;width:max-content;max-width:100%;display:flex;align-items:center;gap:2px;margin:0 0 0 auto;padding:2px;border:1px solid #e9e5df;border-radius:9px;background:#fff;flex:none}
.viewer-controls button{width:29px;min-width:29px;height:27px;padding:0;border:0;border-radius:6px;background:transparent;color:#4a4842;display:grid;place-items:center;transition:background .15s,color .15s}
.viewer-controls button svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.viewer-controls button:hover{background:#f1efeb;color:#24231f}
.viewer-controls button:focus-visible{outline:2px solid #bba88f;outline-offset:1px}
.viewer-zoom{font-variant-numeric:tabular-nums;font-size:12px;color:#77746d;min-width:42px;text-align:center}
.viewer-zoom{min-width:48px;padding:4px 7px;border-radius:6px;background:#f3f2ef;color:#46443e;font-size:11px;font-weight:600;line-height:1.2}
.viewer-head{max-width:min(100%,48rem);align-items:center;gap:10px}.viewer-head>div:first-child{min-width:0;flex:1}.viewer-location{max-width:100%;font-size:12px;line-height:1.35;color:#6f766f;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.viewer-open-link{display:block;width:100%;min-width:154px;padding:8px 12px;border:1px solid #e8e5df;border-radius:8px;background:#fff;font-size:14px;font-weight:550;text-align:center;text-decoration-thickness:1px;text-underline-offset:3px}.viewer-open-link:hover{background:#f7f5f1;border-color:#d9d4ca}
.main.source-open.reader-expanded{grid-template-columns:0 0 minmax(0,1fr)}.main.reader-expanded .conversation-pane,.main.reader-expanded .dock-resizer{display:none!important}.main.reader-expanded .source-dock{grid-column:3;padding-left:0;border-left:0}
.viewer-file{font-size:13px;font-weight:600;overflow-wrap:anywhere}
.viewer-meta{display:none!important}
.sidebar-rail{height:100vh;min-width:0;background:#f5f3ef;border-right:1px solid #e8e5df;display:flex;justify-content:center;padding:13px 0}
.sidebar-rail.hidden{display:none!important}
.sidebar-home{width:34px;height:34px;display:grid;place-items:center;border:1px solid transparent;border-radius:8px;background:transparent;color:#5e5c55}
.sidebar-home:hover{background:#ebe8e2;color:#302f2b}
.sidebar-home svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.app.sidebar-collapsed{grid-template-columns:52px minmax(0,1fr)}
.app.sidebar-collapsed .sidebar{display:none}
.welcome{width:min(768px,100%);margin:auto;justify-items:stretch;text-align:left;padding:0}
.conversation-pane:has(#welcome:not(.hidden)){display:grid;place-items:center}
.conversation-pane:has(#welcome:not(.hidden)) .welcome{margin:0}
.composer-wrap{max-width:768px!important}
.composer-wrap #ask .composer-bottom{justify-content:flex-end}
.composer,.composer-wrap #ask{width:min(768px,100%);max-width:768px}
.conversation,.main.source-open .conversation{width:min(768px,100%);max-width:768px}
#followup,.main.source-open #followup,.app.sidebar-collapsed .main #followup{width:min(768px,100%);max-width:768px}
@media(max-width:800px){.main{padding:18px 20px 0}.main.source-open{grid-template-columns:minmax(0,1fr);grid-template-rows:minmax(0,1fr) auto minmax(260px,55vh);padding:18px 20px 0;gap:0}.dock-resizer{display:none}.main.source-open .source-dock{grid-column:1;grid-row:3;height:100%;border-left:0;border-top:1px solid var(--line);padding:12px 0 0}.main.source-open #followup{grid-column:1;grid-row:2;margin:8px auto 12px}.source-dock{position:relative;top:auto}.sidebar-toggle{display:grid}}
@media(max-width:600px){.app{display:block}.sidebar{position:fixed;z-index:6;left:0;top:0;bottom:0;width:270px;height:100vh;transform:translateX(-101%);transition:transform .2s;box-shadow:var(--shadow)}.sidebar.open{transform:translateX(0)}.sidebar-rail{position:fixed;z-index:4;left:0;top:0;bottom:0;width:52px;height:100vh}.sidebar-rail.hidden{display:flex!important}.app.sidebar-collapsed .workspace{margin-left:52px}.main,.main.source-open{height:100vh;min-height:0;padding:14px 14px 0}.main.source-open{grid-template-rows:minmax(0,1fr) auto minmax(230px,48vh)}.welcome{margin:12vh 0 0}.welcome h1{font-size:25px}.user-question{max-width:94%}.main.source-open .source-dock{height:100%}.viewer-frame{height:48vh;min-height:220px}}
</style></head><body>
<div class="app">
<aside class="sidebar" id="sidebar"><div class="sidebar-head"><div class="brand"><div class="brand-mark">A</div><div><div class="brand-name">Aegis</div><div class="brand-caption">Evidence workspace</div></div></div><button class="sidebar-toggle" id="sidebarToggle" type="button" aria-label="Hide question history" title="Hide question history"><svg viewBox="0 0 24 24" aria-hidden="true"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/><path d="m16 15-3-3 3-3"/></svg></button></div>
<button class="new-chat" id="newChat"><span class="plus">＋</span> New question</button>
<div class="side-label">Recent questions</div><nav class="history" id="history" aria-label="Recent questions"></nav>
<div class="sidebar-bottom"><div class="local-note"><strong><span class="dot"></span>Private, local workspace</strong><p>Answers use the supplied assessment files. Unknown details are called out clearly.</p></div></div></aside>
<aside class="sidebar-rail hidden" id="sidebarRail"><button class="sidebar-home" id="sidebarRestore" type="button" aria-label="Show question history" title="Show question history"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 10 9-7 9 7"/><path d="M5 9v12h14V9"/><path d="M9 21v-8h6v8"/></svg></button></aside>
<div class="workspace">
<main class="main"><div class="conversation-pane" id="conversationPane"><section class="welcome" id="welcome"><h1>Ask a question</h1>
<div class="composer-wrap" style="width:100%"><form class="composer" id="ask" autocomplete="off"><textarea id="question" name="question" maxlength="1200" required aria-label="Your question" placeholder="Ask anything about the supplied documents…"></textarea><div class="composer-bottom"><button class="send" id="submit" type="submit" aria-label="Ask Aegis"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg></button></div></form>
 </div></section>
<section class="conversation hidden" id="conversation" aria-live="polite" aria-busy="false"></section></div>
<div class="dock-resizer hidden" id="dockResizer" role="separator" aria-orientation="vertical" aria-label="Resize source reader" aria-valuemin="360" aria-valuemax="850" aria-valuenow="650" tabindex="0"></div>
<aside class="source-dock hidden" id="sourceDock" aria-label="Source reader"><div class="dock-tabs" id="sourceTabs" role="tablist" aria-label="Open sources"></div><div class="dock-content" id="sourceContent" role="tabpanel"></div></aside>
<form class="composer hidden" id="followup" autocomplete="off"><textarea id="followupQuestion" maxlength="1200" required aria-label="Ask a follow-up question" placeholder="Ask a follow-up question…"></textarea><div class="composer-bottom"><span class="composer-hint">Ask a follow-up</span><button class="send" type="submit" aria-label="Ask Aegis"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg></button></div></form>
</main></div></div>
<script>
const welcome=document.querySelector('#welcome'),conversation=document.querySelector('#conversation'),conversationPane=document.querySelector('#conversationPane'),form=document.querySelector('#ask'),followup=document.querySelector('#followup'),input=document.querySelector('#question'),followupInput=document.querySelector('#followupQuestion'),historyNode=document.querySelector('#history'),sidebar=document.querySelector('#sidebar'),sidebarRail=document.querySelector('#sidebarRail'),sourceDock=document.querySelector('#sourceDock'),dockResizer=document.querySelector('#dockResizer'),sourceTabsNode=document.querySelector('#sourceTabs'),sourceContent=document.querySelector('#sourceContent'),main=document.querySelector('.main'),app=document.querySelector('.app'),sidebarToggle=document.querySelector('#sidebarToggle'),sidebarRestore=document.querySelector('#sidebarRestore');
let sourceTabs=[],activeSourceKey=null,readerExpanded=false;
let threads=[];try{threads=JSON.parse(localStorage.getItem('aegis-history')||'[]');if(!Array.isArray(threads))threads=[]}catch{threads=[]}let activeId=null;
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n}
function save(){try{localStorage.setItem('aegis-history',JSON.stringify(threads.slice(0,30)))}catch{}}
function newThread(){activeId=null;welcome.classList.remove('hidden');conversation.classList.add('hidden');followup.classList.add('hidden');conversation.replaceChildren();input.value='';input.focus();renderHistory();sidebar.classList.remove('open')}
function renderHistory(){historyNode.replaceChildren();for(const thread of threads){const b=el('button','history-item'+(thread.id===activeId?' active':''),thread.title);b.type='button';b.title=thread.title;b.addEventListener('click',()=>showThread(thread.id));historyNode.append(b)}}
function pageNumber(locator){const match=locator.match(/\bp\.\s*(\d+)/i);return match?Number(match[1]):1}
function sourceUrl(source){return '/source/'+source.split('/').map(encodeURIComponent).join('/')}
function sourceViewUrl(source,quote,locator){const params=new URLSearchParams({quote,locator});return '/source-view/'+source.split('/').map(encodeURIComponent).join('/')+'?'+params.toString()}
function closeSourceTab(key){sourceTabs=sourceTabs.filter(tab=>tab.key!==key);if(activeSourceKey===key)activeSourceKey=sourceTabs.at(-1)?.key||null;renderSourceDock()}
function renderSourceDock(){sourceTabsNode.replaceChildren();const active=sourceTabs.find(tab=>tab.key===activeSourceKey);sourceDock.classList.toggle('hidden',!active);dockResizer.classList.toggle('hidden',!active);main.classList.toggle('source-open',!!active);main.classList.toggle('reader-expanded',!!active&&readerExpanded);if(!active){readerExpanded=false;return}for(const tab of sourceTabs){const item=el('div','dock-tab'+(tab.key===activeSourceKey?' active':''));item.setAttribute('role','tab');item.setAttribute('aria-selected',String(tab.key===activeSourceKey));const select=el('button','dock-tab-select',tab.evidence.source.split('/').pop());select.type='button';select.title=tab.evidence.source+' · '+tab.evidence.locator;select.addEventListener('click',()=>{activeSourceKey=tab.key;renderSourceDock()});const close=el('button','dock-tab-close','×');close.type='button';close.setAttribute('aria-label','Close '+tab.evidence.source);close.addEventListener('click',()=>closeSourceTab(tab.key));item.append(select,close);sourceTabsNode.append(item)}renderSourceContent(active.evidence)}
function openSource(evidence){const key=evidence.source+'\u0000'+evidence.locator+'\u0000'+evidence.quote;let tab=sourceTabs.find(item=>item.key===key);if(!tab){tab={key,evidence};sourceTabs.push(tab)}activeSourceKey=key;renderSourceDock()}
function openOriginal(url, text){const link=el('a','viewer-open-link',text);link.href=url;link.target='_blank';link.rel='noopener';return link}
function zoomIcon(kind){const paths={out:'<circle cx="10.8" cy="10.8" r="6.5"/><path d="m16 16 4.2 4.2M8.2 10.8h5.2"',in:'<circle cx="10.8" cy="10.8" r="6.5"/><path d="m16 16 4.2 4.2M8.2 10.8h5.2m-2.6-2.6V13.4"',reset:'<path d="M20 11a8 8 0 0 0-14.8-4L3 9"/><path d="M3 4v5h5M4 13a8 8 0 0 0 14.8 4L21 15"/><path d="M21 20v-5h-5"'};return '<svg viewBox="0 0 24 24" aria-hidden="true">'+paths[kind]+'</svg>'}
function formatLocator(locator){return locator.replace(/\bp\.\s*(\d+)/gi,'Page $1').replace(/;\s*/g,' · ')}
function expandIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3H3v5m0-5 7 7m6-7h5v5m0-5-7 7M3 16v5h5m-5 0 7-7m11 2v5h-5m5 0-7-7"/></svg>'}
function collapseIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3v6H3m0 0 7-7m5 0h6v6m0 0-7-7M3 15h6v6m0 0 1-7m11 1h-6v6m0 0-1-7"/></svg>'}
function addZoomControls(viewer,content){let zoom=100;const controls=el('div','viewer-controls'),out=el('button','',''),label=el('span','viewer-zoom','100%'),inc=el('button','',''),reset=el('button','',''),expand=el('button','','');out.type=inc.type=reset.type=expand.type='button';out.innerHTML=zoomIcon('out');inc.innerHTML=zoomIcon('in');reset.innerHTML=zoomIcon('reset');out.setAttribute('aria-label','Zoom out');out.title='Zoom out';inc.setAttribute('aria-label','Zoom in');inc.title='Zoom in';reset.setAttribute('aria-label','Reset zoom');reset.title='Reset zoom';function updateExpand(){expand.innerHTML=readerExpanded?collapseIcon():expandIcon();expand.setAttribute('aria-label',readerExpanded?'Return to split view':'Expand reader');expand.title=readerExpanded?'Return to split view':'Expand reader'}expand.addEventListener('click',()=>{readerExpanded=!readerExpanded;main.classList.toggle('reader-expanded',readerExpanded);updateExpand()});function update(){zoom=Math.max(50,Math.min(250,zoom));label.textContent=zoom+'%';if(content.tagName==='IMG'){content.style.width=zoom+'%';content.style.maxWidth='none'}else content.style.zoom=String(zoom/100)}out.addEventListener('click',()=>{zoom-=10;update()});inc.addEventListener('click',()=>{zoom+=10;update()});reset.addEventListener('click',()=>{zoom=100;update()});updateExpand();controls.append(out,label,inc,reset,expand);const header=viewer.querySelector('.viewer-head');if(header)header.append(controls);else{const contentStart=viewer.querySelector('.viewer-body,.viewer-content');viewer.insertBefore(controls,contentStart||null)}update()}
function renderSourceContent(evidence){sourceContent.replaceChildren();const url=sourceUrl(evidence.source),top=el('div','viewer-head'),heading=el('div','');heading.append(el('div','viewer-location',formatLocator(evidence.locator)));top.append(heading);sourceContent.append(top);const extension=evidence.source.split('.').pop().toLowerCase();if(extension==='pdf'){const page=pageNumber(evidence.locator),search=evidence.quote.replace(/\s+/g,' ').trim().slice(0,140),body=el('div','viewer-body');const image=el('img','viewer-image viewer-pdf-image');image.alt=evidence.source+' — cited page with highlighted passage';const params=new URLSearchParams({page:String(page),quote:search});image.src='/source-preview/'+evidence.source.split('/').map(encodeURIComponent).join('/')+'?'+params.toString();body.append(image);sourceContent.append(body);addZoomControls(sourceContent,image);sourceContent.append(openOriginal(url+'#page='+page+'&:~:text='+encodeURIComponent(search),'Open original PDF'))}else if(['png','jpg','jpeg','gif','webp','bmp'].includes(extension)){const body=el('div','viewer-body');const image=el('img','viewer-image');image.alt=evidence.source;image.src=url;body.append(image);sourceContent.append(body);addZoomControls(sourceContent,image);sourceContent.append(openOriginal(url,'Open full-size image'))}else if(['html','htm','xlsx','xlsm','docx','pptx','json','txt','csv'].includes(extension)){const frame=el('iframe','viewer-content');frame.title='Source document '+evidence.source;frame.setAttribute('sandbox','');frame.src=sourceViewUrl(evidence.source,evidence.quote,evidence.locator);sourceContent.append(frame);addZoomControls(sourceContent,frame);sourceContent.append(openOriginal(url,'Download original file'))}else{const quote=el('blockquote','viewer-quote'),mark=el('mark','',evidence.quote);quote.append(mark);sourceContent.append(quote);sourceContent.append(openOriginal(url,'Open original file'))}}
function appendAnswer(parent,item){
 const layout=el('div','answer-layout'),column=el('div','answer-column'),card=el('article','answer-card'),head=el('div','answer-head');
 head.append(el('span','answer-label','Answer'),el('span','status '+item.data.status,item.data.status==='answered'?'Supported by sources':'Not established'));
 card.append(head,el('p','answer-text',item.data.answer));
 if(item.data.evidence?.length){
  const section=el('section','section');section.append(el('h2','section-title','Sources'));
  const list=el('div','source-list');
  item.data.evidence.forEach(evidence=>{
   const label=evidence.source.split('/').pop()+' · '+evidence.locator,link=el('button','source-link',label);
   link.type='button';link.setAttribute('aria-label','Open source '+evidence.source+', '+evidence.locator);
   link.addEventListener('click',()=>openSource(evidence));
   list.append(link);
  });
  section.append(list);column.append(card,section);layout.append(column);
 }else{column.append(card);layout.append(column)}
 parent.append(layout);
}
function showThread(id){const thread=threads.find(t=>t.id===id);if(!thread)return;activeId=id;welcome.classList.add('hidden');conversation.classList.remove('hidden');followup.classList.remove('hidden');conversation.replaceChildren();for(const item of thread.items){conversation.append(el('div','user-question',item.question));appendAnswer(conversation,item)}renderHistory();sidebar.classList.remove('open');conversationPane.scrollTo({top:conversationPane.scrollHeight,behavior:'smooth'})}
async function ask(question,button,targetForm){button.disabled=true;targetForm.querySelector('textarea').disabled=true;let thread=threads.find(t=>t.id===activeId);if(!thread){thread={id:crypto.randomUUID?crypto.randomUUID():String(Date.now()),title:question.slice(0,62),items:[]};threads.unshift(thread);activeId=thread.id}const pending={question,data:{status:'answered',answer:'Searching the supplied documents…',claims:[],evidence:[]}};thread.items.push(pending);welcome.classList.add('hidden');conversation.classList.remove('hidden');followup.classList.remove('hidden');conversation.setAttribute('aria-busy','true');renderHistory();showThread(thread.id);conversation.setAttribute('aria-busy','true');try{const response=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question})});const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed');pending.data=data;save();showThread(thread.id)}catch(error){pending.data={status:'insufficient_evidence',answer:'The local service could not complete this request. '+error.message,claims:[],evidence:[]};save();showThread(thread.id)}finally{button.disabled=false;targetForm.querySelector('textarea').disabled=false;conversation.setAttribute('aria-busy','false');targetForm.querySelector('textarea').value='';targetForm.querySelector('textarea').focus()}}
form.addEventListener('submit',event=>{event.preventDefault();const question=input.value.trim();if(question)ask(question,form.querySelector('button'),form)});followup.addEventListener('submit',event=>{event.preventDefault();const question=followupInput.value.trim();if(question)ask(question,followup.querySelector('button'),followup)});
function setSidebarCollapsed(collapsed){if(window.matchMedia('(max-width:600px)').matches){if(collapsed)sidebar.classList.remove('open');else sidebar.classList.add('open');return}app.classList.toggle('sidebar-collapsed',collapsed);sidebarRail.classList.toggle('hidden',!collapsed);sidebar.style.display=collapsed?'none':'';app.style.gridTemplateColumns=collapsed?'52px minmax(0,1fr)':''}
function setDockWidth(width){const maxWidth=Math.max(360,Math.min(window.innerWidth*.68,main.clientWidth-420));width=Math.max(360,Math.min(maxWidth,width));main.style.setProperty('--dock-width',width+'px');dockResizer.setAttribute('aria-valuemax',String(Math.round(maxWidth)));dockResizer.setAttribute('aria-valuenow',String(Math.round(width)))}
dockResizer.addEventListener('pointerdown',event=>{if(window.matchMedia('(max-width:800px)').matches)return;event.preventDefault();const startX=event.clientX,startWidth=sourceDock.getBoundingClientRect().width;dockResizer.classList.add('dragging');dockResizer.setPointerCapture(event.pointerId);const move=e=>setDockWidth(startWidth+startX-e.clientX),end=()=>{dockResizer.classList.remove('dragging');dockResizer.removeEventListener('pointermove',move);dockResizer.removeEventListener('pointerup',end);dockResizer.removeEventListener('pointercancel',end)};dockResizer.addEventListener('pointermove',move);dockResizer.addEventListener('pointerup',end);dockResizer.addEventListener('pointercancel',end)});
dockResizer.addEventListener('keydown',event=>{if(event.key!=='ArrowLeft'&&event.key!=='ArrowRight')return;event.preventDefault();const current=sourceDock.getBoundingClientRect().width;setDockWidth(current+(event.key==='ArrowLeft'?32:-32))});
document.querySelector('#newChat').addEventListener('click',newThread);sidebarToggle.addEventListener('click',()=>setSidebarCollapsed(true));sidebarRestore.addEventListener('click',()=>setSidebarCollapsed(false));renderHistory();
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
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-src 'self'; base-uri 'none'; frame-ancestors 'none'")

    def do_GET(self) -> None:
        if urlsplit(self.path).path.startswith("/source-view/"):
            self._serve_document_view()
            return
        if urlsplit(self.path).path.startswith("/source-preview/"):
            self._serve_pdf_preview()
            return
        if urlsplit(self.path).path.startswith("/source/"):
            self._serve_source()
            return
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

    def _serve_document_view(self) -> None:
        """Render office/text documents as a safe, readable HTML document view."""
        target = self._dataset_file(urlsplit(self.path).path.removeprefix("/source-view/"))
        if target is None:
            self._json(404, {"error": "Source not found."})
            return
        suffix = target.suffix.lower()
        query = parse_qs(urlsplit(self.path).query)
        quote = " ".join(query.get("quote", [""])[0].split())[:1000]
        locator = query.get("locator", [""])[0]
        row_match = re.search(r"!\$?[A-Z]{1,3}\$?(\d+)(?::\$?[A-Z]{1,3}\$?(\d+))?", locator, re.I)
        row_range = (int(row_match.group(1)), int(row_match.group(2) or row_match.group(1))) if row_match else None
        sheet_match = re.match(r"([^!]+)!", locator)
        target_sheet = sheet_match.group(1).replace("'", "") if sheet_match else ""
        def render_value(value: Any) -> str:
            text = " ".join(str(value).split())
            safe = html_lib.escape(text)
            if not quote or not text:
                return safe
            words = quote.split()
            candidates = [quote]
            for size in range(min(12, len(words)), 0, -1):
                candidates.extend(" ".join(words[index:index + size]) for index in range(0, len(words) - size + 1) if len(" ".join(words[index:index + size]).strip(".,;:|")) >= 3)
            match = next((candidate for candidate in candidates if candidate.casefold() in text.casefold()), None)
            if not match:
                return safe
            start = text.casefold().find(match.casefold())
            return html_lib.escape(text[:start]) + "<mark>" + html_lib.escape(text[start:start + len(match)]) + "</mark>" + html_lib.escape(text[start + len(match):])
        if suffix in {".html", ".htm"}:
            # This endpoint is always embedded in a sandboxed iframe. The CSP
            # additionally disables scripts and remote resources.
            body = target.read_bytes()
        else:
            esc = html_lib.escape
            parts = ["<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'><style>body{font:16px/1.6 system-ui,sans-serif;color:#26342c;margin:24px}h1{font-size:20px}h2{font-size:17px;margin:28px 0 8px}table{border-collapse:collapse;width:100%;margin:12px 0 26px}td,th{border:1px solid #dce3dc;padding:7px 9px;text-align:left;vertical-align:top}th{background:#f1f5f1;position:sticky;top:0}pre{white-space:pre-wrap;overflow-wrap:anywhere} .sheet{overflow:auto}mark{background:rgba(244,212,90,.32);color:inherit;padding:1px 2px;border-radius:2px;text-decoration:underline;text-decoration-color:#b7831c;text-decoration-thickness:1px;box-decoration-break:clone;-webkit-box-decoration-break:clone}</style><body>"]
            try:
                if suffix in {".xlsx", ".xlsm"}:
                    from openpyxl import load_workbook
                    book = load_workbook(target, read_only=True, data_only=True)
                    for sheet in book.worksheets:
                        if target_sheet and sheet.title.casefold() != target_sheet.casefold():
                            continue
                        parts.append(f"<h2>{esc(sheet.title)}</h2><div class='sheet'><table>")
                        for row_index, row in enumerate(sheet.iter_rows(values_only=True), 1):
                            values = list(row)
                            if not any(value is not None for value in values):
                                continue
                            highlighted_row = row_range is None or row_range[0] <= row_index <= row_range[1]
                            parts.append("<tr>" + "".join(f"<td>{render_value(value) if value is not None and highlighted_row else esc(str(value)) if value is not None else ''}</td>" for value in values) + "</tr>")
                        parts.append("</table></div>")
                    book.close()
                elif suffix == ".docx":
                    from docx import Document
                    document = Document(target)
                    parts.append(f"<h1>{esc(target.name)}</h1>")
                    for paragraph in document.paragraphs:
                        if paragraph.text.strip():
                            parts.append(f"<p>{render_value(paragraph.text)}</p>")
                    for index, table in enumerate(document.tables, 1):
                        parts.append(f"<h2>Table {index}</h2><table>")
                        for row in table.rows:
                            parts.append("<tr>" + "".join(f"<td>{render_value(cell.text)}</td>" for cell in row.cells) + "</tr>")
                        parts.append("</table>")
                elif suffix == ".pptx":
                    from pptx import Presentation
                    deck = Presentation(target)
                    for index, slide in enumerate(deck.slides, 1):
                        parts.append(f"<h2>Slide {index}</h2>")
                        for shape in slide.shapes:
                            if getattr(shape, "has_text_frame", False) and shape.text.strip():
                                parts.append(f"<p>{render_value(shape.text).replace(chr(10), '<br>')}</p>")
                elif suffix in {".json", ".txt", ".csv"}:
                    text = target.read_text(encoding="utf-8", errors="replace")
                    parts.extend([f"<h1>{esc(target.name)}</h1><pre>{render_value(text)}</pre>"])
                else:
                    self._json(415, {"error": "This file type has no in-app preview."})
                    return
            except Exception:
                logging.exception("source document view failed")
                self._json(422, {"error": "The source document could not be rendered."})
                return
            parts.append("</body>")
            body = "".join(parts).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", "default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_source(self) -> None:
        encoded = urlsplit(self.path).path.removeprefix("/source/")
        target = self._dataset_file(encoded)
        if target is None:
            self._json(404, {"error": "Source not found."})
            return

        media_type = guess_type(target.name)[0] or "application/octet-stream"
        suffix = target.suffix.lower()
        viewable = suffix == ".pdf" or media_type.startswith("image/")
        # Active HTML and office files download instead of executing in the app's origin.
        if suffix in {".html", ".htm", ".docx", ".pptx", ".xlsx", ".xlsm"}:
            viewable = False
        body = target.read_bytes()
        disposition = "inline" if viewable else "attachment"
        self.send_response(200)
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Disposition", f'{disposition}; filename="{target.name.replace(chr(34), "")}"')
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _dataset_file(encoded: str) -> Path | None:
        relative = unquote(encoded)
        if not relative or "\\" in relative or "\x00" in relative:
            return None
        parsed = PurePosixPath(relative)
        parts = parsed.parts
        if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parts):
            return None
        try:
            root = DATASET_DIR.resolve(strict=True)
            target = (PROJECT_DIR.parent.joinpath(*parts)).resolve(strict=True)
            target.relative_to(root)
            return target if target.is_file() else None
        except (OSError, ValueError):
            return None

    def _serve_pdf_preview(self) -> None:
        parsed = urlsplit(self.path)
        target = self._dataset_file(parsed.path.removeprefix("/source-preview/"))
        if target is None or target.suffix.lower() != ".pdf":
            self._json(404, {"error": "PDF source not found."})
            return
        params = parse_qs(parsed.query)
        try:
            page_number = int(params.get("page", ["1"])[0])
        except ValueError:
            page_number = 1
        quote = " ".join(params.get("quote", [""])[0].split())[:500].rstrip(" \t\r\n.,;:")
        document = None
        try:
            document = pdfium.PdfDocument(target)
            if page_number < 1 or page_number > len(document):
                self._json(404, {"error": "PDF page not found."})
                return
            page = document[page_number - 1]
            width, height = page.get_size()
            scale = min(1.8, 1400 / max(width, height))
            image = page.render(scale=scale).to_pil().convert("RGBA")
            if quote:
                text_page = page.get_textpage()
                candidates = [quote]
                words = quote.split()
                while len(words) > 5:
                    words = words[:-2]
                    candidates.append(" ".join(words))
                match = None
                for candidate in candidates:
                    match = text_page.search(candidate, match_case=False).get_next()
                    if match:
                        break
                if match:
                    rect_count = text_page.count_rects(*match)
                    highlight_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(highlight_layer)
                    for index in range(rect_count):
                        left, bottom, right, top = text_page.get_rect(index)
                        box = (
                            max(0, int(left * scale) - 3),
                            max(0, int((height - top) * scale) - 3),
                            min(image.width, int(right * scale) + 3),
                            min(image.height, int((height - bottom) * scale) + 3),
                        )
                        draw.rounded_rectangle(box, radius=3, fill=(255, 224, 88, 34), outline=(176, 139, 34, 145), width=2)
                    image = Image.alpha_composite(image, highlight_layer)
            output = BytesIO()
            image.save(output, format="PNG")
            body = output.getvalue()
        except Exception:
            logging.exception("PDF preview failed")
            self._json(422, {"error": "The cited PDF page could not be rendered."})
            return
        finally:
            if document is not None:
                document.close()
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Disposition", "inline; filename=\"source-page.png\"")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
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
