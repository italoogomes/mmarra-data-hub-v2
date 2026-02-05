# 📊 Estado Atual - MMarra Data Hub

**Versão:** v2.1.0
**Última Atualização:** 2026-02-05
**Histórico Completo:** Ver `CHANGELOG.md`

---

## ✅ O Que Está Funcionando

### Infraestrutura
- [x] API Sankhya autenticando via OAuth2
- [x] Azure Data Lake configurado (container: datahub)
- [x] MCP Server para Claude Code (`mcp_sankhya/`)
- [x] Sistema de RAG com ~1500 chunks indexados
- [x] Arquivo `.env` configurado em `mcp_sankhya/.env`

### ETL (Agente Engenheiro)
- [x] Extração: Vendas, Clientes, Produtos, Estoque, Vendedores
- [x] Transformação: Limpeza e normalização
- [x] Carga: Upload para Data Lake em Parquet
- [x] Script: `scripts/extracao/extrair_vendas_completo.py` (extrai 175k+ registros)
- [x] Extractores com métodos de compatibilidade (`extrair()`, `salvar_parquet()`)

### Análise (Agente Analista)
- [x] KPIs de vendas, compras, estoque
- [x] Geração de relatórios HTML
- [x] Templates em `src/agents/analyst/reports/templates/`
- [x] Dashboard Data Prep em `src/agents/analyst/dashboards/`

### Machine Learning (Agente Cientista)
- [x] Prophet para previsão de demanda
- [x] **10 modelos treinados** para TOP 10 produtos
- [x] Modelos salvos em `src/agents/scientist/models/demand/`
- [x] Script: `scripts/treinar_multiplos_modelos.py`

### Detecção de Anomalias
- [x] Isolation Forest com classificação de severidade
- [x] Gerador de alertas em 3 formatos (text, markdown, html)
- [x] Script: `scripts/detectar_anomalias.py`
- [x] Relatórios salvos em `output/reports/`

### Dashboard Web
- [x] Streamlit + Plotly
- [x] KPIs principais (faturamento, pedidos, ticket médio)
- [x] Gráficos: vendas por dia, top produtos, curva ABC
- [x] Script: `python scripts/iniciar_dashboard.py`

### Chat IA (Agente LLM)
- [x] Groq API (modelo: qwen/qwen3-32b)
- [x] RAG com documentação indexada
- [x] Tools: forecast_tool, kpi_tool
- [x] Interface: `python scripts/chat_ia.py`

---

## 📁 Dados Disponíveis

### Local (src/data/raw/)
| Dataset | Registros | Arquivo |
|---------|-----------|---------|
| Vendas | 175.620 | `vendas/vendas.parquet` |

### Azure Data Lake
| Dataset | Registros | Atualização |
|---------|-----------|-------------|
| Vendas | ~340.000 | Diária |
| Clientes | ~57.000 | Diária |
| Produtos | ~393.000 | Diária |
| Estoque ERP | ~36.000 | Diária |
| Estoque WMS | ~45.000 | Diária |
| Vendedores | ~111 | Semanal |

---

## 🤖 Modelos Prophet Treinados

| Produto | Descrição | Previsão 30 dias | Tendência |
|---------|-----------|------------------|-----------|
| 263340 | DIPS INDICADOR PORCA CH32 | 469 un | baixa |
| 306957 | PORCA RODA 22MM CH32 | 959 un | baixa |
| 305273 | DIPS INDICADOR CH33 VERDE | 2479 un | alta |
| 261301 | MOLA PATIM FREIO 132MM | 1691 un | baixa |
| 32007 | TUBO NYLON TECALON 8MM | 1136 un | baixa |
| 305277 | DIPS INDICADOR CH33 AMAR | 760 un | alta |
| 166756 | TRAVA ROLETE PATIM | 614 un | baixa |
| 32037 | INSERT TUBO 5/16 8MM | 387 un | alta |
| 32043 | INSERT TUBO OD 12mm | 467 un | estável |
| 48352 | FLEXIVEL FREIO 3/8 1000MM | 927 un | baixa |

---

## 📊 Tabelas Sankhya Mapeadas

### Core (100% mapeadas)
| Tabela | Colunas | Descrição |
|--------|---------|-----------|
| TGFCAB | 422 | Cabeçalho de notas |
| TGFITE | 231 | Itens das notas |
| TGFPRO | 426 | Produtos |
| TGFPAR | 299 | Parceiros |
| TGFEST | 24 | Estoque ERP |

### WMS (100% mapeadas)
| Tabela | Descrição |
|--------|-----------|
| TGWREC | Recebimento |
| TGWSEP | Separação |
| TGWEMPE | Empenho |
| TGWEST | Estoque WMS |
| VGWRECSITCAB | View situação |

---

## 🎯 Próximos Passos

### Prioridade Alta
1. [x] ~~Expandir modelos Prophet para mais produtos~~
2. [x] ~~Implementar detecção de anomalias~~
3. [x] ~~Criar dashboard web~~
4. [ ] Integrar Prophet e Anomalias com Agente LLM
5. [ ] Agendamento automático de ETL

### Prioridade Média
6. [ ] Adicionar mais KPIs no Analista
7. [ ] Integrar com Clara (cartão corporativo)
8. [ ] Persistência de modelos de anomalia

### Prioridade Baixa
9. [ ] Interface WhatsApp
10. [ ] Notificações automáticas
11. [ ] API REST para consultas

---

## ⚠️ Problemas Conhecidos

| Problema | Workaround | Status |
|----------|------------|--------|
| Timeout em queries pesadas | Usar `ROWNUM < 1000` | Aberto |
| Alguns campos AD_* não mapeados | Documentar conforme descobrir | Aberto |
| Bug filtro empresa no empenho | Ver `docs/bugs/` | Aberto |
| Azure upload com erro 403 | Dados salvos local OK | Aberto |

---

## 🔧 Como Executar

```bash
# ETL completo de vendas
python scripts/extracao/extrair_vendas_completo.py

# Treinar modelos Prophet (TOP 20)
python scripts/treinar_multiplos_modelos.py --top 20

# Detectar anomalias
python scripts/detectar_anomalias.py --top 20

# Iniciar Dashboard Web
python scripts/iniciar_dashboard.py
# Acesse: http://localhost:8501

# Chat com IA
python scripts/chat_ia.py "Qual o faturamento do mês?"

# MCP Server (VS Code)
python -m mcp_sankhya.server
```

---

## 📚 Documentação Rápida

| Tópico | Arquivo |
|--------|---------|
| Instruções para IA | `CLAUDE.md` |
| API Sankhya | `docs/api/sankhya.md` |
| Mapeamento tabelas | `docs/de-para/sankhya/` |
| Status WMS | `docs/de-para/sankhya/wms.md` |
| Investigações | `docs/investigacoes/README.md` |
| Bugs conhecidos | `docs/bugs/` |

---

## 🔄 Mudanças na v2.1 (2026-02-05)

1. **Modelos Prophet expandidos** - 10 produtos treinados
2. **Detecção de anomalias** - Isolation Forest funcionando
3. **Dashboard Streamlit** - Visualização de KPIs e gráficos
4. **Scripts novos:**
   - `scripts/extracao/extrair_vendas_completo.py`
   - `scripts/treinar_multiplos_modelos.py`
   - `scripts/detectar_anomalias.py`
   - `scripts/iniciar_dashboard.py`
5. **Correções:**
   - Formato de data Sankhya (TO_CHAR)
   - Imports de extractors
   - Métodos de compatibilidade no BaseExtractor

---

*Este arquivo é atualizado a cada sessão de trabalho.*
*Para histórico detalhado, consulte `CHANGELOG.md`.*
