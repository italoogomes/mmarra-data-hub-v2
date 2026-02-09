# 📊 Estado Atual - MMarra Data Hub

**Versão:** v2.1.0
**Última Atualização:** 2026-02-09 (Sessão 4)
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

## 📝 Sessão 4 (2026-02-09) - Query Pendência Compras + Transferência data-hub

### 🎯 Objetivo
Criar relatório de pendência de compras e transferir conhecimento para o projeto `data-hub` (LLM Ollama).

### 🔍 Descobertas Críticas

#### 1. Campos Corretos vs Documentação

| Documentado (❌) | Real (✅) | Tabela | Como Descobrir |
|---|---|---|---|
| DTENTREGA | **DTPREVENT** | TGFCAB | `SELECT COLUMN_NAME FROM ALL_TAB_COLUMNS WHERE TABLE_NAME='TGFCAB' AND COLUMN_NAME LIKE '%PREV%'` |
| CODCOMPRADOR | **CODUSUCOMPRADOR** | TGFCAB | `SELECT COLUMN_NAME FROM ALL_TAB_COLUMNS WHERE TABLE_NAME='TGFCAB' AND COLUMN_NAME LIKE '%COMPR%'` |
| MARCA (texto) | **CODMARCA** → TGFMAR.CODIGO | TGFPRO | FK para TGFMAR |

#### 2. TGFMAR - Estrutura Completa

```sql
SELECT COLUMN_NAME FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'TGFMAR'
ORDER BY COLUMN_NAME
```

**Colunas:**
- `CODIGO` (PK)
- `DESCRICAO` (nome da marca, ex: DONALDSON)
- `AD_CODVEND` (FK → TGFVEN - comprador responsável)
- `AD_CONSIDLISTAFORN` (S/N)
- `AD_IDEXTERNO` (ID integração)

**Caminho comprador:** `TGFPRO.CODMARCA → TGFMAR.CODIGO → TGFMAR.AD_CODVEND → TGFVEN.CODVEND`

#### 3. CODTIPOPERs Específicos MMarra

- **1301** - Compra Casada (Empenho - vinculado a venda)
- **1313** - Entrega Futura (compra programada)

**Uso:** `CODTIPOPER IN (1301, 1313)` > `TIPMOV='O'` (mais preciso)

#### 4. TGFVAR - Agregação Obrigatória

**Problema:** Query retornava 16 linhas para pedido com 13 itens (atendimentos parciais multiplicavam).

**Solução:** Agregar ANTES do JOIN:

```sql
LEFT JOIN (
    SELECT V.NUNOTAORIG, V.SEQUENCIAORIG,
           SUM(V.QTDATENDIDA) AS TOTAL_ATENDIDO
    FROM TGFVAR V
    JOIN TGFCAB C ON C.NUNOTA = V.NUNOTA
    WHERE C.STATUSNOTA <> 'C'
    GROUP BY V.NUNOTAORIG, V.SEQUENCIAORIG
) V_AGG ...
```

### 📋 Query Final - Pendência de Compras

Arquivo: `queries/compras/pendencias_completo.sql` (a criar)

Características:
- Nível ITEM (porque filtra marca)
- TGFVAR agregado (pendência real)
- Comprador via TGFMAR.AD_CODVEND
- Valores corretos (ITE.VLRTOT)
- CODTIPOPER IN (1301, 1313)
- Ordenação por STATUS_ENTREGA (atrasados primeiro)

### 🔄 Transferência para data-hub

**3 arquivos atualizados no projeto LLM:**

1. `knowledge/glossario/sinonimos.md` (+15 linhas)
   - Seção "TOPs de Compra MMarra (CODTIPOPER)"
   - Regra: quando usar CODTIPOPER vs TIPMOV

2. `knowledge/sankhya/exemplos_sql.md` (+32 linhas)
   - Exemplo 22: Query completa pendência
   - Responde 5 perguntas simultaneamente

3. `knowledge/sankhya/tabelas/TGFCAB.md`
   - ✅ Verificado: CODUSUCOMPRADOR já documentado

**Sessão 24 documentada** no `data-hub/PROGRESSO.md`

### ✅ Próximos Passos

1. [ ] Atualizar `docs/de-para/sankhya/compras.md` com CODUSUCOMPRADOR
2. [ ] Criar `docs/de-para/sankhya/tgfmar.md`
3. [ ] Salvar query em `queries/compras/pendencias_completo.sql`
4. [ ] Testar LLM data-hub com melhorias (qwen3:8b)
5. [ ] Transferir futuras descobertas entre projetos

### 📝 Aprendizados

✅ Agregar TGFVAR sempre (evita multiplicação)
✅ ALL_TAB_COLUMNS quando doc estiver errada
✅ Projetos sincronizados (mmarra-data-hub-v2 descobre → data-hub treina)
✅ CODTIPOPER > TIPMOV (mais específico)
✅ Comprador via marca (TGFPRO → TGFMAR → TGFVEN)

---

## 📋 Sessão 5 (2026-02-09): Servidor Data Hub, Logo e Descoberta ITE.PENDENTE

### 🎯 Objetivo
- Acessar servidor data-hub (LLM) para testar conhecimento transferido
- Ajustar logo com fundo transparente
- Revisar queries de pendência e identificar problema com itens cancelados

### 🔍 Descobertas Críticas

#### 1. Servidor Data Hub na Porta Errada
**Problema:** Usuário tentou acessar `localhost:8080` mas servidor configurado para porta 8000.

**Solução:** Alterado `start.py` de `PORT = 8000` para `PORT = 8080`.

#### 2. Logo com Fundo Preto
**Problema:** Logo PNG com fundo preto no base64 do HTML.

**Solução:**
- Criado pasta `src/api/static/images/`
- Logo salva como `logo.png` (fundo transparente)
- HTML atualizado para `src="imagens/logo.png"` (3 locais)
- CSS ajustado: `background: white`, `border-radius`, `padding`

#### 3. NUNOTA vs NUMNOTA (Campo Pedido)
**Problema:** Query mostrando `NUNOTA` (ID interno 1185467) ao invés de `NUMNOTA` (número visível 168).

**Correção:**
```sql
-- ❌ ERRADO:
CAB.NUNOTA AS PEDIDO

-- ✅ CORRETO:
CAB.NUMNOTA AS PEDIDO
```

**Diferença:**
- `NUNOTA` = Chave primária (ID único interno)
- `NUMNOTA` = Número do pedido (visível ao usuário)

#### 4. 🔥 Descoberta CRÍTICA: ITE.PENDENTE = 'S'

**Problema Identificado:**
Usuário: "Quando eu corto um item do pedido e marco como não pendente, ele continua aparecendo na consulta. Ele nunca vai sumir porque nunca vai ser entregue!"

**Causa Raiz:**
Query calculava `QTD_PENDENTE = QTDNEG - TOTAL_ATENDIDO`. Se item cancelado/cortado:
- Nunca será entregue (`TOTAL_ATENDIDO` sempre 0)
- `QTD_PENDENTE` sempre > 0
- Aparece eternamente na consulta ❌

**Solução:**
```sql
WHERE ITE.PENDENTE = 'S'  -- CRÍTICO!
```

**Comportamento:**
- Quando usuário cancela/corta item → Sankhya marca `ITE.PENDENTE = 'N'`
- Query filtra por `ITE.PENDENTE = 'S'` → Itens cancelados não aparecem ✅

**Diferença entre campos:**
- `CAB.PENDENTE` = Pedido tem itens pendentes (nível cabeçalho)
- `ITE.PENDENTE` = Item específico está pendente (nível item)

### 📝 Arquivos Atualizados

#### mmarra-data-hub-v2 (este projeto)
- `PROGRESSO_ATUAL.md` - Documentação desta sessão

#### data-hub (projeto LLM)
- `start.py` - Porta 8080
- `src/api/static/index.html` - Logo externa + CSS
- `src/api/static/images/logo.png` - Logo nova (criada pelo usuário)
- `knowledge/sankhya/exemplos_sql.md` - 3 exemplos atualizados + nova regra

**Exemplos SQL Corrigidos:**
1. Exemplo 19 - Previsão entrega por marca (`+ ITE.PENDENTE = 'S'`)
2. Exemplo 20 - Itens pendentes por pedido (`+ I.PENDENTE = 'S'`)
3. Exemplo 22 - Pendentes por marca MMarra (`+ ITE.PENDENTE = 'S'`)

**Nova Regra Crítica Adicionada:**
Seção "ITE.PENDENTE para itens cancelados/cortados" explicando:
- Quando usar
- Por que usar
- O que acontece se não usar

### 🎯 Query Final de Pendência (Completa e Corrigida)

```sql
SELECT
    CAB.NUNOTA AS NUNOTA_PEDIDO,
    CAB.NUMNOTA AS PEDIDO,             -- ✅ Corrigido (era NUNOTA)
    CAB.DTNEG AS DT_PEDIDO,
    CAB.DTPREVENT AS PREVISAO_ENTREGA,
    CAB.APROVADO AS CONFIRMADO,
    PAR.NOMEPARC AS FORNECEDOR,
    VEN.APELIDO AS COMPRADOR,
    PRO.CODPROD,
    PRO.REFERENCIA,
    PRO.DESCRPROD AS PRODUTO,
    MAR.DESCRICAO AS MARCA,
    ITE.CODVOL AS UNIDADE,
    ITE.QTDNEG AS QTD_PEDIDA,
    NVL(V_AGG.TOTAL_ATENDIDO, 0) AS QTD_ATENDIDA,
    (ITE.QTDNEG - NVL(V_AGG.TOTAL_ATENDIDO, 0)) AS QTD_PENDENTE,
    ITE.VLRUNIT AS VLR_UNITARIO,
    ITE.VLRTOT AS VLR_TOTAL_PEDIDO,
    ROUND((ITE.QTDNEG - NVL(V_AGG.TOTAL_ATENDIDO, 0)) * ITE.VLRUNIT, 2) AS VLR_TOTAL_PENDENTE,
    TRUNC(SYSDATE) - TRUNC(CAB.DTNEG) AS DIAS_ABERTO,
    CASE
        WHEN CAB.DTPREVENT IS NULL THEN 'SEM PREVISÃO'
        WHEN CAB.DTPREVENT < SYSDATE THEN 'ATRASADO'
        WHEN CAB.DTPREVENT < SYSDATE + 7 THEN 'PRÓXIMO'
        ELSE 'NO PRAZO'
    END AS STATUS_ENTREGA
FROM TGFITE ITE
JOIN TGFCAB CAB ON CAB.NUNOTA = ITE.NUNOTA
JOIN TGFPRO PRO ON PRO.CODPROD = ITE.CODPROD
LEFT JOIN TGFPAR PAR ON PAR.CODPARC = CAB.CODPARC
LEFT JOIN TGFMAR MAR ON MAR.CODIGO = PRO.CODMARCA
LEFT JOIN TGFVEN VEN ON VEN.CODVEND = MAR.AD_CODVEND
LEFT JOIN (
    SELECT V.NUNOTAORIG, V.SEQUENCIAORIG,
           SUM(V.QTDATENDIDA) AS TOTAL_ATENDIDO
    FROM TGFVAR V
    JOIN TGFCAB C ON C.NUNOTA = V.NUNOTA
    WHERE C.STATUSNOTA <> 'C'
    GROUP BY V.NUNOTAORIG, V.SEQUENCIAORIG
) V_AGG ON V_AGG.NUNOTAORIG = ITE.NUNOTA
       AND V_AGG.SEQUENCIAORIG = ITE.SEQUENCIA
WHERE CAB.CODTIPOPER IN (1301, 1313)
  AND CAB.STATUSNOTA <> 'C'
  AND ITE.PENDENTE = 'S'               -- ✅ CRÍTICO: Exclui cancelados
  AND (ITE.QTDNEG - NVL(V_AGG.TOTAL_ATENDIDO, 0)) > 0
ORDER BY
    CASE
        WHEN CAB.DTPREVENT IS NULL THEN 1
        WHEN CAB.DTPREVENT < SYSDATE THEN 0
        WHEN CAB.DTPREVENT < SYSDATE + 7 THEN 2
        ELSE 3
    END,
    MAR.DESCRICAO,
    PRO.DESCRPROD
```

### 🔑 Aprendizados Chave

| Campo | Significado | Quando Muda |
|-------|-------------|-------------|
| **NUNOTA** | ID único interno (PK) | Nunca (chave primária) |
| **NUMNOTA** | Número do pedido visível | Número sequencial por tipo |
| **CAB.PENDENTE** | Pedido tem pendências | Atualizado pelo Sankhya (cabeçalho) |
| **ITE.PENDENTE** | Item está pendente | Usuário cancela → muda para 'N' |
| **TGFVAR.QTDATENDIDA** | Quantidade entregue | A cada entrega parcial |

**Regras Críticas:**
1. ✅ Sempre usar `NUMNOTA` para mostrar número de pedido ao usuário
2. ✅ Sempre usar `ITE.PENDENTE = 'S'` em queries de pendência de itens
3. ✅ Agregar TGFVAR antes do JOIN (evita multiplicação)
4. ✅ Usar `CODTIPOPER IN (1301, 1313)` para compras MMarra (mais preciso que `TIPMOV = 'O'`)

### 📍 Próximos Passos

1. ⏳ **Testar LLM** com conhecimento atualizado:
   - Instalar modelo: `ollama pull qwen3:8b`
   - Iniciar servidor: `python start.py` no projeto data-hub
   - Testar queries: "Quantos pedidos da marca X em aberto?"

2. ⏳ **Validar query final** com dados reais de produção

3. ⏳ **Documentar em queries/compras/**:
   - Salvar query final como `pendencias_completo_v2.sql`

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
