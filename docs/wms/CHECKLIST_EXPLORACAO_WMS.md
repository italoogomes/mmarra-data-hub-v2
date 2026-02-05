# ✅ Checklist de Exploração - Estoque e WMS

**Data**: 2026-01-30
**Objetivo**: Mapear completamente estrutura de estoque e WMS

---

## 🔍 PARTE 1: Queries SQL (Execute no Oracle)

### Bloco A: Descoberta de Tabelas ⭐ PRIORIDADE

```sql
-- Query A1: Listar TODAS as tabelas WMS
SELECT TABLE_NAME, NUM_ROWS, TABLESPACE_NAME
FROM ALL_TABLES
WHERE TABLE_NAME LIKE '%WMS%'
   OR TABLE_NAME LIKE 'TCS%'
   OR TABLE_NAME LIKE 'TGW%'
ORDER BY TABLE_NAME;
```
- [ ] Executada
- [ ] Resultados salvos
- [ ] Identificadas tabelas relevantes

```sql
-- Query A2: Buscar tabelas com "SALDO" ou "END" no nome de coluna
SELECT DISTINCT TABLE_NAME, COLUMN_NAME
FROM ALL_TAB_COLUMNS
WHERE (COLUMN_NAME LIKE '%SALDO%' OR COLUMN_NAME LIKE '%END%')
  AND TABLE_NAME LIKE 'TG%'
ORDER BY TABLE_NAME, COLUMN_NAME;
```
- [ ] Executada
- [ ] Resultados salvos

---

### Bloco B: Estrutura de TGFEST

```sql
-- Query B1: Todas as colunas de TGFEST
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    DATA_LENGTH,
    DATA_PRECISION,
    DATA_SCALE,
    NULLABLE,
    DATA_DEFAULT,
    COLUMN_ID
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'TGFEST'
ORDER BY COLUMN_ID;
```
- [ ] Executada
- [ ] Resultados salvos

```sql
-- Query B2: Constraints de TGFEST
SELECT
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE,
    SEARCH_CONDITION,
    STATUS
FROM ALL_CONSTRAINTS
WHERE TABLE_NAME = 'TGFEST'
ORDER BY CONSTRAINT_TYPE;
```
- [ ] Executada

```sql
-- Query B3: Relacionamentos de TGFEST (FK)
SELECT
    'FK: ' || a.column_name || ' → ' || c_pk.table_name || '.' || b.column_name AS relacionamento
FROM all_cons_columns a
JOIN all_constraints c ON a.constraint_name = c.constraint_name
JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
JOIN all_cons_columns b ON c_pk.constraint_name = b.constraint_name
WHERE c.constraint_type = 'R'
  AND a.table_name = 'TGFEST';
```
- [ ] Executada

```sql
-- Query B4: Exemplo de dados TGFEST (produto 137216)
SELECT * FROM TGFEST WHERE CODPROD = 137216;
```
- [ ] Executada

---

### Bloco C: Estrutura de TGFRES (Reservas)

```sql
-- Query C1: Todas as colunas de TGFRES
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    DATA_LENGTH,
    NULLABLE,
    COLUMN_ID
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'TGFRES'
ORDER BY COLUMN_ID;
```
- [ ] Executada
- [ ] Resultados salvos

```sql
-- Query C2: Exemplo de reservas (produto 137216)
SELECT * FROM TGFRES
WHERE CODPROD = 137216
  AND ROWNUM <= 10;
```
- [ ] Executada

---

### Bloco D: Validação de Tabelas Importantes

```sql
-- Query D1: Verificar se tabelas existem
SELECT
    'TGFEST' AS TABELA,
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END AS STATUS,
    MAX(NUM_ROWS) AS QTD_REGISTROS
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFEST'
UNION ALL
SELECT 'TGFRES',
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END,
    MAX(NUM_ROWS)
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFRES'
UNION ALL
SELECT 'TGFSAL',
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END,
    MAX(NUM_ROWS)
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFSAL'
UNION ALL
SELECT 'TGFEND',
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END,
    MAX(NUM_ROWS)
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFEND'
UNION ALL
SELECT 'TGFMOV',
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END,
    MAX(NUM_ROWS)
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFMOV'
UNION ALL
SELECT 'TGWREC',
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END,
    MAX(NUM_ROWS)
FROM ALL_TABLES WHERE TABLE_NAME = 'TGWREC';
```
- [ ] Executada
- [ ] Resultados salvos

---

### Bloco E: Campos Customizados (AD_*)

```sql
-- Query E1: Listar campos AD_* em tabelas de estoque
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM ALL_TAB_COLUMNS
WHERE COLUMN_NAME LIKE 'AD_%'
  AND TABLE_NAME IN ('TGFEST', 'TGFRES', 'TGFMOV')
ORDER BY TABLE_NAME, COLUMN_NAME;
```
- [ ] Executada

---

## 📚 PARTE 2: Documentação WMS (Copiar do Site)

**Link**: https://ajuda.sankhya.com.br/hc/pt-br/sections/360007733394-WMS

### Tópico 1: Estrutura de Endereçamento
- [ ] Como funciona (Prédio/Rua/Nível/Apartamento)
- [ ] Tipos de endereço (picking, bulk, doca, quarentena)
- [ ] Tabelas envolvidas
- [ ] Regras de negócio

**Colar aqui:**
```
[INFORMAÇÕES COPIADAS]
```

---

### Tópico 2: Processo de Recebimento
- [ ] Fluxo: Nota → Recebimento → Conferência → Armazenagem
- [ ] Situações WMS (códigos e descrições)
- [ ] Quando o saldo é atualizado
- [ ] Integração TGFCAB → TGWREC

**Colar aqui:**
```
[INFORMAÇÕES COPIADAS]
```

---

### Tópico 3: Saldo de Estoque
- [ ] Diferença entre saldo TGFEST vs saldo WMS
- [ ] Como calcular disponível
- [ ] Quando usar cada um
- [ ] Regras de reserva

**Colar aqui:**
```
[INFORMAÇÕES COPIADAS]
```

---

### Tópico 4: Tabelas Principais do WMS
- [ ] Lista completa de tabelas
- [ ] Descrição de cada uma
- [ ] Relacionamentos

**Colar aqui:**
```
[INFORMAÇÕES COPIADAS]
```

---

### Tópico 5: Separação/Picking
- [ ] Como funciona
- [ ] Tabelas envolvidas
- [ ] Integração com pedidos

**Colar aqui:**
```
[INFORMAÇÕES COPIADAS]
```

---

## 🎯 PARTE 3: Análise e Documentação

### Após Coletar Tudo

- [ ] Consolidar resultados das queries em `estoque.md`
- [ ] Adicionar informações da documentação em `estoque.md`
- [ ] Criar seção "Tabelas WMS Mapeadas"
- [ ] Identificar qual tabela tem os 124 de estoque
- [ ] Criar diagrama de relacionamento (ERD)
- [ ] Atualizar `PROGRESSO_SESSAO.md`

---

## 📋 Template para Enviar Resultados

**Para queries SQL:**
```
Query [NOME]:
┌─────────────┬──────────┬─────────┐
│ CAMPO1      │ CAMPO2   │ CAMPO3  │
├─────────────┼──────────┼─────────┤
│ valor1      │ valor2   │ valor3  │
└─────────────┴──────────┴─────────┘

Ou simplesmente cole o resultado do SQL Developer/DBeaver
```

**Para documentação:**
```
Tópico: [NOME]

[Texto copiado da documentação]

Observações/Destaques:
- Ponto importante 1
- Ponto importante 2
```

---

## ⚡ Sugestão de Ordem

**Melhor sequência para fazer em paralelo:**

1. **Execute Query A1** (descobrir tabelas WMS) ← PRIMEIRO
2. **Copie Tópico 4** (lista de tabelas da doc) ← PARALELO
3. **Compare** se as tabelas encontradas batem com a doc
4. **Execute Queries B*** (TGFEST)
5. **Copie Tópico 3** (saldo de estoque)
6. **Execute Queries C*** (TGFRES)
7. **Copie Tópicos 1, 2, 5** restantes

---

## 📞 Como Me Enviar

Pode enviar de 3 formas:

**A) Por partes** (conforme for executando)
```
Executei Query A1, aqui está o resultado:
[resultado]
```

**B) Tudo junto no final**
```
Segue todas as queries executadas:
[todos os resultados]

E documentação copiada:
[textos da doc]
```

**C) Screenshots** (se preferir)
- Print dos resultados SQL
- Print das páginas da documentação

---

**Última atualização**: 2026-01-30
**Status**: 🔄 Aguardando resultados
