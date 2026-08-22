"""
Os achados publicados, como asserção — Expansão de Mercado

Execute com: pytest tests/ -v   (roda `run_analysis.py` antes, uma vez)

POR QUE ESTE ARQUIVO EXISTE
---------------------------
Este repositório já publicou, ao mesmo tempo:

  - um comentário de dez linhas explicando que 87,0% era número inventado, e
    sessenta linhas abaixo um gráfico plotando 87,0% sob o título "IBGE";
  - "São Paulo tem a melhor taxa do país", quando SP é o 5º (DF, MS, SC e GO
    vêm antes) — e o próprio `market_scores.csv` do repositório trazia
    `rank_taxa = 23`, que é o 5º melhor de 27, contradizendo o texto ao lado.

Nos dois casos o dado estava certo e a afirmação errada, e nada quebrava, porque
número em README não é executado. Aqui ele passa a ser: cada teste amarra uma
frase publicada ao valor que o pipeline devolve. Se o gerador ou a fonte mudar,
o teste falha e obriga a atualizar o texto — em vez de deixar os dois divergirem
em silêncio por meses.

Os valores conferidos aqui são os de 2023, o ano em que o método foi validado
contra o release do IBGE (92,6% calculado contra 92,5% publicado).
"""

import os
import subprocess
import sys

import pandas as pd
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCORES = os.path.join(RAIZ, "outputs", "market_scores.csv")
TOP5 = os.path.join(RAIZ, "outputs", "top5_recommendation.csv")


@pytest.fixture(scope="session", autouse=True)
def roda_pipeline():
    """Regera as saídas antes de conferir — testar o CSV velho não prova nada."""
    subprocess.run(
        [sys.executable, "run_analysis.py"],
        cwd=RAIZ, check=True, capture_output=True,
    )


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(SCORES, encoding="utf-8-sig")


@pytest.fixture(scope="module")
def top5():
    return pd.read_csv(TOP5, encoding="utf-8-sig")


# ── O paradoxo taxa × volume ──────────────────────────────────────────────────

def test_sao_paulo_e_quinto_em_taxa(df):
    """README: "São Paulo é o 5º estado em taxa de acesso"."""
    ordem = df.sort_values("pct_total", ascending=False)["sigla"].tolist()
    assert ordem.index("SP") + 1 == 5, (
        f"SP aparece em {ordem.index('SP') + 1}º em taxa, e o texto diz 5º. "
        f"Ordem atual: {ordem[:6]}"
    )


def test_sao_paulo_e_primeiro_em_volume(df):
    """README: "e o 1º em número absoluto de domicílios desconectados"."""
    ordem = df.sort_values("dom_sem_k", ascending=False)["sigla"].tolist()
    assert ordem[0] == "SP", f"O 1º em volume virou {ordem[0]}"


def test_sao_paulo_nao_e_o_melhor_do_pais(df):
    """Guarda contra a afirmação que este repositório já publicou.

    O paradoxo não precisa de exagero: 5º em taxa e 1º em volume já é o
    achado. Dizer "melhor do país" tornava a frase falsa de graça.
    """
    melhor = df.loc[df["pct_total"].idxmax(), "sigla"]
    assert melhor != "SP", "Se SP virou o 1º em taxa, o achado mudou de forma"


# ── As três hipóteses ─────────────────────────────────────────────────────────

def test_h1_gap_regional_refutada(df):
    """README: "H1 Refutada — 4,6pp", ponderado por domicílios."""
    ne = df[df["regiao"].isin(["Norte", "Nordeste"])]
    ss = df[df["regiao"].isin(["Sul", "Sudeste"])]

    def pond(g):
        dom = g["dom_sem_k"] / (1 - g["pct_total"] / 100)   # total de domicílios
        return (dom * g["pct_total"] / 100).sum() / dom.sum() * 100

    gap = pond(ss) - pond(ne)
    assert 4.0 <= gap <= 5.2, f"Gap regional em {gap:.1f}pp; o README diz 4,6pp"


def test_h2_rankings_discordam(df):
    """README: "H2 Confirmada — ρ = 0,24"."""
    rho = df["rank_taxa"].corr(df["rank_volume"], method="spearman")
    assert abs(rho) < 0.45, (
        f"rho de Spearman em {rho:.2f}. Acima de 0,45 os dois rankings deixam "
        "de discordar e H2 precisa ser reescrita."
    )


def test_h3_idh_explica(df):
    """README: "H3 Confirmada — r = 0,769 (r² = 0,59)"."""
    r = df["idh"].corr(df["pct_total"])
    assert 0.72 <= r <= 0.82, f"r = {r:.3f}; o README diz 0,769"


# ── A fila de prioridade ──────────────────────────────────────────────────────

def test_top5_publicado(top5):
    """README traz a fila nomeada: BA, PE, CE, MA, AM."""
    assert top5["sigla"].tolist() == ["BA", "PE", "CE", "MA", "AM"], (
        f"A fila mudou para {top5['sigla'].tolist()} e o README não sabe"
    )


def test_corte_de_92_ainda_discrimina(df):
    """A fila só faz sentido enquanto o corte separa estados.

    Em 2025 sobra um estado abaixo de 92% e o exercício perde o sentido — é o
    que o README explica na seção "Por que a fila é de 2023". Se este teste
    falhar no recorte de 2023, a premissa do projeto caiu junto.
    """
    abaixo = (df["pct_total"] < 92).sum()
    assert abaixo >= 8, (
        f"Só {abaixo} estados abaixo de 92%: o corte parou de discriminar e a "
        "fila vira ranking de população"
    )


def test_27_estados(df):
    assert len(df) == 27


# ── Incerteza amostral ────────────────────────────────────────────────────────

def test_intervalo_vem_do_ibge(df):
    """A margem de erro e' calculada do CV publicado, nao arbitrada.

    Se `margem_pp` sumir ou vier zerada, o painel voltou a tratar estimativa
    amostral como contagem.
    """
    assert "margem_pp" in df.columns, "A coluna de margem sumiu do pipeline"
    assert df["margem_pp"].notna().all(), "Ha UF sem margem de erro"
    assert (df["margem_pp"] > 0).all(), "Margem zerada: o CV nao esta sendo lido"
    # CV por UF na PNAD fica na casa de 0,6% a 2%; margem de 95% sobre ~90%
    # cai entre ~1pp e ~4pp. Fora disso, o calculo quebrou.
    assert df["margem_pp"].between(0.5, 6.0).all(), (
        f"Margens fora da faixa plausivel: {df['margem_pp'].min():.2f} a "
        f"{df['margem_pp'].max():.2f}pp"
    )


def test_ranking_por_taxa_nao_separa_vizinhos(df):
    """README: "os 26 pares vizinhos se sobrepoem. Todos."

    E o achado que sustenta a tese do projeto: o ranking por taxa aponta para o
    lugar errado, e entre vizinhos ele nem chega a medir.
    """
    r = df.sort_values("pct_total", ascending=False).reset_index(drop=True)
    pares = list(zip(r.itertuples(), r.iloc[1:].itertuples()))
    sobrepostos = sum(1 for a, b in pares if a.ic_inf <= b.ic_sup)
    assert sobrepostos == len(pares), (
        f"So {sobrepostos} de {len(pares)} pares vizinhos se sobrepoem. Se caiu, "
        "o texto do README precisa mudar junto."
    )


def test_ic_contem_a_estimativa(df):
    """Sanidade: o intervalo tem que conter o ponto."""
    assert (df["ic_inf"] <= df["pct_total"]).all()
    assert (df["pct_total"] <= df["ic_sup"]).all()


def test_volume_separa_melhor_que_taxa(df):
    """A tese: o ranking por volume discrimina onde o de taxa empata.

    Nao usa IC no volume de proposito — o IBGE nao publica a estimativa de
    domicilios SEM internet, entao a margem dela dependeria de uma correlacao
    que tambem nao e publicada. O que da para afirmar sem suposicao nenhuma e
    que a distancia RELATIVA entre o 1o e o 2o e de outra ordem de grandeza.
    """
    v = df.sort_values("dom_sem_k", ascending=False).reset_index(drop=True)
    salto_volume = (v.loc[0, "dom_sem_k"] - v.loc[1, "dom_sem_k"]) / v.loc[1, "dom_sem_k"]

    t = df.sort_values("pct_total", ascending=False).reset_index(drop=True)
    salto_taxa = (t.loc[0, "pct_total"] - t.loc[1, "pct_total"]) / t.loc[1, "pct_total"]

    assert salto_volume > 10 * salto_taxa, (
        f"O 1o em volume esta {salto_volume:.1%} acima do 2o; em taxa, "
        f"{salto_taxa:.1%}. A tese depende dessa diferenca de ordem."
    )
