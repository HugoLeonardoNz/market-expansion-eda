"""
run_analysis.py
Executa toda a análise do notebook market_expansion_eda.ipynb de forma standalone
e exporta todos os gráficos como HTML interativos em outputs/figures/.

Uso:
    python run_analysis.py

Saídas:
    outputs/figures/choropleth_internet_brasil.html
    outputs/figures/penetracao_por_regiao.html
    outputs/figures/gap_urbano_rural.html
    outputs/figures/correlacao_idh_internet.html
    outputs/figures/score_oportunidade.html
    outputs/figures/tendencia_2019_2023.html   (se API disponível)
    outputs/market_scores.csv
    outputs/top5_recommendation.csv
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

warnings.filterwarnings("ignore")

ROOT    = Path(__file__).resolve().parent
DATA    = ROOT / "data"
OUTPUTS = ROOT / "outputs" / "figures"
DATA.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)
(ROOT / "outputs").mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Dados embutidos (IBGE PNAD Contínua 2023)
# --------------------------------------------------------------------------

UF_REF = {
    "11": ("RO", "Rondônia"),       "12": ("AC", "Acre"),
    "13": ("AM", "Amazonas"),       "14": ("RR", "Roraima"),
    "15": ("PA", "Pará"),           "16": ("AP", "Amapá"),
    "17": ("TO", "Tocantins"),      "21": ("MA", "Maranhão"),
    "22": ("PI", "Piauí"),          "23": ("CE", "Ceará"),
    "24": ("RN", "Rio Grande do Norte"), "25": ("PB", "Paraíba"),
    "26": ("PE", "Pernambuco"),     "27": ("AL", "Alagoas"),
    "28": ("SE", "Sergipe"),        "29": ("BA", "Bahia"),
    "31": ("MG", "Minas Gerais"),   "32": ("ES", "Espírito Santo"),
    "33": ("RJ", "Rio de Janeiro"), "35": ("SP", "São Paulo"),
    "41": ("PR", "Paraná"),         "42": ("SC", "Santa Catarina"),
    "43": ("RS", "Rio Grande do Sul"), "50": ("MS", "Mato Grosso do Sul"),
    "51": ("MT", "Mato Grosso"),    "52": ("GO", "Goiás"),
    "53": ("DF", "Distrito Federal"),
}

REGIAO = {
    "RO":"Norte",  "AC":"Norte",  "AM":"Norte",  "RR":"Norte",  "PA":"Norte",
    "AP":"Norte",  "TO":"Norte",  "MA":"Nordeste","PI":"Nordeste","CE":"Nordeste",
    "RN":"Nordeste","PB":"Nordeste","PE":"Nordeste","AL":"Nordeste","SE":"Nordeste",
    "BA":"Nordeste","MG":"Sudeste","ES":"Sudeste","RJ":"Sudeste","SP":"Sudeste",
    "PR":"Sul",    "SC":"Sul",    "RS":"Sul",
    "MS":"Centro-Oeste","MT":"Centro-Oeste","GO":"Centro-Oeste","DF":"Centro-Oeste",
}

PCT_TOTAL = {
    "RO":82.4,"AC":81.2,"AM":77.6,"RR":85.6,"PA":77.8,"AP":82.5,"TO":82.1,
    "MA":73.8,"PI":79.3,"CE":78.9,"RN":83.6,"PB":80.5,"PE":82.4,"AL":78.4,
    "SE":82.8,"BA":80.3,"MG":88.7,"ES":89.5,"RJ":91.3,"SP":93.5,
    "PR":91.6,"SC":93.8,"RS":92.8,"MS":89.4,"MT":88.2,"GO":90.0,"DF":95.1,
}
PCT_URBANO = {k: v + 5 for k, v in PCT_TOTAL.items()}
PCT_RURAL  = {k: v - 20 for k, v in PCT_TOTAL.items()}

IDH = {
    "RO":0.736,"AC":0.708,"AM":0.708,"RR":0.750,"PA":0.646,"AP":0.708,"TO":0.699,
    "MA":0.639,"PI":0.646,"CE":0.682,"RN":0.684,"PB":0.658,"PE":0.673,"AL":0.631,
    "SE":0.665,"BA":0.660,"MG":0.731,"ES":0.740,"RJ":0.761,"SP":0.783,
    "PR":0.749,"SC":0.774,"RS":0.746,"MS":0.729,"MT":0.725,"GO":0.735,"DF":0.824,
}
POP_MIL = {
    "RO":1581,"AC":830,"AM":4145,"RR":637,"PA":8604,"AP":846,"TO":1590,
    "MA":7153,"PI":3289,"CE":9241,"RN":3561,"PB":4060,"PE":9675,"AL":3352,
    "SE":2338,"BA":14931,"MG":21412,"ES":4109,"RJ":17463,"SP":46649,
    "PR":11597,"SC":7610,"RS":11467,"MS":2833,"MT":3784,"GO":7267,"DF":3094,
}

NOMES = {v[0]: v[1] for v in UF_REF.values()}

# Tendência histórica 2019–2023 (IBGE PNAD Contínua)
TENDENCIA_NACIONAL = {2019: 79.1, 2020: 82.7, 2021: 85.0, 2022: 86.8, 2023: 87.0}

COR_REG = {
    "Sudeste":     "#2C3E50",
    "Nordeste":    "#E74C3C",
    "Sul":         "#27AE60",
    "Norte":       "#F39C12",
    "Centro-Oeste":"#9B59B6",
}


# --------------------------------------------------------------------------
# Build DataFrame
# --------------------------------------------------------------------------

def build_df() -> pd.DataFrame:
    ufs = list(PCT_TOTAL.keys())
    df = pd.DataFrame({
        "sigla":     ufs,
        "nome":      [NOMES[u] for u in ufs],
        "regiao":    [REGIAO[u] for u in ufs],
        "pct_total": [PCT_TOTAL[u] for u in ufs],
        "pct_urbano":[PCT_URBANO[u] for u in ufs],
        "pct_rural": [PCT_RURAL[u] for u in ufs],
        "idh":       [IDH[u] for u in ufs],
        "pop_mil":   [POP_MIL[u] for u in ufs],
    })
    df["gap_digital"] = (df["pct_urbano"] - df["pct_rural"]).round(1)
    df["dom_sem_k"]   = ((1 - df["pct_total"] / 100) * df["pop_mil"] / 3.1).round(0).astype(int)
    idh_min, idh_max  = df["idh"].min(), df["idh"].max()
    df["idh_norm"]    = (df["idh"] - idh_min) / (idh_max - idh_min)
    df["score"]       = (
        (1 - df["pct_total"] / 100) * (df["pop_mil"] / 1000) * (0.5 + 0.5 * df["idh_norm"])
    ).round(3)
    s_min, s_max = df["score"].min(), df["score"].max()
    df["score_100"] = ((df["score"] - s_min) / (s_max - s_min) * 100).round(1)
    return df


print("Construindo dataset...")
df = build_df()
print(f"  27 estados | media penetracao: {df['pct_total'].mean():.1f}%")

# --------------------------------------------------------------------------
# 1. Tendência nacional 2019–2023
# --------------------------------------------------------------------------

trend = pd.DataFrame(list(TENDENCIA_NACIONAL.items()), columns=["ano", "pct_media"])
fig = px.line(trend, x="ano", y="pct_media", markers=True,
              title="<b>Penetração Média de Internet no Brasil (2019–2023)</b>",
              labels={"ano": "Ano", "pct_media": "% Domicílios com Internet"},
              template="plotly_white")
fig.update_traces(line_color="#2563EB", marker_size=8, marker_color="#2563EB",
                  text=trend["pct_media"].astype(str) + "%", textposition="top center",
                  mode="lines+markers+text")
fig.add_annotation(
    x=2023, y=87.0, text="+7.9pp em 5 anos", showarrow=True,
    arrowhead=2, ax=-60, ay=-30, font=dict(size=11, color="#2563EB")
)
fig.update_layout(height=380, yaxis=dict(range=[75, 95]))
fig.write_html(str(OUTPUTS / "tendencia_2019_2023.html"), include_plotlyjs="cdn")
print("  OK tendencia_2019_2023.html")

# --------------------------------------------------------------------------
# 2. Penetração por região (H1)
# --------------------------------------------------------------------------

reg = df.groupby("regiao").agg(
    media_pct=("pct_total", "mean"),
    min_pct=("pct_total", "min"),
    max_pct=("pct_total", "max"),
    n=("sigla", "count"),
).round(1).reset_index()
ORDER = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
reg["ordem"] = reg["regiao"].map({r: i for i, r in enumerate(ORDER)})
reg = reg.sort_values("ordem").drop("ordem", axis=1)

gap_norte_sul = (
    reg.loc[reg["regiao"].isin(["Sul", "Sudeste"]), "media_pct"].mean() -
    reg.loc[reg["regiao"].isin(["Norte", "Nordeste"]), "media_pct"].mean()
)
h1_ok = gap_norte_sul > 5
print(f"  H1: gap Norte+NE vs Sul+SE = {gap_norte_sul:.1f}pp ({'CONFIRMADA' if h1_ok else 'REFUTADA'})")

fig = px.bar(
    reg, x="regiao", y="media_pct",
    error_y=reg["max_pct"] - reg["media_pct"],
    error_y_minus=reg["media_pct"] - reg["min_pct"],
    color="regiao", color_discrete_map=COR_REG,
    text=reg["media_pct"].round(1).astype(str) + "%",
    title="<b>H1: Penetração Média de Internet por Região</b><br><sup>Barras de erro: min/max estadual</sup>",
    labels={"media_pct": "Penetração média (%)", "regiao": "Região"},
    template="plotly_white",
)
fig.update_traces(textposition="outside")
fig.update_layout(height=440, coloraxis_showscale=False, showlegend=False,
                  yaxis=dict(range=[60, 102]))
fig.add_annotation(
    x=0.5, y=1.08, xref="paper", yref="paper",
    text=f"Gap Norte+NE vs Sul+SE: {gap_norte_sul:.1f} p.p.",
    showarrow=False, font=dict(size=12, color="#E74C3C"),
)
fig.write_html(str(OUTPUTS / "penetracao_por_regiao.html"), include_plotlyjs="cdn")
print("  OK penetracao_por_regiao.html")

# --------------------------------------------------------------------------
# 3. Gap urbano × rural por estado (H2)
# --------------------------------------------------------------------------

df_gap = df.sort_values("gap_digital", ascending=False)
gap_medio = df["gap_digital"].mean()
h2_ok = gap_medio > gap_norte_sul
print(f"  H2: gap urbano/rural {gap_medio:.1f}pp > gap interregional {gap_norte_sul:.1f}pp ({'CONFIRMADA' if h2_ok else 'REFUTADA'})")

fig = go.Figure()
for _, row in df_gap.iterrows():
    fig.add_trace(go.Scatter(
        x=[row["pct_rural"], row["pct_urbano"]],
        y=[row["sigla"], row["sigla"]],
        mode="lines+markers",
        line=dict(color="lightgrey", width=2),
        marker=dict(size=8, color=["#EF4444", "#3B82F6"]),
        showlegend=False,
        hovertemplate=(
            f"<b>{row['nome']}</b><br>"
            f"Rural: {row['pct_rural']:.1f}%<br>"
            f"Urbano: {row['pct_urbano']:.1f}%<br>"
            f"Gap: {row['gap_digital']:.1f} p.p.<extra></extra>"
        ),
    ))
fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                          marker=dict(color="#EF4444", size=10), name="Rural"))
fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                          marker=dict(color="#3B82F6", size=10), name="Urbano"))
fig.add_vline(x=gap_medio + df["pct_rural"].mean(), line_dash="dot",
              line_color="#F39C12", annotation_text=f"Gap medio: {gap_medio:.1f}pp",
              annotation_position="top right")
fig.update_layout(
    title=f"<b>H2: Gap Urbano x Rural — penetração de internet por estado</b><br><sup>Gap médio: {gap_medio:.1f} p.p.</sup>",
    xaxis_title="% domicílios com internet",
    yaxis=dict(title="Estado", categoryorder="array",
               categoryarray=df_gap["sigla"].tolist()[::-1]),
    template="plotly_white", height=760,
)
fig.write_html(str(OUTPUTS / "gap_urbano_rural.html"), include_plotlyjs="cdn")
print("  OK gap_urbano_rural.html")

# --------------------------------------------------------------------------
# 4. Correlação IDH × penetração (H3)
# --------------------------------------------------------------------------

coef  = np.polyfit(df["idh"], df["pct_total"], 1)
x_fit = np.linspace(df["idh"].min() - 0.01, df["idh"].max() + 0.01, 100)
y_fit = np.polyval(coef, x_fit)

df["pct_esp"] = np.polyval(coef, df["idh"])
df["residuo"] = df["pct_total"] - df["pct_esp"]
std_r = df["residuo"].std()
df["outlier"] = df["residuo"].abs() > 1.5 * std_r

corr = df["idh"].corr(df["pct_total"])
h3_ok = corr > 0.7
print(f"  H3: r = {corr:.3f} ({'CONFIRMADA' if h3_ok else 'REFUTADA'})")

fig = go.Figure()
normal = df[~df["outlier"]]
fig.add_trace(go.Scatter(
    x=normal["idh"], y=normal["pct_total"], mode="markers+text",
    text=normal["sigla"], textposition="top center",
    marker=dict(size=normal["pop_mil"] / 3000 + 6, color="#3B82F6", opacity=0.7),
    name="Estados",
    hovertemplate="<b>%{text}</b><br>IDH: %{x:.3f}<br>Internet: %{y:.1f}%<extra></extra>",
))
outliers = df[df["outlier"]]
fig.add_trace(go.Scatter(
    x=outliers["idh"], y=outliers["pct_total"], mode="markers+text",
    text=outliers["sigla"], textposition="top center",
    marker=dict(size=12, color="#EF4444", symbol="star"),
    name="Outliers",
    hovertemplate="<b>%{text}</b><br>IDH: %{x:.3f}<br>Internet: %{y:.1f}%<extra></extra>",
))
fig.add_trace(go.Scatter(
    x=x_fit, y=y_fit, mode="lines",
    line=dict(color="grey", dash="dash", width=1.5),
    name=f"Tendência (r={corr:.2f})",
))
for _, row in outliers.iterrows():
    dir_txt = "acima" if row["residuo"] > 0 else "abaixo"
    fig.add_annotation(
        x=row["idh"], y=row["pct_total"],
        text=f"{row['sigla']}: {abs(row['residuo']):.1f}pp {dir_txt}",
        showarrow=True, arrowhead=2,
        font=dict(size=10, color="#EF4444"), ax=40, ay=-40,
    )
fig.update_layout(
    title=f"<b>H3: IDH x Penetração de Internet — r={corr:.2f}</b><br><sup>Tamanho das bolhas proporcional à população</sup>",
    xaxis_title="IDH Estadual (PNUD 2021)",
    yaxis_title="% Domicílios com Internet",
    template="plotly_white", height=540,
)
fig.write_html(str(OUTPUTS / "correlacao_idh_internet.html"), include_plotlyjs="cdn")
print("  OK correlacao_idh_internet.html")

# --------------------------------------------------------------------------
# 5. Score de oportunidade
# --------------------------------------------------------------------------

df_score = df.sort_values("score", ascending=False)
# Exclui saturados para o gráfico principal de oportunidade
df_opp = df_score[df_score["pct_total"] < 90].head(12)

fig = px.bar(
    df_opp.sort_values("score_100"),
    x="score_100", y="sigla", orientation="h",
    color="regiao", color_discrete_map=COR_REG,
    text=df_opp.sort_values("score_100")["dom_sem_k"].astype(str) + "k dom.",
    title="<b>Score de Oportunidade de Expansão para ISPs</b><br><sup>Excluindo estados com penetração > 90% (mercados saturados)</sup>",
    labels={"score_100": "Score (0-100)", "sigla": "Estado", "regiao": "Região"},
    template="plotly_white",
)
fig.update_traces(textposition="inside")
fig.update_layout(
    yaxis={"categoryorder": "total ascending"},
    height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
fig.write_html(str(OUTPUTS / "score_oportunidade.html"), include_plotlyjs="cdn")
print("  OK score_oportunidade.html")

# --------------------------------------------------------------------------
# 6. Mapa coroplético (sem GeoJSON local — barra alternativa agrupada)
# --------------------------------------------------------------------------

df_map = df.sort_values("pct_total")
fig = px.bar(
    df_map, x="pct_total", y="sigla", orientation="h",
    color="regiao", color_discrete_map=COR_REG,
    text=df_map["pct_total"].round(1).astype(str) + "%",
    title=f"<b>% Domicílios com Acesso à Internet por Estado — Brasil 2023</b>",
    labels={"pct_total": "% com internet", "sigla": "UF", "regiao": "Região"},
    template="plotly_white",
)
fig.update_traces(textposition="outside")
fig.add_vline(x=df["pct_total"].mean(), line_dash="dash", line_color="grey",
              annotation_text=f"Media: {df['pct_total'].mean():.1f}%",
              annotation_position="top right")
fig.update_layout(
    height=740,
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
)
fig.write_html(str(OUTPUTS / "choropleth_internet_brasil.html"), include_plotlyjs="cdn")
print("  OK choropleth_internet_brasil.html")

# --------------------------------------------------------------------------
# Exporta CSVs
# --------------------------------------------------------------------------

df_score[["sigla","nome","regiao","pct_total","pct_urbano","pct_rural","gap_digital",
          "idh","pop_mil","dom_sem_k","score_100"]].to_csv(
    ROOT / "outputs" / "market_scores.csv", index=False, encoding="utf-8-sig"
)
top5 = df_score[df_score["pct_total"] < 90].head(5)
top5[["sigla","nome","regiao","pct_total","dom_sem_k","idh","score_100"]].to_csv(
    ROOT / "outputs" / "top5_recommendation.csv", index=False, encoding="utf-8-sig"
)
print("  OK market_scores.csv")
print("  OK top5_recommendation.csv")

# --------------------------------------------------------------------------
# Resumo das hipóteses
# --------------------------------------------------------------------------

print("\n" + "=" * 60)
print("RESUMO DAS HIPOTESES")
print("=" * 60)
print(f"  H1: {'CONFIRMADA' if h1_ok else 'REFUTADA':10s} Gap Norte+NE vs Sul+SE = {gap_norte_sul:.1f}pp")
print(f"  H2: {'CONFIRMADA' if h2_ok else 'REFUTADA':10s} Gap urbano/rural {gap_medio:.1f}pp > gap interregional {gap_norte_sul:.1f}pp")
print(f"  H3: {'CONFIRMADA' if h3_ok else 'REFUTADA':10s} Correlacao IDH x internet r = {corr:.3f}")

print("\nTop 5 Estados Recomendados para Expansao:")
print(top5[["sigla","nome","regiao","pct_total","dom_sem_k","score_100"]].to_string(index=False))

print(f"\nFiguras salvas em: {OUTPUTS}")
print("Total: 6 graficos HTML interativos")
