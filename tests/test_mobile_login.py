#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste usando MobileLogin (usuário/senha) ao invés de OAuth 2.0
"""

import requests
import json

print("=" * 70)
print("TESTE MOBILE LOGIN - SANKHYA")
print("=" * 70)

# Solicitar credenciais
print("\nPara testar, preciso de suas credenciais do Sankhya:")
usuario = input("Usuario: ").strip()
senha = input("Senha: ").strip()

if not usuario or not senha:
    print("\nCredenciais não fornecidas. Abortando.")
    exit(1)

# =============================================================================
# PASSO 1: LOGIN
# =============================================================================
print("\n" + "-" * 70)
print("PASSO 1: Fazendo login com MobileLoginSP.login")
print("-" * 70)

try:
    response = requests.post(
        "https://api.sankhya.com.br/mge/service.sbr",
        params={"serviceName": "MobileLoginSP.login"},
        headers={"Content-Type": "application/json"},
        json={
            "serviceName": "MobileLoginSP.login",
            "requestBody": {
                "NOMUSU": {"$": usuario},
                "INTERNO": {"$": senha},
                "KEEPCONNECTED": {"$": "S"}
            }
        },
        timeout=30
    )

    print(f"Status Code: {response.status_code}")
    data = response.json()

    if data.get("status") == "1":
        jsessionid = data["responseBody"]["jsessionid"]["$"]
        print(f"\n✅ LOGIN SUCESSO!")
        print(f"JSESSIONID: {jsessionid[:50]}...")
    else:
        print(f"\n❌ LOGIN FALHOU!")
        print(f"Status: {data.get('status')}")
        print(f"Mensagem: {data.get('statusMessage')}")
        print(f"\nResposta completa:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        exit(1)

except Exception as e:
    print(f"\n❌ ERRO no login: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

# =============================================================================
# PASSO 2: EXECUTAR QUERY SIMPLES
# =============================================================================
print("\n" + "=" * 70)
print("PASSO 2: Executando query de teste (COUNT de TGFCAB)")
print("=" * 70)

test_sql = "SELECT COUNT(*) AS TOTAL FROM TGFCAB WHERE CODEMP = 7"

try:
    response = requests.post(
        "https://api.sankhya.com.br/gateway/v1/mge/service.sbr",
        params={
            "serviceName": "DbExplorerSP.executeQuery",
            "outputType": "json"
        },
        headers={
            "Content-Type": "application/json",
            "Cookie": f"JSESSIONID={jsessionid}"
        },
        json={
            "serviceName": "DbExplorerSP.executeQuery",
            "requestBody": {
                "sql": test_sql
            }
        },
        timeout=30
    )

    print(f"\nStatus Code: {response.status_code}")
    data = response.json()

    print(f"\nResposta completa:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # Verificar se tem dados
    if "responseBody" in data and "rows" in data["responseBody"]:
        rows = data["responseBody"]["rows"]
        print(f"\n✅ QUERY EXECUTADA COM SUCESSO!")
        print(f"Total de registros na TGFCAB: {rows[0][0]}")
        print(f"\n🎉 MOBILE LOGIN FUNCIONA!")
    else:
        print(f"\n⚠️ Resposta sem dados esperados")
        print(f"Status: {data.get('status')}")
        print(f"Mensagem: {data.get('statusMessage')}")

except Exception as e:
    print(f"\n❌ ERRO ao executar query: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
