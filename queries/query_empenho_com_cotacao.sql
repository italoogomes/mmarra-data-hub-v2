-- GESTÃO DE EMPENHO - POR FORNECEDOR + COTAÇÃO

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

/* 3) EMPENHO CONSOLIDADO (NÍVEL: NUNOTA + CODPROD) */
empe_prod AS (
    SELECT e.nunotapedven AS nunota,
           e.codprod,
           SUM(e.qtdempenho) AS qtdempenho_item
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
             THEN 'Já enviado ao WMS'
             ELSE 'Não enviado ao WMS'
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

/* 9) VALOR DE COMPRA DO ITEM (SOMA DO VLRTOT NA(S) COMPRA(S) LIGADA(S) AO EMPENHO) */
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

/* 9.1) LISTA DE NUNOTAS E NUMNOTAS DE COMPRA (NOTAS FISCAIS DE EMPENHO) */
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

/* 10) DADOS DE COTAÇÃO (CONSOLIDADO POR VENDA + PRODUTO) */
cotacao_info AS (
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
)

SELECT
    /* Data/hora do pedido (cabeçalho) */
    ( TRUNC(c.dtneg)
      + ( TRUNC(NVL(c.hrmov,0) / 10000) / 24 )
      + ( TRUNC(MOD(NVL(c.hrmov,0),10000) / 100) / 1440 )
      + ( MOD(NVL(c.hrmov,0),100) / 86400 )
    ) AS Data,

    /* Pedido */
    c.nunota      AS Num_Unico,
    c.codparc     AS Cod_Cliente,
    par.nomeparc  AS Cliente,
    c.codemp      AS Emp,
    c.dtprevent   AS Previsao_Entrega,
    c.codvend     AS Cod_Vend,
    ven.apelido   AS Vendedor,

    /* Produto consolidado */
    i.codprod     AS Cod_Prod,
    i.descrprod   AS Produto,

    /* Quantidades (consolidado por produto) */
    i.qtdneg_item                          AS Qtd_SKUs,
    NVL(e.qtdempenho_item, 0)              AS Qtd_Com_Empenho,
    (i.qtdneg_item - NVL(e.qtdempenho_item, 0)) AS Qtd_Sem_Empenho,

    /* Valores */
    i.valor_item_venda   AS Valor,
    NVL(cv.valor_compra_total_item, 0) AS Custo,

    /* Custo unitário médio (compra) */
    CASE
        WHEN NVL(cv.qtd_compra_total,0) = 0 THEN 0
        ELSE (NVL(cv.valor_compra_total_item,0) / cv.qtd_compra_total)
    END AS Custo_Medio,

    /* Fornecedor(es) */
    fl.codparc_fornecedor_list AS Cod_Forn,
    fl.fornecedor_list         AS Fornecedor,

    /* Numero(s) Nota Fiscal de Empenho */
    cnl.nunota_compra_list AS Num_Unico_NF_Empenho,
    cnl.numnota_compra_list AS Num_NF_Empenho,

    /* NOVOS CAMPOS DE COTAÇÃO */
    cot.num_cotacao AS Cod_Cotacao,
    cot.nome_responsavel_cotacao AS Nome_Resp_Cotacao,
    cot.status_cotacao AS Status_Cotacao,

    /* Status Empenho */
    CASE
        WHEN NVL(e.qtdempenho_item, 0) = 0
            THEN 'Item não empenhado'
        WHEN NVL(e.qtdempenho_item, 0) < i.qtdneg_item
            THEN 'Item empenhado parcial'
        ELSE 'Item empenhado total'
    END AS status_empenho_item,

    /* Status WMS (pedido) */
    w.status_wms AS status_wms,

    /* Status Logístico (produto) */
    CASE
        WHEN wa.situacao_wms = 6 THEN 'Concluído'
        ELSE 'Pendente'
    END AS status_logistico_item,

    /* Status Geral */
    (CASE
        WHEN NVL(e.qtdempenho_item, 0) = 0
            THEN 'Item não empenhado'
        WHEN NVL(e.qtdempenho_item, 0) < i.qtdneg_item
            THEN 'Item empenhado parcial'
        ELSE 'Item empenhado total'
     END)
     || ' - ' || w.status_wms
     || ' - WMS_ARM: '
     || CASE
            WHEN wa.situacao_wms = 6 THEN 'Concluído'
            ELSE 'Pendente'
        END AS status_geral_item,

    /* Cor */
    CASE
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
LEFT JOIN cotacao_info cot
  ON cot.nunota_venda = i.nunota
 AND cot.codprod      = i.codprod
LEFT JOIN tgfven ven
  ON ven.codvend = c.codvend
JOIN tgfpar par
  ON par.codparc = c.codparc

WHERE
    /* Identificadores principais */
        (c.nunota   = :P_NUNOTA   OR :P_NUNOTA   IS NULL)
    AND (c.codemp   = :P_CODEMP   OR :P_CODEMP   IS NULL)
    AND (c.codparc  = :P_CODPARC  OR :P_CODPARC  IS NULL)
    AND (c.codvend  = :P_CODVEND  OR :P_CODVEND  IS NULL)

    /* Datas */
    AND (c.dtneg     >= :P_DTNEG_INI   OR :P_DTNEG_INI   IS NULL)
    AND (c.dtneg     <  :P_DTNEG_FIM   OR :P_DTNEG_FIM   IS NULL)
    AND (c.dtprevent >= :P_DTPREV_INI  OR :P_DTPREV_INI  IS NULL)
    AND (c.dtprevent <  :P_DTPREV_FIM  OR :P_DTPREV_FIM  IS NULL)

    /* Valor */
    AND (i.valor_item_venda >= :P_VLR_INI OR :P_VLR_INI IS NULL)
    AND (i.valor_item_venda <= :P_VLR_FIM OR :P_VLR_FIM IS NULL)

    /* Produto */
    AND (i.codprod = :P_CODPROD OR :P_CODPROD IS NULL)

    /* StatusEmpenho */
    AND (
          (CASE
              WHEN NVL(e.qtdempenho_item, 0) = 0 THEN 'Item não empenhado'
              WHEN NVL(e.qtdempenho_item, 0) < i.qtdneg_item THEN 'Item empenhado parcial'
              ELSE 'Item empenhado total'
           END) = :P_STATUSEMPENHO
         OR :P_STATUSEMPENHO IS NULL
        )

    /* StatusWMS */
    AND (w.status_wms = :P_STATUSWMS OR :P_STATUSWMS IS NULL)

    /* StatusLogConf */
    AND (
          (CASE WHEN wa.situacao_wms = 6 THEN 'Concluído' ELSE 'Pendente' END) = :P_STATUSLOGCONF
          OR :P_STATUSLOGCONF IS NULL
        )

    /* Fornecedor (código) */
    AND (
          INSTR(',' || NVL(fl.codparc_fornecedor_list,'') || ',', ',' || :P_CODFORN || ',') > 0
          OR :P_CODFORN IS NULL
        )

    /* Fornecedor (nome) */
    AND (fl.fornecedor_list LIKE :P_FORNECEDOR OR :P_FORNECEDOR IS NULL)

    /* NOVOS FILTROS DE COTAÇÃO */
    AND (cot.num_cotacao = :P_NUMCOTACAO OR :P_NUMCOTACAO IS NULL)
    AND (cot.status_cotacao = :P_STATUSCOTACAO OR :P_STATUSCOTACAO IS NULL)
    AND (cot.nome_responsavel_cotacao LIKE :P_NOMERESP OR :P_NOMERESP IS NULL)

    /* Status_Geral */
    AND (
          (
            (CASE
                WHEN NVL(e.qtdempenho_item, 0) = 0 THEN 'Item não empenhado'
                WHEN NVL(e.qtdempenho_item, 0) < i.qtdneg_item THEN 'Item empenhado parcial'
                ELSE 'Item empenhado total'
             END)
             || ' - ' || w.status_wms
             || ' - WMS_ARM: '
             || CASE WHEN wa.situacao_wms = 6 THEN 'Concluído' ELSE 'Pendente' END
          ) = :P_STATUSGERAL
          OR :P_STATUSGERAL IS NULL
        )

    /* Filtros opcionais */
    AND (ven.apelido  = :P_VENDEDOR OR :P_VENDEDOR IS NULL)
    AND (par.nomeparc LIKE :P_CLIENTE OR :P_CLIENTE IS NULL)

ORDER BY
    c.nunota,
    i.codprod
