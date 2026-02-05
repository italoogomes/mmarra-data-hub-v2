-- =============================================================================
-- QUERY: RECEBIMENTO DE CANHOTOS COM STATUS WMS
-- Tabelas: AD_RECEBCANH + TGWREC + TGFCAB + auxiliares
-- Data: 2026-02-03
-- =============================================================================
--
-- MAPEAMENTO DE SITUACAO WMS (TGWREC.SITUACAO):
--   0 = Pendente
--   1 = Aguardando
--   2 = Em Recebimento
--   3 = Em Conferencia
--   4 = Conferido
--   5 = Em Armazenagem
--   6 = Armazenado
--   NULL = Sem WMS (nota nao encontrada na TGWREC)
--
-- =============================================================================

SELECT
    rc.SEQRECCANH AS "Seq_Recebimento_Canhoto",
    rc.NUMNOTA AS "Nro_Nota_Fiscal",
    rc.SERIENOTA AS "Serie_Nota_Fiscal",
    rc.DTRECEB AS "Data_Recebimento",
    rc.CODEMP AS "Cod_Empresa",
    emp.NOMEFANTASIA AS "Nome_Fantasia_Empresa",
    rc.DHINC AS "Data_Hora_Inclusao",
    rc.CODUSU AS "Cod_Usuario_Inclusao",
    usu.NOMEUSU AS "Nome_Usuario",
    rc.NUNOTA AS "Nro_Unico",
    rc.CODPARC AS "Cod_Parceiro",
    par.NOMEPARC AS "Nome_Parceiro",
    rc.DTNEG AS "Data_Negociacao",
    rc.DTPREVFIN AS "Data_Prev_Fin",
    rc.NROCTE AS "Nro_CTe",
    rc.OBS AS "Observacao",
    rc.CODPARCTRANSP AS "Cod_Transportadora",
    transp.NOMEPARC AS "Transportadora",
    cab.CODVEND AS "Cod_Vendedor",
    ven.APELIDO AS "Vendedor",
    cab.VLRNOTA AS "Valor_Nota",
    wms.SITUACAO AS "Cod_Situacao_WMS",
    CASE wms.SITUACAO
        WHEN 0 THEN 'Pendente'
        WHEN 1 THEN 'Aguardando'
        WHEN 2 THEN 'Em Recebimento'
        WHEN 3 THEN 'Em Conferencia'
        WHEN 4 THEN 'Conferido'
        WHEN 5 THEN 'Em Armazenagem'
        WHEN 6 THEN 'Armazenado'
        ELSE 'Sem WMS'
    END AS "Status_WMS",
    wms.DTRECEBIMENTO AS "Data_Recebimento_WMS",
    wms.CONFFINAL AS "Conferencia_Final"
FROM AD_RECEBCANH rc
LEFT JOIN TGFCAB cab ON cab.NUNOTA = rc.NUNOTA
LEFT JOIN TSIEMP emp ON emp.CODEMP = rc.CODEMP
LEFT JOIN TSIUSU usu ON usu.CODUSU = rc.CODUSU
LEFT JOIN TGFPAR par ON par.CODPARC = rc.CODPARC
LEFT JOIN TGFPAR transp ON transp.CODPARC = rc.CODPARCTRANSP
LEFT JOIN TGFVEN ven ON ven.CODVEND = cab.CODVEND
LEFT JOIN TGWREC wms ON wms.NUNOTA = rc.NUNOTA
ORDER BY rc.DTRECEB DESC, rc.SEQRECCANH DESC
