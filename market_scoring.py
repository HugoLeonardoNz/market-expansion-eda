"""
market_scoring.py
Calcula o score de oportunidade de expansão de mercado para ISPs no Brasil,
usando dados públicos IBGE PNAD Contínua 2023 (embutidos como fallback).

Saída:
    outputs/market_scores.csv    — ranking completo de 27 estados
    outputs/top5_recommendation.csv — top 5 estados recomendados

Uso:
    python market_scoring.py
"""

from pathlib import Path

import pandas as pd

ROOT    = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Dados IBGE PNAD Contínua 2023 — embutidos (fallback da API SIDRA)
# --------------------------------------------------------------------------

# % domicílios com acesso à internet por UF
# Penetração e contagem de domicílios: OBSERVADOS, via API do SIDRA.
#
# Aqui existia a QUARTA cópia da mesma tabela escrita à mão — as outras estavam
# em run_analysis.py, no prepare_data.py do projeto de Power BI e no analises.ts
# do site. Copiadas, já tinham divergido entre si (ES saía 89,5 num arquivo e
# 89,4 noutro) e nenhuma delas batia com o PNAD. Agora há uma fonte só.
from sidra import carregar as _carregar_sidra   # noqa: E402

ANO_REF = 2023

_UF_POR_CODIGO = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
    "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
    "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
    "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
    "51": "MT", "52": "GO", "53": "DF",
}

_IBGE = {
    _UF_POR_CODIGO[l["codigo_ibge"]]: l
    for l in _carregar_sidra()
    if l["nivel"] == "N3" and l["situacao"] == "Total" and l["ano"] == ANO_REF
    and l["codigo_ibge"] in _UF_POR_CODIGO
}
assert len(_IBGE) == 27, f"esperava 27 UFs, vieram {len(_IBGE)}"

PCT_INTERNET_2023 = {uf: l["pct"] for uf, l in _IBGE.items()}
DOM_SEM_INTERNET_K = {uf: int(round(l["total"] - l["com_internet"]))
                      for uf, l in _IBGE.items()}

# Nao ha recorte urbano x rural aqui. Existia, construido como total + 5 e
# total - 20, o que dava um gap de exatamente 25,0 pontos em todos os 27 estados
# — um numero com cara de analise que, por construcao, nao distinguia estado
# nenhum. Ver a nota em run_analysis.py.

# IDH 2021 (PNUD Brasil)
IDH_2021 = {
    "RO": 0.736, "AC": 0.708, "AM": 0.708, "RR": 0.750, "PA": 0.646,
    "AP": 0.708, "TO": 0.699, "MA": 0.639, "PI": 0.646, "CE": 0.682,
    "RN": 0.684, "PB": 0.658, "PE": 0.673, "AL": 0.631, "SE": 0.665,
    "BA": 0.660, "MG": 0.731, "ES": 0.740, "RJ": 0.761, "SP": 0.783,
    "PR": 0.749, "SC": 0.774, "RS": 0.746, "MS": 0.729, "MT": 0.725,
    "GO": 0.735, "DF": 0.824,
}

# População estimada 2023 (IBGE, em milhares)
POP_MIL = {
    "RO": 1581, "AC": 830,  "AM": 4145, "RR": 637,  "PA": 8604,
    "AP": 846,  "TO": 1590, "MA": 7153, "PI": 3289, "CE": 9241,
    "RN": 3561, "PB": 4060, "PE": 9675, "AL": 3352, "SE": 2338,
    "BA": 14931,"MG": 21412,"ES": 4109, "RJ": 17463,"SP": 46649,
    "PR": 11597,"SC": 7610, "RS": 11467,"MS": 2833, "MT": 3784,
    "GO": 7267, "DF": 3094,
}

# Regiões
REGIAO = {
    "RO": "Norte",  "AC": "Norte",  "AM": "Norte",  "RR": "Norte",
    "PA": "Norte",  "AP": "Norte",  "TO": "Norte",  "MA": "Nordeste",
    "PI": "Nordeste","CE": "Nordeste","RN": "Nordeste","PB": "Nordeste",
    "PE": "Nordeste","AL": "Nordeste","SE": "Nordeste","BA": "Nordeste",
    "MG": "Sudeste","ES": "Sudeste","RJ": "Sudeste","SP": "Sudeste",
    "PR": "Sul",    "SC": "Sul",    "RS": "Sul",
    "MS": "Centro-Oeste","MT": "Centro-Oeste","GO": "Centro-Oeste","DF": "Centro-Oeste",
}

NOMES = {
    "RO": "Rondônia",  "AC": "Acre",      "AM": "Amazonas",       "RR": "Roraima",
    "PA": "Pará",      "AP": "Amapá",     "TO": "Tocantins",      "MA": "Maranhão",
    "PI": "Piauí",     "CE": "Ceará",     "RN": "Rio Grande do Norte","PB": "Paraíba",
    "PE": "Pernambuco","AL": "Alagoas",   "SE": "Sergipe",        "BA": "Bahia",
    "MG": "Minas Gerais","ES": "Espírito Santo","RJ": "Rio de Janeiro","SP": "São Paulo",
    "PR": "Paraná",    "SC": "Santa Catarina","RS": "Rio Grande do Sul",
    "MS": "Mato Grosso do Sul","MT": "Mato Grosso","GO": "Goiás","DF": "Distrito Federal",
}

# --------------------------------------------------------------------------
# Construção do DataFrame
# --------------------------------------------------------------------------

def build_dataframe() -> pd.DataFrame:
    ufs = list(PCT_INTERNET_2023.keys())
    df = pd.DataFrame({
        "sigla":      ufs,
        "nome":       [NOMES[u] for u in ufs],
        "regiao":     [REGIAO[u] for u in ufs],
        "pct_total":  [PCT_INTERNET_2023[u] for u in ufs],
        "idh":        [IDH_2021[u] for u in ufs],
        "pop_mil":    [POP_MIL[u] for u in ufs],
    })
    df["pct_sem_internet"]         = (100 - df["pct_total"]).round(1)
    # Observado (total - com internet), não estimado por "população / 3,1
    # moradores": a média nacional de moradores por domicílio subestimava
    # justamente o Norte e o Nordeste, onde o domicílio é maior — e são as
    # praças que este ranking recomenda.
    df["domicilios_sem_internet_k"] = [DOM_SEM_INTERNET_K[u] for u in ufs]
    return df


# --------------------------------------------------------------------------
# Score de oportunidade (3 componentes ponderados)
# --------------------------------------------------------------------------

def compute_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Score = (1 - penetração) × população (mi) × (0.5 + 0.5 × IDH normalizado)

    Componente 1: % sem internet — quanto maior o gap, maior a oportunidade
    Componente 2: população em milhões — escala absoluta do mercado
    Componente 3: IDH normalizado com peso 0.5 — proxy de capacidade de pagamento
    """
    idh_min, idh_max = df["idh"].min(), df["idh"].max()
    df = df.copy()
    df["idh_norm"]           = (df["idh"] - idh_min) / (idh_max - idh_min)
    df["score_oportunidade"] = (
        (1 - df["pct_total"] / 100)
        * (df["pop_mil"] / 1000)
        * (0.5 + 0.5 * df["idh_norm"])
    ).round(3)

    # Normalizado 0–100 para facilitar comunicação
    s_min, s_max = df["score_oportunidade"].min(), df["score_oportunidade"].max()
    df["score_normalizado"]  = ((df["score_oportunidade"] - s_min) / (s_max - s_min) * 100).round(1)

    # Classificação de oportunidade
    df["categoria"] = pd.cut(
        df["score_normalizado"],
        bins=[0, 20, 40, 65, 100],
        labels=["Baixa", "Moderada", "Alta", "Muito Alta"],
        include_lowest=True,
    )

    return df.sort_values("score_oportunidade", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------
# Análise de risco (penaliza mercados com IDH muito baixo)
# --------------------------------------------------------------------------

def add_risk_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Sinaliza mercados de alto risco por fragilidade econômica
    df["risco_capacidade_pagamento"] = df["idh"] < 0.65
    # Sinaliza mercados quase saturados (>90%)
    df["mercado_saturado"]           = df["pct_total"] > 90
    # Estratégia recomendada
    def estrategia(row):
        if row["mercado_saturado"]:
            return "Upgrade premium / retenção"
        # A regra usava o percentual rural, que era uma constante disfarçada.
        # Penetração total abaixo de 80% é observada e diz a mesma coisa que
        # importa aqui: o mercado ainda não tem cobertura fixa madura.
        if row["pct_total"] < 80:
            return "Satélite / radiofrequência + FTTH nas capitais"
        if row["idh"] >= 0.72:
            return "Fibra FTTH urbana"
        return "Fibra FTTC + subsídio governo"
    df["estrategia_recomendada"] = df.apply(estrategia, axis=1)
    return df


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Market Scoring — Oportunidades ISP Brasil 2023")
    print("=" * 60)

    df = build_dataframe()
    df = compute_score(df)
    df = add_risk_flags(df)

    # Exporta ranking completo
    out_full = OUTPUTS / "market_scores.csv"
    df.to_csv(out_full, index=False, encoding="utf-8-sig")
    print(f"\nRanking completo exportado: {out_full.name} ({len(df)} estados)")

    # Top 5 recomendados (exclui saturados)
    top5 = df[~df["mercado_saturado"]].head(5)
    out_top5 = OUTPUTS / "top5_recommendation.csv"
    top5.to_csv(out_top5, index=False, encoding="utf-8-sig")
    print(f"Top 5 recomendados exportado: {out_top5.name}")

    # KPIs nacionais
    print("\n=== KPIs Nacionais — IBGE PNAD 2023 ===")
    print(f"  Media nacional de penetracao:     {df['pct_total'].mean():.1f}%")
    print(f"  Domicilios sem internet:           ~{df['domicilios_sem_internet_k'].sum():,}k")
    print(f"  Estados com < 80% penetracao:      {(df['pct_total'] < 80).sum()}")
    print(f"  Estados saturados (> 90%):         {df['mercado_saturado'].sum()}")

    # Top 10 ranking
    print("\n=== Top 10 Oportunidades de Expansao ===")
    cols = ["sigla", "nome", "regiao", "pct_total", "domicilios_sem_internet_k",
            "idh", "score_normalizado", "categoria", "estrategia_recomendada"]
    print(df[cols].head(10).to_string(index=False))

    # Resumo por regiao
    print("\n=== Score Medio por Regiao ===")
    reg = df.groupby("regiao").agg(
        media_score=("score_normalizado", "mean"),
        n_estados=("sigla", "count"),
        media_penetracao=("pct_total", "mean"),
    ).round(1).sort_values("media_score", ascending=False)
    print(reg.to_string())

    print("\n" + "=" * 60)
    print("  Outputs gerados em outputs/")
    print("=" * 60)


if __name__ == "__main__":
    main()
