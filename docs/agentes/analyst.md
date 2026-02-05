# Agente Analista - MMarra Data Hub

**Status:** Operacional
**Versao:** 1.0.0
**Ultima Atualizacao:** 2026-02-04

---

## Visao Geral

O Agente Analista e responsavel por calcular KPIs, gerar relatorios e preparar dados para dashboards. Ele consome dados do Data Lake (ou API Sankhya como fallback) e retorna dados estruturados.

**Importante:** O Agente Analista NAO usa LLM. Ele e 100% Python puro (pandas, jinja2). O Agente LLM (futuro) chamara os metodos do Analista via tools para obter os KPIs e explicar os resultados.

---

## Arquitetura

```
src/agents/analyst/
├── __init__.py              # Exports principais
├── config.py                # Configuracoes centralizadas
├── data_loader.py           # Carregador com fallback DL -> API
│
├── kpis/                    # Calculadores de KPIs
│   ├── __init__.py
│   ├── base.py              # Classe base abstrata
│   ├── vendas.py            # KPIs de vendas
│   ├── compras.py           # KPIs de compras
│   └── estoque.py           # KPIs de estoque
│
├── reports/                 # Gerador de relatorios
│   ├── __init__.py
│   ├── generator.py         # ReportGenerator
│   └── templates/           # Templates Jinja2
│
└── dashboards/              # Preparacao para dashboards
    ├── __init__.py
    └── data_prep.py         # DashboardDataPrep
```

---

## Uso Rapido

### Calcular KPIs de Vendas

```python
from src.agents.analyst import VendasKPI, AnalystDataLoader

# Carregar dados
loader = AnalystDataLoader()
df = loader.load("vendas", data_inicio="2026-01-01", data_fim="2026-01-31")

# Calcular KPIs
kpi = VendasKPI()
resultado = kpi.calculate_all(df)

print(resultado)
# {
#     "faturamento_total": {"valor": 150000.0, "formatted": "R$ 150.000,00"},
#     "ticket_medio": {"valor": 1500.0, "formatted": "R$ 1.500,00"},
#     "qtd_pedidos": {"valor": 100, "formatted": "100"},
#     ...
# }
```

### Gerar Relatorio HTML

```python
from src.agents.analyst import VendasKPI, ReportGenerator, AnalystDataLoader

loader = AnalystDataLoader()
df = loader.load("vendas")

kpi = VendasKPI()
resultado = kpi.calculate_all(df)

gen = ReportGenerator()
html = gen.generate(
    kpis={"vendas": resultado},
    output_path="output/relatorio_vendas.html"
)
```

### Preparar Dados para Dashboard

```python
from src.agents.analyst import DashboardDataPrep

prep = DashboardDataPrep()

# Serie temporal para grafico de linha
dados_linha = prep.prepare_time_series(df, date_col="DTNEG", value_col="VLRNOTA")

# Ranking para grafico de barras
dados_barra = prep.prepare_ranking(df, group_col="CODVEND", value_col="VLRNOTA", top_n=10)

# Curva ABC
dados_abc = prep.prepare_curva_abc(df, item_col="CODPROD", value_col="VLRNOTA")
```

---

## KPIs Disponiveis

### Vendas (VendasKPI)

| KPI | Descricao | Colunas Necessarias |
|-----|-----------|---------------------|
| `faturamento_total` | Soma do valor das notas | NUNOTA, VLRNOTA |
| `ticket_medio` | Faturamento / Numero de pedidos | NUNOTA, VLRNOTA |
| `qtd_pedidos` | Contagem de pedidos unicos | NUNOTA |
| `vendas_por_vendedor` | Faturamento por vendedor | CODVEND, VLRNOTA |
| `vendas_por_cliente` | Faturamento por cliente | CODPARC, VLRNOTA |
| `taxa_desconto` | % de desconto sobre faturamento | VLRDESCTOT, VLRNOTA |
| `crescimento_mom` | Crescimento mes a mes | DTNEG, VLRNOTA |
| `top_produtos` | Produtos mais vendidos | CODPROD, QTDNEG |
| `curva_abc_clientes` | Classificacao ABC de clientes | CODPARC, VLRNOTA |

### Compras (ComprasKPI)

| KPI | Descricao | Colunas Necessarias |
|-----|-----------|---------------------|
| `volume_compras` | Valor total das compras | NUNOTA, VLRNOTA |
| `custo_medio_produto` | Custo medio por produto | CODPROD, VLRUNIT |
| `lead_time_fornecedor` | Tempo medio de entrega | DTNEG, DTENTSAI, CODPARC |
| `pedidos_pendentes` | Pedidos aguardando | COD_SITUACAO |
| `taxa_conferencia_wms` | % de pedidos conferidos | COD_SITUACAO |
| `top_fornecedores` | Fornecedores com maior volume | CODPARC, VLRNOTA |

### Estoque (EstoqueKPI)

| KPI | Descricao | Colunas Necessarias |
|-----|-----------|---------------------|
| `estoque_total_valor` | Valor total em estoque | ESTOQUE, VLRUNIT |
| `estoque_total_unidades` | Quantidade total | ESTOQUE |
| `giro_estoque` | Vendas / Estoque medio | df_vendas necessario |
| `produtos_sem_estoque` | Produtos com estoque zero | ESTOQUE |
| `cobertura_estoque` | Dias de cobertura | df_vendas necessario |
| `divergencia_erp_wms` | Diferenca ERP vs WMS | df_wms necessario |
| `curva_abc_estoque` | Classificacao ABC | CODPROD, ESTOQUE, VLRUNIT |

---

## Data Loader

O `AnalystDataLoader` implementa estrategia de fallback:

1. **Primeiro tenta Data Lake** (arquivos Parquet locais)
2. **Se falhar, usa API Sankhya** (query direta)

```python
loader = AnalystDataLoader()

# Carregar com fallback automatico
df = loader.load("vendas", data_inicio="2026-01-01")

# Forcar fonte especifica
df = loader.load("vendas", force_source="datalake")
df = loader.load("vendas", force_source="sankhya")

# Limpar cache
loader.clear_cache("vendas")
loader.clear_cache()  # Limpa tudo
```

### Entidades Disponiveis

| Entidade | Tabelas Sankhya | Descricao |
|----------|-----------------|-----------|
| `vendas` | TGFCAB + TGFITE | Notas de venda |
| `compras` | TGFCAB + TGFITE | Notas de compra |
| `estoque` | TGFEST + TGFPRO | Estoque atual |
| `empenho` | TGWEMPE + TGFCAB | Empenhos (futuro) |

---

## Configuracao

### config.py

```python
# KPIs habilitados por modulo
KPI_CONFIG = {
    "vendas": {
        "enabled": True,
        "frequency": "daily",
        "metrics": ["faturamento_total", "ticket_medio", ...]
    },
    ...
}

# Fontes de dados
DATA_SOURCES = {
    "datalake": {
        "local_path": "data/raw",
        "prefer_local": True,
    },
    "sankhya": {
        "use_api": True,
        "timeout": 300,
    }
}
```

---

## Integracao com Agente LLM (Futuro)

O Agente LLM chamara os KPIs via tools:

```python
# src/agents/llm/tools/kpi_tool.py (futuro)
def get_kpis(modulo: str, periodo: str = "hoje") -> dict:
    """
    Tool que o LLM chama para obter KPIs.

    Exemplo de pergunta do usuario:
    "Quanto vendemos esse mes?"

    O LLM identifica que precisa de KPIs de vendas e chama esta tool.
    """
    from ...analyst.kpis import VendasKPI, ComprasKPI, EstoqueKPI
    from ...analyst.data_loader import AnalystDataLoader

    kpi_classes = {
        "vendas": VendasKPI,
        "compras": ComprasKPI,
        "estoque": EstoqueKPI
    }

    loader = AnalystDataLoader()
    data = loader.load(modulo, **parse_periodo(periodo))

    kpi = kpi_classes[modulo]()
    return kpi.calculate_all(data)

# Definicao para LangChain/OpenAI Functions
KPI_TOOL = {
    'name': 'get_kpis',
    'description': 'Obtem KPIs de vendas, compras ou estoque. Use quando o usuario perguntar sobre metricas, faturamento, vendas, etc.',
    'parameters': {
        'type': 'object',
        'properties': {
            'modulo': {
                'type': 'string',
                'enum': ['vendas', 'compras', 'estoque'],
                'description': 'Modulo de KPIs a consultar'
            },
            'periodo': {
                'type': 'string',
                'description': 'Periodo da consulta (hoje, semana, mes, ano)',
                'default': 'mes'
            }
        },
        'required': ['modulo']
    }
}
```

---

## Estrutura dos Retornos

Todos os KPIs retornam dicts estruturados com:

```python
{
    "kpi_name": {
        "valor": 150000.0,           # Valor numerico
        "formatted": "R$ 150.000,00", # Valor formatado para exibicao
        "descricao": "Soma do valor..." # Descricao do KPI
    },
    ...
    "metadata": {
        "modulo": "vendas",
        "calculated_at": "2026-02-04T10:30:00",
        "records_analyzed": 1500,
        "periodo": {"inicio": "2026-01-01", "fim": "2026-01-31"}
    }
}
```

Isso permite que:
1. O Agente LLM interprete os valores numericos
2. A interface exiba os valores formatados
3. O usuario entenda o contexto via descricao

---

## Dependencias

```python
# requirements.txt
pandas>=2.0.0
jinja2>=3.0.0
numpy>=1.24.0
```

Opcional para dashboards:
```python
plotly>=5.0.0
streamlit>=1.0.0
```

---

## Changelog

### v1.0.0 (2026-02-04)
- Implementacao inicial
- KPIs de vendas, compras e estoque
- Data Loader com fallback
- Gerador de relatorios HTML
- Preparacao de dados para dashboards
