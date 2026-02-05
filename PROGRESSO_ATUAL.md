# 📊 Estado Atual - MMarra Data Hub

**Versão:** v2.0.0
**Última Atualização:** 2026-02-05
**Histórico Completo:** Ver `CHANGELOG.md`

---

## ✅ O Que Está Funcionando

### Infraestrutura
- [x] API Sankhya autenticando via OAuth2
- [x] Azure Data Lake configurado (container: datahub)
- [x] MCP Server para Claude Code (`mcp_sankhya/`)
- [x] Sistema de RAG com ~1500 chunks indexados

### ETL (Agente Engenheiro)
- [x] Extração: Vendas, Clientes, Produtos, Estoque, Vendedores
- [x] Transformação: Limpeza e normalização
- [x] Carga: Upload para Data Lake em Parquet
- [x] Script: `scripts/extracao/extrair_tudo.py`

### Análise (Agente Analista)
- [x] KPIs de vendas, compras, estoque
- [x] Geração de relatórios HTML
- [x] Templates em `src/agents/analyst/reports/templates/`

### Machine Learning (Agente Cientista)
- [x] Prophet para previsão de demanda
- [x] Produto treinado: 261301 (MOLA PATIM FREIO)
- [x] Modelos em `src/agents/scientist/models/`

### Chat IA (Agente LLM)
- [x] Groq API (modelo: qwen/qwen3-32b)
- [x] RAG com documentação indexada
- [x] Tools: forecast_tool, kpi_tool
- [x] Interface: `python scripts/chat_ia.py`

---

## 📁 Dados Disponíveis no Data Lake

| Dataset | Registros | Atualização |
|---------|-----------|-------------|
| Vendas | ~340.000 | Diária |
| Clientes | ~57.000 | Diária |
| Produtos | ~393.000 | Diária |
| Estoque ERP | ~36.000 | Diária |
| Estoque WMS | ~45.000 | Diária |
| Vendedores | ~111 | Semanal |

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

### Status WMS (22 códigos documentados)
Ver `docs/de-para/sankhya/wms.md`

---

## 🎯 Próximos Passos

### Prioridade Alta
1. [ ] Expandir modelos Prophet para mais produtos
2. [ ] Implementar detecção de anomalias
3. [ ] Criar dashboard web

### Prioridade Média
4. [ ] Adicionar mais KPIs no Analista
5. [ ] Integrar com Clara (cartão corporativo)
6. [ ] Agendamento automático de ETL

### Prioridade Baixa
7. [ ] Interface WhatsApp
8. [ ] Notificações automáticas
9. [ ] API REST para consultas

---

## ⚠️ Problemas Conhecidos

| Problema | Workaround | Status |
|----------|------------|--------|
| Timeout em queries pesadas | Usar `ROWNUM < 1000` | Aberto |
| Alguns campos AD_* não mapeados | Documentar conforme descobrir | Aberto |
| Bug filtro empresa no empenho | Ver `docs/bugs/` | Aberto |

---

## 🔧 Como Executar

```bash
# ETL completo
python scripts/extracao/extrair_tudo.py

# Chat com IA
python scripts/chat_ia.py "Qual o faturamento do mês?"

# Treinar modelos
python scripts/treinar_modelos.py

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

## 🔄 Mudanças na v2.0

1. **Dados movidos** de `src/data/` para `data/`
2. **RAG expandido** com mais fontes de conhecimento
3. **Investigações documentadas** em `docs/investigacoes/`
4. **API Sankhya** totalmente documentada
5. **Queries organizadas** por módulo
6. **.gitignore** otimizado

---

*Este arquivo é atualizado a cada sessão de trabalho.*
*Para histórico detalhado, consulte `CHANGELOG.md`.*
