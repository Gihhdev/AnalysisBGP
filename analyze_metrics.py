"""
Calcula as metricas quantitativas pedidas no trabalho a partir dos JSONs
brutos salvos por collect_data.py.
 
Metricas calculadas (ver tabela "Metricas minimas recomendadas" do enunciado):
1. Numero de ASNs de origem distintos observados para o prefixo na janela
   (mudanca de origin AS -> possivel hijack/reorganizacao)
2. Numero de TRANSICOES de origin AS na janela (quantas vezes o AS que
   origina o prefixo muda de um periodo pro seguinte)
3. Status RPKI (valid/invalid/unknown) do prefixo para o ASN vitima e,
   quando aplicavel, para o ASN suspeito
 
NOTA METODOLOGICA IMPORTANTE (ver Tarefa 7 do enunciado):
Os endpoints "bgplay" e "bgp-updates" do RIPEstat so tem cobertura de
eventos BGP em nivel de update a partir de janeiro de 2024 (confirmado na
documentacao oficial: https://stat.ripe.net/docs/data-api/api-endpoints/bgplay
e https://stat.ripe.net/docs/data-api/api-endpoints/bgp-updates). Como todos
os nossos incidentes sao de 2022, esses dois endpoints retornam eventos
vazios -- NAO e um bug de coleta, e uma limitacao de cobertura historica da
API. Por isso a metrica de "eventos de anuncio/withdrawal" foi substituida
pela contagem de transicoes de origin AS, derivada do endpoint
"routing-history" (que tem cobertura historica completa e ja usamos em
collect_data.py).
 
Da mesma forma, o "rpki-validation" usado aqui reflete o estado ATUAL dos
ROAs (nao o estado em 2022) -- isso deve ser explicitado no relatorio como
limitacao. Se for necessario o status RPKI historico, seria preciso usar o
endpoint "rpki-history" em vez de "rpki-validation".
 
Roda depois de collect_data.py. Uso: python analyze_metrics.py
"""
 
import json
import os
import csv
 
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
    """
    A partir do routing-history, calcula:
    - n_distinct_origins: quantos ASNs distintos originaram o prefixo na janela
    - n_origin_transitions: quantas vezes o origin mudou de um periodo pro
      seguinte, olhando a linha do tempo em ordem cronologica
    """
    rh = _load(name, "routing-history")
    if not rh:
        return {
            "n_distinct_origins": None,
            "origins": None,
            "n_origin_transitions": None,
        }
 
    # rh ja vem "desembrulhado" (sem chave "data" no topo) -- confirmado
    # inspecionando os JSONs salvos em output/raw/*_routing-history.json
    origins = {o.get("origin") for o in rh.get("by_origin", [])}
 
    # monta uma lista achatada de (starttime, origin) olhando dentro de
    # by_origin -> prefixes -> timelines (a estrutura real do endpoint)
    flat_periods = []
    for origin_entry in rh.get("by_origin", []):
        asn = origin_entry.get("origin")
        for pref_entry in origin_entry.get("prefixes", []):
            for period in pref_entry.get("timelines", []):
                start = period.get("starttime")
                if start:
                    flat_periods.append((start, asn))
 
    flat_periods.sort(key=lambda x: x[0])
 
    n_transitions = 0
    prev_asn = None
    for _, asn in flat_periods:
        if prev_asn is not None and asn != prev_asn:
            n_transitions += 1
        prev_asn = asn
 
    return {
        "n_distinct_origins": len(origins),
        "origins": ";".join(sorted(o for o in origins if o)),
        "n_origin_transitions": n_transitions,
    }
 
 
def metric_rpki(name: str) -> dict:
    """
    Status RPKI atual (nao historico) para o par (ASN, prefixo) da vitima e,
    quando aplicavel, do suspeito. Ver nota metodologica no topo do arquivo.
    """
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