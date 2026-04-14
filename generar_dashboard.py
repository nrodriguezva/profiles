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
HTML_TEMPLATE = r"""<style>

/* ── Tema oscuro (defecto) ── */
#cap-dashboard {
  --bg:      #111111; --surface:  #1A1A1A; --surface2: #222222;
  --surface3:#2A2A2A; --border:   #333333; --border2:  #444444;
  --text:    #F0F0F0; --muted:    #888888; --subtle:   #555555;
  --primary: #00915A; --pdark:    #006B43; --pglow:    rgba(0,145,90,0.14);
  --coral:   #EF7B5B; --amber:    #E8A020; --sky:      #56B4C0;
  --stok-bg: rgba(0,145,90,0.18);  --stok-t:  #00915A;
  --swarn-bg:rgba(163,196,57,0.18);--swarn-t: #8aaa2e;
  --scrit-bg:rgba(239,123,91,0.2); --scrit-t: #EF7B5B;
}

/* ── Tema claro — Confluence en modo claro ── */
@media (prefers-color-scheme: light) {
  #cap-dashboard {
    --bg:      #F4F5F7; --surface:  #FFFFFF; --surface2: #F0F1F3;
    --surface3:#E8E9EB; --border:   #DFE1E6; --border2:  #C1C7D0;
    --text:    #172B4D; --muted:    #5E6C84; --subtle:   #97A0AF;
    --primary: #00915A; --pdark:    #006B43; --pglow:    rgba(0,145,90,0.10);
    --coral:   #C9402A; --amber:    #B37400; --sky:      #0052CC;
    --stok-bg: rgba(0,145,90,0.12);  --stok-t:  #006B43;
    --swarn-bg:rgba(130,100,0,0.12); --swarn-t: #7A5000;
    --scrit-bg:rgba(191,38,0,0.10);  --scrit-t: #BF2600;
  }
}

/* ── Confluence activa modo oscuro con estas clases en el body ── */
body.dark #cap-dashboard,
body[data-color-mode="dark"] #cap-dashboard,
body[class*="dark-mode"] #cap-dashboard,
.dark #cap-dashboard {
  --bg:      #111111; --surface:  #1A1A1A; --surface2: #222222;
  --surface3:#2A2A2A; --border:   #333333; --border2:  #444444;
  --text:    #F0F0F0; --muted:    #888888; --subtle:   #555555;
}

/* ── Confluence activa modo claro con estas clases ── */
body.light #cap-dashboard,
body[data-color-mode="light"] #cap-dashboard,
body[class*="light-mode"] #cap-dashboard {
  --bg:      #F4F5F7; --surface:  #FFFFFF; --surface2: #F0F1F3;
  --surface3:#E8E9EB; --border:   #DFE1E6; --border2:  #C1C7D0;
  --text:    #172B4D; --muted:    #5E6C84; --subtle:   #97A0AF;
}

/* ── BASE ── */
#cap-dashboard *{box-sizing:border-box;margin:0;padding:0;}
#cap-dashboard{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);border-radius:8px;overflow:hidden;width:100%;display:block;transition:background .3s,color .3s;}
#cap-dashboard header{background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:stretch;}
#cap-dashboard .h-accent{width:5px;flex-shrink:0;background:linear-gradient(180deg,#595959 0%,var(--primary) 100%);}
#cap-dashboard .h-content{flex:1;display:flex;align-items:center;justify-content:space-between;padding:14px 32px;flex-wrap:wrap;gap:10px;}
#cap-dashboard .h-left{display:flex;align-items:center;gap:14px;}
#cap-dashboard .logo-slot{width:48px;height:48px;border-radius:8px;border:1px solid var(--border);background:var(--surface2);display:flex;align-items:center;justify-content:center;flex-shrink:0;overflow:hidden;}
#cap-dashboard .logo-slot img{width:100%;height:100%;object-fit:contain;}
#cap-dashboard .logo-placeholder{font-size:8px;color:var(--subtle);text-align:center;line-height:1.3;pointer-events:none;}
#cap-dashboard .h-title{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;line-height:1;color:var(--text);}
#cap-dashboard .h-sub{font-size:10px;color:var(--muted);margin-top:2px;letter-spacing:.3px;}
#cap-dashboard .h-badge{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);background:var(--surface2);border:1px solid var(--border);border-radius:20px;padding:5px 12px;}
#cap-dashboard .live{width:6px;height:6px;background:var(--primary);border-radius:50%;animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
#cap-dashboard .tabs{display:flex;gap:2px;padding:12px 32px 0;background:var(--surface);border-bottom:1px solid var(--border);overflow-x:auto;}
#cap-dashboard .tbtn{font-family:'Inter',sans-serif;font-size:12px;font-weight:500;color:var(--muted);background:transparent;border:none;cursor:pointer;padding:7px 14px;border-radius:5px 5px 0 0;border-bottom:2px solid transparent;white-space:nowrap;transition:all .15s;}
#cap-dashboard .tbtn:hover{color:var(--text);background:rgba(128,128,128,0.08);}
#cap-dashboard .tbtn.active{color:var(--primary);border-bottom-color:var(--primary);background:var(--pglow);}
#cap-dashboard .tbadge{display:inline-block;font-size:9px;font-weight:700;border-radius:10px;padding:1px 6px;margin-left:4px;vertical-align:middle;}
#cap-dashboard .tbr{background:rgba(239,123,91,.22);color:var(--coral);}
#cap-dashboard .tbg{background:var(--stok-bg);color:var(--primary);}
#cap-dashboard main{padding:20px 32px 60px;max-width:1600px;margin:0 auto;background:var(--bg);}
#cap-dashboard .tab-panel{display:none;}
#cap-dashboard .tab-panel.active{display:block;animation:fu .2s ease;}
@keyframes fu{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
#cap-dashboard .fbar{display:flex;align-items:center;gap:6px;margin-bottom:20px;flex-wrap:wrap;}
#cap-dashboard .fl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-right:2px;}
#cap-dashboard .fbtn{font-size:11px;font-weight:500;background:var(--surface2);color:var(--muted);border:1px solid var(--border);border-radius:14px;padding:4px 12px;cursor:pointer;transition:all .14s;white-space:nowrap;font-family:'Inter',sans-serif;}
#cap-dashboard .fbtn:hover{color:var(--text);border-color:var(--primary);}
#cap-dashboard .fbtn.active{background:var(--primary);color:#fff;border-color:var(--primary);}
#cap-dashboard .area-nav{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;padding:10px 14px;background:var(--surface);border:1px solid var(--border);border-radius:8px;}
#cap-dashboard .area-nav-title{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:var(--primary);}
#cap-dashboard .nav-arrow{font-size:11px;color:var(--muted);cursor:pointer;padding:5px 10px;border-radius:5px;border:1px solid var(--border);background:transparent;transition:all .14s;font-family:'Inter',sans-serif;}
#cap-dashboard .nav-arrow:hover{color:var(--text);border-color:var(--primary);}
#cap-dashboard .area-body{display:grid;grid-template-columns:220px 1fr 260px;gap:12px;align-items:start;}
#cap-dashboard .left-panel{display:flex;flex-direction:column;gap:10px;}
#cap-dashboard .lp-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px;}
#cap-dashboard .lp-section-title{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--primary);margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid var(--border);}
#cap-dashboard .func-status{display:flex;align-items:center;gap:8px;margin-bottom:6px;}
#cap-dashboard .func-label{font-size:13px;font-weight:600;color:var(--text);}
#cap-dashboard .func-check{width:18px;height:18px;background:var(--primary);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:10px;color:#fff;}
#cap-dashboard .func-desc{font-size:11px;color:var(--muted);line-height:1.5;}
#cap-dashboard .kpi-row{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--border);}
#cap-dashboard .kpi-row:last-child{border-bottom:none;}
#cap-dashboard .kpi-name{font-size:11px;color:var(--muted);}
#cap-dashboard .kpi-val{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:700;color:var(--text);}
#cap-dashboard .kpi-total-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0 0;margin-top:2px;}
#cap-dashboard .kpi-total-name{font-size:11px;font-weight:600;color:var(--text);}
#cap-dashboard .kpi-total-val{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:700;color:var(--primary);}
#cap-dashboard .kpi-note{font-size:9px;color:var(--subtle);line-height:1.4;margin-top:8px;}
#cap-dashboard .cov-item{display:flex;align-items:flex-start;gap:7px;margin-bottom:8px;}
#cap-dashboard .cov-icon{width:14px;height:14px;background:var(--primary);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;font-size:8px;color:#fff;}
#cap-dashboard .cov-text{font-size:11px;color:var(--muted);line-height:1.4;}
#cap-dashboard .panel-header{background:var(--primary);border-radius:8px 8px 0 0;padding:10px 14px;display:flex;align-items:center;justify-content:space-between;}
#cap-dashboard .panel-header-title{font-family:'Barlow Condensed',sans-serif;font-size:15px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#fff;}
#cap-dashboard .impact-pills{display:flex;gap:6px;}
#cap-dashboard .ipill{font-size:10px;font-weight:700;padding:3px 10px;border-radius:5px;}
#cap-dashboard .ipill-alto{background:#fff;color:#C9402A;}
#cap-dashboard .ipill-medio{background:#fff;color:#B37400;}
#cap-dashboard .ipill-bajo{background:#fff;color:#006B43;}
#cap-dashboard .alerts-table{background:var(--surface);border:1px solid var(--border);border-top:none;border-radius:0 0 8px 8px;overflow:hidden;}
#cap-dashboard .at-header{display:grid;grid-template-columns:36px 1fr 80px 160px 100px;background:var(--surface2);border-bottom:1px solid var(--border);}
#cap-dashboard .at-header div{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);padding:7px 10px;}
#cap-dashboard .alert-row{display:grid;grid-template-columns:36px 1fr 80px 160px 100px;border-bottom:1px solid var(--border);align-items:start;}
#cap-dashboard .alert-row:last-child{border-bottom:none;}
#cap-dashboard .alert-row:hover{background:var(--surface2);}
#cap-dashboard .ar-icon{padding:14px 8px;display:flex;align-items:flex-start;justify-content:center;}
#cap-dashboard .ar-desc{padding:12px 10px;}
#cap-dashboard .ar-desc-title{font-size:12px;font-weight:600;margin-bottom:4px;color:var(--text);}
#cap-dashboard .ar-desc-text{font-size:11px;color:var(--muted);line-height:1.5;}
#cap-dashboard .ar-impact{padding:12px 10px;display:flex;align-items:flex-start;justify-content:center;}
#cap-dashboard .impact-badge{font-size:10px;font-weight:700;padding:3px 10px;border-radius:5px;border:1.5px solid;white-space:nowrap;}
#cap-dashboard .ib-alto{border-color:var(--coral);color:var(--coral);}
#cap-dashboard .ib-medio{border-color:var(--amber);color:var(--amber);}
#cap-dashboard .ib-bajo{border-color:var(--primary);color:var(--primary);}
#cap-dashboard .ar-plan{padding:12px 10px;font-size:11px;color:var(--muted);line-height:1.5;}
#cap-dashboard .ar-resp{padding:12px 10px;display:flex;flex-direction:column;gap:5px;align-items:flex-start;}
#cap-dashboard .resp-text{font-size:11px;color:var(--muted);}
#cap-dashboard .quarter-badge{font-family:'Barlow Condensed',sans-serif;font-size:13px;font-weight:700;background:var(--pdark);color:#fff;padding:3px 10px;border-radius:5px;letter-spacing:1px;}
#cap-dashboard .right-panel{display:flex;flex-direction:column;gap:10px;}
#cap-dashboard .rp-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;overflow:hidden;}
#cap-dashboard .rp-header{background:var(--surface2);padding:9px 14px;border-bottom:1px solid var(--border);}
#cap-dashboard .rp-header-title{font-family:'Barlow Condensed',sans-serif;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text);}
#cap-dashboard .rp-body{padding:12px 14px;}
#cap-dashboard .rp-tag{display:inline-block;font-size:10px;font-weight:700;padding:3px 10px;border-radius:5px;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px;}
#cap-dashboard .tag-green{background:var(--primary);color:#fff;}
#cap-dashboard .tag-gray{background:var(--surface3);color:var(--muted);border:1px solid var(--border2);}
#cap-dashboard .rp-text{font-size:11px;color:var(--muted);line-height:1.6;}
#cap-dashboard .rp-text li{margin-left:12px;margin-top:3px;}
#cap-dashboard .rp-section{margin-bottom:10px;}
#cap-dashboard .rp-section:last-child{margin-bottom:0;}
#cap-dashboard .alist{display:flex;flex-direction:column;gap:8px;}
#cap-dashboard .aitem{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--coral);border-radius:0 8px 8px 0;padding:13px 15px;display:flex;gap:11px;align-items:flex-start;}
#cap-dashboard .aitem.warn{border-left-color:var(--amber);}
#cap-dashboard .aitem.info{border-left-color:var(--sky);}
#cap-dashboard .asev{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 7px;border-radius:8px;white-space:nowrap;flex-shrink:0;margin-top:1px;}
#cap-dashboard .sc{background:var(--scrit-bg);color:var(--scrit-t);}
#cap-dashboard .sw{background:var(--swarn-bg);color:var(--swarn-t);}
#cap-dashboard .si2{background:rgba(86,180,192,.15);color:var(--sky);}
#cap-dashboard .abody{flex:1;}
#cap-dashboard .atitle{font-size:12px;font-weight:600;margin-bottom:3px;color:var(--text);}
#cap-dashboard .adesc{font-size:11px;color:var(--muted);line-height:1.5;}
#cap-dashboard .atags{display:flex;gap:5px;margin-top:7px;flex-wrap:wrap;}
#cap-dashboard .atag{font-size:9px;background:var(--surface2);border:1px solid var(--border);border-radius:5px;padding:2px 7px;color:var(--muted);}
#cap-dashboard .adate{font-size:9px;color:var(--subtle);margin-top:3px;}
#cap-dashboard .clist{display:flex;flex-direction:column;gap:8px;}
#cap-dashboard .citem{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:13px 15px;display:flex;gap:13px;align-items:flex-start;}
#cap-dashboard .cnum{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:700;color:var(--primary);flex-shrink:0;min-width:28px;}
#cap-dashboard .cbody{flex:1;}
#cap-dashboard .ctitle2{font-size:12px;font-weight:600;margin-bottom:3px;color:var(--text);}
#cap-dashboard .cdesc{font-size:11px;color:var(--muted);line-height:1.5;}
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
#cap-dashboard .lbox{text-align:center;padding:50px 20px;color:var(--muted);font-size:12px;}
@media(max-width:900px){#cap-dashboard .area-body{grid-template-columns:1fr;}#cap-dashboard .at-header,#cap-dashboard .alert-row{grid-template-columns:32px 1fr 70px;}#cap-dashboard .at-header div:nth-child(4),#cap-dashboard .at-header div:nth-child(5),#cap-dashboard .alert-row .ar-plan,#cap-dashboard .alert-row .ar-resp{display:none;}}
@media(max-width:600px){#cap-dashboard .h-content,#cap-dashboard .tabs,#cap-dashboard main{padding-left:14px;padding-right:14px;}}
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



// ── Detección de tema Confluence ─────────────────────
(function() {
  var el = document.getElementById('cap-dashboard');
  if (!el) return;

  function applyTheme(dark) {
    if (dark) {
      // Modo oscuro
      el.style.setProperty('--bg',       '#111111');
      el.style.setProperty('--surface',  '#1A1A1A');
      el.style.setProperty('--surface2', '#222222');
      el.style.setProperty('--surface3', '#2A2A2A');
      el.style.setProperty('--border',   '#333333');
      el.style.setProperty('--border2',  '#444444');
      el.style.setProperty('--text',     '#F0F0F0');
      el.style.setProperty('--muted',    '#888888');
      el.style.setProperty('--subtle',   '#555555');
      el.style.setProperty('--coral',    '#EF7B5B');
      el.style.setProperty('--amber',    '#E8A020');
      el.style.setProperty('--sky',      '#56B4C0');
      el.style.setProperty('--stok-bg',  'rgba(0,145,90,0.18)');
      el.style.setProperty('--stok-t',   '#00915A');
      el.style.setProperty('--swarn-bg', 'rgba(163,196,57,0.18)');
      el.style.setProperty('--swarn-t',  '#8aaa2e');
      el.style.setProperty('--scrit-bg', 'rgba(239,123,91,0.2)');
      el.style.setProperty('--scrit-t',  '#EF7B5B');
    } else {
      // Modo claro
      el.style.setProperty('--bg',       '#F4F5F7');
      el.style.setProperty('--surface',  '#FFFFFF');
      el.style.setProperty('--surface2', '#F0F1F3');
      el.style.setProperty('--surface3', '#E8E9EB');
      el.style.setProperty('--border',   '#DFE1E6');
      el.style.setProperty('--border2',  '#C1C7D0');
      el.style.setProperty('--text',     '#172B4D');
      el.style.setProperty('--muted',    '#5E6C84');
      el.style.setProperty('--subtle',   '#97A0AF');
      el.style.setProperty('--coral',    '#C9402A');
      el.style.setProperty('--amber',    '#B37400');
      el.style.setProperty('--sky',      '#0052CC');
      el.style.setProperty('--stok-bg',  'rgba(0,145,90,0.12)');
      el.style.setProperty('--stok-t',   '#006B43');
      el.style.setProperty('--swarn-bg', 'rgba(130,100,0,0.12)');
      el.style.setProperty('--swarn-t',  '#7A5000');
      el.style.setProperty('--scrit-bg', 'rgba(191,38,0,0.10)');
      el.style.setProperty('--scrit-t',  '#BF2600');
    }
  }

  function detectDark() {
    // 1. Intentar acceder al body del padre (funciona si no hay cross-origin)
    try {
      var parentBody = window.parent.document.body;
      var cls = parentBody.className || '';
      var attr = parentBody.getAttribute('data-color-mode') || '';
      var html = parentBody.parentElement;
      var htmlCls = html ? (html.className || '') : '';
      if (cls.includes('dark') || attr === 'dark' || htmlCls.includes('dark')) return true;
      if (cls.includes('light') || attr === 'light') return false;
    } catch(e) {}

    // 2. Revisar el body actual (cuando NO hay iframe)
    try {
      var b = document.body;
      var bc = (b.className || '') + ' ' + (b.getAttribute('data-color-mode') || '');
      var hc = (document.documentElement.className || '');
      if (bc.includes('dark') || hc.includes('dark')) return true;
      if (bc.includes('light') || hc.includes('light')) return false;
    } catch(e) {}

    // 3. Fallback: prefers-color-scheme del sistema
    try {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    } catch(e) {}

    return true; // defecto oscuro
  }

  // Aplicar tema al cargar
  applyTheme(detectDark());

  // Observar cambios de clase en el body padre en tiempo real
  try {
    var target = window.parent.document.body;
    var observer = new MutationObserver(function() {
      applyTheme(detectDark());
    });
    observer.observe(target, { attributes: true, attributeFilter: ['class', 'data-color-mode'] });
  } catch(e) {
    // También observar el body local
    try {
      var observer2 = new MutationObserver(function() {
        applyTheme(detectDark());
      });
      observer2.observe(document.body, { attributes: true, attributeFilter: ['class', 'data-color-mode'] });
    } catch(e2) {}
  }

  // También escuchar cambio de sistema operativo
  try {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
      applyTheme(detectDark());
    });
  } catch(e) {}
})();

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
