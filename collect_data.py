"""
Coleta os dados brutos do RIPEstat para cada incidente definido em config.py
e salva:
- JSON bruto de cada endpoint em output/raw/<incident_name>_<endpoint>.json
- Um CSV resumido em output/routing_history_summary.csv com uma linha por
  (incidente, ASN de origem, periodo em que foi visto originando o prefixo)

Rodar com: python collect_data.py
Requisitos: pip install -r requirements.txt
"""

import json
import csv
import os
from datetime import datetime, timedelta

from config import INCIDENTS
import ripestat_client as ripe

OUT_DIR = "output"
RAW_DIR = os.path.join(OUT_DIR, "raw")


def _daterange(center_date: str, window_days: int):
    center = datetime.strptime(center_date, "%Y-%m-%d")
    start = center - timedelta(days=window_days)
    end = center + timedelta(days=window_days)
    return start.strftime("%Y-%m-%dT00:00:00"), end.strftime("%Y-%m-%dT00:00:00")


def _save_raw(name: str, endpoint: str, data: dict):
    os.makedirs(RAW_DIR, exist_ok=True)
    path = os.path.join(RAW_DIR, f"{name}_{endpoint}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  salvo {path}")


def collect_incident(incident: dict, summary_rows: list):
    name = incident["name"]
    prefix = incident["prefix"]
    date = incident["date"]
    window = incident["window_days"]

    if not prefix:
        print(f"[{name}] prefixo nao definido em config.py -- pulando (preencher TODO).")
        return

    start, end = _daterange(date, window)
    print(f"[{name}] janela {start} -> {end} | prefixo {prefix}")

    # 1) routing-history: quem originou o prefixo ao longo da janela
# 1) routing-history: quem originou o prefixo ao longo da janela
    try:
        rh = ripe.routing_history(prefix, start, end)
        _save_raw(name, "routing-history", rh)

        # CORREÇÃO: rh já é o conteúdo de "data" (o client desembrulha isso),
        # então não usamos rh.get("data", {}) -- usamos rh direto.
        for origin in rh.get("by_origin", []):
            asn = origin.get("origin")
            # CORREÇÃO: timelines fica dentro de "prefixes", não direto em "origin"
            for pref_entry in origin.get("prefixes", []):
                pfx = pref_entry.get("prefix", prefix)
                for period in pref_entry.get("timelines", []):
                    summary_rows.append({
                        "incident": name,
                        "prefix": pfx,
                        "origin_asn": asn,
                        "starttime": period.get("starttime"),
                        "endtime": period.get("endtime"),
                        "expected_victim_asn": incident.get("victim_asn"),
                        "expected_suspect_asn": incident.get("suspect_asn"),
                    })
    except Exception as e:  # noqa: BLE001
        print(f"  ERRO routing-history: {e}")

    # 2) bgplay: eventos detalhados (announcements/withdrawals) -- janela menor
    #    para nao pesar demais (bgplay eh caro para intervalos longos)
    try:
        bgplay_start, bgplay_end = _daterange(date, min(window, 3))
        bp = ripe.bgplay(prefix, bgplay_start, bgplay_end)
        _save_raw(name, "bgplay", bp)
    except Exception as e:  # noqa: BLE001
        print(f"  ERRO bgplay: {e}")

    # 3) rpki-validation para o par (suspect_asn ou victim_asn, prefix)
    for role, asn in [("victim", incident.get("victim_asn")), ("suspect", incident.get("suspect_asn"))]:
        if not asn:
            continue
        try:
            rpki = ripe.rpki_validation(asn, prefix)
            _save_raw(name, f"rpki-{role}", rpki)
        except Exception as e:  # noqa: BLE001
            print(f"  ERRO rpki-validation ({role}): {e}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    summary_rows = []
    for incident in INCIDENTS:
        collect_incident(incident, summary_rows)
    print(f"Resumo dos incidentes:{summary_rows}")

    if summary_rows:
        csv_path = os.path.join(OUT_DIR, "routing_history_summary.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)
        print(f"\nResumo salvo em {csv_path} ({len(summary_rows)} linhas)")
    else:
        print("\nNenhum dado coletado -- confira os TODOs em config.py")


if __name__ == "__main__":
    main()
