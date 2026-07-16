"""
Gera os graficos exigidos no trabalho (2-3 graficos) a partir de
output/metrics_summary.csv e output/routing_history_summary.csv.

Uso: python plot_results.py
Salva PNGs em output/figures/
"""

import os
import csv
from collections import defaultdict

import matplotlib.pyplot as plt

OUT_DIR = os.path.join("output", "figures")


def _read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def plot_announcements_withdrawals(metrics_rows):
    """Grafico de barras: anuncios vs withdrawals por incidente."""
    incidents = [r["incident"] for r in metrics_rows]
    ann = [int(r["n_announcements"]) if r["n_announcements"] else 0 for r in metrics_rows]
    wd = [int(r["n_withdrawals"]) if r["n_withdrawals"] else 0 for r in metrics_rows]

    x = range(len(incidents))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar([i - width / 2 for i in x], ann, width, label="Anuncios (A)")
    ax.bar([i + width / 2 for i in x], wd, width, label="Withdrawals (W)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(incidents, rotation=20, ha="right")
    ax.set_ylabel("Numero de eventos BGP")
    ax.set_title("Anuncios vs withdrawals por incidente (janela do bgplay)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "announcements_vs_withdrawals.png"), dpi=150)
    plt.close(fig)


def plot_as_path_length(metrics_rows):
    """Grafico de barras: tamanho medio do AS_PATH por incidente."""
    incidents = [r["incident"] for r in metrics_rows]
    lens = [float(r["avg_as_path_len"]) if r["avg_as_path_len"] else 0 for r in metrics_rows]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(incidents, lens, color="darkorange")
    ax.set_ylabel("Tamanho medio do AS_PATH")
    ax.set_title("AS_PATH medio observado durante a janela do incidente")
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "avg_as_path_length.png"), dpi=150)
    plt.close(fig)


def plot_distinct_origins(metrics_rows):
    """Grafico de barras: numero de ASNs de origem distintos por incidente."""
    incidents = [r["incident"] for r in metrics_rows]
    n_origins = [int(r["n_distinct_origins"]) if r["n_distinct_origins"] else 0 for r in metrics_rows]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(incidents, n_origins, color="seagreen")
    ax.set_ylabel("N. de ASNs de origem distintos")
    ax.set_title("Diversidade de origin AS por incidente (indicio de hijack/reorganizacao)")
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "distinct_origin_asns.png"), dpi=150)
    plt.close(fig)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    metrics_rows = _read_csv(os.path.join("output", "metrics_summary.csv"))
    if not metrics_rows:
        print("Nenhuma metrica encontrada -- rode collect_data.py e analyze_metrics.py primeiro.")
        return

    plot_announcements_withdrawals(metrics_rows)
    plot_as_path_length(metrics_rows)
    plot_distinct_origins(metrics_rows)
    print(f"Graficos salvos em {OUT_DIR}/")


if __name__ == "__main__":
    main()
