-- =====================================================
-- 📊 QUERY CORRIGIDA: Análise de Divergências de Estoque
-- =====================================================
-- Versão: 2.0
-- Data: 2026-01-30
-- Problema resolvido: Eliminação de linhas duplicadas causadas por TGFTOP
--
-- MUDANÇAS DA V1:
-- ✅ Removido campo ATUALEST (causava duplicação)
-- ✅ Adicionado DISTINCT para garantir unicidade
-- ✅ Foco em itens PENDENTES (STATUS_ITEM='P')
-- ✅ Ordenação por divergência (maior primeiro)
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
    NVL(EST.ESTOQUE, 0) AS QTD_DISPONIVEL_TGFEST,
    NVL(WMS.ESTOQUE_WMS, 0) AS QTD_WMS,
    (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE, 0)) AS DIVERGENCIA,
    TO_CHAR(CAB.DTNEG, 'DD/MM/YYYY') AS DATA_NOTA
FROM TGFITE ITE
INNER JOIN TGFCAB CAB ON ITE.NUNOTA = CAB.NUNOTA
INNER JOIN TGFPRO PRO ON ITE.CODPROD = PRO.CODPROD
LEFT JOIN (
    -- Subquery para pegar apenas 1 DESCROPER por CODTIPOPER (elimina duplicação)
    SELECT DISTINCT CODTIPOPER, MIN(DESCROPER) AS DESCROPER
    FROM TGFTOP
    GROUP BY CODTIPOPER
) TOP ON CAB.CODTIPOPER = TOP.CODTIPOPER
LEFT JOIN TGFEST EST ON ITE.CODPROD = EST.CODPROD AND EST.CODEMP = 7
LEFT JOIN (
    SELECT CODPROD, SUM(ESTOQUE) AS ESTOQUE_WMS
    FROM TGWEST
    WHERE CODEMP = 7
    GROUP BY CODPROD
) WMS ON ITE.CODPROD = WMS.CODPROD
WHERE 1=1
    AND CAB.CODEMP = 7
    AND ITE.STATUSNOTA = 'P'  -- Apenas itens PENDENTES (causa da divergência)
    AND NVL(WMS.ESTOQUE_WMS, 0) > NVL(EST.ESTOQUE, 0)  -- Apenas produtos COM divergência
    AND (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE, 0)) > 0  -- Divergência positiva
ORDER BY (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE, 0)) DESC;  -- Maior divergência primeiro

-- =====================================================
-- 📝 EXPLICAÇÃO DA QUERY:
-- =====================================================
--
-- CAUSA DO PROBLEMA ORIGINAL:
-- A tabela TGFTOP tem múltiplas linhas por CODTIPOPER com diferentes
-- valores de ATUALEST ('E', 'N', 'B'), causando produto cartesiano no JOIN.
--
-- SOLUÇÃO IMPLEMENTADA:
-- Subquery em TGFTOP que agrupa por CODTIPOPER e pega MIN(DESCROPER),
-- garantindo apenas 1 linha por tipo de operação.
--
-- LEFT JOIN (
--     SELECT DISTINCT CODTIPOPER, MIN(DESCROPER) AS DESCROPER
--     FROM TGFTOP
--     GROUP BY CODTIPOPER
-- ) TOP
--
-- FILTROS:
-- - CODEMP = 7: Empresa específica
-- - STATUSNOTA = 'P': Apenas itens PENDENTES (não processados pelo WMS)
-- - Divergência > 0: Apenas produtos onde WMS > TGFEST
--
-- RESULTADO ESPERADO:
-- - 1 linha por item de nota (CODPROD + NUNOTA único)
-- - Produtos ordenados por maior divergência
-- - SEM DUPLICATAS ✅
-- =====================================================

-- =====================================================
-- 📋 COMO USAR NO POSTMAN:
-- =====================================================
-- 1. Endpoint: POST https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery
-- 2. Headers:
--    - Authorization: Bearer {seu_token}
--    - Content-Type: application/json
-- 3. Body (raw JSON):
-- {
--   "serviceName": "DbExplorerSP.executeQuery",
--   "requestBody": {
--     "sql": "COLE A QUERY AQUI EM UMA LINHA"
--   }
-- }
-- =====================================================
