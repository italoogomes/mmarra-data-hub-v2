-- =====================================================
-- QUERIES DE EXPLORAÇÃO - SANKHYA ERP
-- =====================================================
-- Objetivo: Mapear toda a estrutura do banco para treinar LLM
-- Data: 2026-01-30
-- Responsável: Ítalo Gomes
-- =====================================================

-- =====================================================
-- FASE 1: DESCOBERTA DE TABELAS
-- =====================================================

-- 1.1) Listar TODAS as tabelas do Sankhya (prefixo TG*)
SELECT TABLE_NAME, NUM_ROWS
FROM ALL_TABLES
WHERE TABLE_NAME LIKE 'TG%'
ORDER BY TABLE_NAME;

-- 1.2) Listar tabelas WMS
SELECT TABLE_NAME, NUM_ROWS
FROM ALL_TABLES
WHERE TABLE_NAME LIKE '%WMS%'
   OR TABLE_NAME LIKE 'TCS%'
   OR TABLE_NAME LIKE 'TGWSAL%'
ORDER BY TABLE_NAME;

-- 1.3) Listar views importantes
SELECT VIEW_NAME
FROM ALL_VIEWS
WHERE VIEW_NAME LIKE 'VG%'
   OR VIEW_NAME LIKE '%WMS%'
ORDER BY VIEW_NAME;

-- 1.4) Listar tabelas de cadastro (master data)
SELECT TABLE_NAME, NUM_ROWS
FROM ALL_TABLES
WHERE TABLE_NAME IN (
    'TGFPAR',  -- Parceiros (clientes/fornecedores)
    'TGFPRO',  -- Produtos
    'TGFGRU',  -- Grupos de produtos
    'TGFVEN',  -- Vendedores
    'TGFBAN',  -- Bancos
    'TGFNAT',  -- Naturezas financeiras
    'TGFTOP',  -- Tipos de operação
    'TGFCID',  -- Cidades
    'TGFUSU'   -- Usuários
)
ORDER BY TABLE_NAME;

-- 1.5) Listar tabelas transacionais (movimento)
SELECT TABLE_NAME, NUM_ROWS
FROM ALL_TABLES
WHERE TABLE_NAME IN (
    'TGFCAB',  -- Cabeçalho de notas
    'TGFITE',  -- Itens de notas
    'TGFMOV',  -- Movimentações de estoque
    'TGFFIN',  -- Financeiro (títulos)
    'TGFREC',  -- Recebimentos
    'TGFEST'   -- Estoque
)
ORDER BY TABLE_NAME;


-- =====================================================
-- FASE 2: ESTRUTURA DETALHADA (EXECUTAR PARA CADA TABELA)
-- =====================================================

-- 2.1) Ver TODAS as colunas de uma tabela
-- SUBSTITUA 'NOME_TABELA' pela tabela desejada
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
WHERE TABLE_NAME = 'NOME_TABELA'
ORDER BY COLUMN_ID;

-- Exemplo: TGFCAB
SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'TGFCAB'
ORDER BY COLUMN_ID;

-- Exemplo: TGFEST (estoque)
SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'TGFEST'
ORDER BY COLUMN_ID;

-- Exemplo: TGFRES (reservas)
SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'TGFRES'
ORDER BY COLUMN_ID;


-- 2.2) Ver constraints (PK, FK, UNIQUE, CHECK)
SELECT
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE,
    SEARCH_CONDITION,
    STATUS
FROM ALL_CONSTRAINTS
WHERE TABLE_NAME = 'NOME_TABELA'
ORDER BY CONSTRAINT_TYPE;

-- Legenda CONSTRAINT_TYPE:
-- 'P' = Primary Key
-- 'R' = Foreign Key (Referential)
-- 'U' = Unique
-- 'C' = Check


-- 2.3) Ver índices de uma tabela
SELECT
    INDEX_NAME,
    COLUMN_NAME,
    COLUMN_POSITION,
    DESCEND
FROM ALL_IND_COLUMNS
WHERE TABLE_NAME = 'NOME_TABELA'
ORDER BY INDEX_NAME, COLUMN_POSITION;


-- =====================================================
-- FASE 3: RELACIONAMENTOS (FOREIGN KEYS)
-- =====================================================

-- 3.1) Ver TODOS os relacionamentos entre tabelas TGF*
SELECT
    a.table_name AS tabela_origem,
    a.column_name AS coluna_origem,
    a.constraint_name AS fk_name,
    c_pk.table_name AS tabela_destino,
    b.column_name AS coluna_destino
FROM all_cons_columns a
JOIN all_constraints c ON a.constraint_name = c.constraint_name
JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
JOIN all_cons_columns b ON c_pk.constraint_name = b.constraint_name
WHERE c.constraint_type = 'R'
  AND a.table_name LIKE 'TGF%'
ORDER BY a.table_name, a.constraint_name;

-- 3.2) Ver relacionamentos de uma tabela específica
-- SUBSTITUA 'NOME_TABELA'
SELECT
    'FK: ' || a.column_name || ' → ' || c_pk.table_name || '.' || b.column_name AS relacionamento
FROM all_cons_columns a
JOIN all_constraints c ON a.constraint_name = c.constraint_name
JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
JOIN all_cons_columns b ON c_pk.constraint_name = b.constraint_name
WHERE c.constraint_type = 'R'
  AND a.table_name = 'NOME_TABELA'
ORDER BY a.column_name;

-- Exemplo: Relacionamentos de TGFCAB
SELECT
    'FK: ' || a.column_name || ' → ' || c_pk.table_name || '.' || b.column_name AS relacionamento
FROM all_cons_columns a
JOIN all_constraints c ON a.constraint_name = c.constraint_name
JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
JOIN all_cons_columns b ON c_pk.constraint_name = b.constraint_name
WHERE c.constraint_type = 'R'
  AND a.table_name = 'TGFCAB';

-- Exemplo: Relacionamentos de TGFITE
SELECT
    'FK: ' || a.column_name || ' → ' || c_pk.table_name || '.' || b.column_name AS relacionamento
FROM all_cons_columns a
JOIN all_constraints c ON a.constraint_name = c.constraint_name
JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
JOIN all_cons_columns b ON c_pk.constraint_name = b.constraint_name
WHERE c.constraint_type = 'R'
  AND a.table_name = 'TGFITE';


-- =====================================================
-- FASE 4: CAMPOS CUSTOMIZADOS (AD_*)
-- =====================================================

-- 4.1) Listar TODOS os campos AD_* do sistema
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    DATA_LENGTH
FROM ALL_TAB_COLUMNS
WHERE COLUMN_NAME LIKE 'AD_%'
  AND TABLE_NAME LIKE 'TG%'
ORDER BY TABLE_NAME, COLUMN_NAME;

-- 4.2) Ver descrição dos campos customizados (se existir TDDCAD)
SELECT
    NUMCAMPO,
    NOME AS CAMPO,
    DESCRICAO,
    TIPO
FROM TDDCAD
WHERE NOME LIKE 'AD_%'
ORDER BY NOME;

-- 4.3) Campos AD_* nas tabelas principais
SELECT TABLE_NAME, COLUMN_NAME
FROM ALL_TAB_COLUMNS
WHERE COLUMN_NAME LIKE 'AD_%'
  AND TABLE_NAME IN ('TGFCAB', 'TGFITE', 'TGFPAR', 'TGFPRO')
ORDER BY TABLE_NAME, COLUMN_NAME;


-- =====================================================
-- FASE 5: ANÁLISE DE DADOS (AMOSTRAGEM)
-- =====================================================

-- 5.1) Contar registros por tipo de movimento (TGFCAB)
SELECT
    TIPMOV,
    COUNT(*) AS QTD_NOTAS,
    MIN(DTNEG) AS PRIMEIRA_DATA,
    MAX(DTNEG) AS ULTIMA_DATA
FROM TGFCAB
GROUP BY TIPMOV
ORDER BY COUNT(*) DESC;

-- 5.2) Ver tipos de operação mais usados
SELECT
    t.CODTIPOPER,
    t.DESCROPER,
    COUNT(c.NUNOTA) AS QTD_NOTAS
FROM TGFCAB c
JOIN TGFTOP t ON c.CODTIPOPER = t.CODTIPOPER
GROUP BY t.CODTIPOPER, t.DESCROPER
ORDER BY COUNT(c.NUNOTA) DESC
FETCH FIRST 20 ROWS ONLY;

-- 5.3) Ver exemplo de dados (primeiras 5 linhas)
SELECT *
FROM TGFCAB
WHERE ROWNUM <= 5
ORDER BY NUNOTA DESC;

-- 5.4) Estatísticas de estoque
SELECT
    COUNT(DISTINCT CODPROD) AS PRODUTOS_COM_ESTOQUE,
    SUM(ESTOQUE) AS ESTOQUE_TOTAL,
    SUM(RESERVADO) AS RESERVADO_TOTAL,
    SUM(ESTOQUE - NVL(RESERVADO, 0)) AS DISPONIVEL_TOTAL
FROM TGFEST;


-- =====================================================
-- FASE 6: EXPLORAÇÃO ESPECÍFICA - ESTOQUE E WMS
-- =====================================================

-- 6.1) Ver estrutura completa de TGFEST
SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'TGFEST'
ORDER BY COLUMN_ID;

-- 6.2) Ver estrutura completa de TGFRES
SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'TGFRES'
ORDER BY COLUMN_ID;

-- 6.3) Buscar tabelas que possam ter saldo por endereço
SELECT TABLE_NAME, COLUMN_NAME
FROM ALL_TAB_COLUMNS
WHERE (COLUMN_NAME LIKE '%END%' OR COLUMN_NAME LIKE '%SALDO%')
  AND TABLE_NAME LIKE 'TG%'
ORDER BY TABLE_NAME, COLUMN_NAME;

-- 6.4) Tabelas relacionadas a movimentação de estoque
SELECT TABLE_NAME
FROM ALL_TABLES
WHERE TABLE_NAME LIKE 'TGFMOV%'
   OR TABLE_NAME LIKE 'TGWEST%'
   OR TABLE_NAME LIKE '%ESTOQUE%'
ORDER BY TABLE_NAME;

-- 6.5) Ver exemplo de produto com estoque (TGFEST)
SELECT *
FROM TGFEST
WHERE CODPROD = 137216;  -- Produto do exemplo anterior

-- 6.6) Ver exemplo de reservas (TGFRES)
SELECT *
FROM TGFRES
WHERE CODPROD = 137216
  AND ROWNUM <= 10;


-- =====================================================
-- FASE 7: EXPLORAÇÃO ESPECÍFICA - WMS
-- =====================================================

-- 7.1) Listar TODAS as tabelas WMS
SELECT TABLE_NAME, NUM_ROWS, TABLESPACE_NAME
FROM ALL_TABLES
WHERE TABLE_NAME LIKE '%WMS%'
   OR TABLE_NAME LIKE 'TCS%'
   OR TABLE_NAME LIKE 'TGW%'
ORDER BY TABLE_NAME;

-- 7.2) Ver estrutura de TGWREC (recebimento WMS)
SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'TGWREC'
ORDER BY COLUMN_ID;

-- 7.3) Ver views de WMS
SELECT VIEW_NAME, TEXT_LENGTH
FROM ALL_VIEWS
WHERE VIEW_NAME LIKE '%WMS%'
   OR VIEW_NAME LIKE 'VGW%'
ORDER BY VIEW_NAME;

-- 7.4) Ver situações WMS disponíveis (TDDOPC)
SELECT
    OPCAO AS COD_SITUACAO,
    DESCRICAO
FROM TDDOPC
WHERE NUCAMPO = 65738  -- Campo de situação WMS
ORDER BY OPCAO;

-- 7.5) Exemplo de nota com situação WMS
SELECT
    c.NUNOTA,
    c.NUMNOTA,
    c.DTNEG,
    wms.COD_SITUACAO
FROM TGFCAB c
LEFT JOIN VGWRECSITCAB wms ON c.NUNOTA = wms.NUNOTA
WHERE c.TIPMOV = 'C'
  AND ROWNUM <= 10
ORDER BY c.NUNOTA DESC;


-- =====================================================
-- FASE 8: VALIDAÇÃO DE COMPLETUDE
-- =====================================================

-- 8.1) Verificar se todas as tabelas principais existem
SELECT
    'TGFCAB' AS TABELA,
    CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END AS STATUS
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFCAB'
UNION ALL
SELECT 'TGFITE', CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFITE'
UNION ALL
SELECT 'TGFPAR', CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFPAR'
UNION ALL
SELECT 'TGFPRO', CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFPRO'
UNION ALL
SELECT 'TGFEST', CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFEST'
UNION ALL
SELECT 'TGFRES', CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFRES'
UNION ALL
SELECT 'TGFSAL', CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END
FROM ALL_TABLES WHERE TABLE_NAME = 'TGFSAL'
UNION ALL
SELECT 'TGWREC', CASE WHEN COUNT(*) > 0 THEN '✅ Existe' ELSE '❌ Não existe' END
FROM ALL_TABLES WHERE TABLE_NAME = 'TGWREC';


-- =====================================================
-- FASE 9: METADATA PARA LLM (EXPORTAR PARA JSON)
-- =====================================================

-- 9.1) Schema completo de uma tabela (formato para JSON)
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    NULLABLE,
    COLUMN_ID,
    DATA_LENGTH
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'TGFCAB'
ORDER BY COLUMN_ID;

-- 9.2) Relacionamentos em formato estruturado
SELECT
    a.table_name || '.' || a.column_name AS source,
    c_pk.table_name || '.' || b.column_name AS target,
    'foreign_key' AS relationship_type
FROM all_cons_columns a
JOIN all_constraints c ON a.constraint_name = c.constraint_name
JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
JOIN all_cons_columns b ON c_pk.constraint_name = b.constraint_name
WHERE c.constraint_type = 'R'
  AND a.table_name LIKE 'TGF%'
ORDER BY a.table_name;

-- 9.3) Estatísticas de cardinalidade
SELECT
    TABLE_NAME,
    NUM_ROWS,
    BLOCKS,
    AVG_ROW_LEN,
    LAST_ANALYZED
FROM ALL_TABLES
WHERE TABLE_NAME IN ('TGFCAB', 'TGFITE', 'TGFPAR', 'TGFPRO', 'TGFEST')
ORDER BY NUM_ROWS DESC;


-- =====================================================
-- NOTAS IMPORTANTES
-- =====================================================

/*
ORDEM DE EXECUÇÃO RECOMENDADA:

1. Execute FASE 1 completa - para descobrir o que existe
2. Para cada tabela importante, execute FASE 2 - estrutura detalhada
3. Execute FASE 3 - para mapear relacionamentos
4. Execute FASE 4 - para identificar campos customizados
5. Execute FASE 6 e 7 - foco em estoque e WMS
6. Execute FASE 8 - validação
7. Use FASE 9 - para exportar metadados

DICAS:
- Salve os resultados em arquivos .csv ou .xlsx
- Documente cada tabela em docs/tabelas/NOME_TABELA.md
- Crie diagrams ERD com as descobertas
- Atualize metadata/database_schema.json

ATENÇÃO:
- Queries podem demorar em bancos grandes
- Use ROWNUM ou FETCH FIRST para limitar resultados
- Sempre teste com ROWNUM <= 10 antes de rodar completo
*/

-- =====================================================
-- FIM DO ARQUIVO
-- =====================================================
