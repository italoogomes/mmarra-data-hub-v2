# Scripts do MMarra Data Hub

Documentação dos scripts disponíveis para execução.

---

## Scripts de Extração

### extrair_vendas_completo.py
**Localização:** `scripts/extracao/extrair_vendas_completo.py`

Extrai todas as vendas do Sankhya por faixas de NUNOTA.

```bash
python scripts/extracao/extrair_vendas_completo.py
```

**Saída:** `src/data/raw/vendas/vendas.parquet`

**Detalhes:**
- Extrai por faixas de 10.000 para contornar limite da API
- Converte datas para formato ISO (YYYY-MM-DD)
- ~175.000 registros

---

### extrair_para_datalake.py
**Localização:** `scripts/extracao/extrair_para_datalake.py`

Extrai dados do Sankhya e envia para Azure Data Lake.

```bash
# Todos os extratores
python scripts/extracao/extrair_para_datalake.py --extrator todos

# Apenas vendas
python scripts/extracao/extrair_para_datalake.py --extrator vendas

# Com limite (teste)
python scripts/extracao/extrair_para_datalake.py --extrator vendas --limite 1000
```

**Extratores disponíveis:**
- vendedores
- clientes
- produtos
- estoque
- vendas

---

## Scripts de Machine Learning

### treinar_multiplos_modelos.py
**Localização:** `scripts/treinar_multiplos_modelos.py`

Treina modelos Prophet para os TOP N produtos.

```bash
# TOP 20 produtos (padrão)
python scripts/treinar_multiplos_modelos.py --top 20

# TOP 10 com previsão de 60 dias
python scripts/treinar_multiplos_modelos.py --top 10 --periodos 60
```

**Saída:** `src/agents/scientist/models/demand/demand_model_{codprod}_{timestamp}.pkl`

---

### detectar_anomalias.py
**Localização:** `scripts/detectar_anomalias.py`

Detecta anomalias nos dados usando Isolation Forest.

```bash
# Vendas (padrão)
python scripts/detectar_anomalias.py --tipo vendas --top 20

# Estoque
python scripts/detectar_anomalias.py --tipo estoque --top 10
```

**Saída:**
- `output/reports/anomalias_vendas_{timestamp}.csv`
- `output/divergencias/{data}_anomalias_vendas.md`

---

## Scripts de Dashboard

### iniciar_dashboard.py
**Localização:** `scripts/iniciar_dashboard.py`

Inicia o Dashboard Web (Streamlit).

```bash
python scripts/iniciar_dashboard.py
```

**Acesso:** http://localhost:8501

**Features:**
- KPIs: Faturamento, Pedidos, Ticket Médio, Clientes
- Gráfico de vendas diárias
- Top 10 produtos
- Curva ABC
- Previsões Prophet
- Anomalias detectadas

---

## Scripts de Chat/IA

### chat_ia.py
**Localização:** `scripts/chat_ia.py`

Chat interativo com a IA (Orquestrador).

```bash
# Pergunta direta
python scripts/chat_ia.py "Qual o faturamento do mês?"

# Chat interativo
python scripts/chat_ia.py
```

**Tools disponíveis:**
- `search_documentation` - Busca no RAG
- `forecast_demand` - Previsão Prophet
- `get_kpis` - KPIs de vendas/compras
- `detect_anomalies` - Detecção de anomalias
- `generate_anomaly_alerts` - Gera alertas

---

## Scripts de Teste

| Script | Função |
|--------|--------|
| `testar_agente_cientista.py` | Testa Prophet, Anomalias, Clustering |
| `testar_cientista_sintetico.py` | Testa com dados sintéticos |
| `testar_analista.py` | Testa KPIs e relatórios |
| `testar_engenheiro.py` | Testa extractors e ETL |
| `testar_azure.py` | Testa conexão Azure Data Lake |

---

**Última atualização:** 2026-02-05
