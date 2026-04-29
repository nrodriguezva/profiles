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
df_bita  = read_sheet("Bitacora_Compromisos")

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

logo_row = df_cfg[df_cfg.iloc[:, 0].astype(str).str.strip() == "logo_base64"]
logo_b64 = ""
if not logo_row.empty:
    raw = logo_row.iloc[0, 1]
    if raw is not None and str(raw).strip() not in ("", "nan"):
        logo_b64 = str(raw).strip()
        if not logo_b64.startswith("data:"):
            logo_b64 = "data:image/png;base64," + logo_b64

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
# Build bitacora indexed by commitment ID (1-based)
bitacora = {}
for _, br in df_bita.iterrows():
    try:
        cid = int(float(str(br.iloc[0]).strip()))
    except:
        continue
    entry = {
        "fecha": safe(br.iloc[2]) or "",
        "tipo":  safe(br.iloc[3]) or "otro",
        "desc":  safe(br.iloc[4]) or "",
        "quien": safe(br.iloc[5]) or "",
    }
    bitacora.setdefault(cid, []).append(entry)

commitments = []
for _, co in df_comp.iterrows():
    if not safe(co.iloc[0]): continue
    try:    avance = int(float(str(co.iloc[6]).strip())) if co.iloc[6] is not None and str(co.iloc[6]).strip() not in ('','nan') else 0
    except: avance = 0
    commitments.append({
        "title":  safe(co.iloc[0]) or "",
        "desc":   safe(co.iloc[1]) or "",
        "status": safe(co.iloc[2]) or "pend",
        "label":  safe(co.iloc[3]) or "Pendiente",
        "due":    safe(co.iloc[4]) or "",
        "owner":  safe(co.iloc[5]) or "",
        "avance": avance,
        "hitos":  safe(co.iloc[7]) or "",
        "bitacora": bitacora.get(len(commitments)+1, []),
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
HTML_TEMPLATE = r"""<style>

/* ── Tema claro ── */
#cap-dashboard {
  --bg:      #F5F6FA; --surface:  #FFFFFF; --surface2: #EEF0F5;
  --surface3:#E4E6EE; --border:   #D0D4E0; --border2:  #B8BDCC;
  --text:    #1A1F36; --muted:    #5E6780; --subtle:   #9099B2;
  --primary: #00915A; --pdark:    #006B43; --pglow:    rgba(0,145,90,0.10);
  --coral:   #C9402A; --amber:    #B37400; --sky:      #0060A8;
  --stok-bg: rgba(0,145,90,0.12);  --stok-t:  #006B43;
  --swarn-bg:rgba(179,116,0,0.12); --swarn-t: #8A5700;
  --scrit-bg:rgba(201,64,42,0.10); --scrit-t: #C9402A;
}


/* ── Tema claro — Confluence en modo claro ── */
#cap-dashboard header{background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:stretch;}
#cap-dashboard .h-accent{width:5px;flex-shrink:0;background:linear-gradient(180deg,#595959 0%,var(--primary) 100%);}
#cap-dashboard .h-content{flex:1;display:flex;align-items:center;justify-content:space-between;padding:14px 32px;flex-wrap:wrap;gap:10px;}
#cap-dashboard .h-left{display:flex;align-items:center;gap:14px;}
#cap-dashboard .logo-slot{width:48px;height:48px;border-radius:8px;border:1px solid var(--border);background:var(--surface2);display:flex;align-items:center;justify-content:center;flex-shrink:0;overflow:hidden;}
#cap-dashboard .logo-slot img{width:100%;height:100%;object-fit:contain;}
#cap-dashboard .logo-placeholder{font-size:8px;color:var(--subtle);text-align:center;line-height:1.3;pointer-events:none;}
#cap-dashboard .h-title{font-family:'Barlow Condensed',sans-serif;font-size:26px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;line-height:1;color:var(--text);}
#cap-dashboard .h-sub{font-size:12px;color:var(--muted);margin-top:2px;letter-spacing:.3px;}
#cap-dashboard .h-badge{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--muted);background:var(--surface2);border:1px solid var(--border);border-radius:20px;padding:5px 12px;}
#cap-dashboard .live{width:6px;height:6px;background:var(--primary);border-radius:50%;animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
#cap-dashboard .tabs{display:flex;gap:2px;padding:12px 32px 0;background:var(--surface);border-bottom:1px solid var(--border);overflow-x:auto;}
#cap-dashboard .tbtn{font-family:'Inter',sans-serif;font-size:14px;font-weight:500;color:var(--muted);background:transparent;border:none;cursor:pointer;padding:7px 14px;border-radius:5px 5px 0 0;border-bottom:2px solid transparent;white-space:nowrap;transition:all .15s;}
#cap-dashboard .tbtn:hover{color:var(--text);background:rgba(128,128,128,0.08);}
#cap-dashboard .tbtn.active{color:var(--primary);border-bottom-color:var(--primary);background:rgba(0,145,90,0.08);}
#cap-dashboard .tbadge{display:inline-block;font-size:11px;font-weight:700;border-radius:10px;padding:2px 8px;margin-left:4px;vertical-align:middle;}
#cap-dashboard .tbr{background:rgba(239,123,91,.22);color:var(--coral);}
#cap-dashboard .tbg{background:var(--stok-bg);color:var(--primary);}
#cap-dashboard main{padding:20px 32px 60px;max-width:1600px;margin:0 auto;background:var(--bg);}
#cap-dashboard .tab-panel{display:none;}
#cap-dashboard .tab-panel.active{display:block;animation:fu .2s ease;}
@keyframes fu{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
#cap-dashboard .fbar{display:flex;align-items:center;gap:6px;margin-bottom:20px;flex-wrap:wrap;}
#cap-dashboard .fl{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-right:2px;}
#cap-dashboard .fbtn{font-size:13px;font-weight:500;background:var(--surface2);color:var(--muted);border:1px solid var(--border);border-radius:14px;padding:5px 14px;cursor:pointer;transition:all .14s;white-space:nowrap;font-family:'Inter',sans-serif;}
#cap-dashboard .fbtn:hover{color:var(--text);border-color:var(--primary);}
#cap-dashboard .fbtn.active{background:var(--primary);color:#fff;border-color:var(--primary);}
#cap-dashboard .area-nav{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;padding:10px 14px;background:var(--surface);border:1px solid var(--border);border-radius:8px;}
#cap-dashboard .area-nav-title{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:var(--primary);}
#cap-dashboard .nav-arrow{font-size:11px;color:var(--muted);cursor:pointer;padding:5px 10px;border-radius:5px;border:1px solid var(--border);background:transparent;transition:all .14s;font-family:'Inter',sans-serif;}
#cap-dashboard .nav-arrow:hover{color:var(--text);border-color:var(--primary);}
#cap-dashboard .area-body{display:grid;grid-template-columns:220px 1fr 260px;gap:12px;align-items:start;}
#cap-dashboard .left-panel{display:flex;flex-direction:column;gap:10px;}
#cap-dashboard .lp-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px;}
#cap-dashboard .lp-section-title{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--primary);margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid var(--border);}
#cap-dashboard .func-status{display:flex;align-items:center;gap:8px;margin-bottom:6px;}
#cap-dashboard .func-label{font-size:15px;font-weight:600;color:var(--text);}
#cap-dashboard .func-check{width:18px;height:18px;background:var(--primary);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:10px;color:#fff;}
#cap-dashboard .func-desc{font-size:13px;color:var(--muted);line-height:1.5;}
#cap-dashboard .kpi-row{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--border);}
#cap-dashboard .kpi-row:last-child{border-bottom:none;}
#cap-dashboard .kpi-name{font-size:13px;color:var(--muted);}
#cap-dashboard .kpi-val{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:700;color:var(--text);}
#cap-dashboard .kpi-total-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0 0;margin-top:2px;}
#cap-dashboard .kpi-total-name{font-size:11px;font-weight:600;color:var(--text);}
#cap-dashboard .kpi-total-val{font-family:'Barlow Condensed',sans-serif;font-size:26px;font-weight:700;color:var(--primary);}
#cap-dashboard .kpi-note{font-size:11px;color:var(--subtle);line-height:1.4;margin-top:8px;}
#cap-dashboard .cov-item{display:flex;align-items:flex-start;gap:7px;margin-bottom:8px;}
#cap-dashboard .cov-icon{width:14px;height:14px;background:var(--primary);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;font-size:8px;color:#fff;}
#cap-dashboard .cov-text{font-size:13px;color:var(--muted);line-height:1.4;}
#cap-dashboard .panel-header{background:var(--primary);border-radius:8px 8px 0 0;padding:10px 14px;display:flex;align-items:center;justify-content:space-between;}
#cap-dashboard .panel-header-title{font-family:'Barlow Condensed',sans-serif;font-size:17px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#fff;}
#cap-dashboard .impact-pills{display:flex;gap:6px;}
#cap-dashboard .ipill{font-size:12px;font-weight:700;padding:4px 12px;border-radius:5px;}
#cap-dashboard .ipill-alto{background:#FDECEA;color:#C9402A;border:1px solid #FBBCB5;}
#cap-dashboard .ipill-medio{background:#FEF6E4;color:#B37400;border:1px solid #F5D78A;}
#cap-dashboard .ipill-bajo{background:#E6F4EE;color:#006B43;border:1px solid #A3D4BC;}
#cap-dashboard .alerts-table{background:var(--surface);border:1px solid var(--border);border-top:none;border-radius:0 0 8px 8px;overflow:hidden;}
#cap-dashboard .at-header{display:grid;grid-template-columns:36px 1fr 80px 160px 100px;background:var(--surface2);border-bottom:1px solid var(--border);}
#cap-dashboard .at-header div{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);padding:8px 10px;}
#cap-dashboard .alert-row{display:grid;grid-template-columns:36px 1fr 80px 160px 100px;border-bottom:1px solid var(--border);align-items:start;}
#cap-dashboard .alert-row:last-child{border-bottom:none;}
#cap-dashboard .alert-row:hover{background:var(--surface2);}
#cap-dashboard .ar-icon{padding:14px 8px;display:flex;align-items:flex-start;justify-content:center;}
#cap-dashboard .ar-desc{padding:12px 10px;}
#cap-dashboard .ar-desc-title{font-size:14px;font-weight:600;margin-bottom:4px;color:var(--text);}
#cap-dashboard .ar-desc-text{font-size:13px;color:var(--muted);line-height:1.5;}
#cap-dashboard .ar-impact{padding:12px 10px;display:flex;align-items:flex-start;justify-content:center;}
#cap-dashboard .impact-badge{font-size:12px;font-weight:700;padding:4px 12px;border-radius:5px;border:1.5px solid;white-space:nowrap;}
#cap-dashboard .ib-alto{border-color:var(--coral);color:var(--coral);}
#cap-dashboard .ib-medio{border-color:var(--amber);color:var(--amber);}
#cap-dashboard .ib-bajo{border-color:var(--primary);color:var(--primary);}
#cap-dashboard .ar-plan{padding:12px 10px;font-size:13px;color:var(--muted);line-height:1.5;}
#cap-dashboard .ar-resp{padding:12px 10px;display:flex;flex-direction:column;gap:5px;align-items:flex-start;}
#cap-dashboard .resp-text{font-size:13px;color:var(--muted);}
#cap-dashboard .quarter-badge{font-family:'Barlow Condensed',sans-serif;font-size:14px;font-weight:700;background:var(--pdark);color:#fff;padding:3px 10px;border-radius:5px;letter-spacing:1px;}
#cap-dashboard .right-panel{display:flex;flex-direction:column;gap:10px;}
#cap-dashboard .rp-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;overflow:hidden;}
#cap-dashboard .rp-header{background:var(--surface2);padding:9px 14px;border-bottom:1px solid var(--border);}
#cap-dashboard .rp-header-title{font-family:'Barlow Condensed',sans-serif;font-size:15px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text);}
#cap-dashboard .rp-body{padding:12px 14px;}
#cap-dashboard .rp-tag{display:inline-block;font-size:12px;font-weight:700;padding:4px 12px;border-radius:5px;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px;}
#cap-dashboard .tag-green{background:var(--primary);color:#fff;}
#cap-dashboard .tag-gray{background:var(--surface3);color:var(--muted);border:1px solid var(--border2);}
#cap-dashboard .rp-text{font-size:13px;color:var(--muted);line-height:1.6;}
#cap-dashboard .rp-text li{margin-left:12px;margin-top:3px;}
#cap-dashboard .rp-section{margin-bottom:10px;}
#cap-dashboard .rp-section:last-child{margin-bottom:0;}
#cap-dashboard .alist{display:flex;flex-direction:column;gap:8px;}
#cap-dashboard .aitem{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--coral);border-radius:0 8px 8px 0;padding:13px 15px;display:flex;gap:11px;align-items:flex-start;}
#cap-dashboard .aitem.warn{border-left-color:var(--amber);}
#cap-dashboard .aitem.info{border-left-color:var(--sky);}
#cap-dashboard .asev{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:3px 9px;border-radius:8px;white-space:nowrap;flex-shrink:0;margin-top:1px;}
#cap-dashboard .sc{background:var(--scrit-bg);color:var(--scrit-t);}
#cap-dashboard .sw{background:var(--swarn-bg);color:var(--swarn-t);}
#cap-dashboard .si2{background:rgba(86,180,192,.15);color:var(--sky);}
#cap-dashboard .abody{flex:1;}
#cap-dashboard .atitle{font-size:14px;font-weight:600;margin-bottom:3px;color:var(--text);}
#cap-dashboard .adesc{font-size:13px;color:var(--muted);line-height:1.5;}
#cap-dashboard .atags{display:flex;gap:5px;margin-top:7px;flex-wrap:wrap;}
#cap-dashboard .atag{font-size:11px;background:var(--surface2);border:1px solid var(--border);border-radius:5px;padding:3px 9px;color:var(--muted);}
#cap-dashboard .adate{font-size:11px;color:var(--subtle);margin-top:3px;}
#cap-dashboard .clist{display:flex;flex-direction:column;gap:8px;}
#cap-dashboard .citem{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:13px 15px;display:flex;gap:13px;align-items:flex-start;}
#cap-dashboard .cnum{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:700;color:var(--primary);flex-shrink:0;min-width:28px;}
#cap-dashboard .cbody{flex:1;}
#cap-dashboard .ctitle2{font-size:14px;font-weight:600;margin-bottom:3px;color:var(--text);}
#cap-dashboard .cdesc{font-size:13px;color:var(--muted);line-height:1.5;}
#cap-dashboard .cfoot{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;align-items:center;}
#cap-dashboard .csbadge{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 8px;border-radius:8px;}
#cap-dashboard .cp{background:rgba(86,180,192,.18);color:var(--sky);}
#cap-dashboard .cd{background:var(--stok-bg);color:var(--primary);}
#cap-dashboard .ce{background:var(--swarn-bg);color:var(--amber);}
#cap-dashboard .cl{background:rgba(186,48,117,.18);color:#BA3075;}
#cap-dashboard .cmeta2{font-size:10px;color:var(--muted);}
#cap-dashboard .st-ok{background:var(--stok-bg);color:var(--stok-t);}
#cap-dashboard .st-warn{background:var(--swarn-bg);color:var(--swarn-t);}
#cap-dashboard .st-crit{background:var(--scrit-bg);color:var(--scrit-t);}
#cap-dashboard .lbox{text-align:center;padding:50px 20px;color:var(--muted);font-size:14px;}

/* ── COMPROMISOS MEJORADOS ── */
#cap-dashboard .citem{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:0;display:flex;flex-direction:column;overflow:hidden;}
#cap-dashboard .citem-header{display:flex;align-items:center;gap:14px;padding:16px 18px 12px;}
#cap-dashboard .cnum{font-family:'Barlow Condensed',sans-serif;font-size:28px;font-weight:700;color:var(--primary);flex-shrink:0;min-width:36px;}
#cap-dashboard .cbody{flex:1;}
#cap-dashboard .ctitle2{font-size:16px;font-weight:700;margin-bottom:4px;color:var(--text);}
#cap-dashboard .cdesc{font-size:13px;color:var(--muted);line-height:1.6;}
#cap-dashboard .cfoot{display:flex;gap:10px;margin-top:10px;flex-wrap:wrap;align-items:center;}
#cap-dashboard .csbadge{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:3px 10px;border-radius:8px;}
#cap-dashboard .cp{background:rgba(86,180,192,.18);color:var(--sky);}
#cap-dashboard .cd{background:var(--stok-bg);color:var(--primary);}
#cap-dashboard .ce{background:var(--swarn-bg);color:var(--amber);}
#cap-dashboard .cl{background:rgba(186,48,117,.18);color:#BA3075;}
#cap-dashboard .cmeta2{font-size:12px;color:var(--muted);}
#cap-dashboard .c-progress-wrap{padding:0 18px 14px;}
#cap-dashboard .c-progress-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}
#cap-dashboard .c-progress-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;}
#cap-dashboard .c-progress-pct{font-size:16px;font-weight:700;}
#cap-dashboard .c-progress-track{height:8px;background:var(--surface2);border-radius:4px;overflow:hidden;margin-bottom:10px;}
#cap-dashboard .c-progress-fill{height:100%;border-radius:4px;transition:width .8s cubic-bezier(.16,1,.3,1);}
#cap-dashboard .c-hitos{display:flex;flex-wrap:wrap;gap:6px;}
#cap-dashboard .c-hito{font-size:12px;color:var(--muted);background:var(--surface2);border-radius:6px;padding:4px 10px;border:1px solid var(--border);}
#cap-dashboard .c-hito-done{color:var(--primary);border-color:rgba(0,145,90,0.3);}
#cap-dashboard .c-hito-prog{color:var(--amber);border-color:rgba(232,160,32,0.3);}
#cap-dashboard .c-hito-pend{color:var(--muted);}
#cap-dashboard .c-hito-block{color:#D94F4F;border-color:rgba(217,79,79,0.3);}
#cap-dashboard .c-bita{margin-top:12px;border-top:1px solid var(--border);padding-top:10px;}
#cap-dashboard .c-bita-title{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:8px;}
#cap-dashboard .c-bita-entry{display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid var(--border);opacity:1;}
#cap-dashboard .c-bita-entry:last-child{border-bottom:none;}
#cap-dashboard .c-bita-dot{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0;margin-top:1px;}
#cap-dashboard .c-bita-dot-avance{background:rgba(0,82,204,0.15);}
#cap-dashboard .c-bita-dot-documento{background:rgba(0,107,67,0.15);}
#cap-dashboard .c-bita-dot-reunion{background:rgba(179,116,0,0.15);}
#cap-dashboard .c-bita-dot-correo{background:rgba(122,0,128,0.15);}
#cap-dashboard .c-bita-dot-otro{background:rgba(89,89,89,0.15);}
#cap-dashboard .c-bita-content{flex:1;}
#cap-dashboard .c-bita-desc{font-size:13px;color:var(--text);line-height:1.5;}
#cap-dashboard .c-bita-meta{font-size:11px;color:var(--muted);margin-top:3px;}
#cap-dashboard .c-bita-tag{display:inline-block;font-size:10px;font-weight:700;padding:1px 7px;border-radius:5px;margin-right:5px;text-transform:uppercase;}
#cap-dashboard .c-bita-tag-avance{background:rgba(0,82,204,0.12);color:#0052CC;}
#cap-dashboard .c-bita-tag-documento{background:rgba(0,107,67,0.12);color:#006B43;}
#cap-dashboard .c-bita-tag-reunion{background:rgba(179,116,0,0.12);color:#B37400;}
#cap-dashboard .c-bita-tag-correo{background:rgba(122,0,128,0.12);color:#7A0080;}
#cap-dashboard .c-bita-tag-otro{background:rgba(89,89,89,0.12);color:#595959;}
#cap-dashboard .c-bita-toggle{font-size:12px;color:var(--primary);cursor:pointer;background:none;border:none;padding:4px 0;font-family:'Inter',sans-serif;font-weight:600;text-decoration:underline;}

/* ── FILTRO PAÍS ── */
#cap-dashboard .pbar{display:flex;align-items:center;gap:6px;margin-bottom:16px;flex-wrap:wrap;padding:10px 14px;background:var(--surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.06);}
#cap-dashboard .pl{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-right:4px;}
#cap-dashboard .pbtn{font-size:12px;font-weight:500;background:var(--surface2);color:var(--muted);border:1px solid var(--border);border-radius:14px;padding:5px 14px;cursor:pointer;transition:all .14s;white-space:nowrap;font-family:'Inter',sans-serif;}
#cap-dashboard .pbtn:hover{color:var(--text);border-color:var(--primary);}
#cap-dashboard .pbtn.active{background:var(--primary);color:#fff;border-color:var(--primary);}

/* ── PLEGABLE ── */
#cap-dashboard .citem-body{overflow:hidden;transition:max-height .35s cubic-bezier(.16,1,.3,1);max-height:0;}
#cap-dashboard .citem-body.open{max-height:2000px;}
#cap-dashboard .citem-toggle{display:flex;align-items:center;justify-content:space-between;padding:10px 18px;cursor:pointer;border-top:1px solid var(--border);background:var(--surface2);transition:background .15s;border-radius:0 0 10px 10px;}
#cap-dashboard .citem-toggle:hover{background:var(--surface3);}
#cap-dashboard .citem-toggle-label{font-size:12px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.8px;}
#cap-dashboard .citem-arrow{font-size:14px;color:var(--muted);transition:transform .3s;}
#cap-dashboard .citem-arrow.open{transform:rotate(180deg);}

/* ── ESTADO GENERAL ── */
#cap-dashboard .gen-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px;}
#cap-dashboard .gen-group{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;}
#cap-dashboard .gen-group-header{padding:12px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--border);}
#cap-dashboard .gen-group-icon{font-size:10px;font-weight:800;letter-spacing:1.5px;background:rgba(0,0,0,0.12);color:#fff;padding:3px 9px;border-radius:4px;flex-shrink:0;}
#cap-dashboard .gen-group-title{font-family:'Barlow Condensed',sans-serif;font-size:20px;font-weight:800;text-transform:uppercase;letter-spacing:1.5px;color:var(--text);}
#cap-dashboard .gen-group-badge{margin-left:auto;font-size:13px;font-weight:700;padding:4px 12px;border-radius:20px;}
#cap-dashboard .gen-areas{padding:12px 14px;display:flex;flex-direction:column;gap:10px;}
#cap-dashboard .gen-area-row{display:flex;align-items:center;gap:12px;padding:14px 16px;border-radius:8px;cursor:pointer;transition:background .15s;border:1px solid transparent;}
#cap-dashboard .gen-area-row:hover{background:var(--surface2);border-color:var(--primary);}
#cap-dashboard .gen-status-dot{width:16px;height:16px;border-radius:50%;flex-shrink:0;}
#cap-dashboard .gen-area-name{font-size:16px;font-weight:600;color:var(--text);flex:1;}
#cap-dashboard .gen-area-sub{font-size:13px;color:var(--muted);}
#cap-dashboard .gen-area-right{display:flex;align-items:center;gap:8px;flex-shrink:0;}
#cap-dashboard .gen-pill{font-size:12px;font-weight:700;padding:4px 12px;border-radius:10px;text-transform:uppercase;letter-spacing:.5px;}
#cap-dashboard .gen-pill-ok{background:rgba(0,145,90,0.12);color:#006B43;}
#cap-dashboard .gen-pill-warn{background:rgba(179,116,0,0.12);color:#8A5700;}
#cap-dashboard .gen-pill-crit{background:rgba(201,64,42,0.12);color:#C9402A;}
#cap-dashboard .gen-cap{font-size:13px;font-weight:700;color:var(--muted);}
#cap-dashboard .gen-bar{width:80px;height:6px;background:var(--surface2);border-radius:3px;overflow:hidden;}
#cap-dashboard .gen-bar-fill{height:100%;border-radius:3px;}
@media(max-width:900px){#cap-dashboard .gen-grid{grid-template-columns:1fr;}}
@media(max-width:900px){#cap-dashboard .area-body{grid-template-columns:1fr;}#cap-dashboard .at-header,#cap-dashboard .alert-row{grid-template-columns:32px 1fr 70px;}#cap-dashboard .at-header div:nth-child(4),#cap-dashboard .at-header div:nth-child(5),#cap-dashboard .alert-row .ar-plan,#cap-dashboard .alert-row .ar-resp{display:none;}}
@media(max-width:600px){#cap-dashboard .h-content,#cap-dashboard .tabs,#cap-dashboard main{padding-left:14px;padding-right:14px;}}
</style>
<div id="cap-dashboard">
<header>
  <div class="h-accent"></div>
  <div class="h-content">
    <div class="h-left">
      <div class="logo-slot" id="logo-slot">
        __LOGO_CONTENT__
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
  <button class="tbtn active" data-tab="general" onclick="sw('general')">Estado General por Área</button>
  <button class="tbtn" data-tab="cap" onclick="sw('cap')">Estado Detallado por Área</button>
  <button class="tbtn" data-tab="alt" onclick="sw('alt')">Alertas Comité <span class="tbadge tbr" id="ba">–</span></button>
  <button class="tbtn" data-tab="com" onclick="sw('com')">Compromisos <span class="tbadge tbg" id="bc">–</span></button>
</div>
<main>
  <div class="tab-panel active" id="tab-general">
    <div id="general-view"><div class="lbox">Cargando…</div></div>
  </div>
  <div class="tab-panel" id="tab-cap">
    <div class="fbar" id="fbar"><span class="fl">Área:</span></div>
    <div class="pbar" id="pbar-cap"><span class="pl">País:</span></div>
    <div id="area-detail"><div class="lbox">Cargando…</div></div>
  </div>
  <div class="tab-panel" id="tab-alt">
    <div class="pbar" id="pbar-alt"><span class="pl">País:</span></div>
    <div class="alist" id="alist"></div>
  </div>
  <div class="tab-panel" id="tab-com">
    <div class="pbar" id="pbar-com"><span class="pl">País:</span></div>
    <div class="pbar" id="sbar-com" style="margin-top:-8px;"><span class="pl">Estado:</span></div>
    <div class="clist" id="clist"></div>
  </div>
</main>
</div>
<script>
(function(){
  var l=document.createElement('link');
  l.rel='stylesheet';
  l.href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Barlow+Condensed:wght@700;800&display=swap';
  document.head&&document.head.appendChild(l)||(document.querySelector('head')||document.documentElement).appendChild(l);
})();
const DATA = __DATA_PLACEHOLDER__;

let currentAreaIdx = 0;
const COUNTRIES = ['Brasil','Chile','Colombia','Mexico','Peru','Latam'];
let filterCountry = { cap:'all', alt:'all', com:'all' };
let filterStatus  = { com:'all' };

function buildPbar(containerId, tab, extraBtns) {
  const el = document.getElementById(containerId);
  if (!el) return;
  let html = '<span class="pl">País:</span>';
  ['all', ...COUNTRIES].forEach(c => {
    const label = c === 'all' ? 'Todos' : c;
    const active = filterCountry[tab] === c ? ' active' : '';
    html += '<button class="pbtn' + active + '" data-tab="' + tab + '" data-val="' + c + '" onclick="setCountry(this.dataset.tab,this.dataset.val)">' + label + '</button>';
  });
  el.innerHTML = html;
}

function buildSbar(containerId, tab) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const statuses = [['all','Todos'],['prog','En progreso'],['done','Completado'],['pend','Pendiente'],['late','Vencido']];
  let html = '<span class="pl">Estado:</span>';
  statuses.forEach(([v, label]) => {
    const active = filterStatus[tab] === v ? ' active' : '';
    html += '<button class="pbtn' + active + '" data-tab="' + tab + '" data-val="' + v + '" onclick="setStatus(this.dataset.tab,this.dataset.val)">' + label + '</button>';
  });
  el.innerHTML = html;
}

function setCountry(tab, country) {
  filterCountry[tab] = country;
  buildPbar('pbar-' + tab, tab);
  if (tab === 'cap') renderAreaDetail(DATA, currentAreaIdx);
  if (tab === 'alt') renderAlerts(DATA);
  if (tab === 'com') renderCommits(DATA);
}

function setStatus(tab, status) {
  filterStatus[tab] = status;
  buildSbar('sbar-' + tab, tab);
  if (tab === 'com') renderCommits(DATA);
}

function toggleCommit(idx) {
  const body  = document.getElementById('cbody-' + idx);
  const arrow = document.getElementById('carrow-' + idx);
  if (!body) return;
  body.classList.toggle('open');
  if (arrow) arrow.classList.toggle('open');
}

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
  renderGeneral(d);
  renderAlerts(d);
  renderCommits(d);
  buildPbar('pbar-cap', 'cap');
  buildPbar('pbar-alt', 'alt');
  buildPbar('pbar-com', 'com');
  buildSbar('sbar-com', 'com');
}

// ── GROUPS ── area id -> group
const GROUPS = [
  {
    name: 'Infraestructura',
    icon: 'INFRA',
    areas: ['datacenter','databases','cloud','openshift','telecom']
  },
  {
    name: 'Producción APP',
    icon: 'APP',
    areas: ['mashery','tibco','sesame','sugar','kafka','stcp','rhsso']
  },
  {
    name: 'Operación (Delivery)',
    icon: 'OPS',
    areas: ['devsecops','controltower','montools','monfit']
  }
];

// Sub-labels within each group (matches area id order)
const SUBLABELS = {
  datacenter:   'HCI/Backup',
  databases:    'Database',
  cloud:        'Cloud',
  openshift:    'OpenShift',
  telecom:      'Telecom',
  mashery:      'Mashery',
  tibco:        'Tibco',
  sesame:       'Sesame',
  sugar:        'Sugar',
  kafka:        'Kafka',
  stcp:         'STCP a Gemini',
  rhsso:        'RH SSO',
  devsecops:    'DevSecOps',
  controltower: 'Control Tower',
  montools:     'Monitoring Tools',
  monfit:       'Monitoreo FactorIT'
};

function areaStatus(area) {
  // crit if any country crit, warn if any warn, else ok
  const statuses = area.countries.map(c => c.status);
  // also check alertas
  const hasCrit = statuses.includes('crit') || area.alertas.some(a => a.impacto === 'Alto');
  const hasWarn = statuses.includes('warn') || area.alertas.some(a => a.impacto === 'Medio');
  if (hasCrit) return 'crit';
  if (hasWarn) return 'warn';
  return 'ok';
}

function groupStatus(areas) {
  if (areas.some(a => areaStatus(a) === 'crit')) return 'crit';
  if (areas.some(a => areaStatus(a) === 'warn')) return 'warn';
  return 'ok';
}

function statusDotColor(s) {
  return s === 'ok' ? '#00915A' : s === 'warn' ? '#E8A020' : '#D94F4F';
}
function statusBarColor(s) {
  return s === 'ok' ? '#00915A' : s === 'warn' ? '#E8A020' : '#D94F4F';
}
function statusPillClass(s) {
  return s === 'ok' ? 'gen-pill gen-pill-ok' : s === 'warn' ? 'gen-pill gen-pill-warn' : 'gen-pill gen-pill-crit';
}
function statusLabel(s) {
  return s === 'ok' ? 'Estable' : s === 'warn' ? 'Atención' : 'Riesgo Alto';
}
function groupBorderColor(s) {
  return s === 'ok' ? '#00915A' : s === 'warn' ? '#E8A020' : '#D94F4F';
}
function groupBadgeStyle(s) {
  if (s === 'ok')   return 'background:rgba(0,145,90,0.18);color:#00915A;';
  if (s === 'warn') return 'background:rgba(232,160,32,0.20);color:#E8A020;';
  return 'background:rgba(217,79,79,0.18);color:#D94F4F;';
}

function renderGeneral(d) {
  const container = document.getElementById('general-view');
  if (!container) return;

  // Map area id -> area object
  const areaMap = {};
  d.areas.forEach(a => { areaMap[a.id] = a; });

  let html = '<div class="gen-grid">';

  GROUPS.forEach(group => {
    const groupAreas = group.areas.map(id => areaMap[id]).filter(Boolean);
    const gs = groupStatus(groupAreas);
    const borderColor = groupBorderColor(gs);

    html += `<div class="gen-group" style="border-color:${borderColor};">`;
    const gCrit = groupAreas.filter(a => areaStatus(a)==='crit').length;
    const gWarn = groupAreas.filter(a => areaStatus(a)==='warn').length;
    const gOk   = groupAreas.filter(a => areaStatus(a)==='ok').length;
    const totalGroupAlerts = groupAreas.reduce((s,a) => s + a.alertas.length, 0);

    html += `<div class="gen-group-header" style="background:${borderColor}18;">
      <span class="gen-group-icon">${group.icon}</span>
      <span class="gen-group-title">${group.name}</span>
      <div style="margin-left:auto;display:flex;align-items:center;gap:8px;">
        <div style="display:flex;gap:4px;font-size:11px;font-weight:700;">
          ${gCrit>0?`<span style="background:rgba(217,79,79,0.18);color:#D94F4F;padding:2px 8px;border-radius:6px;">${gCrit} &#9679;</span>`:''}
          ${gWarn>0?`<span style="background:rgba(232,160,32,0.18);color:#E8A020;padding:2px 8px;border-radius:6px;">${gWarn} &#9679;</span>`:''}
          ${gOk>0?`<span style="background:rgba(0,145,90,0.15);color:#00915A;padding:2px 8px;border-radius:6px;">${gOk} &#9679;</span>`:''}
        </div>
        <span class="gen-group-badge" style="${groupBadgeStyle(gs)}">${totalGroupAlerts > 0 ? totalGroupAlerts+' alerta'+(totalGroupAlerts>1?'s':'') : 'Estable'}</span>
      </div>
    </div>`;
    html += '<div class="gen-areas">';

    groupAreas.forEach((area, i) => {
      const as = areaStatus(area);
      const dotColor = statusDotColor(as);
      const pillClass = statusPillClass(as);
      const pillLabel = statusLabel(as);
      const sublabel = SUBLABELS[area.id] || '';

      const areaIdx = d.areas.findIndex(a => a.id === area.id);

      const totalAlertas = area.alertas.length;
      const altasAlertas  = area.alertas.filter(a => a.impacto === 'Alto').length;
      const medAlertas    = area.alertas.filter(a => a.impacto === 'Medio').length;
      const bajaAlertas   = area.alertas.filter(a => a.impacto === 'Bajo').length;

      html += `<div class="gen-area-row" onclick="sw('cap');document.querySelectorAll('.fbtn')[${areaIdx}]&&document.querySelectorAll('.fbtn')[${areaIdx}].click();">
        <div class="gen-status-dot" style="background:${dotColor};box-shadow:0 0 6px ${dotColor}60;flex-shrink:0;"></div>
        <div style="flex:1;min-width:0;">
          <div class="gen-area-name">${area.name}</div>
          <div class="gen-area-sub">${sublabel}</div>
        </div>
        <div class="gen-area-right" style="gap:6px;">
          ${totalAlertas === 0
            ? `<span style="font-size:12px;color:#00915A;font-weight:600;">Sin alertas</span>`
            : `<div style="display:flex;gap:5px;align-items:center;">
                ${altasAlertas  > 0 ? `<span style="font-size:11px;font-weight:700;background:rgba(217,79,79,0.18);color:#D94F4F;padding:2px 8px;border-radius:8px;">${altasAlertas} Alto</span>` : ''}
                ${medAlertas    > 0 ? `<span style="font-size:11px;font-weight:700;background:rgba(232,160,32,0.18);color:#E8A020;padding:2px 8px;border-radius:8px;">${medAlertas} Medio</span>` : ''}
                ${bajaAlertas   > 0 ? `<span style="font-size:11px;font-weight:700;background:rgba(0,145,90,0.15);color:#00915A;padding:2px 8px;border-radius:8px;">${bajaAlertas} Bajo</span>` : ''}
               </div>`
          }
          <span class="${pillClass}" style="white-space:nowrap;">${pillLabel}</span>
        </div>
      </div>`;
    });

    html += '</div></div>';
  });

  html += '</div>';
  container.innerHTML = html;
}

function renderAreaDetail(d, idx) {
  const area = d.areas[idx];
  const prev = d.areas[idx > 0 ? idx - 1 : d.areas.length - 1];
  const next = d.areas[idx < d.areas.length - 1 ? idx + 1 : 0];
  const fc   = filterCountry.cap; // 'all' or specific country

  // Filter countries
  const countries = fc === 'all' ? area.countries : area.countries.filter(c => c.country === fc);

  // When a country is selected: filter alertas by resp matching country, show country chip in header
  const alertas = fc === 'all' ? area.alertas :
    area.alertas.filter(al =>
      al.titulo.toLowerCase().includes(fc.toLowerCase()) ||
      al.desc.toLowerCase().includes(fc.toLowerCase()) ||
      al.resp.toLowerCase().includes(fc.toLowerCase())
    );

  const alto  = alertas.filter(a => a.impacto === 'Alto').length;
  const medio = alertas.filter(a => a.impacto === 'Medio').length;
  const bajo  = alertas.filter(a => a.impacto === 'Bajo').length;

  // Country summary chip
  const countryChip = fc !== 'all'
    ? '<span style="background:rgba(0,145,90,0.18);color:#00915A;font-size:12px;font-weight:700;padding:3px 12px;border-radius:20px;margin-left:10px;">📍 ' + fc + '</span>'
    : '';

  // Country capacity card — when filtered show big card for that country
  let capHtml = '';
  if (fc !== 'all' && countries.length === 1) {
    const c = countries[0];
    const pct = Math.round(c.available / c.total * 100);
    const bc  = c.status==='ok'?'#00915A':c.status==='warn'?'#A3C439':'#EF7B5B';
    const nc  = c.status==='ok'?'var(--primary)':c.status==='warn'?'#A3C439':'#EF7B5B';
    const sl  = c.status==='ok'?'Estable':c.status==='warn'?'Atención':'Crítico';
    const sc  = c.status==='ok'?'st-ok':c.status==='warn'?'st-warn':'st-crit';
    capHtml = '<div class="lp-card">' +
      '<div class="lp-section-title">Capacity — ' + c.country + ' ' + c.flag + '</div>' +
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">' +
        '<span style="font-size:13px;color:var(--muted);">Disponibles</span>' +
        '<span class="' + sc + '" style="font-size:11px;font-weight:700;padding:2px 10px;border-radius:10px;">' + sl + '</span>' +
      '</div>' +
      '<div style="font-size:36px;font-weight:800;color:' + nc + ';line-height:1;">' + c.available +
        '<span style="font-size:18px;color:var(--muted);font-weight:400;"> / ' + c.total + '</span>' +
      '</div>' +
      '<div style="background:var(--surface2);border-radius:4px;height:8px;overflow:hidden;margin:10px 0 6px;">' +
        '<div style="width:' + pct + '%;height:100%;background:' + bc + ';border-radius:4px;"></div>' +
      '</div>' +
      '<div style="display:flex;justify-content:space-between;font-size:12px;color:var(--muted);">' +
        '<span>Rol: <strong style="color:var(--text)">' + c.role + '</strong></span>' +
        '<span>Lead: <strong style="color:var(--text)">' + c.lead + '</strong></span>' +
      '</div>' +
    '</div>';
  } else {
    // All countries — compact bars
    capHtml = '<div class="lp-card">' +
      '<div class="lp-section-title">Capacity por País</div>' +
      countries.map(c => {
        const pct = Math.round(c.available / c.total * 100);
        const bc  = c.status==='ok'?'#00915A':c.status==='warn'?'#A3C439':'#EF7B5B';
        const nc  = c.status==='ok'?'var(--primary)':c.status==='warn'?'#A3C439':'#EF7B5B';
        return '<div style="margin-bottom:10px;">' +
          '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:3px;">' +
            '<span style="font-size:12px;font-weight:500;">' + c.flag + ' ' + c.country + '</span>' +
            '<span style="font-size:12px;color:' + nc + ';font-weight:700;">' + c.available +
              '<span style="color:var(--muted);font-weight:400;">/' + c.total + '</span></span>' +
          '</div>' +
          '<div style="background:var(--surface2);border-radius:3px;height:4px;overflow:hidden;">' +
            '<div style="width:' + pct + '%;height:100%;background:' + bc + ';border-radius:3px;"></div>' +
          '</div>' +
        '</div>';
      }).join('') +
    '</div>';
  }

  const alertasHtml = alertas.length
    ? alertas.map(al => {
        const ic = al.impacto==='Alto'?'ib-alto':al.impacto==='Medio'?'ib-medio':'ib-bajo';
        const planLines = al.plan.split('\n').map(l => '• ' + l).join('<br>');
        return '<div class="alert-row">' +
          '<div class="ar-icon">⚠️</div>' +
          '<div class="ar-desc"><div class="ar-desc-title">' + al.titulo + '</div>' +
            '<div class="ar-desc-text">' + al.desc.replace(/\n/g,'<br>') + '</div>' +
            '<div style="font-size:11px;color:var(--subtle);margin-top:4px;">' + al.tipo + '</div></div>' +
          '<div class="ar-impact"><span class="impact-badge ' + ic + '">' + al.impacto + '</span></div>' +
          '<div class="ar-plan">' + planLines + '</div>' +
          '<div class="ar-resp"><span class="resp-text">' + al.resp + '</span><span class="quarter-badge">' + al.eta + '</span></div>' +
        '</div>';
      }).join('')
    : '<div style="padding:24px;text-align:center;color:var(--muted);font-size:13px;">✅ Sin alertas' + (fc !== 'all' ? ' para ' + fc : ' activas para esta área') + '</div>';

  document.getElementById('area-detail').innerHTML =
    '<div class="area-nav">' +
      '<button class="nav-arrow" onclick="navArea(' + (idx>0?idx-1:d.areas.length-1) + ')">&lt; ' + prev.name + '</button>' +
      '<span class="area-nav-title">ESTADO GENERAL — ' + area.name + countryChip + '</span>' +
      '<button class="nav-arrow" onclick="navArea(' + (idx<d.areas.length-1?idx+1:0) + ')">' + next.name + ' &gt;</button>' +
    '</div>' +
    '<div class="area-body">' +
      '<div class="left-panel">' +
        '<div class="lp-card">' +
          '<div class="func-status">' +
            '<span class="func-label">Funcionalidad: <strong>' + area.funcionalidad + '</strong></span>' +
            '<span class="func-check">✓</span>' +
          '</div>' +
          '<p class="func-desc">' + area.funcDesc + '</p>' +
        '</div>' +
        '<div class="lp-card">' +
          '<div class="lp-section-title">KPIs Clave</div>' +
          '<p style="font-size:11px;color:var(--muted);margin-bottom:8px;">Primer corte 2026:</p>' +
          area.kpis.map(k =>
            '<div class="kpi-row"><span class="kpi-name">' + k.n + '</span><span class="kpi-val">' + k.v + '</span></div>'
          ).join('') +
          '<div class="kpi-total-row"><span class="kpi-total-name">Total</span>' +
            '<span class="kpi-total-val">' + area.kpis.reduce((s,k)=>s+k.v,0) + '</span></div>' +
          '<p class="kpi-note">✅ ' + area.kpiNote + '</p>' +
        '</div>' +
        '<div class="lp-card">' +
          '<div class="lp-section-title">Cobertura</div>' +
          area.cobertura.map(c =>
            '<div class="cov-item"><span class="cov-icon">✓</span><span class="cov-text">' + c + '</span></div>'
          ).join('') +
        '</div>' +
        capHtml +
      '</div>' +
      '<div class="center-panel">' +
        '<div class="panel-header">' +
          '<span class="panel-header-title">Alertas y Riesgos' + (fc !== 'all' ? ' — ' + fc : '') + '</span>' +
          '<div class="impact-pills">' +
            '<span class="ipill ipill-alto">' + alto + ' Alto</span>' +
            '<span class="ipill ipill-medio">' + medio + ' Medio</span>' +
            '<span class="ipill ipill-bajo">' + bajo + ' Bajo</span>' +
          '</div>' +
        '</div>' +
        '<div class="alerts-table">' +
          '<div class="at-header"><div>Tipo</div><div>Descripción</div><div>Impacto</div><div>Plan de Acción</div><div>Resp. / ETA</div></div>' +
          alertasHtml +
        '</div>' +
      '</div>' +
      '<div class="right-panel">' +
        '<div class="rp-card">' +
          '<div class="rp-header"><div class="rp-header-title">Novedades Relevantes</div></div>' +
          '<div class="rp-body">' +
            '<div class="rp-section"><span class="rp-tag tag-green">Logros</span>' +
              '<div class="rp-text"><ul>' + area.novedades.logros.map(l=>'<li>'+l+'</li>').join('') + '</ul></div></div>' +
            '<div class="rp-section"><span class="rp-tag tag-gray">Proyectos / Iniciativas</span>' +
              '<div class="rp-text"><ul>' + area.novedades.proyectos.map(p=>'<li>'+p+'</li>').join('') + '</ul></div></div>' +
            '<div class="rp-section"><span class="rp-tag tag-gray">Otros</span>' +
              '<div class="rp-text">' + area.novedades.otros.map(o=>o.replace(/\n/g,'<br>')).join('<br><br>') + '</div></div>' +
          '</div>' +
        '</div>' +
      '</div>' +
    '</div>' +
    '<div style="text-align:center;margin-top:20px;padding:10px;font-size:11px;color:var(--subtle);letter-spacing:2px;border-top:1px solid var(--border);">· Comité I &nbsp; IT Capacity ·</div>';
}

function navArea(idx){
  currentAreaIdx=idx;
  document.querySelectorAll('.fbtn').forEach((b,i)=>b.classList.toggle('active',i===idx));
  renderAreaDetail(DATA,idx);
  window.scrollTo({top:0,behavior:'smooth'});
}

function renderAlerts(d){
  const filtered = d.alerts.filter(a => {
    if (filterCountry.alt === 'all') return true;
    return a.tags && a.tags.some(t => t === filterCountry.alt);
  });
  document.getElementById('alist').innerHTML = filtered.length === 0
    ? '<div class="lbox">Sin alertas para el país seleccionado</div>'
    : filtered.map(a=>{
    const cls=a.sev==='warn'?' warn':a.sev==='info'?' info':'';
    const sc=a.sev==='crit'?'sc':a.sev==='warn'?'sw':'si2';
    const sl=a.sev==='crit'?'Crítico':a.sev==='warn'?'Advertencia':'Información';
    return '<div class="aitem'+cls+'"><span class="asev '+sc+'">'+sl+'</span><div class="abody"><div class="atitle">'+a.title+'</div><div class="adesc">'+a.desc+'</div><div class="atags">'+a.tags.map(t=>'<span class="atag">'+t+'</span>').join('')+'</div><div class="adate">📅 '+a.date+'</div></div></div>';
  }).join('');
}

function renderCommits(d){
  const filtered = d.commitments.filter((c, i) => {
    const countryOk = filterCountry.com === 'all' ||
      (c.title + ' ' + c.desc + ' ' + (c.owner||'')).includes(filterCountry.com) ||
      (c.bitacora||[]).some(b => (b.desc||'').includes(filterCountry.com));
    const statusOk  = filterStatus.com === 'all' || c.status === filterStatus.com;
    return countryOk && statusOk;
  });

  if (filtered.length === 0) {
    document.getElementById('clist').innerHTML = '<div class="lbox">Sin compromisos para el filtro seleccionado</div>';
    return;
  }

  document.getElementById('clist').innerHTML = filtered.map((c, i) => {
    const origIdx  = d.commitments.indexOf(c);
    const bc       = c.status==='prog'?'cp':c.status==='done'?'cd':c.status==='late'?'cl':'ce';
    const bita     = c.bitacora || [];
    const pct      = Math.min(100, Math.max(0, c.avance || 0));
    const pctColor = pct === 100 ? '#00915A' : pct >= 60 ? '#E8A020' : '#56B4C0';

    const hitoLines = (c.hitos || '').split('\n').filter(h => h.trim());
    const hitosHtml = hitoLines.map(h => {
      const t = h.trim();
      let cls = 'c-hito c-hito-pend';
      if (t.startsWith('✅')) cls = 'c-hito c-hito-done';
      else if (t.startsWith('🔄')) cls = 'c-hito c-hito-prog';
      else if (t.startsWith('❌')) cls = 'c-hito c-hito-block';
      return '<span class="' + cls + '">' + t + '</span>';
    }).join('');

    const TIPO_ICON = { avance:'📈', documento:'📄', reunion:'🤝', correo:'✉️', otro:'📌' };
    const bitaHtml = bita.length === 0 ? '' :
      '<div class="c-bita">' +
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">' +
          '<div class="c-bita-title">Bitácora de actividad</div>' +
          '<span style="font-size:11px;color:var(--muted);">' + bita.length + ' registro' + (bita.length > 1 ? 's' : '') + '</span>' +
        '</div>' +
        bita.slice().reverse().map(b => {
          const icon = TIPO_ICON[b.tipo] || '📌';
          return '<div class="c-bita-entry">' +
            '<div class="c-bita-dot c-bita-dot-' + b.tipo + '">' + icon + '</div>' +
            '<div class="c-bita-content">' +
              '<div class="c-bita-desc">' + b.desc + '</div>' +
              '<div class="c-bita-meta">' +
                '<span class="c-bita-tag c-bita-tag-' + b.tipo + '">' + b.tipo + '</span>' +
                ' 📅 ' + b.fecha + ' &nbsp;·&nbsp; 👤 ' + b.quien +
              '</div>' +
            '</div>' +
          '</div>';
        }).join('') +
      '</div>';

    const hasDetail = hitosHtml || bitaHtml;
    const detailCount = bita.length + hitoLines.length;

    return '<div class="citem">' +
      '<div class="citem-header">' +
        '<div class="cnum">' + String(origIdx+1).padStart(2,'0') + '</div>' +
        '<div class="cbody">' +
          '<div class="ctitle2">' + c.title + '</div>' +
          '<div class="cdesc">' + c.desc + '</div>' +
          '<div class="cfoot">' +
            '<span class="csbadge ' + bc + '">' + c.label + '</span>' +
            '<span class="cmeta2">👤 ' + c.owner + '</span>' +
            '<span class="cmeta2">📅 ' + c.due + '</span>' +
          '</div>' +
        '</div>' +
      '</div>' +
      '<div class="c-progress-wrap">' +
        '<div class="c-progress-header">' +
          '<span class="c-progress-label">Avance</span>' +
          '<span class="c-progress-pct" style="color:' + pctColor + ';">' + pct + '%</span>' +
        '</div>' +
        '<div class="c-progress-track">' +
          '<div class="c-progress-fill" style="width:' + pct + '%;background:' + pctColor + ';"></div>' +
        '</div>' +
      '</div>' +
      (hasDetail ? (
        '<div class="citem-toggle" onclick="toggleCommit(' + origIdx + ')">' +
          '<span class="citem-toggle-label">Hitos y Bitácora ' + (detailCount > 0 ? '(' + detailCount + ')' : '') + '</span>' +
          '<span class="citem-arrow" id="carrow-' + origIdx + '">▼</span>' +
        '</div>' +
        '<div class="citem-body" id="cbody-' + origIdx + '">' +
          '<div style="padding:14px 18px;">' +
            (hitosHtml ? '<div class="c-hitos" style="margin-bottom:12px;">' + hitosHtml + '</div>' : '') +
            bitaHtml +
          '</div>' +
        '</div>'
      ) : '') +
    '</div>';
  }).join('');
}

function sw(id){
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tbtn').forEach(b=>b.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  document.querySelector('[data-tab="'+id+'"]').classList.add('active');
}





renderAll(DATA);
</script>
"""

# ════════════════════════════════════════════════════════
#  GENERAR HTML
# ════════════════════════════════════════════════════════
data_json = json.dumps(DATA, ensure_ascii=False, indent=2)
# Build logo content
if logo_b64:
    logo_content = f'<img src="{logo_b64}" alt="Logo empresa" style="width:100%;height:100%;object-fit:contain;">'
else:
    logo_content = '<div class="logo-placeholder">LOGO<br>empresa</div>'

html_final = HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", data_json)
html_final = html_final.replace("__LOGO_CONTENT__", logo_content)

# Documento HTML completo — funciona en navegador directo Y en Confluence
standalone = (
    '<!DOCTYPE html>\n'
    '<html lang="es">\n'
    '<head>\n'
    '<meta charset="UTF-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    '<title>Gestión de Capacity e Iniciativas de Delivery</title>\n'
    '</head>\n'
    '<body style="margin:0;padding:0;background:#F5F6FA;">\n'
    + html_final +
    '\n</body>\n</html>'
)

OUTPUT_PATH.write_text(standalone, encoding='utf-8')

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
