-- Historico de compras por fornecedor
-- Query referencia para listar pedidos e notas de entrada de um fornecedor
-- Autor: Italo Gomes
-- Data: 2026-02-10
--
-- Uso:
--   Trocar '%DONALDSON%' pelo nome do fornecedor desejado
--   Ajustar periodo: -6 (meses), -12 (ano), etc
--   Para apenas pedidos: trocar TIPMOV IN ('C','O') por TIPMOV = 'O'
--   Para CODTIPOPERs MMarra: AND CAB.CODTIPOPER IN (1301, 1313)
--
-- Regras de negocio MMarra:
--   TIPMOV 'O' = Pedido de Compra
--   TIPMOV 'C' = Nota de Entrada (ja recebida)
--   STATUSNOTA = 'L' = Confirmado (regra MMarra)
--   STATUSNOTA <> 'C' = Exclui cancelados
--   Fornecedor = TGFPAR via CODPARC (nivel cabecalho)
--
-- Colunas de valor:
--   VLR_TOTAL_PEDIDO = valor total pedido (SUM dos itens)
--   VLR_TOTAL_ATENDIDO = valor ja entregue/recebido
--   VLR_TOTAL_PENDENTE = valor faltando entregar
--   Para TIPMOV='C' (nota entrada): tudo atendido (mercadoria ja recebida)
--   Para TIPMOV='O' (pedido): usa TGFVAR para entregas parciais

SELECT * FROM (
    SELECT
        CAB.NUNOTA AS PEDIDO,
        TO_CHAR(CAB.DTNEG, 'DD/MM/YYYY') AS DT_PEDIDO,
        CASE CAB.TIPMOV
            WHEN 'O' THEN 'Pedido'
            WHEN 'C' THEN 'Nota Entrada'
        END AS TIPO,
        CAB.CODTIPOPER,
        PAR.CODPARC,
        PAR.NOMEPARC AS FORNECEDOR,
        SUM(ITE.VLRTOT) AS VLR_TOTAL_PEDIDO,
        SUM(
            CASE WHEN CAB.TIPMOV = 'C' THEN ITE.VLRTOT
                 ELSE ROUND(NVL(V_AGG.TOTAL_ATENDIDO, 0) * ITE.VLRUNIT, 2)
            END
        ) AS VLR_TOTAL_ATENDIDO,
        SUM(
            CASE WHEN CAB.TIPMOV = 'C' THEN 0
                 ELSE ROUND((ITE.QTDNEG - NVL(V_AGG.TOTAL_ATENDIDO, 0)) * ITE.VLRUNIT, 2)
            END
        ) AS VLR_TOTAL_PENDENTE,
        CASE WHEN CAB.STATUSNOTA = 'L' THEN 'Confirmado' ELSE 'Pendente' END AS STATUS,
        CASE CAB.PENDENTE WHEN 'S' THEN 'Sim' ELSE 'Nao' END AS PENDENTE,
        NVL(TO_CHAR(CAB.DTPREVENT, 'DD/MM/YYYY'), '-') AS PREVISAO,
        VEN.APELIDO AS COMPRADOR,
        EMP.NOMEFANTASIA AS EMPRESA
    FROM TGFCAB CAB
    JOIN TGFPAR PAR ON PAR.CODPARC = CAB.CODPARC
    JOIN TSIEMP EMP ON EMP.CODEMP = CAB.CODEMP
    JOIN TGFITE ITE ON ITE.NUNOTA = CAB.NUNOTA
    LEFT JOIN TGFVEN VEN ON VEN.CODVEND = CAB.CODVEND
    LEFT JOIN (
        SELECT V.NUNOTAORIG, V.SEQUENCIAORIG,
               SUM(V.QTDATENDIDA) AS TOTAL_ATENDIDO
        FROM TGFVAR V
        JOIN TGFCAB C ON C.NUNOTA = V.NUNOTA
        WHERE C.STATUSNOTA <> 'C'
        GROUP BY V.NUNOTAORIG, V.SEQUENCIAORIG
    ) V_AGG ON V_AGG.NUNOTAORIG = ITE.NUNOTA
           AND V_AGG.SEQUENCIAORIG = ITE.SEQUENCIA
    WHERE CAB.TIPMOV IN ('C', 'O')
      AND CAB.STATUSNOTA <> 'C'
      AND UPPER(PAR.NOMEPARC) LIKE UPPER('%DONALDSON%')  -- Filtro de fornecedor
      AND CAB.DTNEG >= ADD_MONTHS(TRUNC(SYSDATE), -6)   -- Ultimos 6 meses
    GROUP BY CAB.NUNOTA, CAB.DTNEG, CAB.TIPMOV, CAB.CODTIPOPER,
             PAR.CODPARC, PAR.NOMEPARC, CAB.STATUSNOTA, CAB.PENDENTE,
             CAB.DTPREVENT, VEN.APELIDO, EMP.NOMEFANTASIA
    ORDER BY CAB.DTNEG DESC
) WHERE ROWNUM <= 100
