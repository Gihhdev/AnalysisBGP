"""
Configuracao dos incidentes a investigar.

Dimensao A8 (ataques ciberneticos e manipulacao de rotas) x
Questao B1 (guerra Russia-Ucrania e seguranca europeia)

Cada incidente tem:
- name: identificador curto
- prefix: prefixo IP envolvido (vitima)
- victim_asn: AS "dono" legitimo do prefixo
- suspect_asn: AS suspeito de ter originado/desviado o anuncio
- date: data central do incidente (str "YYYY-MM-DD")
- window_days: quantos dias antes/depois olhar para comparacao
- source: referencia da onde veio o relato do incidente (para o relatorio)

IMPORTANTE: as datas/ASNs abaixo vieram de reportagens e posts da MANRS/CERT-EU/
Reuters/Kentik. Confirmem os numeros exatos de ASN e prefixo consultando o
RIPEstat (endpoint search-completion ou o proprio looking-glass) antes de
publicar no relatorio -- fontes jornalisticas as vezes simplificam o dado
tecnico.
"""

INCIDENTS = [
    {
        "name": "twitter_blackhole_leak_2022",
        "prefix": "45.89.72.0/22",  # bloco citado no post da MANRS
        "victim_asn": "AS210512",   # origin legitimo apontado pela MANRS
        "suspect_asn": None,        # MANRS contesta que tenha havido hijack -- comparem com a narrativa jornalistica
        "date": "2022-02-28",
        "window_days": 10,
        "source": "MANRS (2022) - 'Did Ukraine suffer a BGP hijack...'",
    },
    {
        "name": "apple_rostelecom_2022",
        "prefix": "17.70.96.0/19",  # bloco da Apple
        "victim_asn": "AS714",      # Apple
        "suspect_asn": "AS12389",   # Rostelecom
        "date": "2022-07-26",
        "window_days": 5,
        "source": "MANRS / Reuters / The Register (jul/2022)",
    },
    {
        "name": "kherson_reroute_2022",
        # Territorio ocupado de Kherson: em vez de um prefixo unico, o caso
        # e melhor observado a nivel de ASN (redes locais ucranianas
        # ocupadas que passaram a anunciar via upstream russo).
        # Preencher prefix/ASN exatos apos pesquisa nas fontes do PDF /
        # RIPEstat (ex.: buscar ASes registrados na regiao de Kherson).
        "prefix": "91.206.110.0/23",
        "victim_asn": "AS47598",  # TODO: identificar ASN(s) da regiao de Kherson
        "suspect_asn": "AS201776",  # TODO: identificar upstream russo assumido
        "date": "2022-05-02",
        "window_days": 15,
        "source": "Reuters (2022-05-02) - 'Russia reroutes internet traffic in occupied Ukraine'",
    },
]

# Route collectors do RIPE RIS com boa cobertura europeia -- uteis se
# formos direto na API do RIPE RIS em vez do RIPEstat.
RELEVANT_RRC = ["rrc00", "rrc03", "rrc04", "rrc05"]

RIPESTAT_BASE = "https://stat.ripe.net/data"
