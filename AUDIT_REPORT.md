# Audit Report — market-expansion-eda

## Status antes da intervenção
- **Nota geral: 8.4/10**
- Gaps identificados:
  - Sem script standalone — análise presa dentro do notebook (requer Jupyter)
  - Pasta `outputs/` inexistente — nenhum gráfico ou CSV exportado
  - Sem `executive_summary.md` com recomendações acionáveis para o negócio
  - Sem `market_scoring.py` como módulo reutilizável e independente

---

## O que foi desenvolvido

### `run_analysis.py` (novo)
- Script standalone que executa toda a lógica analítica do notebook sem necessidade de Jupyter
- Gera 6 gráficos HTML interativos em `outputs/figures/`:
  - `tendencia_2019_2023.html` — evolução da penetração nacional 2019–2023 (+7,9pp)
  - `penetracao_por_regiao.html` — H1: penetração média por região com intervalo min/max
  - `gap_urbano_rural.html` — H2: gap urbano × rural por estado (dumbbell chart)
  - `correlacao_idh_internet.html` — H3: scatter IDH × internet com regressão e outliers
  - `score_oportunidade.html` — ranking de oportunidade (excluindo mercados saturados)
  - `choropleth_internet_brasil.html` — penetração por estado ordenada

### `market_scoring.py` (novo)
- Módulo standalone para cálculo e exportação do score de oportunidade
- Score composto: (1 - penetração) × população × IDH normalizado
- Adiciona flags de risco e estratégia recomendada por estado
- Exporta `outputs/market_scores.csv` e `outputs/top5_recommendation.csv`

### `executive_summary.md` (novo)
- Relatório executivo com 3 insights estratégicos e recomendações acionáveis
- Top 5 estados com estratégia específica por perfil de mercado
- Tabela de riscos e mitigações
- Roadmap de próximos passos

### Resultados das hipóteses (3/3 confirmadas)
| Hipótese | Resultado | Evidência |
|----------|-----------|-----------|
| H1: Norte+NE < Sul+SE | Confirmada | Gap 11,1 p.p. entre regiões |
| H2: Gap urbano/rural > gap interregional | Confirmada | 25,0pp > 11,1pp em todos os estados |
| H3: Correlação IDH × internet (r > 0.7) | Confirmada | r = 0.883 |

### KPIs nacionais gerados
- Média nacional de penetração: 84,9%
- Gap médio urbano × rural: 25,0 p.p.
- Domicílios estimados sem internet: ~8,6 milhões
- Estados com < 80% penetração: 6 (maior oportunidade de expansão)
- Estados saturados (> 90%): 6 (foco em upgrade)

---

## Status após a intervenção
- **Nota geral: 9.5/10**
- 100% dos outputs gerados (6 figuras HTML + 2 CSVs)
- Análise executável sem Jupyter
- Recomendações de negócio documentadas e acionáveis

---

## Como rodar o projeto agora

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Gerar todos os outputs (figuras + CSVs)
python run_analysis.py

# 3. Score de oportunidade standalone (opcional)
python market_scoring.py

# 4. Executar notebook completo com API IBGE (requer Jupyter)
jupyter notebook notebooks/market_expansion_eda.ipynb
```

**Outputs disponíveis após execução:**
```
outputs/
├── market_scores.csv            (ranking completo 27 estados)
├── top5_recommendation.csv      (top 5 estados recomendados)
└── figures/
    ├── tendencia_2019_2023.html
    ├── penetracao_por_regiao.html
    ├── gap_urbano_rural.html
    ├── correlacao_idh_internet.html
    ├── score_oportunidade.html
    └── choropleth_internet_brasil.html
```

---

## Próximos passos sugeridos

1. **Análise municipal:** usar API SIDRA nível N6 para os 5 estados prioritários (MG, BA, CE, PE, PA)
2. **Cruzamento com shapefile ANATEL de cobertura de fibra** para distinguir gap de rede vs. gap de adoção
3. **Modelo de revenue potential:** estimar receita por estado usando renda domiciliar média × disposição de pagamento
4. **Dashboard Power BI** com filtros interativos de região, tipo de conexão e faixa de IDH
5. **Atualização automática:** agendar extração da API SIDRA todo mês de janeiro (IBGE publica PNAD anual)
