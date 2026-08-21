"""
run_analysis.py
Executa toda a análise do notebook market_expansion_eda.ipynb de forma standalone
e exporta todos os gráficos como HTML interativos em outputs/figures/.

Uso:
    python run_analysis.py

Saídas:
    outputs/figures/choropleth_internet_brasil.html
    outputs/figures/penetracao_por_regiao.html
    outputs/figures/taxa_x_volume.html
    outputs/figures/correlacao_idh_internet.html
    outputs/figures/score_oportunidade.html
    outputs/figures/tendencia_nacional.html
    outputs/market_scores.csv
    outputs/top5_recommendation.csv
"""

import json
import warnings
from pathlib import Path

import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import SEQ, finish, save  # noqa: E402
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

# ── Dado observado, direto da API do IBGE ────────────────────────────────────
# Antes havia aqui um dicionário PCT_TOTAL com 27 percentuais escritos à mão sob
# o comentário "(IBGE PNAD Contínua 2023)". Eles não vinham do PNAD: o Brasil
# saía em 87,0% quando o IBGE publicou 92,5%, e o erro era MAIOR nos estados
# pobres (Maranhão 13,0pp abaixo do real; São Paulo, 1,5). Como este projeto
# entrega um RANKING de prioridade de expansão, um erro correlacionado com a
# renda do estado não é ruído — é viés na única saída que importa.
#
# `sidra.py` documenta as tabelas e o método. Sem API e sem cache, ele levanta
# SidraIndisponivel e este script para: melhor não rodar do que rodar inventando.
from sidra import carregar as _carregar_sidra   # noqa: E402

ANO_REF = 2023


def _dados_ibge(ano: int = ANO_REF) -> dict:
    """{sigla_uf: {"pct": float, "dom_sem_k": int, "dom_total_k": int}}"""
    por_codigo = {
        l["codigo_ibge"]: l
        for l in _carregar_sidra()
        if l["nivel"] == "N3" and l["situacao"] == "Total" and l["ano"] == ano
    }
    out = {}
    for codigo, (sigla, _nome) in UF_REF.items():
        linha = por_codigo.get(codigo)
        if not linha:
            continue
        out[sigla] = {
            "pct":         linha["pct"],
            "dom_total_k": int(round(linha["total"])),
            # Domicílios sem internet OBSERVADOS (total - com internet). Antes
            # eram estimados como `populacao / 3,1 moradores` — uma média
            # nacional aplicada a 27 estados que têm tamanhos de domicílio
            # diferentes, e justamente no Norte/Nordeste, onde o domicílio é
            # maior, a conta subestimava o número de casas.
            "dom_sem_k":   int(round(linha["total"] - linha["com_internet"])),
        }
    if len(out) != 27:
        raise RuntimeError(f"esperava 27 UFs do SIDRA, vieram {len(out)}")
    return out


IBGE = _dados_ibge()
PCT_TOTAL = {sigla: v["pct"] for sigla, v in IBGE.items()}

# IDH estadual — PNUD/Atlas do Desenvolvimento Humano, Censo 2010.
# Continua embutido, e de propósito: é um valor CENSITÁRIO, publicado uma vez a
# cada dez anos. Não existe série anual para buscar, e uma constante que não muda
# é honesta enquanto a fonte e o ano estiverem declarados — o problema do
# PCT_TOTAL antigo nunca foi ser constante, foi ser um número que não batia com
# a fonte que ele citava.
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

# ── Tendência nacional, observada ────────────────────────────────────────────
# Aqui existia um dicionário escrito à mão:
#   {2019: 79.1, 2020: 82.7, 2021: 85.0, 2022: 86.8, 2023: 87.0}
# Os 87,0% de 2023 são EXATAMENTE o número que o comentário sessenta linhas acima
# identifica como inventado — a limpeza tirou o PCT_TOTAL fabricado e deixou a
# série fabricada no lugar, plotada sob o título "IBGE PNAD Contínua". Pior: ela
# tinha um ponto em 2020, ano em que a PNAD não coletou o módulo de TIC. O gráfico
# mostrava um dado que não foi coletado.
#
# Agora sai da mesma fonte do resto do script: N1 (Brasil), situação Total.
def _tendencia_nacional() -> dict[int, float]:
    return {
        l["ano"]: round(l["pct"], 1)
        for l in _carregar_sidra()
        if l["nivel"] == "N1" and l["situacao"] == "Total"
    }


TENDENCIA_NACIONAL = _tendencia_nacional()
ANO_INI = min(TENDENCIA_NACIONAL)
ANO_FIM = max(TENDENCIA_NACIONAL)

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
        "idh":       [IDH[u] for u in ufs],
        "pop_mil":   [POP_MIL[u] for u in ufs],
    })
    df["dom_sem_k"]   = [IBGE[u]["dom_sem_k"] for u in ufs]
    df["dom_total_k"] = [IBGE[u]["dom_total_k"] for u in ufs]
    # Os dois criterios de prioridade, lado a lado: 1 = pior taxa de acesso;
    # 1 = maior numero absoluto de domicilios sem internet.
    df["rank_taxa"]   = df["pct_total"].rank(method="min").astype(int)
    df["rank_volume"] = df["dom_sem_k"].rank(method="min", ascending=False).astype(int)
    df["dist_rank"]   = (df["rank_taxa"] - df["rank_volume"]).abs()
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
# 1. Tendência nacional observada
# --------------------------------------------------------------------------

trend = pd.DataFrame(sorted(TENDENCIA_NACIONAL.items()), columns=["ano", "pct_media"])

# 2020 entra como linha com valor nulo: o plotly quebra a linha no buraco em vez
# de ligar 2019 a 2021 numa reta que sugere uma medição que nunca houve.
if 2020 not in TENDENCIA_NACIONAL and ANO_INI < 2020 < ANO_FIM:
    trend = pd.concat(
        [trend, pd.DataFrame([{"ano": 2020, "pct_media": None}])]
    ).sort_values("ano").reset_index(drop=True)

fig = px.line(trend, x="ano", y="pct_media", markers=True,
              labels={"ano": "Ano", "pct_media": "% Domicílios com Internet"})
fig.update_traces(
    line_color="#2563EB", marker_size=8, marker_color="#2563EB",
    text=[("" if pd.isna(v) else f"{v:.1f}%".replace(".", ",")) for v in trend["pct_media"]],
    textposition="top center", mode="lines+markers+text",
    connectgaps=False,
)

avanco = TENDENCIA_NACIONAL[ANO_FIM] - TENDENCIA_NACIONAL[ANO_INI]
fig.add_annotation(
    x=ANO_FIM, y=TENDENCIA_NACIONAL[ANO_FIM],
    text=f"+{avanco:.1f}pp em {ANO_FIM - ANO_INI} anos".replace(".", ","),
    showarrow=True, arrowhead=2, ax=-60, ay=-30, font=dict(size=11, color="#2563EB"),
)
fig.add_annotation(
    x=2020, y=TENDENCIA_NACIONAL.get(2019, 0), yshift=-34,
    text="2020: a PNAD não coletou<br>o módulo de TIC",
    showarrow=False, font=dict(size=10, color="#94A3B8"), align="center",
)
fig.update_layout(yaxis=dict(range=[65, 100]),
                  xaxis=dict(dtick=1, tickmode="linear"))
finish(fig, "Penetração de internet no Brasil",
       f"domicílios com acesso, {ANO_INI}–{ANO_FIM} · IBGE PNAD Contínua · "
       "razão entre as tabelas SIDRA 9649/7311 e 7167", height=420)
save(fig, OUTPUTS, "tendencia_nacional")
print("  OK tendencia_nacional.html")

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

# Ponderado por DOMICILIOS, nao media de medias estaduais. A media simples de
# 27 percentuais da a Roraima (270 mil domicilios) o mesmo peso que a Sao Paulo
# (17 milhoes), e a pergunta de negocio aqui e "que fracao dos domicilios da
# regiao tem acesso" — nao "quanto marca o estado tipico".
# As duas contas davam 3,5pp e 4,6pp: o notebook usava uma e o script a outra.
_nne = df[df["regiao"].isin(["Norte", "Nordeste"])]
_sse = df[df["regiao"].isin(["Sul", "Sudeste"])]
gap_norte_sul = (
    (_sse["dom_total_k"] - _sse["dom_sem_k"]).sum() / _sse["dom_total_k"].sum() -
    (_nne["dom_total_k"] - _nne["dom_sem_k"]).sum() / _nne["dom_total_k"].sum()
) * 100
h1_ok = gap_norte_sul > 5
print(f"  H1: gap Norte+NE vs Sul+SE = {gap_norte_sul:.1f}pp ({'CONFIRMADA' if h1_ok else 'REFUTADA'})")

fig = px.bar(
    reg, x="regiao", y="media_pct",
    error_y=reg["max_pct"] - reg["media_pct"],
    error_y_minus=reg["media_pct"] - reg["min_pct"],
    color="regiao", color_discrete_map=COR_REG,
    text=reg["media_pct"].round(1).astype(str) + "%",
    labels={"media_pct": "Penetração média (%)", "regiao": "Região"},
)
fig.update_traces(textposition="outside")
fig.update_layout(coloraxis_showscale=False, showlegend=False,
                  yaxis=dict(range=[60, 102]))
fig.add_annotation(
    x=0.5, y=1.08, xref="paper", yref="paper",
    text=f"Gap Norte+NE vs Sul+SE: {gap_norte_sul:.1f} p.p.",
    showarrow=False, font=dict(size=12, color="#E74C3C"),
)
finish(fig, "H1 · Penetração média por região",
       f"barra de erro = mínimo e máximo estadual · gap Norte+NE contra Sul+SE: {gap_norte_sul:.1f}pp",
       height=470)
save(fig, OUTPUTS, "penetracao_por_regiao")
print("  OK penetracao_por_regiao.html")

# --------------------------------------------------------------------------
# 3. Taxa x volume: os dois rankings discordam (H2)
# --------------------------------------------------------------------------

# A hipotese antiga comparava um gap urbano x rural construido por deslocamento
# fixo — nao podia ser refutada. Esta pode: se os dois criterios apontassem para
# os mesmos estados, a correlacao de postos seria alta e a pergunta nao existiria.
rho = df["rank_taxa"].corr(df["rank_volume"], method="spearman")
top5_taxa   = set(df.nsmallest(5, "pct_total")["sigla"])
top5_volume = set(df.nlargest(5, "dom_sem_k")["sigla"])
coincidem   = len(top5_taxa & top5_volume)
h2_ok = rho < 0.5
print(f"  H2: rho de Spearman = {rho:.2f} | {coincidem} de 5 estados coincidem "
      f"({'CONFIRMADA' if h2_ok else 'REFUTADA'})")

df_rk = df.sort_values("dom_sem_k", ascending=False)
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_rk["pct_total"], y=df_rk["dom_sem_k"],
    mode="markers+text", text=df_rk["sigla"], textposition="top center",
    marker=dict(size=df_rk["pop_mil"] / 3000 + 7,
                color=[COR_REG[r] for r in df_rk["regiao"]], opacity=0.85),
    showlegend=False,
    hovertemplate=("<b>%{text}</b><br>Penetração: %{x:.1f}%<br>"
                   "Domicílios sem internet: %{y:.0f} mil<extra></extra>"),
))
fig.add_vline(x=df["pct_total"].mean(), line_dash="dot", line_color="#94A3B8",
              annotation_text="média nacional", annotation_position="bottom left")
fig.update_layout(
    xaxis_title="% de domicílios com internet",
    yaxis_title="domicílios sem internet (mil)",
)
finish(fig, "H2 · Taxa de acesso × volume desconectado",
       f"ρ de Spearman entre os dois rankings: {rho:.2f} · "
       f"apenas {coincidem} dos 5 piores em taxa estão entre os 5 maiores em volume",
       height=560)
save(fig, OUTPUTS, "taxa_x_volume", png=True)
print("  OK taxa_x_volume.html")

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
    xaxis_title="IDH estadual (PNUD 2021)",
    yaxis_title="% de domicílios com internet",
)
finish(fig, f"H3 · IDH × penetração de internet — r = {corr:.2f}",
       "cada ponto é um estado · tamanho proporcional à população · "
       "estrela = mais de 1,5 desvio fora da reta",
       height=580)
save(fig, OUTPUTS, "correlacao_idh_internet", png=True)
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
    labels={"score_100": "Score (0-100)", "sigla": "Estado", "regiao": "Região"},
)
fig.update_traces(textposition="inside")
fig.update_layout(yaxis={"categoryorder": "total ascending"})
finish(fig, "Score de oportunidade de expansão",
       "excluindo estados com penetração acima de 90% · o rótulo traz o mercado endereçável",
       height=540)
save(fig, OUTPUTS, "score_oportunidade", png=True)
print("  OK score_oportunidade.html")

# --------------------------------------------------------------------------
# 6. Mapa coroplético (sem GeoJSON local — barra alternativa agrupada)
# --------------------------------------------------------------------------

df_map = df.sort_values("pct_total")
fig = px.bar(
    df_map, x="pct_total", y="sigla", orientation="h",
    color="regiao", color_discrete_map=COR_REG,
    text=df_map["pct_total"].round(1).astype(str) + "%",
    labels={"pct_total": "% com internet", "sigla": "UF", "regiao": "Região"},
)
fig.update_traces(textposition="outside")
fig.add_vline(x=df["pct_total"].mean(), line_dash="dash", line_color="grey",
              annotation_text=f"Media: {df['pct_total'].mean():.1f}%",
              annotation_position="top right")
finish(fig, "Acesso à internet por estado — Brasil, 2023",
       "cor por região · linha tracejada na média nacional", height=780)
save(fig, OUTPUTS, "choropleth_internet_brasil")

# ---------------------------------------------------------------------------
# Gap urbano x rural por regiao — o achado central
# ---------------------------------------------------------------------------
# Dumbbell e nao barra empilhada: o que interessa aqui e a DISTANCIA entre dois
# pontos, e barra empilhada some com ela. Ordenado pelo gap, nao pelo alfabeto.

_sit = [l for l in _carregar_sidra()
        if l["ano"] == ANO_REF and l["nivel"] in ("N1", "N2")]
_REG = {("N1", "1"): "Brasil", ("N2", "1"): "Norte", ("N2", "2"): "Nordeste",
        ("N2", "3"): "Sudeste", ("N2", "4"): "Sul", ("N2", "5"): "Centro-Oeste"}
_por_local = {}
for l in _sit:
    nome = _REG.get((l["nivel"], l["codigo_ibge"]))
    if nome:
        _por_local.setdefault(nome, {})[l["situacao"]] = l["pct"]

gap_rows = sorted(
    [(n, v["Urbana"], v["Rural"], v["Urbana"] - v["Rural"])
     for n, v in _por_local.items() if "Urbana" in v and "Rural" in v],
    key=lambda r: r[3])

fig = go.Figure()
for nome, urb, rur, gap in gap_rows:
    destaque = nome in ("Norte", "Brasil")
    fig.add_trace(go.Scatter(
        x=[rur, urb], y=[nome, nome], mode="lines",
        line=dict(color="#c94f2e" if nome == "Norte" else "#b8b0a4",
                  width=6 if destaque else 4),
        showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=[rur, urb], y=[nome, nome], mode="markers+text",
        marker=dict(size=[13, 13], color=["#c94f2e", "#2e6f7d"]),
        text=[f"{rur:.1f}%", f"{urb:.1f}%"],
        textposition=["middle left", "middle right"],
        textfont=dict(size=11), showlegend=False,
        hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>"))
    fig.add_annotation(x=(urb + rur) / 2, y=nome, text=f"<b>{gap:.1f}pp</b>",
                       showarrow=False, yshift=15, font=dict(size=11))

fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Rural",
                         marker=dict(size=12, color="#c94f2e")))
fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Urbana",
                         marker=dict(size=12, color="#2e6f7d")))

finish(fig,
       "Onde mora a exclusão digital: no campo, não na região",
       f"% de domicílios com internet, {ANO_REF} · IBGE PNAD Contínua "
       f"(tabelas 9649 e 7167) · o rótulo no meio é a distância entre os dois pontos",
       height=400)
fig.update_xaxes(title="% de domicílios com internet", range=[65, 100], ticksuffix="%")
fig.update_layout(showlegend=True)
save(fig, OUTPUTS, "gap_urbano_rural", png=True, width=1400)
print("  OK gap_urbano_rural.html")
print(f"  Gap Brasil: {_por_local['Brasil']['Urbana'] - _por_local['Brasil']['Rural']:.1f}pp"
      f" | Norte: {_por_local['Norte']['Urbana'] - _por_local['Norte']['Rural']:.1f}pp")

print("  OK choropleth_internet_brasil.html")

# --------------------------------------------------------------------------
# Exporta CSVs
# --------------------------------------------------------------------------

df_score[["sigla","nome","regiao","pct_total","idh","pop_mil","dom_sem_k",
          "rank_taxa","rank_volume","dist_rank","score_100"]].to_csv(
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
print(f"  H2: {'CONFIRMADA' if h2_ok else 'REFUTADA':10s} Taxa x volume: rho = {rho:.2f}, {coincidem}/5 coincidem")
print(f"  H3: {'CONFIRMADA' if h3_ok else 'REFUTADA':10s} Correlacao IDH x internet r = {corr:.3f}")

print("\nTop 5 Estados Recomendados para Expansao:")
print(top5[["sigla","nome","regiao","pct_total","dom_sem_k","score_100"]].to_string(index=False))

print(f"\nFiguras salvas em: {OUTPUTS}")
print("Total: 6 graficos HTML interativos")
