#!/usr/bin/env python3
"""
generar_dashboard.py
Lee capacity-data.xlsx y genera capacity-dashboard.html con los datos
ya incrustados. El HTML resultante se abre directamente en el navegador
sin necesidad de servidor ni JSON.

Uso:
    python generar_dashboard.py
    python generar_dashboard.py --excel otro.xlsx --output dashboard.html
"""

import json
import argparse
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

# ── Auto-instalación de dependencias ────────────────────
def _install(package):
    print(f"  Instalando {package} (primera vez, espere un momento)...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", package, "--quiet"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print(f"  {package} instalado OK.")

for _pkg in ["pandas", "openpyxl"]:
    try:
        __import__(_pkg)
    except ImportError:
        _install(_pkg)

import pandas as pd

# ── Argumentos ───────────────────────────────────────────
parser = argparse.ArgumentParser(description="Excel → HTML Dashboard (datos incrustados)")
parser.add_argument("--excel",  default="capacity-data.xlsx", help="Ruta al archivo Excel")
parser.add_argument("--output", default="capacity-dashboard.html", help="Ruta del HTML de salida")
args = parser.parse_args()

EXCEL_PATH  = Path(args.excel)
OUTPUT_PATH = Path(args.output)

if not EXCEL_PATH.exists():
    raise SystemExit(f"\n❌ No se encontró: {EXCEL_PATH}\n   Asegúrate de que el Excel esté en la misma carpeta que este script.\n")

print(f"\n📂 Leyendo {EXCEL_PATH} ...")

# ════════════════════════════════════════════════════════
#  LECTURA DE HOJAS
# ════════════════════════════════════════════════════════
def read_sheet(name):
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=name, dtype=str)
        df = df.where(pd.notna(df), None)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        raise SystemExit(f"\n❌ Error leyendo hoja '{name}': {e}\n   Verifica que el archivo Excel no esté abierto en otro programa.\n")

df_cfg   = read_sheet("Config")
df_areas = read_sheet("Areas")
df_kpis  = read_sheet("KPIs")
df_cob   = read_sheet("Cobertura")
df_pais  = read_sheet("Países")
df_alt   = read_sheet("Alertas_Areas")
df_nov   = read_sheet("Novedades")
df_acom  = read_sheet("Alertas_Comite")
df_comp  = read_sheet("Compromisos")

# ════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════
def safe(val):
    if val is None: return None
    s = str(val).strip()
    return None if s == "" else s

def safe_int(val):
    try: return int(float(str(val).strip()))
    except: return 0

# ════════════════════════════════════════════════════════
#  lastUpdate
# ════════════════════════════════════════════════════════
cfg_row = df_cfg[df_cfg.iloc[:, 0].astype(str).str.strip() == "lastUpdate"]
last_update = cfg_row.iloc[0, 1].strip() if not cfg_row.empty else datetime.now().isoformat(timespec='seconds')

# ════════════════════════════════════════════════════════
#  CONSTRUIR DATOS
# ════════════════════════════════════════════════════════
areas = []
for _, ar in df_areas.iterrows():
    aid   = safe(ar.iloc[0])
    aname = safe(ar.iloc[1])
    if not aid: continue

    # KPIs
    kr = df_kpis[df_kpis.iloc[:, 0].astype(str).str.strip() == aid]
    kpis = []
    if not kr.empty:
        r = kr.iloc[0]
        for idx, label in [(2,"RITM"),(3,"Change"),(4,"Incidentes")]:
            kpis.append({"n": label, "v": safe_int(r.iloc[idx])})

    # Cobertura
    cr = df_cob[df_cob.iloc[:, 0].astype(str).str.strip() == aid]
    cobertura = []
    if not cr.empty:
        for idx in range(2, len(cr.iloc[0])):
            v = safe(cr.iloc[0].iloc[idx])
            if v: cobertura.append(v)

    # Países
    countries = []
    for _, pr in df_pais[df_pais.iloc[:, 0].astype(str).str.strip() == aid].iterrows():
        if not safe(pr.iloc[1]): continue
        countries.append({
            "country":   safe(pr.iloc[1]),
            "flag":      safe(pr.iloc[2]) or "🌎",
            "available": safe_int(pr.iloc[3]),
            "total":     safe_int(pr.iloc[4]),
            "status":    safe(pr.iloc[5]) or "ok",
            "role":      safe(pr.iloc[6]) or "",
            "lead":      safe(pr.iloc[7]) or "",
        })

    # Alertas del área
    alertas = []
    for _, al in df_alt[df_alt.iloc[:, 0].astype(str).str.strip() == aid].iterrows():
        if not safe(al.iloc[1]): continue
        alertas.append({
            "tipo":    "Alerta",
            "icono":   "⚠️",
            "titulo":  safe(al.iloc[1]) or "",
            "desc":    safe(al.iloc[2]) or "",
            "impacto": safe(al.iloc[3]) or "Medio",
            "plan":    safe(al.iloc[4]) or "",
            "resp":    safe(al.iloc[5]) or "",
            "eta":     safe(al.iloc[6]) or "Q2",
        })

    # Novedades
    logros, proyectos, otros = [], [], []
    for _, nr in df_nov[df_nov.iloc[:, 0].astype(str).str.strip() == aid].iterrows():
        tipo  = safe(nr.iloc[1]) or ""
        texto = safe(nr.iloc[2]) or ""
        if not texto: continue
        if   tipo == "logro":    logros.append(texto)
        elif tipo == "proyecto": proyectos.append(texto)
        else:                    otros.append(texto)

    areas.append({
        "id":            aid,
        "name":          aname,
        "funcionalidad": safe(ar.iloc[2]) or "Estable",
        "funcDesc":      safe(ar.iloc[3]) or "",
        "kpis":          kpis,
        "kpiNote":       safe(ar.iloc[4]) or "",
        "cobertura":     cobertura,
        "countries":     countries,
        "alertas":       alertas,
        "novedades":     {"logros": logros, "proyectos": proyectos, "otros": otros},
    })

# Alertas Comité
alerts = []
for _, al in df_acom.iterrows():
    if not safe(al.iloc[1]): continue
    tags = [t.strip() for t in (safe(al.iloc[3]) or "").split(",") if t.strip()]
    alerts.append({
        "sev":   safe(al.iloc[0]) or "info",
        "title": safe(al.iloc[1]) or "",
        "desc":  safe(al.iloc[2]) or "",
        "tags":  tags,
        "date":  safe(al.iloc[4]) or "",
    })

# Compromisos
commitments = []
for _, co in df_comp.iterrows():
    if not safe(co.iloc[0]): continue
    commitments.append({
        "title":  safe(co.iloc[0]) or "",
        "desc":   safe(co.iloc[1]) or "",
        "status": safe(co.iloc[2]) or "pend",
        "label":  safe(co.iloc[3]) or "Pendiente",
        "due":    safe(co.iloc[4]) or "",
        "owner":  safe(co.iloc[5]) or "",
    })

DATA = {
    "lastUpdate":  last_update,
    "areas":       areas,
    "alerts":      alerts,
    "commitments": commitments,
}

print(f"   ✓ {len(areas)} áreas  |  {sum(len(a['countries']) for a in areas)} países  |  {len(alerts)} alertas comité  |  {len(commitments)} compromisos")

# ════════════════════════════════════════════════════════
#  PLANTILLA HTML
# ════════════════════════════════════════════════════════
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gestión de Capacity e Iniciativas de Delivery</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Barlow+Condensed:wght@500;700;800&display=swap');
:root{
  --primary:#00915A;--primary-dark:#006B43;--primary-glow:rgba(0,145,90,0.14);
  --gray-main:#595959;--gray-mid:#7F7F7F;--gray-light:#BFBFBF;
  --coral:#EF7B5B;--lime:#A3C439;--amber:#E8A020;--sky:#56B4C0;--pink:#BA3075;
  --bg:#111111;--surface:#1A1A1A;--surface2:#222222;--surface3:#2A2A2A;
  --border:#333333;--border2:#444444;--text:#F0F0F0;--muted:#888888;--subtle:#555555;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;}
header{background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:stretch;}
.h-accent{width:5px;flex-shrink:0;background:linear-gradient(180deg,var(--gray-main) 0%,var(--primary) 100%);}
.h-content{flex:1;display:flex;align-items:center;justify-content:space-between;padding:14px 32px;flex-wrap:wrap;gap:10px;}
.h-left{display:flex;align-items:center;gap:14px;}
.logo-slot{width:48px;height:48px;border-radius:8px;border:1.5px dashed var(--border2);background:var(--surface2);display:flex;align-items:center;justify-content:center;flex-shrink:0;overflow:hidden;cursor:pointer;transition:border-color .2s;}
.logo-slot:hover{border-color:var(--primary);}
.logo-slot img{width:100%;height:100%;object-fit:contain;}
.logo-placeholder{font-size:8px;color:var(--subtle);text-align:center;line-height:1.3;pointer-events:none;}
.h-title{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;line-height:1;}
.h-sub{font-size:10px;color:var(--muted);margin-top:2px;letter-spacing:.3px;}
.h-badge{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);background:var(--surface2);border:1px solid var(--border);border-radius:20px;padding:5px 12px;}
.live{width:6px;height:6px;background:var(--primary);border-radius:50%;animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

.tabs{display:flex;gap:2px;padding:12px 32px 0;background:var(--surface);border-bottom:1px solid var(--border);overflow-x:auto;}
.tbtn{font-family:'Inter',sans-serif;font-size:12px;font-weight:500;color:var(--muted);background:transparent;border:none;cursor:pointer;padding:7px 14px;border-radius:5px 5px 0 0;border-bottom:2px solid transparent;white-space:nowrap;transition:all .15s;}
.tbtn:hover{color:var(--text);background:rgba(255,255,255,.04);}
.tbtn.active{color:var(--primary);border-bottom-color:var(--primary);background:var(--primary-glow);}
.tbadge{display:inline-block;font-size:9px;font-weight:700;border-radius:10px;padding:1px 6px;margin-left:4px;vertical-align:middle;}
.tbr{background:rgba(239,123,91,.22);color:var(--coral);}
.tbg{background:rgba(0,145,90,.2);color:var(--primary);}
main{padding:20px 32px 60px;max-width:1600px;margin:0 auto;}
.tab-panel{display:none;}
.tab-panel.active{display:block;animation:fu .2s ease;}
@keyframes fu{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.fbar{display:flex;align-items:center;gap:6px;margin-bottom:20px;flex-wrap:wrap;}
.fl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-right:2px;}
.fbtn{font-size:11px;font-weight:500;background:var(--surface2);color:var(--muted);border:1px solid var(--border);border-radius:14px;padding:4px 12px;cursor:pointer;transition:all .14s;white-space:nowrap;font-family:'Inter',sans-serif;}
.fbtn:hover{color:var(--text);border-color:var(--primary);}
.fbtn.active{background:var(--primary);color:#fff;border-color:var(--primary);}
.area-nav{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;padding:10px 14px;background:var(--surface);border:1px solid var(--border);border-radius:8px;}
.area-nav-title{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:var(--primary);}
.nav-arrow{font-size:11px;color:var(--muted);cursor:pointer;padding:5px 10px;border-radius:5px;border:1px solid var(--border);background:transparent;transition:all .14s;font-family:'Inter',sans-serif;}
.nav-arrow:hover{color:var(--text);border-color:var(--primary);}
.area-body{display:grid;grid-template-columns:220px 1fr 260px;gap:12px;align-items:start;}
.left-panel{display:flex;flex-direction:column;gap:10px;}
.lp-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px;}
.lp-section-title{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--primary);margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid var(--border);}
.func-status{display:flex;align-items:center;gap:8px;margin-bottom:6px;}
.func-label{font-size:13px;font-weight:600;}
.func-check{width:18px;height:18px;background:var(--primary);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:10px;color:#fff;}
.func-desc{font-size:11px;color:var(--muted);line-height:1.5;}
.kpi-row{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--border);}
.kpi-row:last-child{border-bottom:none;}
.kpi-name{font-size:11px;color:var(--muted);}
.kpi-val{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:700;color:var(--text);}
.kpi-total-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0 0;margin-top:2px;}
.kpi-total-name{font-size:11px;font-weight:600;color:var(--text);}
.kpi-total-val{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:700;color:var(--primary);}
.kpi-note{font-size:9px;color:var(--subtle);line-height:1.4;margin-top:8px;}
.cov-item{display:flex;align-items:flex-start;gap:7px;margin-bottom:8px;}
.cov-icon{width:14px;height:14px;background:var(--primary);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;font-size:8px;color:#fff;}
.cov-text{font-size:11px;color:var(--muted);line-height:1.4;}
.cov-text strong{color:var(--text);font-weight:500;}
.panel-header{background:var(--primary);border-radius:8px 8px 0 0;padding:10px 14px;display:flex;align-items:center;justify-content:space-between;}
.panel-header-title{font-family:'Barlow Condensed',sans-serif;font-size:15px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#fff;}
.impact-pills{display:flex;gap:6px;}
.ipill{font-size:10px;font-weight:700;padding:3px 10px;border-radius:5px;}
.ipill-alto{background:#fff;color:var(--coral);}
.ipill-medio{background:#fff;color:var(--amber);}
.ipill-bajo{background:#fff;color:var(--primary);}
.alerts-table{background:var(--surface);border:1px solid var(--border);border-top:none;border-radius:0 0 8px 8px;overflow:hidden;}
.at-header{display:grid;grid-template-columns:36px 1fr 80px 160px 100px;background:var(--surface2);border-bottom:1px solid var(--border);}
.at-header div{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);padding:7px 10px;}
.alert-row{display:grid;grid-template-columns:36px 1fr 80px 160px 100px;border-bottom:1px solid var(--border);align-items:start;}
.alert-row:last-child{border-bottom:none;}
.alert-row:hover{background:var(--surface2);}
.ar-icon{padding:14px 8px;display:flex;align-items:flex-start;justify-content:center;}
.ar-desc{padding:12px 10px;}
.ar-desc-title{font-size:12px;font-weight:600;margin-bottom:4px;}
.ar-desc-text{font-size:11px;color:var(--muted);line-height:1.5;}
.ar-impact{padding:12px 10px;display:flex;align-items:flex-start;justify-content:center;}
.impact-badge{font-size:10px;font-weight:700;padding:3px 10px;border-radius:5px;border:1.5px solid;white-space:nowrap;}
.ib-alto{border-color:var(--coral);color:var(--coral);}
.ib-medio{border-color:var(--amber);color:var(--amber);}
.ib-bajo{border-color:var(--primary);color:var(--primary);}
.ar-plan{padding:12px 10px;font-size:11px;color:var(--muted);line-height:1.5;}
.ar-resp{padding:12px 10px;display:flex;flex-direction:column;gap:5px;align-items:flex-start;}
.resp-text{font-size:11px;color:var(--muted);}
.quarter-badge{font-family:'Barlow Condensed',sans-serif;font-size:13px;font-weight:700;background:var(--primary-dark);color:#fff;padding:3px 10px;border-radius:5px;letter-spacing:1px;}
.right-panel{display:flex;flex-direction:column;gap:10px;}
.rp-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;overflow:hidden;}
.rp-header{background:var(--surface2);padding:9px 14px;border-bottom:1px solid var(--border);}
.rp-header-title{font-family:'Barlow Condensed',sans-serif;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text);}
.rp-body{padding:12px 14px;}
.rp-tag{display:inline-block;font-size:10px;font-weight:700;padding:3px 10px;border-radius:5px;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px;}
.tag-green{background:var(--primary);color:#fff;}
.tag-gray{background:var(--surface3);color:var(--gray-light);border:1px solid var(--border2);}
.rp-text{font-size:11px;color:var(--muted);line-height:1.6;}
.rp-text li{margin-left:12px;margin-top:3px;}
.rp-text li::marker{color:var(--primary);}
.rp-section{margin-bottom:10px;}
.rp-section:last-child{margin-bottom:0;}
.alist{display:flex;flex-direction:column;gap:8px;}
.aitem{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--coral);border-radius:0 8px 8px 0;padding:13px 15px;display:flex;gap:11px;align-items:flex-start;}
.aitem.warn{border-left-color:var(--amber);}
.aitem.info{border-left-color:var(--sky);}
.asev{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 7px;border-radius:8px;white-space:nowrap;flex-shrink:0;margin-top:1px;}
.sc{background:rgba(239,123,91,.18);color:var(--coral);}
.sw{background:rgba(232,160,32,.18);color:var(--amber);}
.si2{background:rgba(86,180,192,.15);color:var(--sky);}
.abody{flex:1;}
.atitle{font-size:12px;font-weight:600;margin-bottom:3px;}
.adesc{font-size:11px;color:var(--muted);line-height:1.5;}
.atags{display:flex;gap:5px;margin-top:7px;flex-wrap:wrap;}
.atag{font-size:9px;background:var(--surface2);border:1px solid var(--border);border-radius:5px;padding:2px 7px;color:var(--muted);}
.adate{font-size:9px;color:var(--subtle);margin-top:3px;}
.clist{display:flex;flex-direction:column;gap:8px;}
.citem{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:13px 15px;display:flex;gap:13px;align-items:flex-start;}
.cnum{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:700;color:var(--primary);flex-shrink:0;min-width:28px;}
.cbody{flex:1;}
.ctitle2{font-size:12px;font-weight:600;margin-bottom:3px;}
.cdesc{font-size:11px;color:var(--muted);line-height:1.5;}
.cfoot{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;align-items:center;}
.csbadge{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 8px;border-radius:8px;}
.cp{background:rgba(86,180,192,.18);color:var(--sky);}
.cd{background:rgba(0,145,90,.18);color:var(--primary);}
.ce{background:rgba(232,160,32,.15);color:var(--amber);}
.cl{background:rgba(186,48,117,.18);color:var(--pink);}
.cmeta2{font-size:10px;color:var(--muted);}
.lbox{text-align:center;padding:50px 20px;color:var(--muted);font-size:12px;}
@media(max-width:900px){.area-body{grid-template-columns:1fr;}.at-header,.alert-row{grid-template-columns:32px 1fr 70px;}.at-header div:nth-child(4),.at-header div:nth-child(5),.alert-row .ar-plan,.alert-row .ar-resp{display:none;}}
@media(max-width:600px){.h-content,.tabs,main{padding-left:14px;padding-right:14px;}}
</style>
</head>
<body>
<header>
  <div class="h-accent"></div>
  <div class="h-content">
    <div class="h-left">
      <div class="logo-slot" id="logo-slot" title="Clic para cargar logo">
        <div class="logo-placeholder">LOGO<br>empresa</div>
      </div>
      <div>
        <div class="h-title">Gestión de Capacity e Iniciativas de Delivery</div>
        <div class="h-sub">Capacity por país y área · Comités &amp; Compromisos</div>
      </div>
    </div>
    <div class="h-badge">
      <span class="live"></span>
      <span id="lupd">--</span>
    </div>
  </div>
</header>

<div class="tabs">
  <button class="tbtn active" data-tab="cap" onclick="sw('cap')">Estado General por Área</button>
  <button class="tbtn" data-tab="alt" onclick="sw('alt')">Alertas Comité <span class="tbadge tbr" id="ba">–</span></button>
  <button class="tbtn" data-tab="com" onclick="sw('com')">Compromisos <span class="tbadge tbg" id="bc">–</span></button>
</div>
<main>
  <div class="tab-panel active" id="tab-cap">
    <div class="fbar" id="fbar"><span class="fl">Área:</span></div>
    <div id="area-detail"><div class="lbox">Cargando…</div></div>
  </div>
  <div class="tab-panel" id="tab-alt">
    <div class="alist" id="alist"></div>
  </div>
  <div class="tab-panel" id="tab-com">
    <div class="clist" id="clist"></div>
  </div>
</main>
<script>
const DATA = __DATA_PLACEHOLDER__;

let currentAreaIdx = 0;

function renderAll(d){
  const dt = new Date(d.lastUpdate);
  document.getElementById('lupd').textContent =
    'Generado: ' + dt.toLocaleDateString('es-CO',{day:'2-digit',month:'short',year:'numeric'}) +
    ' · ' + dt.toLocaleTimeString('es-CO',{hour:'2-digit',minute:'2-digit'});

  document.getElementById('ba').textContent = d.alerts.length;
  document.getElementById('bc').textContent = d.commitments.length;

  const fb = document.getElementById('fbar');
  fb.innerHTML = '<span class="fl">\u00c1rea:</span>';
  d.areas.forEach((a,i) => {
    const b = document.createElement('button');
    b.className = 'fbtn' + (i===0?' active':'');
    b.textContent = a.name;
    b.onclick = () => {
      currentAreaIdx = i;
      document.querySelectorAll('.fbtn').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      renderAreaDetail(d, i);
    };
    fb.appendChild(b);
  });

  renderAreaDetail(d, 0);
  renderAlerts(d);
  renderCommits(d);
}

function renderAreaDetail(d,idx){
  const area=d.areas[idx];
  const prev=d.areas[idx>0?idx-1:d.areas.length-1];
  const next=d.areas[idx<d.areas.length-1?idx+1:0];
  const alto=area.alertas.filter(a=>a.impacto==='Alto').length;
  const medio=area.alertas.filter(a=>a.impacto==='Medio').length;
  const bajo=area.alertas.filter(a=>a.impacto==='Bajo').length;
  document.getElementById('area-detail').innerHTML=`
    <div class="area-nav">
      <button class="nav-arrow" onclick="navArea(${idx>0?idx-1:d.areas.length-1})">&lt; ${prev.name}</button>
      <span class="area-nav-title">ESTADO GENERAL — ${area.name}</span>
      <button class="nav-arrow" onclick="navArea(${idx<d.areas.length-1?idx+1:0})">${next.name} &gt;</button>
    </div>
    <div class="area-body">
      <div class="left-panel">
        <div class="lp-card">
          <div class="func-status">
            <span class="func-label">Funcionalidad: <strong>${area.funcionalidad}</strong></span>
            <span class="func-check">✓</span>
          </div>
          <p class="func-desc">${area.funcDesc}</p>
        </div>
        <div class="lp-card">
          <div class="lp-section-title">KPIs Clave</div>
          <p style="font-size:10px;color:var(--muted);margin-bottom:8px;">Durante el primer corte del 2026 se tienen las siguientes cifras en cuanto a solicitudes:</p>
          ${area.kpis.map(k=>`<div class="kpi-row"><span class="kpi-name">${k.n}</span><span class="kpi-val">${k.v}</span></div>`).join('')}
          <div class="kpi-total-row"><span class="kpi-total-name">Total</span><span class="kpi-total-val">${area.kpis.reduce((s,k)=>s+k.v,0)}</span></div>
          <p class="kpi-note">✅ ${area.kpiNote}</p>
        </div>
        <div class="lp-card">
          <div class="lp-section-title">Cobertura</div>
          ${area.cobertura.map(c=>`<div class="cov-item"><span class="cov-icon">✓</span><span class="cov-text">${c}</span></div>`).join('')}
        </div>
        <div class="lp-card">
          <div class="lp-section-title">Capacity por País</div>
          ${area.countries.map(c=>{
            const pct=Math.round(c.available/c.total*100);
            const bc=c.status==='ok'?'#00915A':c.status==='warn'?'#A3C439':'#EF7B5B';
            const nc=c.status==='ok'?'var(--primary)':c.status==='warn'?'#A3C439':'#EF7B5B';
            return `<div style="margin-bottom:10px;">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:3px;">
                <span style="font-size:11px;font-weight:500;">${c.flag} ${c.country}</span>
                <span style="font-size:11px;color:${nc};font-weight:700;">${c.available}<span style="color:var(--muted);font-weight:400;">/${c.total}</span></span>
              </div>
              <div style="background:var(--surface2);border-radius:3px;height:4px;overflow:hidden;">
                <div style="width:${pct}%;height:100%;background:${bc};border-radius:3px;"></div>
              </div>
            </div>`;
          }).join('')}
        </div>
      </div>
      <div class="center-panel">
        <div class="panel-header">
          <span class="panel-header-title">Alertas y Riesgos</span>
          <div class="impact-pills">
            <span class="ipill ipill-alto">${alto} Alto</span>
            <span class="ipill ipill-medio">${medio} Medio</span>
            <span class="ipill ipill-bajo">${bajo} Bajo</span>
          </div>
        </div>
        <div class="alerts-table">
          <div class="at-header">
            <div>Tipo</div><div>Descripción</div><div>Impacto</div><div>Plan de Acción</div><div>Resp. / ETA</div>
          </div>
          ${area.alertas.length?area.alertas.map(al=>{
            const ic=al.impacto==='Alto'?'ib-alto':al.impacto==='Medio'?'ib-medio':'ib-bajo';
            const planLines=al.plan.split('\n').map(l=>`• ${l}`).join('<br>');
            return `<div class="alert-row">
              <div class="ar-icon">⚠️</div>
              <div class="ar-desc"><div class="ar-desc-title">${al.titulo}</div><div class="ar-desc-text">${al.desc.replace(/\n/g,'<br>')}</div><div style="font-size:9px;color:var(--subtle);margin-top:4px;">${al.tipo}</div></div>
              <div class="ar-impact"><span class="impact-badge ${ic}">${al.impacto}</span></div>
              <div class="ar-plan">${planLines}</div>
              <div class="ar-resp"><span class="resp-text">${al.resp}</span><span class="quarter-badge">${al.eta}</span></div>
            </div>`;
          }).join(''):`<div style="padding:24px;text-align:center;color:var(--muted);font-size:12px;">✅ Sin alertas activas para esta área</div>`}
        </div>
      </div>
      <div class="right-panel">
        <div class="rp-card">
          <div class="rp-header"><div class="rp-header-title">Novedades Relevantes</div></div>
          <div class="rp-body">
            <div class="rp-section"><span class="rp-tag tag-green">Logros</span><div class="rp-text"><ul>${area.novedades.logros.map(l=>`<li>${l}</li>`).join('')}</ul></div></div>
            <div class="rp-section"><span class="rp-tag tag-gray">Proyectos / Iniciativas</span><div class="rp-text"><ul>${area.novedades.proyectos.map(p=>`<li>${p}</li>`).join('')}</ul></div></div>
            <div class="rp-section"><span class="rp-tag tag-gray">Otros</span><div class="rp-text">${area.novedades.otros.map(o=>o.replace(/\n/g,'<br>')).join('<br><br>')}</div></div>
          </div>
        </div>
      </div>
    </div>
    <div style="text-align:center;margin-top:20px;padding:10px;font-size:10px;color:var(--subtle);letter-spacing:2px;border-top:1px solid var(--border);">· Comité I &nbsp; IT Capacity ·</div>`;
}

function navArea(idx){
  currentAreaIdx=idx;
  document.querySelectorAll('.fbtn').forEach((b,i)=>b.classList.toggle('active',i===idx));
  renderAreaDetail(DATA,idx);
  window.scrollTo({top:0,behavior:'smooth'});
}

function renderAlerts(d){
  document.getElementById('alist').innerHTML=d.alerts.map(a=>{
    const cls=a.sev==='warn'?' warn':a.sev==='info'?' info':'';
    const sc=a.sev==='crit'?'sc':a.sev==='warn'?'sw':'si2';
    const sl=a.sev==='crit'?'Crítico':a.sev==='warn'?'Advertencia':'Información';
    return `<div class="aitem${cls}"><span class="asev ${sc}">${sl}</span><div class="abody"><div class="atitle">${a.title}</div><div class="adesc">${a.desc}</div><div class="atags">${a.tags.map(t=>`<span class="atag">${t}</span>`).join('')}</div><div class="adate">📅 ${a.date}</div></div></div>`;
  }).join('');
}

function renderCommits(d){
  document.getElementById('clist').innerHTML=d.commitments.map((c,i)=>{
    const bc=c.status==='prog'?'cp':c.status==='done'?'cd':c.status==='late'?'cl':'ce';
    return `<div class="citem"><div class="cnum">${String(i+1).padStart(2,'0')}</div><div class="cbody"><div class="ctitle2">${c.title}</div><div class="cdesc">${c.desc}</div><div class="cfoot"><span class="csbadge ${bc}">${c.label}</span><span class="cmeta2">👤 ${c.owner}</span><span class="cmeta2">📅 ${c.due}</span></div></div></div>`;
  }).join('');
}

function sw(id){
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tbtn').forEach(b=>b.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  document.querySelector('[data-tab="'+id+'"]').classList.add('active');
}

(function(){
  const slot=document.getElementById('logo-slot');
  const inp=document.createElement('input');
  inp.type='file';inp.accept='image/*';inp.style.display='none';
  document.body.appendChild(inp);
  slot.onclick=()=>inp.click();
  inp.onchange=()=>{
    const file=inp.files[0];if(!file)return;
    const reader=new FileReader();
    reader.onload=e=>{slot.innerHTML=`<img src="${e.target.result}" alt="Logo">`;};
    reader.readAsDataURL(file);
  };
})();

renderAll(DATA);
</script>
</body>
</html>"""

# ════════════════════════════════════════════════════════
#  GENERAR HTML
# ════════════════════════════════════════════════════════
data_json = json.dumps(DATA, ensure_ascii=False, indent=2)
html_final = HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", data_json)

OUTPUT_PATH.write_text(html_final, encoding='utf-8')

print(f"\n✅ Dashboard generado: {OUTPUT_PATH}")
print(f"   Abre el archivo directamente en tu navegador (doble clic).")
print(f"\n   No necesitas servidor ni conexión a Nexus para visualizarlo.\n")

# Abrir automáticamente en el navegador
try:
    import webbrowser
    webbrowser.open(OUTPUT_PATH.resolve().as_uri())
    print("   🌐 Abriendo en el navegador...")
except Exception:
    pass
