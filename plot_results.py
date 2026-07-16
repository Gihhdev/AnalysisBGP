"""
Gera os graficos exigidos no trabalho (2-3 graficos) a partir de
output/metrics_summary.csv e output/routing_history_summary.csv.
 
Uso: python plot_results.py
Salva PNGs em output/figures/
"""
 
import os
import csv
from collections import defaultdict
from datetime import datetime
 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
 
OUT_DIR = os.path.join("output", "figures")
 
 
def _read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))
 
 
def plot_origin_timeline(routing_rows):
    """
    Timeline (estilo Gantt) mostrando qual ASN originou o prefixo ao longo
    do tempo, um subplot por incidente. Esse e o grafico mais direto pra
    visualizar hijacks/mudancas de origin.
    """
    by_incident = defaultdict(list)
    for r in routing_rows:
        start = r.get("starttime")
        end = r.get("endtime")
        if not start or not end:
            continue
        by_incident[r["incident"]].append(
            {
                "origin": r["origin_asn"],
                "start": datetime.fromisoformat(start),
                "end": datetime.fromisoformat(end),
                "expected_victim": r.get("expected_victim_asn", ""),
                "expected_suspect": r.get("expected_suspect_asn", ""),
            }
        )
 
    incidents = list(by_incident.keys())
    if not incidents:
        print("  (timeline) sem dados em routing_history_summary.csv -- pulando")
        return
 
    fig, axes = plt.subplots(len(incidents), 1, figsize=(10, 3 * len(incidents)), squeeze=False)
 
    for ax, incident in zip(axes[:, 0], incidents):
        periods = sorted(by_incident[incident], key=lambda p: p["start"])
        origins = sorted({p["origin"] for p in periods})
        expected_suspect = periods[0]["expected_suspect"]
 
        color_map = {}
        palette = plt.cm.tab10.colors
        for i, asn in enumerate(origins):
            color_map[asn] = palette[i % len(palette)]
 
        y_pos = {asn: i for i, asn in enumerate(origins)}
 
        for p in periods:
            color = color_map[p["origin"]]
            # destaca em vermelho se o origin bater com o suspeito esperado
            if expected_suspect and p["origin"] == expected_suspect.replace("AS", ""):
                color = "crimson"
            ax.barh(
                y_pos[p["origin"]],
                width=p["end"] - p["start"],
                left=p["start"],
                height=0.6,
                color=color,
            )
 
        ax.set_yticks(list(y_pos.values()))
        ax.set_yticklabels([f"AS{a}" for a in y_pos.keys()])
        ax.set_title(incident)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        ax.grid(axis="x", linestyle="--", alpha=0.4)
 
    fig.suptitle("Origin AS observado ao longo do tempo (RIPEstat routing-history)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "origin_timeline.png"), dpi=150)
    plt.close(fig)
 
 
def plot_origin_transitions(metrics_rows):
    """Grafico de barras: numero de transicoes de origin AS por incidente."""
    incidents = [r["incident"] for r in metrics_rows]
    transitions = [
        int(r["n_origin_transitions"]) if r.get("n_origin_transitions") else 0
        for r in metrics_rows
    ]
 
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(incidents, transitions, color="darkorange")
    ax.set_ylabel("N. de transicoes de origin AS")
    ax.set_title("Transicoes de origin AS por incidente (janela do routing-history)")
    ax.set_yticks(range(0, max(transitions, default=0) + 2))
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "origin_transitions.png"), dpi=150)
    plt.close(fig)
 
 
def plot_distinct_origins(metrics_rows):
    """Grafico de barras: numero de ASNs de origem distintos por incidente."""
    incidents = [r["incident"] for r in metrics_rows]
    n_origins = [
        int(r["n_distinct_origins"]) if r.get("n_distinct_origins") else 0
        for r in metrics_rows
    ]
 
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(incidents, n_origins, color="seagreen")
    ax.set_ylabel("N. de ASNs de origem distintos")
    ax.set_title("Diversidade de origin AS por incidente (indicio de hijack/reorganizacao)")
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "distinct_origin_asns.png"), dpi=150)
    plt.close(fig)
 
 
def plot_rpki_status(metrics_rows):
    """Grafico de barras empilhadas: status RPKI (victim/suspect) por incidente."""
    incidents = [r["incident"] for r in metrics_rows]
    statuses = ["valid", "invalid", "invalid_asn", "invalid_length", "unknown"]
    color_map = {
        "valid": "seagreen",
        "invalid": "crimson",
        "invalid_asn": "crimson",
        "invalid_length": "indianred",
        "unknown": "gray",
    }
 
    fig, ax = plt.subplots(figsize=(8, 5))
    width = 0.35
    x = range(len(incidents))
 
    victim_vals = [r.get("rpki_victim_status") or "unknown" for r in metrics_rows]
    suspect_vals = [r.get("rpki_suspect_status") or "n/a" for r in metrics_rows]
 
    for i, (v, s) in enumerate(zip(victim_vals, suspect_vals)):
        ax.bar(i - width / 2, 1, width, color=color_map.get(v, "lightgray"), edgecolor="black")
        ax.text(i - width / 2, 1.05, v, ha="center", fontsize=8, rotation=15)
        if s != "n/a":
            ax.bar(i + width / 2, 1, width, color=color_map.get(s, "lightgray"), edgecolor="black")
            ax.text(i + width / 2, 1.05, s, ha="center", fontsize=8, rotation=15)
 
    ax.set_xticks(list(x))
    ax.set_xticklabels(incidents, rotation=20, ha="right")
    ax.set_yticks([])
    ax.set_ylim(0, 1.3)
    ax.set_title("Status RPKI atual: vitima (esq.) vs suspeito (dir.)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "rpki_status.png"), dpi=150)
    plt.close(fig)
 
 
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    metrics_rows = _read_csv(os.path.join("output", "metrics_summary.csv"))
    routing_rows = _read_csv(os.path.join("output", "routing_history_summary.csv"))
 
    if not metrics_rows:
        print("Nenhuma metrica encontrada -- rode collect_data.py e analyze_metrics.py primeiro.")
        return
 
    plot_origin_timeline(routing_rows)
    plot_origin_transitions(metrics_rows)
    plot_distinct_origins(metrics_rows)
    plot_rpki_status(metrics_rows)
    print(f"Graficos salvos em {OUT_DIR}/")
 
 
if __name__ == "__main__":
    main()
 