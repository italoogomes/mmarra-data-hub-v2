-- =====================================================
-- 📊 QUERY CORRIGIDA V3: Análise de Divergências de Estoque
-- =====================================================
-- Versão: 3.0 (DEFINITIVA - SEM MULTIPLICAÇÃO)
-- Data: 2026-02-01
-- Problema resolvido: Eliminação de TODAS as fontes de duplicação
--
-- MUDANÇAS DA V2:
-- ✅ TGFEST agora usa SUM() com GROUP BY (corrige multiplicação por CODLOCAL)
-- ✅ TGWEST já estava correto (SUM com GROUP BY)
-- ✅ TGFTOP já estava correto (GROUP BY)
-- ✅ Resultado: 1 linha única por CODPROD + NUNOTA
-- =====================================================

SELECT
    CAB.CODEMP,
    ITE.CODPROD,
    PRO.DESCRPROD,
    PRO.REFERENCIA,
    ITE.NUNOTA,
    CAB.NUMNOTA,
    CAB.CODTIPOPER AS TOP,
    TOP.DESCROPER AS DESCR_TOP,
    ITE.QTDNEG AS QTD_NOTA,
    ITE.STATUSNOTA AS STATUS_ITEM,
    CAB.STATUSNOTA AS STATUS_CAB,
    NVL(EST.ESTOQUE_TGFEST, 0) AS QTD_DISPONIVEL_TGFEST,
    NVL(WMS.ESTOQUE_WMS, 0) AS QTD_WMS,
    (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE_TGFEST, 0)) AS DIVERGENCIA,
    TO_CHAR(CAB.DTNEG, 'DD/MM/YYYY') AS DATA_NOTA
FROM TGFITE ITE
INNER JOIN TGFCAB CAB ON ITE.NUNOTA = CAB.NUNOTA
INNER JOIN TGFPRO PRO ON ITE.CODPROD = PRO.CODPROD

-- 🔧 TGFTOP: Subquery para evitar duplicação por ATUALEST
LEFT JOIN (
    SELECT DISTINCT CODTIPOPER, MIN(DESCROPER) AS DESCROPER
    FROM TGFTOP
    GROUP BY CODTIPOPER
) TOP ON CAB.CODTIPOPER = TOP.CODTIPOPER

-- 🔧 TGFEST: Subquery com SUM para evitar duplicação por CODLOCAL
LEFT JOIN (
    SELECT
        CODPROD,
        CODEMP,
        SUM(NVL(ESTOQUE, 0)) AS ESTOQUE_TGFEST
    FROM TGFEST
    WHERE CODEMP = 7
    GROUP BY CODPROD, CODEMP
) EST ON ITE.CODPROD = EST.CODPROD AND EST.CODEMP = CAB.CODEMP

-- 🔧 TGWEST: Subquery com SUM para consolidar estoque físico
LEFT JOIN (
    SELECT
        CODPROD,
        SUM(NVL(ESTOQUE, 0)) AS ESTOQUE_WMS
    FROM TGWEST
    WHERE CODEMP = 7
    GROUP BY CODPROD
) WMS ON ITE.CODPROD = WMS.CODPROD

WHERE 1=1
    AND CAB.CODEMP = 7
    AND ITE.STATUSNOTA = 'P'  -- Apenas itens PENDENTES
    AND NVL(WMS.ESTOQUE_WMS, 0) > NVL(EST.ESTOQUE_TGFEST, 0)  -- Divergência positiva
    AND (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE_TGFEST, 0)) > 0

ORDER BY (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE_TGFEST, 0)) DESC;

-- =====================================================
-- 📝 EXPLICAÇÃO DAS CORREÇÕES:
-- =====================================================
--
-- PROBLEMA DA V2:
-- LEFT JOIN TGFEST EST ON ITE.CODPROD = EST.CODPROD AND EST.CODEMP = 7
--
-- Se o produto 137216 tem:
-- - 100 unidades no CODLOCAL 1
-- - 50 unidades no CODLOCAL 2
-- - 30 unidades no CODLOCAL 3
--
-- O JOIN retornava 3 linhas para cada item de nota!
-- Total de 180 unidades, mas distribuído em 3 linhas.
--
-- SOLUÇÃO V3:
-- LEFT JOIN (
--     SELECT CODPROD, CODEMP, SUM(ESTOQUE) AS ESTOQUE_TGFEST
--     FROM TGFEST
--     WHERE CODEMP = 7
--     GROUP BY CODPROD, CODEMP
-- ) EST
--
-- Agora retorna:
-- - 1 linha com 180 unidades totais
-- - SEM MULTIPLICAÇÃO ✅
--
-- =====================================================
-- 🎯 RESULTADO ESPERADO:
-- =====================================================
--
-- ✅ 1 linha única por CODPROD + NUNOTA
-- ✅ ESTOQUE_TGFEST = soma de todos os locais
-- ✅ ESTOQUE_WMS = soma de todos os endereços
-- ✅ SEM DUPLICATAS
-- ✅ SEM TRIPLICATAS
-- ✅ SEM MULTIPLICAÇÃO
--
-- =====================================================
-- 🔍 COMO VALIDAR SE ESTÁ CORRETO:
-- =====================================================
--
-- 1. Execute a query
-- 2. Escolha um NUNOTA qualquer do resultado
-- 3. Execute esta validação:
--
-- SELECT COUNT(*)
-- FROM (RESULTADO DA QUERY)
-- WHERE NUNOTA = 1171669  -- Substitua pelo NUNOTA escolhido
--
-- Resultado esperado:
-- - Se o NUNOTA tem 1 item: COUNT(*) = 1
-- - Se o NUNOTA tem 3 itens: COUNT(*) = 3
-- - NUNCA deve ter múltiplas linhas para o mesmo CODPROD + NUNOTA
--
-- =====================================================
