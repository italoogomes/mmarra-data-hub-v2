# 📊 Estado Atual - MMarra Data Hub

**Versao:** v2.2.0
**Ultima Atualizacao:** 2026-02-10 (Sessao 9)
**Historico de Sessoes:** Ver `PROGRESSO_HISTORICO.md`
**Changelog:** Ver `CHANGELOG.md`

---

## ✅ O Que Esta Funcionando

### Infraestrutura
- [x] API Sankhya autenticando via OAuth2
- [x] Azure Data Lake configurado (container: datahub)
- [x] MCP Server para Claude Code (`mcp_sankhya/`)
- [x] Sistema de RAG com ~1500 chunks indexados
- [x] Arquivo `.env` configurado em `mcp_sankhya/.env`

### ETL (Agente Engenheiro)
- [x] Extracao: Vendas, Clientes, Produtos, Estoque, Vendedores
- [x] Transformacao: Limpeza e normalizacao
- [x] Carga: Upload para Data Lake em Parquet
- [x] Script: `scripts/extracao/extrair_vendas_completo.py` (extrai 175k+ registros)
- [x] Extractores com metodos de compatibilidade (`extrair()`, `salvar_parquet()`)

### Analise (Agente Analista)
- [x] KPIs de vendas, compras, estoque
- [x] Geracao de relatorios HTML
- [x] Templates em `src/agents/analyst/reports/templates/`
- [x] Dashboard Data Prep em `src/agents/analyst/dashboards/`

### Machine Learning (Agente Cientista)
- [x] Prophet para previsao de demanda
- [x] **10 modelos treinados** para TOP 10 produtos
- [x] Modelos salvos em `src/agents/scientist/models/demand/`
- [x] Script: `scripts/treinar_multiplos_modelos.py`

### Deteccao de Anomalias
- [x] Isolation Forest com classificacao de severidade
- [x] Gerador de alertas em 3 formatos (text, markdown, html)
- [x] Script: `scripts/detectar_anomalias.py`
- [x] Relatorios salvos em `output/reports/`

### Dashboard Web
- [x] Streamlit + Plotly
- [x] KPIs principais (faturamento, pedidos, ticket medio)
- [x] Graficos: vendas por dia, top produtos, curva ABC
- [x] Script: `python scripts/iniciar_dashboard.py`

### Chat IA (Agente LLM - data-hub)
- [x] Ollama qwen3:8b (com /no_think otimizado)
- [x] RAG com documentacao indexada
- [x] Tools: forecast_tool, kpi_tool
- [x] Login Sankhya (OAuth + MobileLogin) funcionando
- [x] Menu lateral com Chat IA e Relatorios
- [x] Sistema RBAC (4 perfis: Vendedor, Comprador, Gerente, Admin)
- [x] Tela de login com imagem de fundo e toggle de senha

---

## 📁 Dados Disponiveis

### Local (src/data/raw/)
| Dataset | Registros | Arquivo |
|---------|-----------|---------|
| Vendas | 175.620 | `vendas/vendas.parquet` |

### Azure Data Lake
| Dataset | Registros | Atualizacao |
|---------|-----------|-------------|
| Vendas | ~340.000 | Diaria |
| Clientes | ~57.000 | Diaria |
| Produtos | ~393.000 | Diaria |
| Estoque ERP | ~36.000 | Diaria |
| Estoque WMS | ~45.000 | Diaria |
| Vendedores | ~111 | Semanal |

---

## 🤖 Modelos Prophet Treinados

| Produto | Descricao | Previsao 30 dias | Tendencia |
|---------|-----------|------------------|-----------|
| 263340 | DIPS INDICADOR PORCA CH32 | 469 un | baixa |
| 306957 | PORCA RODA 22MM CH32 | 959 un | baixa |
| 305273 | DIPS INDICADOR CH33 VERDE | 2479 un | alta |
| 261301 | MOLA PATIM FREIO 132MM | 1691 un | baixa |
| 32007 | TUBO NYLON TECALON 8MM | 1136 un | baixa |
| 305277 | DIPS INDICADOR CH33 AMAR | 760 un | alta |
| 166756 | TRAVA ROLETE PATIM | 614 un | baixa |
| 32037 | INSERT TUBO 5/16 8MM | 387 un | alta |
| 32043 | INSERT TUBO OD 12mm | 467 un | estavel |
| 48352 | FLEXIVEL FREIO 3/8 1000MM | 927 un | baixa |

---

## 📊 Tabelas Sankhya Mapeadas

### Core (100% mapeadas)
| Tabela | Colunas | Descricao |
|--------|---------|-----------|
| TGFCAB | 422 | Cabecalho de notas |
| TGFITE | 231 | Itens das notas |
| TGFPRO | 426 | Produtos |
| TGFPAR | 299 | Parceiros |
| TGFEST | 24 | Estoque ERP |

### WMS (100% mapeadas)
| Tabela | Descricao |
|--------|-----------|
| TGWREC | Recebimento |
| TGWSEP | Separacao |
| TGWEMPE | Empenho |
| TGWEST | Estoque WMS |
| VGWRECSITCAB | View situacao |

---

## ⚠️ Problemas Conhecidos

| Problema | Workaround | Status |
|----------|------------|--------|
| Timeout em queries pesadas | Usar `ROWNUM < 1000` | Aberto |
| Alguns campos AD_* nao mapeados | Documentar conforme descobrir | Aberto |
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
python scripts/chat_ia.py "Qual o faturamento do mes?"

# MCP Server (VS Code)
python -m mcp_sankhya.server

# Data Hub LLM (projeto data-hub)
cd data-hub && python start.py
# Acesse: http://localhost:8080
```

---

## 📚 Documentacao Rapida

| Topico | Arquivo |
|--------|---------|
| Instrucoes para IA | `CLAUDE.md` |
| Historico sessoes | `PROGRESSO_HISTORICO.md` |
| API Sankhya | `docs/api/sankhya.md` |
| Mapeamento tabelas | `docs/de-para/sankhya/` |
| Status WMS | `docs/de-para/sankhya/wms.md` |
| Investigacoes | `docs/investigacoes/README.md` |
| Bugs conhecidos | `docs/bugs/` |

---

## 📋 Sessao 9 (2026-02-10): Login Sankhya Corrigido + RBAC + Melhorias Visuais

### 🎯 Objetivo
Corrigir login com credenciais reais do Sankhya, implementar sistema de permissoes RBAC e melhorias visuais na tela de login.

### ✅ Correcao Login Sankhya (4 bugs corrigidos)

**Bug 1: serviceName duplicado**
- Body JSON continha `serviceName` E URL tinha `serviceName` como param
- Solucao: Removido `serviceName` do body JSON

**Bug 2: Gateway exige OAuth**
- Erro GTW2510: "O Header Authorization e obrigatorio"
- Solucao: Obter token OAuth (client_id + client_secret) ANTES de chamar MobileLogin

**Bug 3: outputType=json faltando**
- Sankhya retornava XML em vez de JSON
- Solucao: Adicionado `outputType=json` nos params da URL

**Bug 4: URL incorreta**
- Usava `https://api.sankhya.com.br/mge/service.sbr` (sem gateway)
- Solucao: Corrigido para `https://api.sankhya.com.br/gateway/v1/mge/service.sbr`

**Fluxo final correto:**
```
1. POST /authenticate (OAuth client_credentials) → Bearer token
2. POST /gateway/v1/mge/service.sbr?serviceName=MobileLoginSP.login&outputType=json
   Headers: Authorization: Bearer {oauth_token}
   Body: { requestBody: { NOMUSU, INTERNO, KEEPCONNECTED } }
```

### ✅ Sistema RBAC (Role-Based Access Control)

**4 perfis implementados:**

| Perfil | Identificacao | Ve o que | Filtro SQL |
|--------|--------------|----------|------------|
| Vendedor | TGFVEN.TIPVEND = 'V' | So vendas dele | WHERE CODVEND = X |
| Comprador | TGFVEN.TIPVEND = 'C' | So compras dele | WHERE CODVEND = X |
| Gerente | Tem subordinados (CODGER) | Dados da equipe | WHERE CODVEND IN (...) |
| Admin | Lista fixa no .env | Tudo | Sem filtro |

**Backend (src/api/app.py):**
- `fetch_user_profile(username)` - Busca CODVEND, TIPVEND, CODGER na TGFVEN via DbExplorerSP
- `determine_role(username, profile)` - Logica: ADMIN_USERS → admin, tem subordinados → gerente, TIPVEND → vendedor/comprador
- `fetch_team_codvends(codvend)` - Lista CODVENDs da equipe do gerente
- `get_current_user()` - Retorna sessao completa (dict com role, codvend, etc)
- `/api/login` retorna `role` e `modules`
- `/api/me` retorna `role` e `modules`
- `/api/chat` passa `user_context` para o agente LLM

**Frontend (index.html):**
- localStorage guarda `datahub_role` e `datahub_modules`
- Sidebar mostra cargo (Vendedor/Comprador/Gerente/Administrador)
- Report cards com `data-module="compras"` ou `data-module="vendas"` filtrados por perfil

**LLM (src/llm/agent.py):**
- Camada 1 (Prompt): `_build_rbac_filter()` injeta instrucao obrigatoria no prompt SQL
- Camada 2 (Safety net): `_enforce_rbac_filter()` valida e envolve SQL com filtro CODVEND
- Vendedor tentando ver compras → LLM bloqueia
- Comprador tentando ver vendas → LLM bloqueia

**Configuracao (.env):**
- `ADMIN_USERS=ITALO` (lista de APELIDOs administradores)

### ✅ Melhorias Visuais (Tela de Login)

1. **Imagem de fundo** - `fundo01.jpg` na tela de login (cover, centralizado)
2. **Botao ver senha** - Icone SVG (olho aberto/fechado) profissional
3. **Cores ajustadas** - Fundo de preto (#0a0a0b) para cinza escuro (#1e1e22)
4. **Titulo** - "Centro de dados" em vez de "Data Hub"

### 📝 Arquivos Modificados

**data-hub (projeto LLM):**
- `src/api/app.py` - OAuth + MobileLogin corrigido + RBAC completo
- `src/llm/agent.py` - user_context + _build_rbac_filter + _enforce_rbac_filter
- `src/api/static/index.html` - Fundo, botao senha, cores, RBAC frontend
- `.env` - ADMIN_USERS=ITALO

---

## 🎯 Proximos Passos

### Prioridade Alta
1. [ ] **Implementar relatorio Pendencia de Compras** (primeiro relatorio real)
2. [ ] Testar RBAC com vendedor e comprador reais
3. [ ] Testar LLM na maquina pessoal (GPU)

### Prioridade Media
4. [ ] Sessao de testes com usuario real do time de compras
5. [ ] Criar avisos.md (limitacoes conhecidas)
6. [ ] Atingir 90/100 no checklist beta
7. [ ] Integrar Prophet e Anomalias com Agente LLM

### Prioridade Baixa
8. [ ] Agendamento automatico de ETL
9. [ ] Interface WhatsApp
10. [ ] Notificacoes automaticas

---

*Este arquivo contem apenas o estado atual e a sessao mais recente.*
*Para historico de sessoes anteriores (4-8), ver `PROGRESSO_HISTORICO.md`.*
*Para changelog completo, ver `CHANGELOG.md`.*
