# -*- coding: utf-8 -*-
"""
MAPEAMENTO DE TABELAS POR VOLUME
================================
Identifica as tabelas com mais registros e suas estruturas
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Carregar credenciais
env_path = os.path.join(os.path.dirname(__file__), 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

def autenticar():
    print("[1] Autenticando...")
    auth_response = requests.post(
        "https://api.sankhya.com.br/authenticate",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Token": X_TOKEN
        },
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials"
        },
        timeout=30
    )
    if auth_response.status_code != 200:
        return None
    print("[OK] Token obtido!")
    return auth_response.json()["access_token"]

def executar_query(access_token, query_sql, silencioso=True):
    query_payload = {"requestBody": {"sql": query_sql}}
    try:
        query_response = requests.post(
            "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=query_payload,
            timeout=120
        )
        if query_response.status_code != 200:
            return None
        result = query_response.json()
        if result.get("status") != "1":
            return None
        return result.get("responseBody", {})
    except:
        return None

def main():
    print("=" * 80)
    print("IDENTIFICANDO TABELAS COM MAIOR VOLUME")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        return

    # Lista de tabelas importantes para contar
    # Baseado nos prefixos mais relevantes: TGF, TGW, TSI, AD_
    tabelas_para_contar = [
        # Comercial Principal
        'TGFCAB', 'TGFITE', 'TGFPAR', 'TGFPRO', 'TGFVEN', 'TGFFIN',
        'TGFEST', 'TGFMOV', 'TGFRES', 'TGFTOP', 'TGFEMP', 'TGFNAT',
        'TGFCPL', 'TGFCUS', 'TGFDFE', 'TGFDIN', 'TGFEXA', 'TGFEXC',
        'TGFIMP', 'TGFIPO', 'TGFLOT', 'TGFMAR', 'TGFPRC', 'TGFPRE',
        'TGFPRV', 'TGFREG', 'TGFSER', 'TGFTIP', 'TGFTPV', 'TGFUSU',
        'TGFVAR', 'TGFVOL', 'TGFCFO', 'TGFACO', 'TGFAGD', 'TGFALC',
        # Cotacao
        'TGFCOT', 'TGFITC',
        # WMS
        'TGWEST', 'TGWEND', 'TGWREC', 'TGWSEP', 'TGWEMPE', 'TGWSXN',
        'TGWRXN', 'TGWARM', 'TGWCON', 'TGWENT', 'TGWINV', 'TGWMOV',
        'TGWORD', 'TGWPRD', 'TGWPRO', 'TGWREA', 'TGWRET', 'TGWSAI',
        # Sistema
        'TSIUSU', 'TSIEMP', 'TSILOG', 'TSIPER', 'TSICID', 'TSIUF',
        'TSIBAI', 'TSICEP', 'TSIAGE', 'TSIAUT', 'TSICAM', 'TSICFG',
        # Customizadas importantes
        'AD_COTACOESDEITENS', 'AD_INTEGRACOES', 'AD_LOGS',
    ]

    print(f"\nContando registros de {len(tabelas_para_contar)} tabelas...")
    print("-" * 60)

    resultados = []

    for i, tabela in enumerate(tabelas_para_contar):
        print(f"  [{i+1}/{len(tabelas_para_contar)}] {tabela}...", end=" ")

        query = f"SELECT COUNT(*) FROM {tabela}"
        result = executar_query(access_token, query)

        if result and result.get("rows"):
            qtd = result["rows"][0][0] or 0
            print(f"{qtd:,} registros")
            resultados.append({"tabela": tabela, "registros": qtd})
        else:
            print("(tabela nao existe ou erro)")

    # Ordenar por quantidade de registros
    resultados.sort(key=lambda x: x["registros"], reverse=True)

    print("\n" + "=" * 80)
    print("TOP 30 TABELAS POR VOLUME")
    print("=" * 80)
    print(f"{'#':>3} | {'TABELA':<20} | {'REGISTROS':>15}")
    print("-" * 50)

    for i, r in enumerate(resultados[:30]):
        if r["registros"] > 0:
            print(f"{i+1:>3} | {r['tabela']:<20} | {r['registros']:>15,}")

    # Salvar resultados
    output = {
        "data": datetime.now().isoformat(),
        "tabelas_por_volume": resultados
    }

    with open("tabelas_por_volume.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n[OK] Salvo em: tabelas_por_volume.json")

if __name__ == "__main__":
    main()
