# Executive Summary — Oportunidades de Expansão para ISPs no Brasil (2023)

**Fonte:** IBGE PNAD Contínua 2023 | **Metodologia:** EDA + Score de Oportunidade Composto

---

## Contexto

Com **84,9% de penetração nacional de internet**, o Brasil ainda conta com ~8,6 milhões de domicílios
sem acesso. A distribuição desse déficit é profundamente desigual — definindo onde um ISP deve investir
em infraestrutura para maximizar ROI e crescimento de base.

---

## 3 Insights Estratégicos

### 1. O gap urbano × rural é o maior desafio — não o gap regional

O gap médio entre domicílios **urbanos e rurais** dentro de cada estado é de **25 p.p.**,
mais do que o dobro do gap entre regiões (Norte+Nordeste vs Sul+Sudeste = 11 p.p.).

> Implicação: a estratégia de expansão mais impactante não é "ir para o Nordeste" — é
> resolver a conectividade rural dentro de cada estado, inclusive nos mais desenvolvidos.

### 2. IDH explica 78% da variação de penetração (r = 0.883)

Há forte correlação positiva entre IDH e penetração. Dois outliers notáveis:
- **DF (acima da curva):** penetração de ~95% para IDH 0.824 — mercado saturado
- **PA, MA (abaixo da curva):** penetração abaixo do esperado para o IDH — indicando
  falha de oferta, não de demanda. Alto potencial para ativação.

### 3. O crescimento nacional desacelerou

Entre 2019–2023 o Brasil cresceu **+7,9 p.p.** (de 79,1% para 87,0%), mas o incremento
anual caiu de ~2 p.p. para ~0,2 p.p. A fase de expansão orgânica chegou ao limite;
crescimento futuro exige investimento ativo em infraestrutura, especialmente rural.

---

## Top 5 Estados Recomendados para Expansão

| Rank | UF | Região | Penetração | Domicílios sem internet | IDH | Estratégia |
|------|-----|--------|-----------|------------------------|-----|-----------|
| 1 | **MG** | Sudeste | 88,7% | ~781k | 0.731 | Fibra FTTH urbana — alta densidade, IDH elevado |
| 2 | **BA** | Nordeste | 80,3% | ~949k | 0.660 | Fibra FTTC + parceria governo (FUST/EUA) |
| 3 | **CE** | Nordeste | 78,9% | ~629k | 0.682 | Satélite/radiofrequência rural + FTTH Fortaleza |
| 4 | **PE** | Nordeste | 82,4% | ~549k | 0.673 | FTTH em Recife/Caruaru + expansão rural |
| 5 | **PA** | Norte | 77,8% | ~616k | 0.646 | Satélite LEO (Starlink/concorrentes) + fibra Belém |

**Nota sobre SP/RJ:** São Paulo e Rio de Janeiro têm o maior volume absoluto de domicílios
sem internet por causa da população, mas com penetração acima de 91% o crescimento incremental
é limitado ao mercado de upgrade (fibra premium, velocidades maiores).

---

## Riscos e Considerações

| Risco | Estados afetados | Mitigação |
|-------|-----------------|-----------|
| Capacidade de pagamento baixa (IDH < 0.65) | AL, MA, PI, PA | Parceria com programas governo (Plano Nacional Banda Larga, FUST) |
| Infraestrutura de backbone inexistente | AM, RR, AP | Satélite LEO como primeira milha; backbone via financiamento federal |
| Concorrência intensa em mercados maduros | SP, SC, DF | Diferenciação por velocidade/SLA, não por cobertura |
| Tempo de retorno elevado em zonas rurais | Todos | Subsidiar com cross-selling (TV, telefonia, IoT agronegócio) |

---

## Próximos Passos

1. **Análise municipal:** descer ao nível de município via API SIDRA (N6) para os 5 estados prioritários
2. **Mapa de cobertura ANATEL:** cruzar com shapefile de cobertura de fibra para identificar gaps de rede vs. gaps de adoção
3. **Modelo de churn e ARPU:** estimar receita potencial por estado usando PNAD — renda média + disposição de pagamento por internet
4. **Dashboard Power BI:** integrar os scores em painel executivo com filtros interativos por região e tipo de conexão

---

*Análise desenvolvida por Hugo Leonardo | Analista de Dados Pleno — Speed Fibra*
*Dados: IBGE PNAD Contínua 2023 (Creative Commons 4.0) | IDH: PNUD Brasil 2021*
