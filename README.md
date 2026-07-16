# BGP e geopolítica — A8 (ataques cibernéticos / manipulação de rotas) × B1 (guerra Rússia–Ucrânia)

Código de coleta e análise de dados públicos de BGP (via API do RIPEstat) para
o trabalho final de Redes de Computadores.

## Como rodar

```bash
pip install -r requirements.txt
python collect_data.py     # baixa os dados brutos do RIPEstat -> output/raw/*.json
python analyze_metrics.py  # calcula as métricas -> output/metrics_summary.csv
python plot_results.py     # gera os gráficos -> output/figures/*.png
```

## ⚠️ Antes de rodar de verdade, façam isto:

1. **Preencher os TODOs em `config.py`.** O incidente `kherson_reroute_2022`
   está sem prefixo/ASN definidos — vocês precisam pesquisar (na Reuters, no
   NetBlocks, ou direto no RIPEstat/PeeringDB) qual(is) AS(es) da região de
   Kherson foram redirecionados para upstream russo em 2022, e qual ASN
   russo passou a ser o trânsito.
2. **Conferir a estrutura real do JSON do `bgplay`.** A API do RIPEstat pode
   mudar o formato de quando em quando. Rodem `collect_data.py` uma vez,
   abram `output/raw/<incidente>_bgplay.json` num editor e confirmem que os
   campos usados em `analyze_metrics.py` (`ev["type"]`, `ev["attrs"]["path"]`)
   batem com o que veio. Ajustem o parser se necessário — deixei comentários
   no código indicando esse ponto.
3. **Este ambiente (onde escrevi o código) não tem acesso à rede**, então não
   consegui testar as chamadas HTTP de verdade. O código segue a
   documentação oficial da API (https://stat.ripe.net/docs/data_api) mas
   testem localmente antes de confiar nos números.

## Estrutura

- `config.py` — lista de incidentes (prefixo, ASN vítima, ASN suspeito, data, fontes)
- `ripestat_client.py` — wrapper das chamadas à API do RIPEstat
- `collect_data.py` — baixa routing-history, bgplay e rpki-validation para cada incidente
- `analyze_metrics.py` — calcula as métricas quantitativas
- `plot_results.py` — gera os gráficos
- `output/` — dados brutos, CSVs de métricas e figuras geradas

## Métricas calculadas

| Métrica | O que indica |
|---|---|
| Nº de ASNs de origem distintos | Mudança de origin AS → possível hijack ou reorganização de rota |
| Nº de anúncios (A) e withdrawals (W) | Instabilidade de rota na janela do incidente |
| AS_PATH médio | Caminhos mais longos → reroteamento |
| Status RPKI (valid/invalid/unknown) | Se o anúncio malicioso seria bloqueado por ROV |

## Próximos passos sugeridos

- Adicionar mais 1-2 incidentes da lista de referências do MANRS
  (https://manrs.org/category/routing-security-incidents/) para ter uma
  amostra maior que 3 casos.
- Cruzar com CAIDA AS-relationships para ver se o ASN suspeito é
  cliente/peer/upstream de algum AS de trânsito relevante da Ucrânia.
- Considerar comparar com dados do Cloudflare Radar ou IODA para o mesmo
  período, para reforçar (ou não) a hipótese de disrupção real de tráfego —
  lembrando da observação metodológica do enunciado: BGP mostra o plano de
  controle, não o caminho físico dos pacotes.

## Lembrete metodológico (do enunciado)

> BGP não mostra necessariamente o caminho físico percorrido pelos pacotes.
> A interpretação correta é: "os caminhos BGP observados incluem ASes
> associados a determinado país ou região."
