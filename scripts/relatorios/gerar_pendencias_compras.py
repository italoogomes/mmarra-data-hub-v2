# -*- coding: utf-8 -*-
"""
Gerador de Relatorio de Pendencias de Compras

Gera relatorio HTML com todas as compras pendentes do Sankhya.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from datetime import datetime
from src.utils.sankhya_client import SankhyaClient


def gerar_relatorio_html():
    """Gera relatorio HTML de pendencias de compras."""

    client = SankhyaClient()

    query = """
    SELECT
        c.NUNOTA,
        c.NUMNOTA,
        c.CODEMP,
        c.CODPARC,
        p.NOMEPARC AS FORNECEDOR,
        c.DTNEG,
        c.DTPREVENT,
        c.VLRNOTA,
        c.PENDENTE,
        t.DESCROPER AS TIPO_OPERACAO,
        i.SEQUENCIA,
        i.CODPROD,
        pr.DESCRPROD,
        pr.REFERENCIA,
        i.QTDNEG,
        i.VLRUNIT,
        i.VLRTOT
    FROM TGFCAB c
    INNER JOIN TGFITE i ON i.NUNOTA = c.NUNOTA
    LEFT JOIN TGFPAR p ON p.CODPARC = c.CODPARC
    LEFT JOIN TGFPRO pr ON pr.CODPROD = i.CODPROD
    LEFT JOIN (
        SELECT CODTIPOPER, DESCROPER,
               ROW_NUMBER() OVER (PARTITION BY CODTIPOPER ORDER BY DHALTER DESC) AS RN
        FROM TGFTOP
    ) t ON t.CODTIPOPER = c.CODTIPOPER AND t.RN = 1
    WHERE c.TIPMOV = 'C'
      AND c.PENDENTE = 'S'
    ORDER BY c.DTNEG DESC
    """

    print("Buscando dados do Sankhya...")
    result = client.executar_query(query)
    rows = result.get('rows', [])
    fields = result.get('fieldsMetadata', [])
    columns = [f.get('name', f'col_{i}') for i, f in enumerate(fields)]

    df = pd.DataFrame(rows, columns=columns)

    # Converter tipos
    df['VLRTOT'] = pd.to_numeric(df['VLRTOT'], errors='coerce').fillna(0)
    df['VLRNOTA'] = pd.to_numeric(df['VLRNOTA'], errors='coerce').fillna(0)
    df['QTDNEG'] = pd.to_numeric(df['QTDNEG'], errors='coerce').fillna(0)
    df['CODEMP'] = pd.to_numeric(df['CODEMP'], errors='coerce').fillna(0).astype(int)
    df['DTNEG_DT'] = pd.to_datetime(df['DTNEG'], format='%d%m%Y %H:%M:%S', errors='coerce')

    # Calcular metricas
    total_valor = df['VLRTOT'].sum()
    total_pedidos = df['NUNOTA'].nunique()
    total_fornecedores = df['FORNECEDOR'].nunique()
    total_produtos = df['CODPROD'].nunique()

    # Por empresa
    por_empresa = df.groupby('CODEMP').agg({
        'NUNOTA': 'nunique',
        'VLRTOT': 'sum'
    }).sort_values('VLRTOT', ascending=False)

    # Por tipo
    por_tipo = df.groupby('TIPO_OPERACAO').agg({
        'NUNOTA': 'nunique',
        'VLRTOT': 'sum'
    }).sort_values('VLRTOT', ascending=False).head(10)

    # Por fornecedor
    por_fornecedor = df.groupby('FORNECEDOR').agg({
        'NUNOTA': 'nunique',
        'VLRTOT': 'sum',
        'CODPROD': 'nunique'
    }).rename(columns={'CODPROD': 'Itens'}).sort_values('VLRTOT', ascending=False).head(20)

    # Mais antigas
    antigas = df.sort_values('DTNEG_DT').drop_duplicates('NUNOTA')[
        ['NUNOTA', 'FORNECEDOR', 'DTNEG_DT', 'VLRNOTA']
    ].head(15)

    # Gerar HTML
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pendencias de Compras - MMarra</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .date {{ opacity: 0.8; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card .value {{ font-size: 28px; font-weight: bold; color: #1a237e; }}
        .card .label {{ color: #666; font-size: 14px; margin-top: 5px; }}
        .section {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .section h2 {{ color: #1a237e; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #e0e0e0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        th {{ background: #f5f5f5; color: #333; font-weight: 600; }}
        tr:hover {{ background: #fafafa; }}
        .valor {{ text-align: right; font-family: monospace; }}
        .destaque {{ background: #fff3e0 !important; }}
        .alert {{ background: #ffebee; color: #c62828; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .footer {{ text-align: center; color: #666; padding: 20px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Relatorio de Pendencias de Compras</h1>
            <div class="date">Gerado em: {datetime.now().strftime('%d/%m/%Y as %H:%M')}</div>
        </div>

        <div class="cards">
            <div class="card">
                <div class="value">R$ {total_valor:,.2f}</div>
                <div class="label">Valor Total Pendente</div>
            </div>
            <div class="card">
                <div class="value">{total_pedidos:,}</div>
                <div class="label">Pedidos Pendentes</div>
            </div>
            <div class="card">
                <div class="value">{total_fornecedores}</div>
                <div class="label">Fornecedores</div>
            </div>
            <div class="card">
                <div class="value">{total_produtos:,}</div>
                <div class="label">Produtos Distintos</div>
            </div>
        </div>

        <div class="section">
            <h2>Por Empresa</h2>
            <table>
                <tr><th>Empresa</th><th>Pedidos</th><th class="valor">Valor</th><th class="valor">%</th></tr>
"""

    for emp, row in por_empresa.iterrows():
        pct = row['VLRTOT'] / total_valor * 100
        html += f'<tr><td>Empresa {int(emp)}</td><td>{int(row["NUNOTA"])}</td><td class="valor">R$ {row["VLRTOT"]:,.2f}</td><td class="valor">{pct:.1f}%</td></tr>\n'

    html += """
            </table>
        </div>

        <div class="section">
            <h2>Por Tipo de Operacao</h2>
            <table>
                <tr><th>Tipo</th><th>Pedidos</th><th class="valor">Valor</th></tr>
"""

    for tipo, row in por_tipo.iterrows():
        tipo_str = str(tipo)[:50] if tipo else 'N/A'
        html += f'<tr><td>{tipo_str}</td><td>{int(row["NUNOTA"])}</td><td class="valor">R$ {row["VLRTOT"]:,.2f}</td></tr>\n'

    html += """
            </table>
        </div>

        <div class="section">
            <h2>Top 20 Fornecedores com Pendencias</h2>
            <table>
                <tr><th>Fornecedor</th><th>Pedidos</th><th>Itens</th><th class="valor">Valor</th><th class="valor">%</th></tr>
"""

    for i, (forn, row) in enumerate(por_fornecedor.iterrows()):
        pct = row['VLRTOT'] / total_valor * 100
        forn_str = str(forn)[:45] if forn else 'N/A'
        destaque = ' class="destaque"' if i < 5 else ''
        html += f'<tr{destaque}><td>{forn_str}</td><td>{int(row["NUNOTA"])}</td><td>{int(row["Itens"])}</td><td class="valor">R$ {row["VLRTOT"]:,.2f}</td><td class="valor">{pct:.1f}%</td></tr>\n'

    html += """
            </table>
        </div>

        <div class="alert">
            <strong>Atencao:</strong> Existem pendencias desde 09/12/2025 (quase 2 meses). Verifique as notas mais antigas.
        </div>

        <div class="section">
            <h2>Pendencias Mais Antigas</h2>
            <table>
                <tr><th>Nota</th><th>Data</th><th>Fornecedor</th><th class="valor">Valor</th></tr>
"""

    for _, row in antigas.iterrows():
        data = row['DTNEG_DT'].strftime('%d/%m/%Y') if pd.notna(row['DTNEG_DT']) else 'N/A'
        forn = str(row['FORNECEDOR'])[:40] if row['FORNECEDOR'] else 'N/A'
        html += f'<tr><td>{row["NUNOTA"]}</td><td>{data}</td><td>{forn}</td><td class="valor">R$ {float(row["VLRNOTA"]):,.2f}</td></tr>\n'

    html += f"""
            </table>
        </div>

        <div class="footer">
            MMarra Data Hub - Relatorio gerado automaticamente<br>
            {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""

    # Salvar
    output_dir = Path(__file__).parent.parent.parent / "src" / "data" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'pendencias_compras_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nRelatorio salvo em: {output_file}")
    print(f"Tamanho: {output_file.stat().st_size / 1024:.1f} KB")

    return output_file


if __name__ == "__main__":
    gerar_relatorio_html()
