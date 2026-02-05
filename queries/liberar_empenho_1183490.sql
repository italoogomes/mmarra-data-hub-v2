-- =====================================================
-- LIBERAR EMPENHOS DO PEDIDO CANCELADO 1183490
-- =====================================================
-- Data: 2026-02-04
-- Motivo: Pedido 1183490 foi cancelado mas empenhos permaneceram
--         vinculados, impedindo o pedido 1192177 de empenhar
-- =====================================================

-- 1. VERIFICAR SITUACAO ATUAL (ANTES)
-- =====================================================
SELECT
    'ANTES' AS MOMENTO,
    NUNOTAPEDVEN,
    NUNOTA AS NUNOTA_COMPRA,
    CODPROD,
    QTDEMPENHO,
    PENDENTE
FROM TGWEMPE
WHERE NUNOTAPEDVEN = 1183490
ORDER BY CODPROD;

-- Resultado esperado: 8 registros

-- 2. FAZER BACKUP (SALVAR RESULTADO DESTA QUERY)
-- =====================================================
SELECT * FROM TGWEMPE WHERE NUNOTAPEDVEN = 1183490;

-- 3. DELETAR OS EMPENHOS DO PEDIDO CANCELADO
-- =====================================================
DELETE FROM TGWEMPE
WHERE NUNOTAPEDVEN = 1183490;

-- Resultado esperado: 8 rows deleted

-- 4. CONFIRMAR A TRANSACAO
-- =====================================================
COMMIT;

-- 5. VERIFICAR SE FOI REMOVIDO (DEPOIS)
-- =====================================================
SELECT
    'DEPOIS' AS MOMENTO,
    COUNT(*) AS QTD_EMPENHOS
FROM TGWEMPE
WHERE NUNOTAPEDVEN = 1183490;

-- Resultado esperado: 0

-- 6. VERIFICAR SE O PEDIDO 1192177 AGORA PODE EMPENHAR
-- =====================================================
SELECT
    i.CODPROD,
    i.QTDNEG,
    NVL(e.QTDEMPENHO, 0) AS QTDEMPENHO,
    i.QTDNEG - NVL(e.QTDEMPENHO, 0) AS FALTA_EMPENHAR
FROM TGFITE i
LEFT JOIN (
    SELECT CODPROD, SUM(QTDEMPENHO) AS QTDEMPENHO
    FROM TGWEMPE
    WHERE NUNOTAPEDVEN = 1192177
    GROUP BY CODPROD
) e ON e.CODPROD = i.CODPROD
WHERE i.NUNOTA = 1192177
ORDER BY i.CODPROD;

-- =====================================================
-- FIM
-- =====================================================
