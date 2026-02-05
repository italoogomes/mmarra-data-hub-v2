-- GESTÃO DE EMPENHO - POR FORNECEDOR + COTAÇÃO V2
-- VERSÃO COM DETECÇÃO DE INCONSISTÊNCIA
-- Detecta quando existe cotação mas compra é diferente

WITH
/* 1) PEDIDOS (CAB) FILTRADOS */
cab_f AS (
    SELECT cab.nunota,
           cab.codvend,
           cab.codparc,
           cab.codemp,
           cab.dtneg,
           cab.hrmov,
           cab.dtprevent,
           cab.vlrnota
      FROM tgfcab cab
     WHERE 1=1
       AND cab.pendente   = 'S'
       AND cab.statusnota = 'L'
       AND EXISTS (
            SELECT 1
            FROM (
                SELECT
                    TGFTOP.CODTIPOPER,
                    TGFTOP.AD_RESERVAEMPENHO,
                    ROW_NUMBER() OVER (
                        PARTITION BY TGFTOP.CODTIPOPER
                        ORDER BY TGFTOP.DHALTER DESC
                    ) AS RN
                FROM TGFTOP
            ) TOP_U
            WHERE TOP_U.RN = 1
              AND TOP_U.CODTIPOPER = CAB.CODTIPOPER
              AND TOP_U.AD_RESERVAEMPENHO = 'S')
),

/* 2) ITENS CONSOLIDADOS (NÍVEL: NUNOTA + CODPROD) */
ite_prod AS (
    SELECT i.nunota,
           i.codprod,
           MAX(p.descrprod)  AS descrprod,
           SUM(i.qtdneg)     AS qtdneg_item,
           SUM(i.vlrtot)     AS valor_item_venda,
           COUNT(*)          AS qtd_linhas_item
      FROM tgfite i
      JOIN cab_f c
        ON c.nunota = i.nunota
      LEFT JOIN tgfpro p
        ON p.codprod = i.codprod
     GROUP BY i.nunota, i.codprod
),

/* 3) EMPENHO CONSOLIDADO (NÍVEL: NUNOTA + CODPROD) - AGORA COM NUNOTA_COMPRA */
empe_prod AS (
    SELECT e.nunotapedven AS nunota,
           e.codprod,
           SUM(e.qtdempenho) AS qtdempenho_item,
           MAX(e.nunota) AS nunota_compra_empenho
      FROM tgwempe e
      JOIN cab_f c
        ON c.nunota = e.nunotapedven
     GROUP BY e.nunotapedven, e.codprod
),

/* 4) STATUS WMS (NÍVEL CABEÇALHO) */
wms_f AS (
    SELECT c.nunota,
           CASE
             WHEN EXISTS (
                 SELECT 1
                   FROM vgwsepsitcab w
                  WHERE w.nunota = c.nunota
             )
             THEN 'Ja enviado ao WMS'
             ELSE 'Nao enviado ao WMS'
           END AS status_wms
      FROM cab_f c
),

/* 5) WMS_ARM (CONFERÊNCIA/ARMAZENAGEM) CONSOLIDADO (NÍVEL: NUNOTA + CODPROD) */
wms_arm_prod AS (
    SELECT e.nunotapedven AS nunota,
           e.codprod,
           MAX(CASE WHEN r.situacao = 6 THEN 6 ELSE NULL END) AS situacao_wms
      FROM tgwempe e
      LEFT JOIN tgwrec r
        ON r.nunota = e.nunota
     WHERE e.nunotapedven IN (SELECT nunota FROM cab_f)
     GROUP BY e.nunotapedven, e.codprod
),

/* 6) COMPRAS VINCULADAS AO EMPENHO (BASE) */
compra_base AS (
    SELECT e.nunotapedven AS nunota_venda,
           e.codprod      AS codprod,
           cb.nunota      AS nunota_compra,
           cb.codparc     AS codparc_fornecedor
      FROM tgwempe e
      JOIN cab_f v
        ON v.nunota = e.nunotapedven
      JOIN tgfcab cb
        ON cb.nunota = e.nunota
),

/* 7) FORNECEDORES (DISTINTOS) POR (VENDA, PRODUTO) */
forn_dist AS (
    SELECT DISTINCT
           b.nunota_venda,
           b.codprod,
           b.codparc_fornecedor,
           p.nomeparc AS fornecedor
      FROM compra_base b
      LEFT JOIN tgfpar p
        ON p.codparc = b.codparc_fornecedor
),

/* 8) LISTA DE FORNECEDORES POR (VENDA, PRODUTO) */
forn_list AS (
    SELECT d.nunota_venda,
           d.codprod,
           LISTAGG(TO_CHAR(d.codparc_fornecedor), ', ') WITHIN GROUP (ORDER BY d.codparc_fornecedor) AS codparc_fornecedor_list,
           LISTAGG(d.fornecedor, ' | ') WITHIN GROUP (ORDER BY d.fornecedor)                          AS fornecedor_list
      FROM forn_dist d
     GROUP BY d.nunota_venda, d.codprod
),

/* 9) VALOR DE COMPRA DO ITEM */
compra_val AS (
    SELECT b.nunota_venda,
           b.codprod,
           SUM(NVL(ic.qtdneg, 0))  AS qtd_compra_total,
           SUM(NVL(ic.vlrtot, 0))  AS valor_compra_total_item
      FROM compra_base b
      LEFT JOIN tgfite ic
        ON ic.nunota  = b.nunota_compra
       AND ic.codprod = b.codprod
     GROUP BY b.nunota_venda, b.codprod
),

/* 9.1) LISTA DE NUNOTAS E NUMNOTAS DE COMPRA */
compra_nunota_list AS (
    SELECT DISTINCT
           b.nunota_venda,
           b.codprod,
           b.nunota_compra,
           cb.numnota
      FROM compra_base b
      LEFT JOIN tgfcab cb ON cb.nunota = b.nunota_compra
),

compra_nunota_agg AS (
    SELECT d.nunota_venda,
           d.codprod,
           LISTAGG(TO_CHAR(d.nunota_compra), ', ') WITHIN GROUP (ORDER BY d.nunota_compra) AS nunota_compra_list,
           LISTAGG(TO_CHAR(d.numnota), ', ') WITHIN GROUP (ORDER BY d.nunota_compra) AS numnota_compra_list
      FROM compra_nunota_list d
     GROUP BY d.nunota_venda, d.codprod
),

/* 10) COTAÇÃO VIA EMPENHO (caminho original) */
cotacao_via_empenho AS (
    SELECT
        b.nunota_venda,
        b.codprod,
        MAX(itc.NUMCOTACAO) AS num_cotacao,
        MAX(itc.STATUSPRODCOT) AS status_cotacao,
        MAX(u.NOMEUSU) AS nome_responsavel_cotacao
    FROM compra_base b
    JOIN tgfite ic
      ON ic.nunota = b.nunota_compra
     AND ic.codprod = b.codprod
    LEFT JOIN tgfitc itc
      ON itc.CODPARC = b.codparc_fornecedor
     AND itc.CODPROD = b.codprod
    LEFT JOIN tgfcot cot
      ON cot.NUMCOTACAO = itc.NUMCOTACAO
    LEFT JOIN TSIUSU u
      ON u.CODUSU = cot.CODUSURESP
    GROUP BY b.nunota_venda, b.codprod
),

/* 11) COTAÇÃO VIA SOLICITAÇÃO (busca alternativa - quando não acha via empenho) */
cotacao_via_solicitacao AS (
    SELECT
        c.nunota AS nunota_venda,
        i.codprod,
        MAX(cot.NUMCOTACAO) AS num_cotacao,
        MAX(itc.STATUSPRODCOT) AS status_cotacao,
        MAX(itc.NUNOTACPA) AS nunota_compra_cotacao,
        MAX(u.NOMEUSU) AS nome_responsavel
    FROM cab_f c
    JOIN tgfite i ON i.nunota = c.nunota
    JOIN tgfcab sol ON sol.nunota = c.nunota + 1
                   AND sol.tipmov = 'J'
    JOIN tgfcot cot ON cot.NUNOTAORIG = sol.nunota
    JOIN tgfitc itc ON itc.NUMCOTACAO = cot.NUMCOTACAO
                   AND itc.CODPROD = i.codprod
    LEFT JOIN TSIUSU u ON u.CODUSU = cot.CODUSURESP
    GROUP BY c.nunota, i.codprod
),

/* 12) STATUS XML/ENTRADA DA COMPRA */
compra_status AS (
    SELECT
        b.nunota_venda,
        b.codprod,
        MAX(cb.CHAVENFE) AS chavenfe,
        MAX(cb.DTENTSAI) AS dt_entrada,
        MAX(cb.PENDENTE) AS pendente_compra,
        MAX(wms.SITUACAO) AS situacao_wms_compra,
        COUNT(wms.NUNOTA) AS tem_registro_wms
    FROM compra_base b
    JOIN tgfcab cb ON cb.nunota = b.nunota_compra
    LEFT JOIN tgwrec wms ON wms.nunota = b.nunota_compra
    GROUP BY b.nunota_venda, b.codprod
)

SELECT * FROM (
    SELECT
        ( TRUNC(c.dtneg)
          + ( TRUNC(NVL(c.hrmov,0) / 10000) / 24 )
          + ( TRUNC(MOD(NVL(c.hrmov,0),10000) / 100) / 1440 )
          + ( MOD(NVL(c.hrmov,0),100) / 86400 )
        ) AS Data,

        c.nunota      AS Num_Unico,
        c.codparc     AS Cod_Cliente,
        par.nomeparc  AS Cliente,
        c.codemp      AS Emp,
        c.dtprevent   AS Previsao_Entrega,
        c.codvend     AS Cod_Vend,
        ven.apelido   AS Vendedor,

        i.codprod     AS Cod_Prod,
        i.descrprod   AS Produto,

        i.qtdneg_item                          AS Qtd_SKUs,
        NVL(e.qtdempenho_item, 0)              AS Qtd_Com_Empenho,
        (i.qtdneg_item - NVL(e.qtdempenho_item, 0)) AS Qtd_Sem_Empenho,

        i.valor_item_venda   AS Valor,
        NVL(cv.valor_compra_total_item, 0) AS Custo,

        CASE
            WHEN NVL(cv.qtd_compra_total,0) = 0 THEN 0
            ELSE (NVL(cv.valor_compra_total_item,0) / cv.qtd_compra_total)
        END AS Custo_Medio,

        fl.codparc_fornecedor_list AS Cod_Forn,
        fl.fornecedor_list         AS Fornecedor,

        cnl.nunota_compra_list AS Num_Unico_NF_Empenho,
        cnl.numnota_compra_list AS Num_NF_Empenho,

        /* CAMPOS DE COTAÇÃO - prioriza via empenho, senão via solicitacao */
        COALESCE(cot_e.num_cotacao, cot_s.num_cotacao) AS Cod_Cotacao,
        COALESCE(cot_e.nome_responsavel_cotacao, cot_s.nome_responsavel) AS Nome_Resp_Cotacao,
        COALESCE(cot_e.status_cotacao, cot_s.status_cotacao) AS Status_Cotacao,
        cot_s.nunota_compra_cotacao AS Num_Unico_Compra_Cotacao,

        /* CAMPOS XML/ENTRADA DA COMPRA */
        CASE
            WHEN cs.chavenfe IS NOT NULL THEN 'Sim'
            ELSE 'Nao'
        END AS Tem_XML,
        cs.dt_entrada AS Data_Entrada_Compra,
        CASE
            WHEN cs.tem_registro_wms = 0 THEN 'Aguardando envio WMS'
            WHEN cs.situacao_wms_compra = 0 THEN 'Aguardando conferencia'
            WHEN cs.situacao_wms_compra = 1 THEN 'Aguardando'
            WHEN cs.situacao_wms_compra = 2 THEN 'Em Recebimento'
            WHEN cs.situacao_wms_compra = 3 THEN 'Em Conferencia'
            WHEN cs.situacao_wms_compra = 4 THEN 'Conferido'
            WHEN cs.situacao_wms_compra = 5 THEN 'Em Armazenagem'
            WHEN cs.situacao_wms_compra = 6 THEN 'Armazenado'
            ELSE 'Sem compra'
        END AS Status_WMS_Compra,

        /* Status Empenho - COM DETECÇÃO DE INCONSISTÊNCIA */
        CASE
            /* Inconsistencia: tem cotacao via solicitacao mas compra diferente do empenho */
            WHEN cot_s.num_cotacao IS NOT NULL
             AND e.nunota_compra_empenho IS NOT NULL
             AND cot_s.nunota_compra_cotacao IS NOT NULL
             AND cot_s.nunota_compra_cotacao != e.nunota_compra_empenho
                THEN 'Verificar inconsistencia'
            WHEN NVL(e.qtdempenho_item, 0) = 0
                THEN 'Item nao empenhado'
            WHEN NVL(e.qtdempenho_item, 0) < i.qtdneg_item
                THEN 'Item empenhado parcial'
            ELSE 'Item empenhado total'
        END AS status_empenho_item,

        w.status_wms AS status_wms,

        CASE
            WHEN wa.situacao_wms = 6 THEN 'Concluido'
            ELSE 'Pendente'
        END AS status_logistico_item,

        /* Status Geral - COM DETECÇÃO DE INCONSISTÊNCIA */
        CASE
            WHEN cot_s.num_cotacao IS NOT NULL
             AND e.nunota_compra_empenho IS NOT NULL
             AND cot_s.nunota_compra_cotacao IS NOT NULL
             AND cot_s.nunota_compra_cotacao != e.nunota_compra_empenho
                THEN 'INCONSISTENCIA: Compra cotacao (' || cot_s.nunota_compra_cotacao || ') != Empenho (' || e.nunota_compra_empenho || ')'
            ELSE
                (CASE
                    WHEN NVL(e.qtdempenho_item, 0) = 0
                        THEN 'Item nao empenhado'
                    WHEN NVL(e.qtdempenho_item, 0) < i.qtdneg_item
                        THEN 'Item empenhado parcial'
                    ELSE 'Item empenhado total'
                 END)
                 || ' - ' || w.status_wms
                 || ' - WMS_ARM: '
                 || CASE
                        WHEN wa.situacao_wms = 6 THEN 'Concluido'
                        ELSE 'Pendente'
                    END
        END AS status_geral_item,

        /* Cor - LARANJA para inconsistência */
        CASE
            WHEN cot_s.num_cotacao IS NOT NULL
             AND e.nunota_compra_empenho IS NOT NULL
             AND cot_s.nunota_compra_cotacao IS NOT NULL
             AND cot_s.nunota_compra_cotacao != e.nunota_compra_empenho
                THEN '#FFB347'
            WHEN NVL(e.qtdempenho_item, 0) >= i.qtdneg_item
             AND wa.situacao_wms = 6
                THEN '#CFE2D6'
            WHEN NVL(e.qtdempenho_item, 0) >= i.qtdneg_item
                THEN '#D1E7DD'
            WHEN NVL(e.qtdempenho_item, 0) > 0
             AND NVL(e.qtdempenho_item, 0) < i.qtdneg_item
                THEN '#FFF3CD'
            ELSE '#F8D7DA'
        END AS bkcolor,

        '#1F2937' AS fgcolor

    FROM cab_f c
    JOIN ite_prod i
      ON i.nunota = c.nunota
    LEFT JOIN empe_prod e
      ON e.nunota   = i.nunota
     AND e.codprod  = i.codprod
    JOIN wms_f w
      ON w.nunota = c.nunota
    LEFT JOIN wms_arm_prod wa
      ON wa.nunota  = i.nunota
     AND wa.codprod = i.codprod
    LEFT JOIN forn_list fl
      ON fl.nunota_venda = i.nunota
     AND fl.codprod      = i.codprod
    LEFT JOIN compra_val cv
      ON cv.nunota_venda = i.nunota
     AND cv.codprod      = i.codprod
    LEFT JOIN compra_nunota_agg cnl
      ON cnl.nunota_venda = i.nunota
     AND cnl.codprod      = i.codprod
    LEFT JOIN cotacao_via_empenho cot_e
      ON cot_e.nunota_venda = i.nunota
     AND cot_e.codprod      = i.codprod
    LEFT JOIN cotacao_via_solicitacao cot_s
      ON cot_s.nunota_venda = i.nunota
     AND cot_s.codprod      = i.codprod
    LEFT JOIN compra_status cs
      ON cs.nunota_venda = i.nunota
     AND cs.codprod      = i.codprod
    LEFT JOIN tgfven ven
      ON ven.codvend = c.codvend
    JOIN tgfpar par
      ON par.codparc = c.codparc

    ORDER BY
        c.nunota,
        i.codprod
)
WHERE ROWNUM <= 5000
