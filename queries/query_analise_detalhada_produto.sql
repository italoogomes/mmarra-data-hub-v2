-- =====================================================
-- 📊 Query de Análise Detalhada de Produto
-- =====================================================
-- Versão: 1.0
-- Data: 2026-01-30
-- Autor: Claude (baseado em query fornecida)
--
-- DESCRIÇÃO:
--     Calcula o disponível real final de um produto considerando
--     todas as camadas: estoque, reservas, bloqueios WMS, pedidos
--     pendentes, etc.
--
-- USO:
--     Altere os parâmetros na CTE "Parametros" para analisar
--     diferentes produtos/empresas.
-- =====================================================

WITH
-- 1. Parâmetros de entrada
Parametros AS (
    SELECT
        7       AS CODEMP,   -- ← ALTERE AQUI: Código da empresa
        261302  AS CODPROD   -- ← ALTERE AQUI: Código do produto
    FROM DUAL
),

-- 2. Dados da empresa (local de ajuste WMS)
Empresa AS (
    SELECT
        EMP.CODEMP,
        NVL(
            EMP.WMSLOCALAJEST,
            (SELECT INTEIRO FROM TSIPAR WHERE CHAVE = 'WMSLOCALAJEST')
        ) AS CODLOCAL_AJUSTE
    FROM TGFEMP EMP
    JOIN Parametros
      ON Parametros.CODEMP = EMP.CODEMP
),

-- 3. Saldo físico WMS (apenas endereços válidos)
SaldoWmsTela AS (
    SELECT
        SUM(NVL(ESTW.ESTOQUEVOLPAD - ESTW.SAIDPENDVOLPAD, 0)) AS SALDO_WMS_TELA
    FROM TGWEST ESTW
    JOIN TGWEND WEND
      ON WEND.CODEND = ESTW.CODEND
    JOIN TGFEMP EMP
      ON EMP.CODEMP = WEND.CODEMP
    JOIN Parametros
      ON Parametros.CODEMP  = EMP.CODEMP
     AND Parametros.CODPROD = ESTW.CODPROD
    JOIN Empresa
      ON Empresa.CODEMP = EMP.CODEMP
    WHERE EMP.UTILIZAWMS = 'S'                -- Empresa usa WMS
      AND WEND.BLOQUEADO = 'N'                -- Endereço não bloqueado
      AND WEND.EXCLCONF  = 'N'                -- Endereço não excluído da conferência
      AND NOT EXISTS (                         -- Não é doca de saída
            SELECT 1
            FROM TGWDCA DCA
            WHERE DCA.TIPDOCA = 'S'
              AND DCA.CODEND  = WEND.CODEND
      )
      AND ESTW.CONTROLE <> '#EXPLOTESEP'      -- Não é lote de separação
      AND NVL(
            EMP.WMSLOCALAJEST,
            (SELECT INTEIRO FROM TSIPAR WHERE CHAVE = 'WMSLOCALAJEST')
          ) = Empresa.CODLOCAL_AJUSTE
),

-- 4. Cabeçalhos de pedidos de venda pendentes
CabecalhosPV AS (
    SELECT
        CAB.NUNOTA
    FROM TGFCAB CAB
    JOIN Parametros
      ON Parametros.CODEMP = CAB.CODEMP
    WHERE CAB.CODTIPOPER IN (1007, 1017, 1018, 1019, 1020, 1023, 1024, 1025)  -- TOPs de venda
      AND CAB.PENDENTE   = 'S'                -- Nota pendente
      AND CAB.STATUSNOTA = 'L'                -- Nota liberada
),

-- 5. Quantidade de pedidos pendentes do produto
PedidosPendentes AS (
    SELECT
        NVL(SUM(NVL(ITE.QTDNEG, 0)), 0) AS QTD_PEDIDO_PENDENTE
    FROM TGFITE ITE
    JOIN CabecalhosPV CAB
      ON CAB.NUNOTA = ITE.NUNOTA
    JOIN Parametros
      ON Parametros.CODPROD = ITE.CODPROD
),

-- 6. Estoque comercial (ERP/TGFEST)
EstoqueComercial AS (
    SELECT
        SUM(NVL(EST.ESTOQUE, 0))      AS ESTOQUE,
        SUM(NVL(EST.RESERVADO, 0))    AS RESERVADO,
        SUM(NVL(EST.WMSBLOQUEADO, 0)) AS WMSBLOQUEADO
    FROM TGFEST EST
    JOIN Parametros
      ON Parametros.CODEMP  = EST.CODEMP
     AND Parametros.CODPROD = EST.CODPROD
    JOIN Empresa
      ON Empresa.CODEMP = EST.CODEMP
    WHERE EST.CODLOCAL = Empresa.CODLOCAL_AJUSTE
),

-- 7. Cálculos intermediários
Calc AS (
    SELECT
        ESTOQUE,
        RESERVADO,
        WMSBLOQUEADO,

        -- Disponível comercial teórico (ERP)
        (ESTOQUE - RESERVADO - WMSBLOQUEADO) AS DISPONIVEL_COMERCIAL,

        -- Saldo físico WMS
        NVL(SaldoWmsTela.SALDO_WMS_TELA, 0) AS SALDO_WMS_TELA,

        -- Pedidos de venda pendentes
        NVL(PedidosPendentes.QTD_PEDIDO_PENDENTE, 0) AS QTD_PEDIDO_PENDENTE,

        -- WMS após descontar pedidos pendentes
        GREATEST(
            NVL(SaldoWmsTela.SALDO_WMS_TELA, 0) - NVL(PedidosPendentes.QTD_PEDIDO_PENDENTE, 0),
            0
        ) AS WMS_APOS_PEDIDOS

    FROM EstoqueComercial
    CROSS JOIN SaldoWmsTela
    CROSS JOIN PedidosPendentes
)

-- 8. Resultado final
SELECT
    ESTOQUE,
    RESERVADO,
    WMSBLOQUEADO,
    DISPONIVEL_COMERCIAL,
    SALDO_WMS_TELA,
    QTD_PEDIDO_PENDENTE,
    WMS_APOS_PEDIDOS,

    -- Disponível real final = Menor entre disponível comercial e WMS após pedidos
    CASE
        WHEN DISPONIVEL_COMERCIAL <= 0 THEN 0
        ELSE LEAST(DISPONIVEL_COMERCIAL, WMS_APOS_PEDIDOS)
    END AS DISPONIVEL_REAL_FINAL

FROM Calc;

-- =====================================================
-- 📝 EXPLICAÇÃO DOS CAMPOS:
-- =====================================================
--
-- ESTOQUE:
--     Quantidade bruta na TGFEST (estoque comercial)
--
-- RESERVADO:
--     Quantidade reservada para outros processos
--
-- WMSBLOQUEADO:
--     Quantidade bloqueada no WMS (quarentena, etc)
--
-- DISPONIVEL_COMERCIAL:
--     ESTOQUE - RESERVADO - WMSBLOQUEADO
--     É o "disponível" que o ERP mostra
--
-- SALDO_WMS_TELA:
--     Saldo físico real no WMS
--     Soma de ESTOQUEVOLPAD - SAIDPENDVOLPAD
--     Apenas endereços válidos (não bloqueados, não docas saída)
--
-- QTD_PEDIDO_PENDENTE:
--     Pedidos de venda liberados mas não separados
--     TOPs: 1007, 1017, 1018, 1019, 1020, 1023, 1024, 1025
--
-- WMS_APOS_PEDIDOS:
--     SALDO_WMS_TELA - QTD_PEDIDO_PENDENTE
--     É quanto realmente tem no WMS após descontar pedidos
--
-- DISPONIVEL_REAL_FINAL:
--     Menor valor entre DISPONIVEL_COMERCIAL e WMS_APOS_PEDIDOS
--     É o disponível REAL para venda
--     Se DISPONIVEL_COMERCIAL <= 0, retorna 0
--
-- =====================================================
-- 🎯 CASOS DE USO:
-- =====================================================
--
-- 1. Debugar divergências de estoque
--    - Compare DISPONIVEL_COMERCIAL com SALDO_WMS_TELA
--    - Se diferentes, há divergência ERP ↔ WMS
--
-- 2. Entender bloqueios
--    - WMSBLOQUEADO mostra quanto está bloqueado
--    - RESERVADO mostra reservas de outros processos
--
-- 3. Impacto de pedidos pendentes
--    - QTD_PEDIDO_PENDENTE mostra demanda não atendida
--    - WMS_APOS_PEDIDOS mostra disponível real
--
-- 4. Validar cálculo de disponível
--    - DISPONIVEL_REAL_FINAL é o valor correto
--    - Considera todas as camadas de bloqueio
--
-- =====================================================
-- ⚠️ IMPORTANTE:
-- =====================================================
--
-- Esta query é PESADA! Usa múltiplas CTEs e JOINs.
-- Ideal para análise pontual de produtos específicos.
--
-- Para análise em massa, use a query de divergências
-- (query_divergencias_corrigida.sql)
--
-- =====================================================
