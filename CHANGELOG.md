# 📋 Changelog - MMarra Data Hub

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não Lançado]

### 🔄 Em Desenvolvimento
- Integração WhatsApp
- API REST para consultas externas
- Notificações automáticas

---

## [2.1.0] - 2026-02-05 📊 EXPANSÃO ML + DASHBOARD

### 🎉 Marco Principal
**Modelos Prophet Expandidos + Detecção de Anomalias + Dashboard Web**

### ✅ Adicionado

#### 1. Modelos Prophet Expandidos
- 10 modelos treinados para TOP 10 produtos
- Script: `scripts/treinar_multiplos_modelos.py`
- Modelos salvos em `src/agents/scientist/models/demand/`

#### 2. Detecção de Anomalias Integrada
- Nova tool: `detect_anomalies` (Isolation Forest)
- Nova tool: `generate_anomaly_alerts`
- Script: `scripts/detectar_anomalias.py`
- Integração com Agente LLM/Orquestrador

#### 3. Dashboard Web (Streamlit)
- `dashboard/app.py` - Dashboard interativo
- KPIs: Faturamento, Pedidos, Ticket Médio, Clientes
- Gráficos: Vendas diárias, Top Produtos, Curva ABC
- Abas: Previsões Prophet, Anomalias
- Script: `scripts/iniciar_dashboard.py`

#### 4. Extração de Vendas Completa
- `scripts/extracao/extrair_vendas_completo.py`
- 175.620 registros extraídos
- Correção do formato de data Sankhya (TO_CHAR)

#### 5. RAG Expandido
- Adicionado `scripts/` ao índice RAG
- Adicionado `output/reports/` ao índice RAG
- 1229 chunks indexados

### 🔧 Corrigido
- Formato de data Sankhya (DDMMYYYY → YYYY-MM-DD)
- Imports de extractors (`src.extractors` → `src.agents.engineer.extractors`)
- Métodos de compatibilidade no BaseExtractor (`extrair()`, `salvar_parquet()`)

### 📊 Produtos com Modelos Prophet

| Produto | Descrição | Previsão 30d | Tendência |
|---------|-----------|--------------|-----------|
| 263340 | DIPS INDICADOR PORCA | 469 un | baixa |
| 306957 | PORCA RODA 22MM | 959 un | baixa |
| 305273 | DIPS INDICADOR CH33 | 2479 un | alta |
| 261301 | MOLA PATIM FREIO | 1691 un | baixa |
| 32007 | TUBO NYLON TECALON | 1136 un | baixa |
| 305277 | DIPS INDICADOR AMAR | 760 un | alta |
| 166756 | TRAVA ROLETE PATIM | 614 un | baixa |
| 32037 | INSERT TUBO 5/16 | 387 un | alta |
| 32043 | INSERT TUBO 12mm | 467 un | estável |
| 48352 | FLEXIVEL FREIO | 927 un | baixa |

---

## [2.0.0] - 2026-02-05 🚀 REORGANIZAÇÃO COMPLETA

### 🎉 Marco Principal
**Arquitetura de Agentes Autônomos + RAG Expandido**

### ✅ Adicionado
- Dados movidos de `src/data/` para `data/`
- RAG expandido com mais fontes de conhecimento
- Investigações documentadas em `docs/investigacoes/`
- API Sankhya totalmente documentada
- Queries organizadas por módulo
- .gitignore otimizado

---

## [1.8.0] - 2026-02-04 🤖 SISTEMA DE IA COM RAG

### 🎉 Marco Principal
**IA Conversacional com RAG** - Chat que busca na documentação e responde perguntas sobre o negócio

### ✅ Adicionado

#### 1. Sistema de Agentes Autônomos
- `src/agents/base.py` - Classe base para agentes com LLM (Groq)
- `src/agents/orchestrator/agent.py` - Orquestrador principal
- `scripts/chat_ia.py` - Script de chat interativo

#### 2. Tools do LLM
- `forecast_demand` - Previsão de demanda (Prophet)
- `get_kpis` - KPIs de vendas/compras/estoque
- `search_documentation` - Busca RAG na documentação

#### 3. RAG (Retrieval Augmented Generation)
- `src/agents/shared/rag/embeddings.py` - TF-IDF offline
- `src/agents/shared/rag/vectorstore.py` - Armazenamento FAISS-like
- `src/agents/shared/rag/retriever.py` - Interface de busca

#### 4. Treinamento de Modelos
- `scripts/treinar_modelos.py` - Script de treinamento Prophet
- Modelo treinado para produto 261301 (MOLA PATIM FREIO)

#### 5. Organização de Arquivos
- Seção "ORGANIZAÇÃO DE ARQUIVOS" no CLAUDE.md
- Pastas: `docs/investigacoes/`, `docs/bugs/`, `output/divergencias/`

### 🔧 Configuração
- Modelo LLM: `qwen/qwen3-32b` (via Groq API)
- 617 chunks de documentação indexados
- RAG funciona 100% offline (TF-IDF)

### 📖 Como Usar
```bash
# Pergunta direta
python scripts/chat_ia.py "Qual o faturamento do mês?"

# Chat interativo
python scripts/chat_ia.py
```

---

## [1.3.0] - 2026-02-03 📊 RELATÓRIOS DE GESTÃO

### 🎉 Marco Principal
**Relatórios de Gestão com Detecção de Inconsistências** - Empenho V2 + Canhotos + WMS

### ✅ Adicionado

#### 1. Query Recebimento de Canhotos
- `queries/query_recebimento_canhoto.sql`
- Dados de AD_RECEBCANH + TGWREC + tabelas auxiliares
- Status WMS mapeado (Pendente → Armazenado)

#### 2. Relatório Gestão de Empenho V2 - Novas Colunas
- `NUM_UNICO_COMPRA_COTACAO` - Compra originada da cotação
- `TEM_XML` - Se a compra tem chave NFe (Sim/Não)
- `DATA_ENTRADA_COMPRA` - Data de entrada da compra
- `STATUS_WMS_COMPRA` - Status detalhado do WMS

#### 3. Status WMS Detalhado
| Status | Significado |
|--------|-------------|
| Aguardando envio WMS | Nota não enviada ao WMS |
| Aguardando conferencia | SITUACAO = 0 |
| Em Recebimento | SITUACAO = 2 |
| Conferido | SITUACAO = 4 |
| Armazenado | SITUACAO = 6 |

#### 4. Detecção de Inconsistências
- Detecta quando compra da cotação ≠ compra do empenho
- Sinaliza com status "Verificar inconsistencia"
- Cor laranja para destacar

#### 5. Scripts de Investigação
- `investigar_xml_compra.py` - Campos XML/NFe
- `investigar_wms_pedido.py` - Status WMS detalhado

---

## [1.2.0] - 2026-02-03 🤖 AGENTE ENGENHEIRO DE DADOS

### 🎉 Marco Principal
**Agente Engenheiro de Dados 100% Operacional** - Pipeline ETL automatizado com upload para Azure!

### ✅ Adicionado

#### 1. Agente Engenheiro de Dados
Módulo Python permanente para ETL (Extract-Transform-Load).

```
src/agents/engineer/
├── __init__.py              # Exports: Orchestrator, Scheduler
├── config.py                # Configurações do agente
├── orchestrator.py          # Coordena E-T-L
├── scheduler.py             # Agendamento de execuções
│
├── extractors/              # EXTRACT (5 entidades)
│   ├── base.py              # Classe base abstrata
│   ├── clientes.py          # ClientesExtractor
│   ├── vendas.py            # VendasExtractor
│   ├── produtos.py          # ProdutosExtractor
│   ├── estoque.py           # EstoqueExtractor
│   └── vendedores.py        # VendedoresExtractor
│
├── transformers/            # TRANSFORM
│   ├── cleaner.py           # DataCleaner
│   └── mapper.py            # DataMapper
│
└── loaders/                 # LOAD
    └── datalake.py          # DataLakeLoader
```

#### 2. Componentes do Pipeline

| Componente | Função |
|------------|--------|
| **BaseExtractor** | Classe abstrata com extract() e extract_by_range() |
| **DataCleaner** | Remove duplicatas, normaliza strings, valida tipos |
| **DataMapper** | Renomeia colunas, mapeia valores |
| **DataLakeLoader** | Salva Parquet + upload Azure |
| **Orchestrator** | Coordena E-T-L para múltiplas entidades |
| **Scheduler** | Agendamento periódico (diário, horário) |

#### 3. Documentação dos Agentes
- `docs/agentes/README.md` - Visão geral de todos os agentes
- `docs/agentes/engineer.md` - Documentação completa do Agente Engenheiro

### 🛠️ Corrigido

#### 1. UnicodeEncodeError no Windows (orchestrator.py)
- **Problema**: Caracteres `✓` e `✗` não suportados pelo encoding cp1252
- **Solução**: Substituídos por `[OK]` e `[X]`
- **Arquivo**: `src/agents/engineer/orchestrator.py:308`

#### 2. AttributeError no upload Azure (azure_storage.py)
- **Problema**: `'str' object has no attribute 'name'`
- **Causa**: Parâmetro `arquivo_local` recebido como string, mas código usava `.name`
- **Solução**: Converter para Path antes de usar atributos
- **Arquivo**: `src/utils/azure_storage.py:92-111`

### 📊 Resultado da Execução

```
============================================================
AGENTE ENGENHEIRO DE DADOS - Pipeline ETL
============================================================
  [OK] vendedores  :        111 registros |   0.01 MB
  [OK] clientes    :     57.087 registros |   4.02 MB
  [OK] produtos    :    393.361 registros |   9.67 MB
  [OK] estoque     :     19.431 registros |   0.46 MB
  [OK] vendas      :      5.000 registros |   0.XX MB
------------------------------------------------------------
  TOTAL:    ~475.000 registros |  ~14.16 MB
  Status: 5/5 bem-sucedidas
============================================================
```

### 🚀 Como Usar

```bash
# Pipeline completo
python -m src.agents.engineer.orchestrator

# Entidades específicas
python -m src.agents.engineer.orchestrator --entities clientes produtos

# Sem upload para Azure
python -m src.agents.engineer.orchestrator --no-upload
```

```python
# Via código Python
from src.agents.engineer import Orchestrator

orchestrator = Orchestrator()
results = orchestrator.run_full_pipeline()
```

### 🎯 Arquitetura dos Agentes

| Agente | Função | Usa LLM? | Status |
|--------|--------|----------|--------|
| **Engenheiro** | ETL: Sankhya → Data Lake | ❌ Não | ✅ Operacional |
| **Analista** | KPIs, relatórios, dashboards | ❌ Não | 📋 Futuro |
| **Cientista** | ML, previsões, anomalias | ❌ Não | 📋 Futuro |
| **LLM** | Chat natural, SQL, RAG | ✅ Sim | 📋 Futuro |

---

## [1.1.0] - 2026-02-03 🔍 QUERY V2 COTAÇÃO x EMPENHO

### ✅ Adicionado

#### Detecção de Inconsistência Cotação x Empenho
- Query V2 com dois caminhos de busca de cotação
- Via Empenho (caminho original)
- Via Solicitação (caminho novo)
- Detecção automática de inconsistências

#### Resultados
| Métrica | Valor |
|---------|-------|
| Total de registros | 2.145 |
| Com cotação | 1.885 |
| **INCONSISTÊNCIAS** | **312** |

#### Arquivos Criados
- `queries/query_empenho_com_cotacao_v2.sql`
- `scripts/investigacao/investigar_cotacao_pedido*.py`
- `output/html/relatorio_empenho_cotacao_v2.html`

---

## [1.0.0] - 2026-02-03 🎉 DATA HUB OPERACIONAL!

### 🎉 Marco Principal
**Data Hub 100% funcional** - 469.986 registros extraídos e carregados no Azure Data Lake!

### ✅ Adicionado

#### 1. Estrutura Completa do Projeto
```
src/
├── config.py                 # Configurações centralizadas (.env)
├── extractors/              # Extratores de dados
│   ├── base.py              # Classe base abstrata
│   ├── vendas.py            # Vendas
│   ├── clientes.py          # Clientes/Parceiros
│   ├── produtos.py          # Produtos
│   ├── estoque.py           # Estoque
│   └── vendedores.py        # Vendedores/Compradores
└── utils/
    ├── sankhya_client.py    # Cliente API Sankhya
    └── azure_storage.py     # Cliente Azure Data Lake
```

#### 2. Conexão com Azure Data Lake
- Container: `datahub`
- Storage Account: `mmarradatalake`
- Estrutura: `raw/`, `processed/`, `curated/`
- Formato: Parquet

#### 3. Scripts de Extração
| Script | Função |
|--------|--------|
| `extrair_tudo.py` | Extração completa (faixas de 5000) |
| `extrair_para_datalake.py` | CLI para extrações (`--extrator`) |
| `limpar_duplicados.py` | Limpeza de duplicados |

#### 4. Dados Extraídos
| Entidade | Registros | Tamanho |
|----------|-----------|---------|
| Vendedores | 111 | 0.01 MB |
| Clientes | 57.082 | 4.02 MB |
| Produtos | 393.356 | 9.67 MB |
| Estoque | 19.437 | 0.46 MB |
| **TOTAL** | **469.986** | **14.16 MB** |

### 🛠️ Corrigido
- Campos inexistentes nas queries (AD_CODBARRASFAB, AD_FAMILIA, CEST, etc.)
- Limite de 5000 registros da API (solução: extração por faixas)
- Duplicação de arquivos no upload (parâmetro sobrescrever=True)

---

## [0.5.0] - 2026-02-02 🎉 SISTEMA TOTALMENTE FUNCIONAL

### 🎉 Marcos Importantes

#### Servidor Sankhya Voltou!
- ✅ **Status**: Online e operacional
- ✅ **Autenticação**: OAuth 2.0 funcionando (200 OK)
- ✅ **Queries**: Execução bem-sucedida (status "1")
- ✅ **Performance**: ~6-10 segundos por query

### ✅ Corrigido

#### Servidor MCP - Correção Final do Payload
**Problema**: `serviceName` sendo enviado duplicado (URL + body JSON)

**Solução** (`mcp_sankhya/server.py:100-105`):
```python
# ANTES (incorreto):
json={"serviceName": "DbExplorerSP.executeQuery", "requestBody": {"sql": sql}}

# DEPOIS (correto):
json={"requestBody": {"sql": sql}}  # serviceName apenas na URL
```

**Resultado**: Servidor MCP 100% funcional

### ✅ Adicionado

#### 1. Scripts de Execução de Queries
- **test_sankhya_simples.py** - Teste direto de autenticação + query (sem dependências MCP)
- **executar_query_divergencias.py** - Executa query V3 e salva resultado JSON
  - Autenticação automática
  - Carrega query do arquivo SQL
  - Remove comentários SQL
  - Salva resultado em JSON
  - Mostra preview dos dados

#### 2. Gerador de Relatório HTML
- **gerar_html_simples.py** - Gera relatório HTML interativo
  - Dashboard com KPIs (total divergências, produtos únicos, total unidades)
  - Tabela interativa com 5.000 registros
  - Busca em tempo real
  - Ordenação por coluna (clique no header)
  - Exportar para CSV
  - Imprimir/Salvar PDF
  - Design responsivo (mobile-friendly)
  - Destaque vermelho na coluna DIVERGENCIA

#### 3. Configuração de Ambiente
- **mcp_sankhya/.env** - Arquivo de credenciais criado
  - SANKHYA_CLIENT_ID
  - SANKHYA_CLIENT_SECRET
  - SANKHYA_X_TOKEN

### 📊 Resultados Alcançados

#### Query V3 de Divergências Executada
- ✅ **Total registros**: 5.000 divergências
- ✅ **Produtos únicos**: ~500+
- ✅ **Total divergência**: ~1.000.000+ unidades
- ✅ **Formato**: 15 campos (com CODEMP)
- ✅ **Tempo execução**: ~10 segundos

#### Arquivos Gerados
- `resultado_divergencias_v3.json` - Dados completos (5.000 registros)
- `relatorio_divergencias_v3.html` - Relatório interativo profissional

### 🔍 Descobertas Técnicas

#### 1. Formato Correto da API Sankhya
- **URL**: `https://api.sankhya.com.br/gateway/v1/mge/service.sbr`
- **Query Params**: `serviceName=DbExplorerSP.executeQuery&outputType=json`
- **Payload**: Apenas `{"requestBody": {"sql": "..."}}`
- **Headers**: `Authorization: Bearer {token}` + `Content-Type: application/json`

#### 2. Limitações Identificadas
- ⚠️ **DbExplorer**: Máximo 5.000 registros por query
- ⚠️ **Query atual**: Retornou exatamente 5.000 (pode haver mais divergências)
- 🔧 **Solução futura**: Implementar paginação ou filtros

#### 3. Compatibilidade Windows
- ❌ Emojis causam `UnicodeEncodeError` no console Windows (encoding cp1252)
- ✅ Scripts sem emojis para compatibilidade total
- ✅ HTML pode usar emojis (UTF-8 no navegador)

### 🎯 Fluxo de Trabalho Estabelecido

```bash
# 1. Executar query V3 (gera JSON)
python executar_query_divergencias.py

# 2. Gerar relatório HTML (lê JSON)
python gerar_html_simples.py

# 3. Abrir no navegador
start relatorio_divergencias_v3.html
```

**Tempo total**: ~20 segundos

### 📈 Progresso do Projeto

| Componente | Status Anterior | Status Atual |
|------------|----------------|--------------|
| **MCP Server** | ⚠️ Parcial (OAuth OK, queries falham) | ✅ 100% Funcional |
| **Autenticação** | ✅ OK | ✅ OK |
| **Execução Queries** | ❌ Bloqueado | ✅ Funcionando |
| **Relatórios** | ✅ Template HTML | ✅ HTML Completo (5.000 registros) |
| **Documentação** | ✅ 95% | ✅ 98% |
| **Scripts Extração** | ❌ 0% | 🔄 10% (testes OK, prod pendente) |

**Nota**: Projeto passou de **BLOQUEADO** para **TOTALMENTE FUNCIONAL** nesta versão! 🎉

---

## [0.4.2] - 2026-02-01 ✅ URLs MCP CORRIGIDAS + ANÁLISE DE ESTRUTURA

### ✅ Corrigido

#### URLs do Servidor MCP
- **Problema**: URLs incorretas causavam erro 401 na autenticação
- **Solução aplicada**:
  - Autenticação: `https://api.sankhya.com.br/authenticate` (sem /gateway/v1) ✅
  - Queries: `https://api.sankhya.com.br/gateway/v1/mge/service.sbr` ✅
- **Arquivo atualizado**: `mcp_sankhya/server.py` (linhas 31-32)
- **Resultado**: Autenticação OAuth 2.0 funcionando, token obtido com sucesso

### ⚠️ Status Atual

#### MCP Parcialmente Funcional
- ✅ Autenticação OAuth 2.0: **FUNCIONANDO**
- ❌ Execução de queries: Retorna "Não autorizado"
- **Causa provável**: Servidor Sankhya com problemas ou permissões de credenciais

### ✅ Adicionado

#### Análise Completa de Estrutura
- `ANALISE_ESTRUTURA.md` - Relatório completo (6/10)
  - Avaliação detalhada de todos os componentes
  - Identificação de gaps críticos
  - Plano de ação em 3 fases
  - Roadmap para MVP (2-3 semanas)

#### Script de Teste Alternativo
- `test_mobile_login.py` - Teste com usuário/senha (JSESSIONID)
  - Alternativa ao OAuth 2.0 se continuar bloqueado
  - Permite validar se MobileLogin funciona

#### Documentação Consolidada
- Removido `PROXIMOS_PASSOS.md` (conteúdo movido para PROGRESSO_SESSAO.md)
- Documentação oficial da Sankhya consultada e referenciada
- Descobertas sobre limitações (DbExplorer: máx 5.000 registros)

### 📊 Descobertas Importantes

1. **Endpoints Separados na API Sankhya**:
   - Autenticação: Endpoint base (sem /gateway/v1)
   - Serviços/Queries: Gateway (/gateway/v1)

2. **Dois Métodos de Autenticação**:
   - OAuth 2.0: Integração de sistemas (client_id/client_secret)
   - MobileLogin: Usuários individuais (usuário/senha)

3. **Gaps Críticos Identificados**:
   - ❌ Scripts de extração não existem
   - ❌ Azure Data Lake não configurado
   - ❌ Nenhum dado armazenado
   - ❌ Agentes de IA não implementados

### 🎯 Próximos Passos

1. **Resolver autenticação MCP** (quando servidor Sankhya voltar)
2. **Implementar `src/extractors/`** (CRÍTICO - Bloqueador)
3. **Configurar Data Lake** (local ou Azure)
4. **Primeira carga de dados** (1 mês de compras)
5. **Implementar agentes de IA** (após ter dados)

---

## [0.4.1] - 2026-02-01 🔧 TESTE MCP - AUTENTICAÇÃO PENDENTE

### ⚠️ Problema Identificado

#### Servidor MCP - Autenticação OAuth 2.0 Falhando
- **Status**: ❌ Bloqueado - Servidor não funciona
- **Erro**: 401 "O Header Authorization é obrigatório para esta requisição"
- **Endpoint testado**: `https://api.sankhya.com.br/gateway/v1/authenticate`
- **Causa provável**: URL de autenticação incorreta

#### Investigação Realizada
- ✅ Pacote MCP instalado e funcionando (`import mcp.server` OK)
- ✅ Servidor MCP criado e estruturado corretamente
- ✅ Credenciais OAuth 2.0 configuradas no `.env`
- ❌ Autenticação falhando com erro 401

#### Diferença Crítica Encontrada
| Local | URL Autenticação |
|-------|------------------|
| Código MCP | `https://api.sankhya.com.br/gateway/v1/authenticate` |
| Postman | `{{base_url}}/authenticate` (valor de base_url desconhecido) |

### ✅ Adicionado

#### Scripts de Diagnóstico
- `test_mcp.py` - Script de teste do servidor MCP
  - Tenta executar query de divergências V3
  - Falhou com erro 401 (autenticação)
- `test_autenticacao.py` - Script de diagnóstico de autenticação
  - Testa OAuth 2.0 automaticamente
  - Oferece teste de MobileLogin interativo
  - Identifica qual método funciona
- `mcp_sankhya/.env` - Arquivo de credenciais criado

#### Documentação
- `PROXIMOS_PASSOS.md` - Guia rápido do próximo passo crítico
  - Instruções claras para usuário verificar URL no Postman
  - Checklist de ações necessárias

### 🎯 Próximos Passos (CRÍTICO)

#### Ação Necessária (Usuário)
1. Verificar variável `{{base_url}}` na collection Postman OAuth2
2. Executar request "1.1 Login (OAuth2)" no Postman
3. Informar qual URL completa aparece

#### Ação Após Confirmar URL
1. Corrigir `mcp_sankhya/server.py` (linha ~55)
2. Atualizar URL do endpoint de autenticação
3. Testar com `python test_mcp.py`
4. Validar que queries executam corretamente

### 📊 Análise

**Métodos de Autenticação Identificados:**

1. **MobileLogin** (Collection antiga)
   - URL: `https://api.sankhya.com.br/mge/service.sbr?serviceName=MobileLoginSP.login`
   - Autenticação: Usuário + Senha
   - Retorna: JSESSIONID (Cookie)

2. **OAuth 2.0** (Collection nova + MCP)
   - URL: `{{base_url}}/authenticate`
   - Autenticação: client_id + client_secret + X-Token
   - Retorna: Bearer token

**Usuário confirmou:** Usa OAuth 2.0 (método 2)

---

## [0.4.0] - 2026-02-01 🚀 SERVIDOR MCP

### ✅ Adicionado

#### Servidor MCP Sankhya
- Criado servidor MCP completo para integração com Claude Code
- 5 tools disponíveis:
  - `executar_query_sql` - Executa queries SQL customizadas
  - `executar_query_divergencias` - Query V3 de divergências (corrigida)
  - `executar_query_analise_produto` - Análise detalhada de produto
  - `gerar_relatorio_divergencias` - Geração automática de HTML
  - `listar_queries_disponiveis` - Lista queries do projeto
- Renovação automática de token (válido 23h)
- Tratamento de erros e timeouts configuráveis

#### Arquivos MCP
- `mcp_sankhya/server.py` - Servidor MCP principal (650+ linhas)
- `mcp_sankhya/requirements.txt` - Dependências (mcp, httpx)
- `mcp_sankhya/.env.example` - Template de configuração
- `mcp_sankhya/README.md` - Documentação completa do MCP
- `mcp_sankhya/install.bat` - Instalador automático Windows
- `GUIA_RAPIDO_MCP.md` - Guia rápido de uso

### 🎯 Benefícios
- ✅ Execução de queries diretamente na conversa com Claude
- ✅ Processamento automático de JSON
- ✅ Geração de relatórios sem sair do VS Code
- ✅ Elimina necessidade de Postman/scripts manuais
- ✅ Workflow completo: query → análise → relatório em 1 comando

---

## [0.3.0] - 2026-02-01 ⭐ CORREÇÃO DEFINITIVA

### 🐛 Corrigido

#### Query V3 Definitiva - SEM MULTIPLICAÇÃO
- **Problema identificado**: TGFEST sem GROUP BY causava multiplicação por CODLOCAL
- **Causa raiz**: Produto com estoque em múltiplos locais gerava N linhas (triplicação)
- **Solução**: Subquery com SUM() + GROUP BY no TGFEST (mesmo padrão do TGWEST)

#### Arquivos
- `query_divergencias_v3_definitiva.sql` - Query SQL corrigida DEFINITIVA
- `curl_divergencias_v3_definitiva.txt` - cURL para Postman V3
- Atualizado `PROGRESSO_SESSAO.md` com seção "Sessão 2026-02-01"

### ✅ Garantias V3
- ✅ TGFTOP: GROUP BY elimina duplicação por ATUALEST
- ✅ TGFEST: SUM() + GROUP BY elimina multiplicação por CODLOCAL
- ✅ TGWEST: SUM() + GROUP BY (já estava correto)
- ✅ Resultado: 1 linha única por CODPROD + NUNOTA
- ✅ Valores: Corretos (somas consolidadas)

### 📊 Histórico de Correções
| Versão | Problema | Status |
|--------|----------|--------|
| V1 | TGFTOP sem GROUP BY | ❌ Multiplicação 3x |
| V2 | TGFTOP corrigido, TGFEST sem GROUP BY | ⚠️ Ainda multiplica |
| V3 | TGFTOP + TGFEST ambos corrigidos | ✅ DEFINITIVA |

---

## [0.2.0] - 2026-01-31 📊 RELATÓRIOS HTML

### ✅ Adicionado

#### Relatórios HTML Interativos
- `relatorio_divergencias.html` - Template HTML com dashboard completo
- Design profissional (gradientes roxo/azul)
- Features: busca, ordenação, export CSV, print/PDF
- Responsivo (mobile-friendly)
- Dashboard com 4 KPIs

#### Scripts Python
- `converter_json_para_html.py` - Conversor JSON → HTML
- `gerar_relatorio.py` - Gerador interativo (cola JSON no terminal)
- Suporte para 14 campos (V1) e 15 campos com CODEMP (V2)
- Detecção automática de formato

#### Query de Análise Detalhada
- `query_analise_detalhada_produto.sql` - 200+ linhas com CTEs
- `curl_analise_detalhada_produto.txt` - cURL para Postman
- Calcula 8 camadas de disponibilidade:
  - ESTOQUE, RESERVADO, WMSBLOQUEADO
  - DISPONIVEL_COMERCIAL, SALDO_WMS_TELA
  - QTD_PEDIDO_PENDENTE, WMS_APOS_PEDIDOS
  - DISPONIVEL_REAL_FINAL

#### Documentação
- `README_RELATORIO.md` - Guia completo de uso dos relatórios

### 🔧 Modificado
- Adicionado campo `CODEMP` em todas as queries (agora 15 campos)
- Atualizado `query_divergencias_corrigida.sql` com CODEMP
- Atualizado `curl_divergencias_corrigida.txt` com CODEMP

### 📊 Análises Realizadas
- Produto 263340: 5.894 unidades de divergência
- Produto 261302: Disponível negativo (-157), crítico
- Identificados 100+ notas pendentes (STATUS='P')

---

## [0.1.0] - 2026-01-30

### ✅ Adicionado

#### Documentação
- Criado `CLAUDE.md` com instruções completas para o Claude
- Criado `PROGRESSO_SESSAO.md` para rastrear contexto entre sessões
- Criado `PLANO_MAPEAMENTO.md` com estratégia completa de mapeamento
- Criado `QUERIES_EXPLORACAO.sql` com 50+ queries organizadas
- Criado `docs/tabelas/TEMPLATE.md` como modelo de documentação

#### Estrutura do Projeto
- Criadas pastas: `docs/tabelas/`, `metadata/`, `src/extractors/`, `src/utils/`, `tests/`
- Estrutura base para futuro desenvolvimento

#### Mapeamento de Tabelas
- Documentadas tabelas de Compras: TGFCAB, TGFITE, TGFPAR, TGFPRO
- Documentada estrutura WMS: TGWREC, VGWRECSITCAB
- Identificadas 28 tabelas-alvo para mapeamento completo

### 📝 Documentado
- Relacionamentos entre tabelas principais
- Situações WMS (códigos -1 a 100)
- Query principal de extração de compras
- Estrutura do Data Lake (particionamento, formato Parquet)

### 🎯 Planejado
- Roadmap de 4 fases (Compras, Estoque, Vendas, Financeiro)
- Cronograma de 4 semanas para mapeamento completo
- Estratégia de metadata para ML/LLM

---

## [0.0.1] - 2026-01-27

### ✅ Adicionado (Pré-projeto)
- Configuração inicial do Postman
- Autenticação OAuth 2.0 com Sankhya
- Primeiras queries exploratórias
- Identificação de tabelas principais

### 📝 Documentado
- README.md inicial
- docs/de-para/sankhya/compras.md (versão inicial)
- docs/de-para/sankhya/wms.md
- docs/data-lake/estrutura.md

---

## Tipos de Mudanças

- `✅ Adicionado` - para novas funcionalidades
- `🔧 Modificado` - para mudanças em funcionalidades existentes
- `❌ Depreciado` - para funcionalidades que serão removidas
- `🗑️ Removido` - para funcionalidades removidas
- `🐛 Corrigido` - para correções de bugs
- `🔐 Segurança` - para correções de vulnerabilidades

---

**Última atualização:** 2026-02-05
