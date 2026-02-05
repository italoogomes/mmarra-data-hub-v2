# -*- coding: utf-8 -*-
"""
Gerador de relatorio HTML para Gestão de Empenho com Cotação
"""

import json
from datetime import datetime

print("=" * 80)
print("GERADOR DE RELATORIO HTML - EMPENHO COM COTACAO")
print("=" * 80)

# Carregar JSON
print("\n[1] Carregando dados...")
with open('resultado_empenho_com_cotacao.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

response_body = data.get('responseBody', {})
fields = response_body.get('fieldsMetadata', [])
rows = response_body.get('rows', [])

print(f"[OK] {len(rows)} registros carregados")

# Mapear nomes dos campos
field_names = [f["name"] for f in fields]
print(f"[INFO] Campos no resultado: {', '.join(field_names[:10])}...")

# Gerar HTML
print("\n[2] Gerando HTML...")

html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestão de Empenho com Cotação - MMarra Data Hub</title>
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
            max-width: 1800px;
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
            font-size: 0.85em;
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
            white-space: nowrap;
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
            white-space: nowrap;
        }}

        .text-right {{
            text-align: right;
        }}

        .text-center {{
            text-align: center;
        }}

        .status-empenhado-total {{
            background: #d1e7dd;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 500;
        }}

        .status-empenhado-parcial {{
            background: #fff3cd;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 500;
        }}

        .status-nao-empenhado {{
            background: #f8d7da;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 500;
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
                font-size: 0.7em;
            }}

            th, td {{
                padding: 6px 4px;
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
            <h1>Gestão de Empenho com Cotação</h1>
            <p>MMarra Data Hub | Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            <p>Relatório completo incluindo dados de cotação</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>{len(rows)}</h3>
                <p>Total de Registros</p>
            </div>
        </div>

        <div class="controls">
            <input type="text" id="searchInput" placeholder="Buscar por pedido, produto, fornecedor, cotação..." onkeyup="filtrarTabela()">
            <button onclick="exportarCSV()">Exportar CSV</button>
            <button onclick="window.print()">Imprimir</button>
        </div>

        <div class="table-container">
            <table id="tabelaEmpenho">
                <thead>
                    <tr>
"""

# Adicionar cabeçalhos dinamicamente
for i, field in enumerate(fields):
    field_name = field["name"]
    # Determinar classe de alinhamento
    align_class = ""
    if any(x in field_name.upper() for x in ["QTD", "VALOR", "CUSTO"]):
        align_class = ' class="text-right"'

    html_content += f'                        <th onclick="ordenarTabela({i})"{align_class}>{field_name}</th>\n'

html_content += """                    </tr>
                </thead>
                <tbody>
"""

# Adicionar linhas
for row in rows:
    html_content += "                    <tr>\n"

    for i, value in enumerate(row):
        # Formatar valor
        if value is None:
            display_value = ""
        elif isinstance(value, (int, float)):
            # Se for quantidade ou valor
            field_name = fields[i]["name"].upper()
            if any(x in field_name for x in ["QTD", "VALOR", "CUSTO"]):
                display_value = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                td_class = ' class="text-right"'
            else:
                display_value = str(value)
                td_class = ""
        else:
            display_value = str(value)
            td_class = ""

            # Aplicar classes especiais para status de empenho
            if "empenhado total" in display_value.lower():
                td_class = ' class="status-empenhado-total"'
            elif "empenhado parcial" in display_value.lower():
                td_class = ' class="status-empenhado-parcial"'
            elif "não empenhado" in display_value.lower():
                td_class = ' class="status-nao-empenhado"'

        html_content += f"                        <td{td_class}>{display_value}</td>\n"

    html_content += "                    </tr>\n"

html_content += f"""                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>MMarra Data Hub v0.5.0 | Gestão de Empenho com Cotação | {len(rows)} registros</p>
            <p>Gerado automaticamente via API Sankhya | OAuth 2.0</p>
        </div>
    </div>

    <script>
        function filtrarTabela() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('tabelaEmpenho');
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
            const table = document.getElementById('tabelaEmpenho');
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
            const table = document.getElementById('tabelaEmpenho');
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
            link.download = 'gestao_empenho_cotacao.csv';
            link.click();
        }}
    </script>
</body>
</html>
"""

# Salvar HTML
output_file = "relatorio_empenho_cotacao.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"[OK] HTML gerado: {output_file}")
print("\n" + "=" * 80)
print("CONCLUIDO!")
print("=" * 80)
print(f"\nAbra o arquivo '{output_file}' no navegador para visualizar.")
print(f"\nEstatisticas:")
print(f"  - Total de registros: {len(rows)}")
print(f"  - Campos no relatorio: {len(fields)}")
