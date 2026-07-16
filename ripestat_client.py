"""
Wrapper fino sobre a API publica do RIPEstat (https://stat.ripe.net/docs/data_api).
Nao exige API key. Todas as funcoes retornam o JSON já decodificado (dict).

Endpoints usados:
- routing-history: timeline de quais ASNs originaram um prefixo
- bgplay: eventos detalhados de anuncios/withdrawals num intervalo de tempo
- rpki-validation: status RPKI (valid/invalid/unknown) de um par prefixo+ASN
- visibility: quantos prefixos um ASN anuncia, visto pelos peers do RIS
- as-routing-consistency: compara o que o ASN anuncia vs o que esta registrado (IRR)
"""

import time
import requests

from config import RIPESTAT_BASE

HEADERS = {"User-Agent": "trabalho-redes-bgp-geopolitica/1.0"}


def _get(endpoint: str, params: dict, retries: int = 3, backoff: float = 2.0) -> dict:
    """GET generico com retry simples (a API do RIPEstat as vezes tem rate limit)."""
    url = f"{RIPESTAT_BASE}/{endpoint}/data.json"
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("status") != "ok":
                raise RuntimeError(f"RIPEstat status != ok: {payload.get('status_code')}")
            return payload["data"]
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(backoff * (attempt + 1))
    raise RuntimeError(f"Falha ao consultar {endpoint} com {params}: {last_err}")


def routing_history(resource: str, starttime: str, endtime: str) -> dict:
    """
    Historico de quem originou um prefixo (ou ASN) ao longo do tempo.
    resource: prefixo (ex '17.70.96.0/19') ou ASN (ex 'AS714')
    starttime/endtime: 'YYYY-MM-DDTHH:MM:SS' ou 'YYYY-MM-DD'
    """
    return _get("routing-history", {
        "resource": resource,
        "starttime": starttime,
        "endtime": endtime,
    })


def bgplay(resource: str, starttime: str, endtime: str) -> dict:
    """
    Eventos detalhados de BGP (anuncios/withdrawals por route collector)
    para um prefixo especifico, num intervalo de tempo.
    ATENCAO: janelas muito longas (>alguns dias) podem ficar pesadas.
    """
    return _get("bgplay", {
        "resource": resource,
        "starttime": starttime,
        "endtime": endtime,
    })


def rpki_validation(asn: str, prefix: str) -> dict:
    """Status RPKI (valid / invalid_asn / invalid_length / unknown) do par ASN+prefixo."""
    asn_num = asn.replace("AS", "")
    return _get("rpki-validation", {"resource": asn_num, "prefix": prefix})


def visibility(asn: str, at_time: str = None) -> dict:
    """Quantos prefixos o ASN anuncia, visto pelos peers do RIS num dado instante."""
    params = {"resource": asn.replace("AS", "")}
    if at_time:
        params["timestamp"] = at_time
    return _get("visibility", params)


def as_routing_consistency(asn: str) -> dict:
    """Compara anuncios reais do ASN com o que esta registrado em IRR/RPKI."""
    return _get("as-routing-consistency", {"resource": asn.replace("AS", "")})
