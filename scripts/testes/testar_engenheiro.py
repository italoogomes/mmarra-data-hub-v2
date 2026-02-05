# -*- coding: utf-8 -*-
"""
Teste da interface simplificada do Engenheiro

Uso:
    python scripts/testes/testar_engenheiro.py
"""

import sys
from pathlib import Path

# Adicionar raiz ao path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

print("=" * 60)
print("TESTE DO ENGENHEIRO - Interface Simplificada")
print("=" * 60)
print()

# ============================================================================
# 1. IMPORT E INSTANCIACAO
# ============================================================================
print("[1] Importando e instanciando Engenheiro...")

try:
    from src.agents.engineer import Engenheiro

    # Desabilitar upload para Azure (nao instalado)
    engenheiro = Engenheiro(upload_azure=False)

    print("    OK: Engenheiro instanciado com sucesso")
    print(f"    Entidades disponiveis: {engenheiro.listar_entidades()}")
except Exception as e:
    print(f"    ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ============================================================================
# 2. VERIFICAR STATUS DAS ENTIDADES
# ============================================================================
print("[2] Verificando status das entidades...")

for entidade in engenheiro.listar_entidades():
    status = engenheiro.status(entidade)
    print(f"    {status}")

print()

# ============================================================================
# 3. EXTRAIR VENDEDORES (RAPIDO, POUCOS REGISTROS)
# ============================================================================
print("[3] Extraindo VENDEDORES (teste rapido)...")

try:
    result = engenheiro.extrair("vendedores")
    print(f"    {result}")

    if result.success:
        print(f"    Boas praticas aplicadas:")
        for pratica, aplicada in result.boas_praticas.items():
            status = "OK" if aplicada else "X"
            print(f"      [{status}] {pratica}")
except Exception as e:
    print(f"    ERRO: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# 4. EXTRAIR VENDAS (90 DIAS)
# ============================================================================
print("[4] Extraindo VENDAS (ultimos 90 dias)...")

try:
    result = engenheiro.extrair("vendas", periodo="90d")
    print(f"    {result}")

    if result.success:
        print(f"    Periodo: {result.periodo[0]} a {result.periodo[1]}")
        print(f"    Arquivo: {result.caminho_local}")
except Exception as e:
    print(f"    ERRO: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("TESTE CONCLUIDO")
print("=" * 60)
