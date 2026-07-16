"""
Calcula as metricas quantitativas pedidas no trabalho a partir dos JSONs
brutos salvos por collect_data.py.

Metricas calculadas (ver tabela "Metricas minimas recomendadas" do enunciado):
1. Numero de ASNs de origem distintos observados para o prefixo na janela
   (mudanca de origin AS -> possivel hijack/reorganizacao)
2. Numero de eventos de anuncio (A) e retirada (W) na janela do bgplay
3. Tamanho medio do AS_PATH observado nos eventos de anuncio
4. Status RPKI (valid/invalid/unknown) do prefixo para o ASN vitima e,
   quando aplicavel, para o ASN suspeito

Roda depois de collect_data.py. Uso: python analyze_metrics.py
"""

import json
import os
import csv
import statistics as stats

from config import INCIDENTS

RAW_DIR = os.path.join("output", "raw")
OUT_CSV = os.path.join("output", "metrics_summary.csv")


def _load(name: str, endpoint: str):
    path = os.path.join(RAW_DIR, f"{name}_{endpoint}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def metric_origin_changes(name: str) -> dict:
    rh = _load(name, "routing-history")
    if not rh:
        return {"n_distinct_origins": None, "origins": None}
    origins = {o.get("origin") for o in rh.get("by_origin", [])}
    return {"n_distinct_origins": len(origins), "origins": ";".join(sorted(origins))}


def metric_bgplay_events(name: str) -> dict:
    """
    Extrai contagem de anuncios/withdrawals e AS_PATH medio do JSON do bgplay.
    A estrutura do bgplay pode variar de versao; ajuste os campos abaixo
    conforme o JSON real retornado (inspecionem output/raw/*_bgplay.json).
    """
    bp = _load(name, "bgplay")
    if not bp:
        return {"n_announcements": None, "n_withdrawals": None, "avg_as_path_len": None}

    events = bp.get("events", [])
    n_ann, n_wd = 0, 0
    path_lens = []

    for ev in events:
        ev_type = ev.get("type")  # normalmente "A" (announcement) ou "W" (withdrawal)
        if ev_type == "A":
            n_ann += 1
            # o caminho pode estar em ev["attrs"]["path"] ou similar -- confirmar no JSON salvo
            path = ev.get("attrs", {}).get("path") or ev.get("path")
            if path:
                path_lens.append(len(path))
        elif ev_type == "W":
            n_wd += 1

    avg_len = round(stats.mean(path_lens), 2) if path_lens else None
    return {"n_announcements": n_ann, "n_withdrawals": n_wd, "avg_as_path_len": avg_len}


def metric_rpki(name: str) -> dict:
    result = {}
    for role in ["victim", "suspect"]:
        data = _load(name, f"rpki-{role}")
        if data:
            result[f"rpki_{role}_status"] = data.get("status")
        else:
            result[f"rpki_{role}_status"] = None
    return result


def main():
    rows = []
    for incident in INCIDENTS:
        name = incident["name"]
        row = {"incident": name, "date": incident["date"], "source": incident["source"]}
        row.update(metric_origin_changes(name))
        row.update(metric_bgplay_events(name))
        row.update(metric_rpki(name))
        rows.append(row)

    os.makedirs("output", exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Metricas salvas em {OUT_CSV}")
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
