# Dados — IBGE PNAD Contínua + GeoJSON Brasil

## Fonte Principal: IBGE SIDRA API

O notebook usa a **API SIDRA do IBGE**, que é pública e não requer autenticação.

A célula de download no notebook faz as chamadas automaticamente:
- Tabela 9173 — Proporção de domicílios com acesso à internet (por UF)
- Tabela 9174 — Acesso à internet por situação (urbano/rural)
- Tabela 7170 — Complemento de equipamentos e acesso

**Não é necessário baixar nada manualmente** — os dados são recuperados via API e salvos em `data/processed/` na primeira execução.

## GeoJSON — Malha Estadual Brasileira

O choropleth usa a malha geoespacial dos estados brasileiros. O notebook baixa automaticamente via API pública do IBGE:

```
https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?resolucao=2&formato=application/vnd.geo+json
```

Esta é a API oficial de malhas geoespaciais do IBGE. Não requer autenticação.

## Dados Complementares (manual)

Para a análise de correlação socioeconômica, o notebook usa IDH por estado do PNUD Brasil.

Baixe em **pnud.org.br** → Atlas do Desenvolvimento Humano no Brasil → Dados por UF → Salve como `data/idh_estados.csv`.

Formato esperado:
```
uf_sigla,ano,idh
AC,2021,0.708
AL,2021,0.683
...
```
