# 📜 Historico de Sessoes - MMarra Data Hub

**Arquivo:** Historico completo de todas as sessoes de trabalho (1-8).
**Para estado atual:** Ver `PROGRESSO_ATUAL.md`
**Para changelog:** Ver `CHANGELOG.md`

---

## 📋 Sessao 4 (2026-02-09) - Query Pendencia Compras + Transferencia data-hub

### 🎯 Objetivo
Criar relatorio de pendencia de compras e transferir conhecimento para o projeto `data-hub` (LLM Ollama).

### 🔍 Descobertas Criticas

#### 1. Campos Corretos vs Documentacao

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
- `AD_CODVEND` (FK → TGFVEN - comprador responsavel)
- `AD_CONSIDLISTAFORN` (S/N)
- `AD_IDEXTERNO` (ID integracao)

**Caminho comprador:** `TGFPRO.CODMARCA → TGFMAR.CODIGO → TGFMAR.AD_CODVEND → TGFVEN.CODVEND`

#### 3. CODTIPOPERs Especificos MMarra

- **1301** - Compra Casada (Empenho - vinculado a venda)
- **1313** - Entrega Futura (compra programada)

**Uso:** `CODTIPOPER IN (1301, 1313)` > `TIPMOV='O'` (mais preciso)

#### 4. TGFVAR - Agregacao Obrigatoria

**Problema:** Query retornava 16 linhas para pedido com 13 itens (atendimentos parciais multiplicavam).

**Solucao:** Agregar ANTES do JOIN:

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

### 📋 Query Final - Pendencia de Compras

Arquivo: `queries/compras/pendencias_completo.sql` (a criar)

Caracteristicas:
- Nivel ITEM (porque filtra marca)
- TGFVAR agregado (pendencia real)
- Comprador via TGFMAR.AD_CODVEND
- Valores corretos (ITE.VLRTOT)
- CODTIPOPER IN (1301, 1313)
- Ordenacao por STATUS_ENTREGA (atrasados primeiro)

### 🔄 Transferencia para data-hub

**3 arquivos atualizados no projeto LLM:**

1. `knowledge/glossario/sinonimos.md` (+15 linhas)
   - Secao "TOPs de Compra MMarra (CODTIPOPER)"
   - Regra: quando usar CODTIPOPER vs TIPMOV

2. `knowledge/sankhya/exemplos_sql.md` (+32 linhas)
   - Exemplo 22: Query completa pendencia
   - Responde 5 perguntas simultaneamente

3. `knowledge/sankhya/tabelas/TGFCAB.md`
   - ✅ Verificado: CODUSUCOMPRADOR ja documentado

### 📝 Aprendizados

✅ Agregar TGFVAR sempre (evita multiplicacao)
✅ ALL_TAB_COLUMNS quando doc estiver errada
✅ Projetos sincronizados (mmarra-data-hub-v2 descobre → data-hub treina)
✅ CODTIPOPER > TIPMOV (mais especifico)
✅ Comprador via marca (TGFPRO → TGFMAR → TGFVEN)

---

## 📋 Sessao 5 (2026-02-09): Servidor Data Hub, Logo e Descoberta ITE.PENDENTE

### 🎯 Objetivo
- Acessar servidor data-hub (LLM) para testar conhecimento transferido
- Ajustar logo com fundo transparente
- Revisar queries de pendencia e identificar problema com itens cancelados

### 🔍 Descobertas Criticas

#### 1. Servidor Data Hub na Porta Errada
**Problema:** Usuario tentou acessar `localhost:8080` mas servidor configurado para porta 8000.

**Solucao:** Alterado `start.py` de `PORT = 8000` para `PORT = 8080`.

#### 2. Logo com Fundo Preto
**Problema:** Logo PNG com fundo preto no base64 do HTML.

**Solucao:**
- Criado pasta `src/api/static/images/`
- Logo salva como `logo.png` (fundo transparente)
- HTML atualizado para `src="imagens/logo.png"` (3 locais)
- CSS ajustado: `background: white`, `border-radius`, `padding`

#### 3. NUNOTA vs NUMNOTA (Campo Pedido)

**Campos:**
- `NUNOTA` = **Numero do PEDIDO** (usado como referencia pelos usuarios)
- `NUMNOTA` = Numero da **Nota Fiscal** (NF-e do fornecedor)

**Uso correto:**
```sql
-- ✅ CORRETO:
CAB.NUNOTA AS PEDIDO
```

#### 4. 🔥 Descoberta CRITICA: ITE.PENDENTE = 'S'

**Problema Identificado:**
Usuario: "Quando eu corto um item do pedido e marco como nao pendente, ele continua aparecendo na consulta. Ele nunca vai sumir porque nunca vai ser entregue!"

**Causa Raiz:**
Query calculava `QTD_PENDENTE = QTDNEG - TOTAL_ATENDIDO`. Se item cancelado/cortado:
- Nunca sera entregue (`TOTAL_ATENDIDO` sempre 0)
- `QTD_PENDENTE` sempre > 0
- Aparece eternamente na consulta ❌

**Solucao:**
```sql
WHERE ITE.PENDENTE = 'S'  -- CRITICO!
```

**Comportamento:**
- Quando usuario cancela/corta item → Sankhya marca `ITE.PENDENTE = 'N'`
- Query filtra por `ITE.PENDENTE = 'S'` → Itens cancelados nao aparecem ✅

**Diferenca entre campos:**
- `CAB.PENDENTE` = Pedido tem itens pendentes (nivel cabecalho)
- `ITE.PENDENTE` = Item especifico esta pendente (nivel item)

### 🔑 Aprendizados Chave

| Campo | Significado | Quando Muda |
|-------|-------------|-------------|
| **NUNOTA** | Numero do pedido (referencia do usuario) | Nunca (chave primaria) |
| **NUMNOTA** | Numero da nota fiscal (NF-e) | Numero sequencial por tipo |
| **CAB.PENDENTE** | Pedido tem pendencias | Atualizado pelo Sankhya (cabecalho) |
| **ITE.PENDENTE** | Item esta pendente | Usuario cancela → muda para 'N' |
| **TGFVAR.QTDATENDIDA** | Quantidade entregue | A cada entrega parcial |

**Regras Criticas:**
1. ✅ Sempre usar `NUNOTA` para mostrar numero de pedido ao usuario (NUMNOTA = nota fiscal)
2. ✅ Sempre usar `ITE.PENDENTE = 'S'` em queries de pendencia de itens
3. ✅ Agregar TGFVAR antes do JOIN (evita multiplicacao)
4. ✅ Usar `CODTIPOPER IN (1301, 1313)` para compras MMarra (mais preciso que `TIPMOV = 'O'`)

### 📝 Arquivos Atualizados

#### data-hub (projeto LLM)
- `start.py` - Porta 8080
- `src/api/static/index.html` - Logo externa + CSS
- `src/api/static/images/logo.png` - Logo nova (criada pelo usuario)
- `knowledge/sankhya/exemplos_sql.md` - 3 exemplos atualizados + nova regra

---

## 📋 Sessao 5 - Continuacao (2026-02-09): Fix Formatacao de Relatorios

### 🎯 Objetivo
Corrigir problema onde relatorios SQL estavam sendo exibidos como texto continuo (uma linha so) ao inves de tabela formatada.

### 🐛 Problema Identificado

**Sintoma:** Usuario reportou: "quando eu peco um relatorio ao inves dela me mandar o resultado em um planilha, ele monstra o resultado dos pedidos e dos itens tudo em uma linha so kkk"

**Analise:**
1. Python (`agent.py` linhas 688-713) **ja estava criando tabela markdown perfeita**
2. Mas o LLM (qwen3:8b) recebia essa tabela e ao tentar "reformatar", **destruia a estrutura**, juntando tudo em uma linha.

### ✅ Solucao Implementada

1. FORMATTER_PROMPT Simplificado - LLM apenas COPIA a tabela (nao reescreve)
2. System Prompt Reforcado - Instrucao CRITICA sobre preservar quebras de linha

### 🔑 Licao Aprendida

**❌ Problema:** Dar muita "liberdade criativa" ao LLM para formatar dados estruturados pode quebrar a formatacao.

**✅ Solucao:** Instrucao **IMPERATIVA** e **CLARA**: "COPIE EXATAMENTE" + "NAO modifique" + "Mantenha quebras de linha".

---

## 🚀 ANALISE DE READINESS & PLANO BETA

### Avaliacao de Prontidao (Sessao 25)

**Resultado da Analise:** **74/100 pontos - NAO PRONTO**

**Gaps Criticos Identificados:**
1. ❌ Falta exemplo SQL para pedidos **atrasados** (DTPREVENT < SYSDATE)
2. ❌ Falta exemplo SQL para **historico de compras por fornecedor**
3. ❌ Falta exemplo SQL para **analise de performance** de fornecedor (% atrasos)
4. ⚠️ Nenhum teste com usuarios reais do time de compras ainda

**Recomendacao:** **AGUARDAR 1-2 semanas** para adicionar conhecimento faltante

**Plano completo:** Ver `data-hub/PLANO_BETA.md`

**Meta:** Atingir 90/100 pontos antes do lancamento beta

---

## 📋 Sessao 6 (2026-02-10): Otimizacao LLM + Query Referencia Pendencia Itens

### 🎯 Objetivo
Otimizar performance do LLM Ollama (qwen3:8b) e adicionar query referencia para pendencia de itens/produtos.

### ✅ Otimizacao LLM (data-hub)

1. **Desabilitar Thinking Mode do Qwen3** - `/no_think` em todos os system prompts (reducao ~33% tempo)
2. **Parametros Ollama** - `num_predict: 2048` nas options
3. **Fix Timeout** - Removido `timeout=120` de todas as chamadas LLM (usa default 300s)
4. **Teste qwen3:4b** - 2x mais lento e menos preciso → Mantido qwen3:8b

### ✅ Query Referencia: Pendencia Detalhada por Item

**Nova Query (Exemplo 23):** `queries/compras/pendencia_itens_detalhada.sql`

**Diferenciais vs Exemplo 22:**
- Nivel ITEM (cada produto individual)
- TIPO_COMPRA (Casada=1313, Estoque=1301)
- CONFIRMADO via STATUSNOTA='L' (regra MMarra, nao campo APROVADO)
- COD_EMPRESA + NOME_EMPRESA
- AD_NUMFABRICANTE + AD_NUMORIGINAL
- Valores unitario e total pendente

### 📝 Arquivos Atualizados

**data-hub (projeto LLM):**
- `src/llm/agent.py` - /no_think em 5 chamadas + removido timeout=120
- `src/llm/llm_client.py` - num_predict: 2048
- `src/llm/chat.py` - /no_think no SYSTEM_PROMPT
- `knowledge/sankhya/exemplos_sql.md` - Exemplo 23 adicionado
- `knowledge/glossario/sinonimos.md` - Regra CONFIRMADO + termos item/produto

---

## 📋 Sessao 7 (2026-02-10): Exemplos SQL 24-25 (Fornecedores)

### 🎯 Objetivo
Adicionar os dois exemplos SQL faltantes do plano beta: historico de compras por fornecedor e performance/ranking de atrasos.

### ✅ Exemplo 24: Historico de compras por fornecedor

**Query referencia:** `queries/compras/historico_compras_fornecedor.sql`

**Caracteristicas:**
- Nivel CABECALHO (fornecedor = CODPARC em TGFCAB)
- TIPMOV IN ('C','O') = pedidos + notas de entrada (historico completo)
- LIKE com UPPER para busca parcial do nome
- STATUS traduz STATUSNOTA='L' como Confirmado (regra MMarra)
- Variante resumo por mes documentada em comentario

### ✅ Exemplo 25: Performance de fornecedor (ranking de atrasos)

**Query referencia:** `queries/compras/performance_fornecedor.sql`

**Metricas calculadas:**
- TOTAL_PEDIDOS, ENTREGUES, PENDENTES
- ATRASADOS (DTPREVENT < SYSDATE e PENDENTE='S')
- SEM_PREVISAO (DTPREVENT IS NULL e PENDENTE='S')
- PERC_ATRASO (% dos pendentes atrasados)
- MEDIA_DIAS_PENDENTE (media dias em aberto)

### ✅ Correcoes Adicionais (Sessao 7)

1. **NUNOTA vs NUMNOTA** - Corrigido em Exemplos 22, 24 e `historico_compras_fornecedor.sql`
2. **VLR_ATENDIDO adicionado** - Exemplos 22, 23 agora tem VLR_PEDIDO, VLR_ATENDIDO, VLR_PENDENTE
3. **Documentacao colunas de valor** - sinonimos.md com mapeamento "valor entregue" → VLR_ATENDIDO
4. **Exemplo 24: VLRNOTA corrigido** - Substituido por VLR_TOTAL_PEDIDO/ATENDIDO/PENDENTE com JOIN TGFITE+TGFVAR

### 📊 Status Plano Beta

**Exemplos SQL completos:** 25/25 ✅ (Semana 1 CONCLUIDA)

**Semana 2 (testes e ajustes):** PENDENTE
- [ ] Testes com usuario real do time de compras
- [ ] Criar avisos.md (limitacoes conhecidas)
- [ ] Validar acuracia 80%+
- [ ] Testar otimizacoes na maquina pessoal (GPU)

---

## 📋 Sessao 8 (2026-02-10): Tela de Login Sankhya + Menu Lateral

### 🎯 Objetivo
Adicionar autenticacao via Sankhya e menu lateral com area de relatorios ao data-hub web.

### ✅ Login com Sankhya MobileLogin

**Fluxo implementado:**
1. Usuario abre `http://localhost:8080` → ve tela de login
2. Digita usuario e senha do Sankhya
3. Backend chama `MobileLoginSP.login` na API Sankhya
4. Se valido → cria sessao local (token em memoria), retorna token
5. Frontend salva token no `localStorage`
6. Todas as requisicoes seguintes enviam `Authorization: Bearer {token}`
7. Sessao expira em 8 horas de inatividade

### ✅ Menu Lateral de Navegacao

**Layout:**
```
┌──────────┬──────────────────────────────────────┐
│ Logo     │  Header (titulo + status)             │
│          ├──────────────────────────────────────┤
│ Chat IA  │                                      │
│ Reports  │  CONTEUDO (Chat OU Relatorios)       │
│          │                                      │
│          ├──────────────────────────────────────┤
│ Usuario  │  Input area (so no chat)             │
│ Sair     │                                      │
└──────────┴──────────────────────────────────────┘
```

**Funcionalidades:**
- Sidebar fixa esquerda (220px)
- Navegacao entre Chat IA e Relatorios
- Nome do usuario logado no rodape
- Botao Sair (logout)
- Responsivo: sidebar esconde em mobile (< 768px) com hamburger menu

### ✅ Area de Relatorios (Placeholder)

**6 cards preparados para futuros relatorios:**
1. Pendencia de Compras
2. Historico por Fornecedor
3. Performance Fornecedores
4. Vendas por Periodo
5. Estoque Critico
6. Curva ABC

Todos com badge "Em breve" - serao ativados conforme implementados.

### ✅ Rotas Protegidas

Todas as rotas da API agora requerem autenticacao:
- `POST /api/chat` → requer Bearer token
- `POST /api/clear` → requer Bearer token
- `GET /api/status` → requer Bearer token
- `GET /` → serve HTML sem auth (JS controla tela de login)

**Novas rotas:**
- `POST /api/login` → autentica via Sankhya, retorna token
- `POST /api/logout` → remove sessao
- `GET /api/me` → valida token, retorna username

### 📝 Arquivos Modificados

**data-hub (projeto LLM):**
- `src/api/app.py` - Sessoes em memoria + rotas auth + protecao de rotas existentes
- `src/api/static/index.html` - Tela de login + sidebar navegacao + area relatorios + logica JS sessao

---

## 🔄 Mudancas na v2.1 (2026-02-05)

1. **Modelos Prophet expandidos** - 10 produtos treinados
2. **Deteccao de anomalias** - Isolation Forest funcionando
3. **Dashboard Streamlit** - Visualizacao de KPIs e graficos
4. **Scripts novos:**
   - `scripts/extracao/extrair_vendas_completo.py`
   - `scripts/treinar_multiplos_modelos.py`
   - `scripts/detectar_anomalias.py`
   - `scripts/iniciar_dashboard.py`
5. **Correcoes:**
   - Formato de data Sankhya (TO_CHAR)
   - Imports de extractors
   - Metodos de compatibilidade no BaseExtractor

---

*Este arquivo contem o historico de sessoes 4-8.*
*Para estado atual, ver `PROGRESSO_ATUAL.md`.*
*Para changelog completo, ver `CHANGELOG.md`.*
