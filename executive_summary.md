# Executive Summary — Oportunidades de Expansão para ISPs no Brasil (2023)

**Fonte:** IBGE · PNAD Contínua, tabelas SIDRA 9649, 7311 e 7167, buscadas pela API
| **Metodologia:** EDA + Score de Oportunidade Composto | **Ano de referência:** 2023

---

## Contexto

O Brasil fechou 2023 com **92,6% dos domicílios com internet** — 5,68 milhões de
domicílios ainda sem acesso. A série continua e já cobre 2025, quando chegou a
**95,0%**.

Com a média nacional nesse patamar, a pergunta de expansão deixou de ser "onde
falta internet" e passou a ser **"que tipo de falta"** — e a resposta mudou de
eixo nos últimos anos.

---

## 3 Insights Estratégicos

### 1. A brecha regional acabou; a rural, não

O gap entre Norte+Nordeste e Sul+Sudeste é de **3,5 pontos percentuais**. É
pequeno demais para orientar investimento — e derruba a hipótese de trabalho com
que esta análise começou.

O gap que sobrou é entre cidade e campo: **13,0pp no Brasil**, e muito maior em
algumas regiões.

| Região | Urbana | Rural | Gap |
|---|---:|---:|---:|
| **Norte** | **95,2%** | **70,4%** | **24,8pp** |
| Nordeste | 91,8% | 80,1% | 11,7pp |
| Sudeste | 94,8% | 83,8% | 11,0pp |
| Sul | 94,4% | 87,2% | 7,2pp |
| Centro-Oeste | 96,0% | 89,0% | 7,0pp |

> **Implicação:** o Norte urbano tem 95,2% de acesso — **acima da média nacional**.
> Um ISP que entra no Norte mirando cidade está entrando num mercado já atendido,
> para disputar cliente de concorrente. A oportunidade de cobertura ali é rural, e
> rural é outro custo por assinante, outro prazo de retorno e outra tecnologia de
> última milha. Tratar "Norte" como praça única leva à decisão errada nos dois
> sentidos.

### 2. Taxa e volume apontam para estados diferentes

A correlação de postos entre "pior taxa de acesso" e "maior número de domicílios
sem internet" é de **ρ = 0,24**. Dos cinco estados com pior penetração, apenas
**um** está entre os cinco com maior volume desconectado.

O caso extremo é São Paulo: **a melhor taxa do país (95,0%) e o maior número
absoluto de domicílios desconectados (852 mil)** — mais que Bahia e Pernambuco
somados em percentual de prioridade.

> **Implicação:** quem prioriza pelo percentual vai para o Acre (84,4%, 43 mil
> domicílios); quem prioriza por mercado endereçável vai para São Paulo. O score
> de oportunidade existe para combinar os dois critérios de forma declarada, em
> vez de escolher um em silêncio.

### 3. IDH explica 59% da variação de penetração (r = 0,769)

Há correlação positiva forte entre IDH e penetração, embora mais fraca do que
parecia antes — porque o acesso subiu em toda parte e comprimiu a variação entre
estados. Os estados abaixo da reta são a leitura útil: acesso menor do que a
renda da população suportaria costuma indicar **falta de oferta, não de demanda**.

### 3. O crescimento nacional desacelerou

Entre 2016 e 2025 o Brasil foi de **70,8% para 95,0%**, mas o ganho anual caiu de
**+5,5pp (2017)** para **+1,3pp (2025)**. A curva está achatando contra o teto.

| 2016 | 2017 | 2018 | 2019 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 70,8% | 76,3% | 80,5% | 83,9% | 90,0% | 91,6% | 92,6% | 93,7% | 95,0% |

*2020 não aparece: a PNAD Contínua não coletou o módulo de TIC naquele ano.*

A fase de expansão orgânica acabou. O que resta é caro por definição — é o
domicílio que o mercado deixou por último, e ele é majoritariamente rural.

> A série 2019–2023 é **nacional**, não por estado. Ela dá ordem de grandeza da
> desaceleração e não autoriza comparar velocidade de adoção entre unidades da federação.

---

## Top 5 Estados Recomendados para Expansão

| Rank | UF | Região | Penetração | Domicílios sem internet | IDH | Estratégia |
|------|-----|--------|-----------|------------------------|-----|-----------|
| 1 | **MG** | Sudeste | 88,7% | ~781k | 0.731 | Fibra FTTH urbana — alta densidade, IDH elevado |
| 2 | **BA** | Nordeste | 80,3% | ~949k | 0.660 | Fibra FTTC + parceria governo (FUST/EUA) |
| 3 | **CE** | Nordeste | 78,9% | ~629k | 0.682 | Satélite/radiofrequência + FTTH Fortaleza |
| 4 | **PE** | Nordeste | 82,4% | ~549k | 0.673 | FTTH em Recife/Caruaru + expansão no interior |
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
| Tempo de retorno elevado fora dos centros urbanos | Todos | Subsidiar com cross-selling (TV, telefonia, IoT agronegócio) |

---

## Próximos Passos

0. **Recorte por situação do domicílio:** trazer o dado real de urbano × rural da PNAD. O recorte
   foi removido desta análise porque a versão anterior o construía com desvio fixo sobre o total
   (+5pp urbano, −20pp rural), gerando um gap de exatamente 25,0 pontos em todos os 27 estados —
   um número que parecia análise e não era. Com o dado observado, a pergunta volta.
1. **Análise municipal:** descer ao nível de município via API SIDRA (N6) para os 5 estados prioritários
2. **Mapa de cobertura ANATEL:** cruzar com shapefile de cobertura de fibra para identificar gaps de rede vs. gaps de adoção
3. **Modelo de churn e ARPU:** estimar receita potencial por estado usando PNAD — renda média + disposição de pagamento por internet
4. **Dashboard Power BI:** integrar os scores em painel executivo com filtros interativos por região e tipo de conexão

---

*Análise desenvolvida por Hugo Leonardo | Analista de Dados Pleno — Speed Fibra*
*Dados: IBGE PNAD Contínua 2023 (Creative Commons 4.0) | IDH: PNUD Brasil 2021*
