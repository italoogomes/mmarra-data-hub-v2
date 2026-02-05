# -*- coding: utf-8 -*-
"""
Gerador de relatorio HTML consolidado
Para a query V4 - 1 linha por produto
"""

import json
from datetime import datetime

print("=" * 80)
print("GERADOR DE RELATORIO HTML CONSOLIDADO")
print("=" * 80)

# Carregar JSON
print("\n[1] Carregando dados...")
with open('resultado_consolidado_v4.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

response_body = data.get('responseBody', {})
fields = response_body.get('fieldsMetadata', [])
rows = response_body.get('rows', [])

print(f"[OK] {len(rows)} produtos carregados")

# Gerar HTML
print("\n[2] Gerando HTML...")

# Calcular estatisticas
total_estoque = sum(row[4] for row in rows)
total_wms = sum(row[8] for row in rows)
total_div = sum(abs(row[11]) for row in rows)  # DIVERGENCIA_ERP_WMS esta no indice 11

html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatorio Consolidado por Produto - MMarra Data Hub</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .stat-card h3 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 5px;
        }}

        .stat-card p {{
            color: #666;
            font-size: 0.9em;
        }}

        .controls {{
            padding: 20px 30px;
            background: white;
            border-bottom: 1px solid #eee;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}

        .controls input {{
            flex: 1;
            min-width: 300px;
            padding: 12px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 1em;
            transition: border-color 0.3s;
        }}

        .controls input:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .controls button {{
            padding: 12px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
        }}

        .controls button:hover {{
            background: #5568d3;
        }}

        .table-container {{
            padding: 30px;
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            font-size: 0.9em;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        th {{
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
            font-size: 0.85em;
        }}

        th:hover {{
            background: rgba(255,255,255,0.1);
        }}

        tbody tr {{
            border-bottom: 1px solid #eee;
            transition: background 0.2s;
        }}

        tbody tr:hover {{
            background: #f8f9fa;
        }}

        td {{
            padding: 10px 8px;
            color: #333;
        }}

        .divergencia-positiva {{
            color: #e74c3c;
            font-weight: bold;
        }}

        .divergencia-negativa {{
            color: #3498db;
            font-weight: bold;
        }}

        .text-right {{
            text-align: right;
        }}

        .footer {{
            padding: 20px 30px;
            background: #f8f9fa;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}

        @media (max-width: 768px) {{
            .stats {{
                grid-template-columns: 1fr;
            }}

            .controls {{
                flex-direction: column;
            }}

            .controls input {{
                min-width: 100%;
            }}

            table {{
                font-size: 0.75em;
            }}

            th, td {{
                padding: 8px 4px;
            }}
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .controls, .footer {{
                display: none;
            }}

            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Relatorio Consolidado por Produto</h1>
            <p>MMarra Data Hub | Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            <p>1 linha por produto - Mesmos calculos da analise detalhada</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>{len(rows)}</h3>
                <p>Produtos com Divergencia</p>
            </div>
            <div class="stat-card">
                <h3>{total_estoque:,.0f}</h3>
                <p>Total Estoque (TGFEST)</p>
            </div>
            <div class="stat-card">
                <h3>{total_wms:,.0f}</h3>
                <p>Total WMS Disponivel</p>
            </div>
            <div class="stat-card">
                <h3>{total_div:,.0f}</h3>
                <p>Total Divergencia</p>
            </div>
        </div>

        <div class="controls">
            <input type="text" id="searchInput" placeholder="Buscar por produto, descricao, referencia..." onkeyup="filtrarTabela()">
            <button onclick="exportarCSV()">Exportar CSV</button>
            <button onclick="window.print()">Imprimir</button>
        </div>

        <div class="table-container">
            <table id="tabelaConsolidado">
                <thead>
                    <tr>
                        <th onclick="ordenarTabela(0)">CODEMP</th>
                        <th onclick="ordenarTabela(1)">CODPROD</th>
                        <th onclick="ordenarTabela(2)">DESCRICAO</th>
                        <th onclick="ordenarTabela(3)">REFERENCIA</th>
                        <th onclick="ordenarTabela(4)" class="text-right">ESTOQUE</th>
                        <th onclick="ordenarTabela(5)" class="text-right">RESERVADO</th>
                        <th onclick="ordenarTabela(6)" class="text-right">WMS BLOQ</th>
                        <th onclick="ordenarTabela(7)" class="text-right">DISP COMERC</th>
                        <th onclick="ordenarTabela(8)" class="text-right">SALDO WMS</th>
                        <th onclick="ordenarTabela(9)" class="text-right">PEDIDOS PEND</th>
                        <th onclick="ordenarTabela(10)" class="text-right">WMS APOS PED</th>
                        <th onclick="ordenarTabela(11)" class="text-right">DIVERGENCIA</th>
                    </tr>
                </thead>
                <tbody>
"""

# Adicionar linhas
for row in rows:
    codemp = row[0]
    codprod = row[1]
    descr = str(row[2]) if row[2] else ""
    ref = str(row[3]) if row[3] else ""
    estoque = row[4]
    reservado = row[5]
    wmsbloq = row[6]
    disp_comerc = row[7]
    saldo_wms = row[8]
    pedidos = row[9]
    wms_apos_pedidos = row[10]  # WMS_APOS_PEDIDOS
    divergencia = row[11]  # DIVERGENCIA_ERP_WMS (ESTOQUE - SALDO_WMS)

    # Classe CSS para divergencia
    div_class = "divergencia-positiva" if divergencia > 0 else "divergencia-negativa"

    html_content += f"""                    <tr>
                        <td>{codemp}</td>
                        <td>{codprod}</td>
                        <td>{descr}</td>
                        <td>{ref}</td>
                        <td class="text-right">{estoque:.0f}</td>
                        <td class="text-right">{reservado:.0f}</td>
                        <td class="text-right">{wmsbloq:.0f}</td>
                        <td class="text-right">{disp_comerc:.0f}</td>
                        <td class="text-right">{saldo_wms:.0f}</td>
                        <td class="text-right">{pedidos:.0f}</td>
                        <td class="text-right">{wms_apos_pedidos:.0f}</td>
                        <td class="text-right {div_class}">{divergencia:+.0f}</td>
                    </tr>
"""

html_content += f"""                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>MMarra Data Hub v0.5.0 | Query V4 Consolidada | {len(rows)} produtos com divergencia</p>
            <p>Gerado automaticamente via API Sankhya | OAuth 2.0</p>
        </div>
    </div>

    <script>
        function filtrarTabela() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('tabelaConsolidado');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                let txtValue = tr[i].textContent || tr[i].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                    tr[i].style.display = '';
                }} else {{
                    tr[i].style.display = 'none';
                }}
            }}
        }}

        function ordenarTabela(coluna) {{
            const table = document.getElementById('tabelaConsolidado');
            let rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            switching = true;
            dir = 'asc';

            while (switching) {{
                switching = false;
                rows = table.rows;

                for (i = 1; i < (rows.length - 1); i++) {{
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName('TD')[coluna];
                    y = rows[i + 1].getElementsByTagName('TD')[coluna];

                    let xContent = x.innerHTML.replace(/[^0-9.-]/g, '');
                    let yContent = y.innerHTML.replace(/[^0-9.-]/g, '');

                    const xNum = parseFloat(xContent);
                    const yNum = parseFloat(yContent);

                    let comparison;
                    if (!isNaN(xNum) && !isNaN(yNum)) {{
                        comparison = dir == 'asc' ? xNum > yNum : xNum < yNum;
                    }} else {{
                        comparison = dir == 'asc' ? x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase() : x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase();
                    }}

                    if (comparison) {{
                        shouldSwitch = true;
                        break;
                    }}
                }}

                if (shouldSwitch) {{
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount++;
                }} else {{
                    if (switchcount == 0 && dir == 'asc') {{
                        dir = 'desc';
                        switching = true;
                    }}
                }}
            }}
        }}

        function exportarCSV() {{
            const table = document.getElementById('tabelaConsolidado');
            let csv = [];

            // Headers
            const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent);
            csv.push(headers.join(','));

            // Linhas visiveis
            const rows = Array.from(table.querySelectorAll('tbody tr')).filter(tr => tr.style.display !== 'none');
            rows.forEach(row => {{
                const cols = Array.from(row.querySelectorAll('td')).map(td => {{
                    let value = td.textContent.replace(/"/g, '""');
                    return `"${{value}}"`;
                }});
                csv.push(cols.join(','));
            }});

            // Download
            const csvContent = csv.join('\\n');
            const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'relatorio_consolidado_produtos.csv';
            link.click();
        }}
    </script>
</body>
</html>
"""

# Salvar HTML
output_file = "relatorio_consolidado_produtos.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"[OK] HTML gerado: {output_file}")
print("\n" + "=" * 80)
print("CONCLUIDO!")
print("=" * 80)
print(f"\nAbra o arquivo '{output_file}' no navegador para visualizar.")
print(f"\nEstatisticas:")
print(f"  - Produtos: {len(rows)}")
print(f"  - Estoque Total: {total_estoque:,.0f} unidades")
print(f"  - WMS Total: {total_wms:,.0f} unidades")
print(f"  - Divergencia Total: {total_div:,.0f} unidades")
