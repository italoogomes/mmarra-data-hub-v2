# -*- coding: utf-8 -*-
"""
Extrai dados de Recebimento de Canhoto (AD_RECEBCANH)
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

def autenticar():
    auth_response = requests.post(
        "https://api.sankhya.com.br/authenticate",
        headers={"Content-Type": "application/x-www-form-urlencoded", "X-Token": X_TOKEN},
        data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
        timeout=30
    )
    if auth_response.status_code != 200:
        return None
    return auth_response.json()["access_token"]

def executar_query(access_token, query_sql, descricao=""):
    print(f"\n[QUERY] {descricao}")
    query_payload = {"requestBody": {"sql": query_sql}}
    try:
        query_response = requests.post(
            "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=query_payload,
            timeout=120
        )
        if query_response.status_code != 200:
            print(f"[ERRO HTTP] {query_response.status_code}")
            return None
        result = query_response.json()
        if result.get("status") != "1":
            print(f"[ERRO] {result.get('statusMessage')}")
            return None
        return result.get("responseBody", {})
    except Exception as e:
        print(f"[ERRO] {e}")
        return None

def main():
    print("=" * 80)
    print("EXTRACAO: RECEBIMENTO DE CANHOTOS")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        print("[ERRO] Falha na autenticacao")
        return
    print("[OK] Autenticado!")

    # 1. Ver estrutura da tabela AD_RECEBCANH
    query_estrutura = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'AD_RECEBCANH'
    ORDER BY COLUMN_ID
    """
    r1 = executar_query(access_token, query_estrutura, "ESTRUTURA DA AD_RECEBCANH")
    if r1 and r1.get("rows"):
        print("\nColunas encontradas:")
        for row in r1["rows"]:
            print(f"  - {row[0]}: {row[1]}")

    # 2. Extrair dados com JOINs para trazer informacoes completas
    # Inclui status WMS (TGWREC) - Entrada, Conferencia, Armazenagem
    query_dados = """
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
    """

    r2 = executar_query(access_token, query_dados, "DADOS DE RECEBIMENTO DE CANHOTOS")

    if not r2 or not r2.get("rows"):
        print("\n[INFO] Nenhum registro encontrado!")
        return

    fields = r2.get("fieldsMetadata", [])
    rows = r2.get("rows", [])

    print(f"\n[OK] {len(rows)} registros encontrados!")

    # Converter para DataFrame
    field_names = [f["name"] for f in fields]
    df = pd.DataFrame(rows, columns=field_names)

    # Estatisticas
    print(f"\n[INFO] Estatisticas:")
    print(f"  - Total de registros: {len(df)}")
    if "Cod_Empresa" in df.columns:
        print(f"  - Empresas: {df['Cod_Empresa'].nunique()}")
    if "Cod_Usuario_Inclusao" in df.columns:
        print(f"  - Usuarios: {df['Cod_Usuario_Inclusao'].nunique()}")

    # Salvar arquivos
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'canhoto')
    os.makedirs(output_dir, exist_ok=True)

    csv_file = os.path.join(output_dir, 'recebimento_canhoto.csv')
    json_file = os.path.join(output_dir, 'recebimento_canhoto.json')
    parquet_file = os.path.join(output_dir, 'recebimento_canhoto.parquet')

    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    df.to_parquet(parquet_file, index=False)

    # Salvar JSON com resultado completo
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({"fieldsMetadata": fields, "rows": rows}, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Arquivos salvos:")
    print(f"  - CSV: {csv_file}")
    print(f"  - Parquet: {parquet_file}")
    print(f"  - JSON: {json_file}")

    # Preview
    print("\n" + "=" * 80)
    print("PREVIEW (primeiros 10 registros)")
    print("=" * 80)
    print(df.head(10).to_string(index=False))

    print("\n" + "=" * 80)
    print("CONCLUIDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()
