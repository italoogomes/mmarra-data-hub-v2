-- Performance de fornecedor (ranking de atrasos)
-- Query referencia para avaliar pontualidade dos fornecedores
-- Autor: Italo Gomes
-- Data: 2026-02-10
--
-- Uso:
--   Sem filtro: ranking dos 20 fornecedores com mais atrasos
--   Com filtro: descomentar linha AND UPPER(PAR.NOMEPARC) LIKE UPPER('%NOME%')
--   Mais pontuais: trocar ORDER BY para PERC_ATRASO ASC NULLS LAST
--
-- Metricas:
--   TOTAL_PEDIDOS = todos os pedidos do fornecedor (12 meses)
--   ENTREGUES = pedidos ja concluidos (PENDENTE='N')
--   PENDENTES = pedidos em aberto (PENDENTE='S')
--   ATRASADOS = pendentes com DTPREVENT < hoje
--   SEM_PREVISAO = pendentes sem data de previsao
--   PERC_ATRASO = % dos pendentes que estao atrasados
--   MEDIA_DIAS_PENDENTE = media de dias em aberto dos pedidos pendentes
--
-- Regras de negocio MMarra:
--   CODTIPOPER 1301 = Compra Estoque
--   CODTIPOPER 1313 = Compra Casada (vinculada a venda/empenho)
--   DTPREVENT = Previsao de entrega (pode ser NULL)
--   PENDENTE = 'S' = pedido com itens faltando

SELECT * FROM (
    SELECT
        PAR.CODPARC,
        PAR.NOMEPARC AS FORNECEDOR,
        COUNT(*) AS TOTAL_PEDIDOS,
        SUM(CASE WHEN CAB.PENDENTE = 'N' THEN 1 ELSE 0 END) AS ENTREGUES,
        SUM(CASE WHEN CAB.PENDENTE = 'S' THEN 1 ELSE 0 END) AS PENDENTES,
        SUM(CASE WHEN CAB.PENDENTE = 'S' AND CAB.DTPREVENT IS NOT NULL
                  AND CAB.DTPREVENT < TRUNC(SYSDATE) THEN 1 ELSE 0 END) AS ATRASADOS,
        SUM(CASE WHEN CAB.PENDENTE = 'S' AND CAB.DTPREVENT IS NULL
                  THEN 1 ELSE 0 END) AS SEM_PREVISAO,
        ROUND(
            SUM(CASE WHEN CAB.PENDENTE = 'S' AND CAB.DTPREVENT IS NOT NULL
                      AND CAB.DTPREVENT < TRUNC(SYSDATE) THEN 1 ELSE 0 END) * 100.0
            / NULLIF(SUM(CASE WHEN CAB.PENDENTE = 'S' THEN 1 ELSE 0 END), 0)
        , 1) AS PERC_ATRASO,
        ROUND(AVG(
            CASE WHEN CAB.PENDENTE = 'S'
                 THEN TRUNC(SYSDATE) - TRUNC(CAB.DTNEG)
            END
        ), 0) AS MEDIA_DIAS_PENDENTE
    FROM TGFCAB CAB
    JOIN TGFPAR PAR ON PAR.CODPARC = CAB.CODPARC
    WHERE CAB.CODTIPOPER IN (1301, 1313)
      AND CAB.STATUSNOTA <> 'C'
      AND CAB.DTNEG >= ADD_MONTHS(TRUNC(SYSDATE), -12)   -- Ultimos 12 meses
      --AND UPPER(PAR.NOMEPARC) LIKE UPPER('%NOME%')      -- Filtro de fornecedor
    GROUP BY PAR.CODPARC, PAR.NOMEPARC
    --HAVING SUM(CASE WHEN CAB.PENDENTE = 'S' THEN 1 ELSE 0 END) > 0  -- Apenas com pendentes
    ORDER BY ATRASADOS DESC, PERC_ATRASO DESC NULLS LAST
) WHERE ROWNUM <= 20
