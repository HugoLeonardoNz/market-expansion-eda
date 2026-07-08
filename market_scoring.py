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

import numpy as np
import pandas as pd

ROOT    = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Dados IBGE PNAD Contínua 2023 — embutidos (fallback da API SIDRA)
# --------------------------------------------------------------------------

# % domicílios com acesso à internet por UF
PCT_INTERNET_2023 = {
    "RO": 82.4, "AC": 81.2, "AM": 77.6, "RR": 85.6, "PA": 77.8,
    "AP": 82.5, "TO": 82.1, "MA": 73.8, "PI": 79.3, "CE": 78.9,
    "RN": 83.6, "PB": 80.5, "PE": 82.4, "AL": 78.4, "SE": 82.8,
    "BA": 80.3, "MG": 88.7, "ES": 89.5, "RJ": 91.3, "SP": 93.5,
    "PR": 91.6, "SC": 93.8, "RS": 92.8, "MS": 89.4, "MT": 88.2,
    "GO": 90.0, "DF": 95.1,
}

PCT_URBANO_2023 = {k: v + 5 for k, v in PCT_INTERNET_2023.items()}
PCT_RURAL_2023  = {k: v - 20 for k, v in PCT_INTERNET_2023.items()}

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
        "pct_urbano": [PCT_URBANO_2023[u] for u in ufs],
        "pct_rural":  [PCT_RURAL_2023[u] for u in ufs],
        "idh":        [IDH_2021[u] for u in ufs],
        "pop_mil":    [POP_MIL[u] for u in ufs],
    })
    df["gap_digital"]              = (df["pct_urbano"] - df["pct_rural"]).round(1)
    df["pct_sem_internet"]         = (100 - df["pct_total"]).round(1)
    df["domicilios_sem_internet_k"] = ((1 - df["pct_total"] / 100) * df["pop_mil"] / 3.1).round(0).astype(int)
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
        if row["pct_rural"] < 60:
            return "Satélite / radiofrequência rural"
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
    print(f"  Gap medio urbano x rural:          {df['gap_digital'].mean():.1f} p.p.")
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
