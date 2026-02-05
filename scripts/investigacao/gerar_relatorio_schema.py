# -*- coding: utf-8 -*-
"""
GERA RELATORIO HTML DO MAPEAMENTO DO BANCO
==========================================
"""

import json
from datetime import datetime

def gerar_html():
    # Carregar dados do mapeamento
    try:
        with open("mapeamento_banco_sankhya.json", 'r', encoding='utf-8') as f:
            mapeamento = json.load(f)
    except:
        print("[ERRO] Arquivo mapeamento_banco_sankhya.json nao encontrado!")
        return

    try:
        with open("tabelas_por_volume.json", 'r', encoding='utf-8') as f:
            volume = json.load(f)
    except:
        volume = {"tabelas_por_volume": []}

    # Preparar dados
    tabelas_prefixo = mapeamento.get("tabelas_por_prefixo", {})
    tabelas_detalhes = mapeamento.get("tabelas_detalhes", {})
    relacionamentos = mapeamento.get("relacionamentos", [])
    views = mapeamento.get("views", [])
    tabelas_volume = volume.get("tabelas_por_volume", [])

    # Ordenar prefixos por quantidade
    prefixos_ordenados = sorted(tabelas_prefixo.items(), key=lambda x: len(x[1]), reverse=True)

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mapeamento Banco Sankhya - MMarra Data Hub</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            color: #00d4ff;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }}
        .subtitle {{
            text-align: center;
            color: #888;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #2d2d44 0%, #1f1f2e 100%);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            border: 1px solid #3d3d5c;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 212, 255, 0.2);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #00d4ff;
        }}
        .stat-label {{
            color: #888;
            margin-top: 5px;
        }}
        .section {{
            background: #1f1f2e;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid #3d3d5c;
        }}
        .section h2 {{
            color: #00d4ff;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3d3d5c;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #3d3d5c;
        }}
        th {{
            background: #2d2d44;
            color: #00d4ff;
            font-weight: 600;
        }}
        tr:hover {{
            background: #2d2d44;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        .badge-tgf {{ background: #0066cc; color: white; }}
        .badge-tgw {{ background: #00994d; color: white; }}
        .badge-tsi {{ background: #9933cc; color: white; }}
        .badge-ad {{ background: #cc6600; color: white; }}
        .badge-other {{ background: #666; color: white; }}
        .progress-bar {{
            height: 20px;
            background: #2d2d44;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 5px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #0099ff);
            border-radius: 10px;
            transition: width 0.5s;
        }}
        .module-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
        }}
        .module-card {{
            background: #2d2d44;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.2s;
        }}
        .module-card:hover {{
            transform: scale(1.05);
        }}
        .module-name {{
            font-weight: bold;
            color: #00d4ff;
        }}
        .module-count {{
            font-size: 1.5em;
            color: #fff;
        }}
        .search-box {{
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #3d3d5c;
            border-radius: 25px;
            background: #1f1f2e;
            color: #e0e0e0;
            font-size: 1em;
            margin-bottom: 20px;
        }}
        .search-box:focus {{
            outline: none;
            border-color: #00d4ff;
        }}
        .tab-buttons {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .tab-btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 25px;
            background: #2d2d44;
            color: #e0e0e0;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .tab-btn:hover, .tab-btn.active {{
            background: #00d4ff;
            color: #1a1a2e;
        }}
        .highlight {{ background: rgba(0, 212, 255, 0.2); }}
        .number {{ text-align: right; font-family: monospace; }}
        @media (max-width: 768px) {{
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            h1 {{ font-size: 1.8em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Mapeamento Banco Sankhya</h1>
        <p class="subtitle">MMarra Data Hub - Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>

        <!-- Estatisticas Gerais -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{mapeamento.get("estatisticas", {}).get("total_tabelas", 0):,}</div>
                <div class="stat-label">Total de Tabelas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{mapeamento.get("estatisticas", {}).get("total_prefixos", 0)}</div>
                <div class="stat-label">Modulos/Prefixos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(relacionamentos)}</div>
                <div class="stat-label">Relacionamentos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(views)}</div>
                <div class="stat-label">Views</div>
            </div>
        </div>

        <!-- TOP 20 Tabelas por Volume -->
        <div class="section">
            <h2>TOP 20 Tabelas por Volume de Dados</h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Tabela</th>
                        <th>Modulo</th>
                        <th class="number">Registros</th>
                        <th>Volume Relativo</th>
                    </tr>
                </thead>
                <tbody>'''

    # TOP 20 tabelas
    max_registros = tabelas_volume[0]["registros"] if tabelas_volume else 1
    for i, t in enumerate(tabelas_volume[:20]):
        if t["registros"] > 0:
            nome = t["tabela"]
            registros = t["registros"]
            pct = (registros / max_registros) * 100

            # Badge por prefixo
            if nome.startswith("TGF"):
                badge = "badge-tgf"
                modulo = "Comercial"
            elif nome.startswith("TGW"):
                badge = "badge-tgw"
                modulo = "WMS"
            elif nome.startswith("TSI"):
                badge = "badge-tsi"
                modulo = "Sistema"
            elif nome.startswith("AD_"):
                badge = "badge-ad"
                modulo = "Custom"
            else:
                badge = "badge-other"
                modulo = nome[:3]

            html += f'''
                    <tr>
                        <td>{i+1}</td>
                        <td><strong>{nome}</strong></td>
                        <td><span class="badge {badge}">{modulo}</span></td>
                        <td class="number">{registros:,}</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {pct:.1f}%"></div>
                            </div>
                        </td>
                    </tr>'''

    html += '''
                </tbody>
            </table>
        </div>

        <!-- Modulos/Prefixos -->
        <div class="section">
            <h2>Distribuicao por Modulo</h2>
            <div class="module-grid">'''

    for prefixo, tabelas in prefixos_ordenados[:20]:
        html += f'''
                <div class="module-card">
                    <div class="module-name">{prefixo}</div>
                    <div class="module-count">{len(tabelas)}</div>
                    <div style="color: #888; font-size: 0.8em;">tabelas</div>
                </div>'''

    html += '''
            </div>
        </div>

        <!-- Estrutura das Tabelas Principais -->
        <div class="section">
            <h2>Estrutura das Tabelas Principais</h2>
            <input type="text" class="search-box" id="searchTable" placeholder="Buscar tabela..." onkeyup="filterTables()">
            <table id="tableDetails">
                <thead>
                    <tr>
                        <th>Tabela</th>
                        <th>Descricao</th>
                        <th class="number">Registros</th>
                        <th class="number">Colunas</th>
                        <th>Colunas Principais</th>
                    </tr>
                </thead>
                <tbody>'''

    # Descricoes das tabelas principais
    descricoes = {
        "TGFCAB": "Cabecalho de Notas (vendas, compras, transferencias)",
        "TGFITE": "Itens das Notas (produtos por nota)",
        "TGFPAR": "Parceiros (clientes e fornecedores)",
        "TGFPRO": "Produtos (cadastro de produtos)",
        "TGFVEN": "Vendedores",
        "TGFFIN": "Financeiro (titulos a pagar/receber)",
        "TGFEST": "Estoque (saldo por empresa/local)",
        "TGFCOT": "Cotacoes (cabecalho)",
        "TGFITC": "Itens de Cotacao",
        "TGFTOP": "Tipos de Operacao (TOP)",
        "TGFNAT": "Naturezas Financeiras",
        "TGFEMP": "Empresas",
        "TGFPRC": "Precos (lista de precos)",
        "TGFCUS": "Custos (historico de custos)",
        "TGFDIN": "Dinamica (campos dinamicos)",
        "TGFEXC": "Excecoes de Preco (preco especial por produto)",
        "TGFVAR": "Variacoes/Grade de Produtos",
        "TGFCPL": "Complemento de Nota",
        "TGWEST": "Estoque WMS (por endereco)",
        "TGWEND": "Enderecos WMS (localizacoes)",
        "TGWREC": "Recebimento WMS",
        "TGWSEP": "Separacao WMS (cabecalho)",
        "TGWEMPE": "Empenho (vinculo venda-compra)",
        "TGWSXN": "Separacao WMS (itens)",
        "TGWCON": "Conferencia WMS",
        "TSIUSU": "Usuarios do Sistema",
        "TSIEMP": "Empresas do Sistema",
        "TSILOG": "Log do Sistema",
        "TSICID": "Cidades",
        "TSIBAI": "Bairros",
        "TSICFG": "Configuracoes do Sistema",
    }

    for tabela, dados in sorted(tabelas_detalhes.items()):
        registros = dados.get("registros", 0)
        colunas = dados.get("colunas", [])
        qtd_colunas = len(colunas)

        # Colunas principais (primeiras 5)
        cols_principais = ", ".join([c["nome"] for c in colunas[:5]]) if colunas else "-"

        descricao = descricoes.get(tabela, "-")

        html += f'''
                    <tr>
                        <td><strong>{tabela}</strong></td>
                        <td>{descricao}</td>
                        <td class="number">{registros:,}</td>
                        <td class="number">{qtd_colunas}</td>
                        <td style="font-size: 0.85em; color: #888;">{cols_principais}</td>
                    </tr>'''

    html += '''
                </tbody>
            </table>
        </div>

        <!-- Relacionamentos -->
        <div class="section">
            <h2>Relacionamentos Principais</h2>
            <p style="color: #888; margin-bottom: 15px;">Foreign Keys entre tabelas principais</p>
            <table>
                <thead>
                    <tr>
                        <th>Tabela Origem</th>
                        <th>Coluna</th>
                        <th style="text-align: center;">→</th>
                        <th>Tabela Destino</th>
                        <th>Coluna</th>
                    </tr>
                </thead>
                <tbody>'''

    # Filtrar relacionamentos importantes
    tabelas_importantes = ['TGFCAB', 'TGFITE', 'TGFPAR', 'TGFPRO', 'TGFFIN', 'TGFEST', 'TGFCOT', 'TGFITC', 'TGWEMPE', 'TGWEST', 'TGWEND']
    rels_mostrados = 0
    for rel in relacionamentos:
        if rel["tabela_origem"] in tabelas_importantes or rel["tabela_destino"] in tabelas_importantes:
            html += f'''
                    <tr>
                        <td><strong>{rel["tabela_origem"]}</strong></td>
                        <td>{rel["coluna_origem"]}</td>
                        <td style="text-align: center; color: #00d4ff;">→</td>
                        <td><strong>{rel["tabela_destino"]}</strong></td>
                        <td>{rel["coluna_destino"]}</td>
                    </tr>'''
            rels_mostrados += 1
            if rels_mostrados >= 30:
                break

    html += '''
                </tbody>
            </table>
        </div>

        <!-- Recomendacoes para Extracao -->
        <div class="section">
            <h2>Recomendacoes para Extracao de Dados</h2>
            <table>
                <thead>
                    <tr>
                        <th>Modulo</th>
                        <th>Tabelas Principais</th>
                        <th>Prioridade</th>
                        <th>Observacoes</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><span class="badge badge-tgf">Comercial</span></td>
                        <td>TGFCAB + TGFITE + TGFPAR + TGFPRO</td>
                        <td><strong style="color: #00ff88;">ALTA</strong></td>
                        <td>Vendas, compras, clientes, produtos - core do negocio</td>
                    </tr>
                    <tr>
                        <td><span class="badge badge-tgf">Financeiro</span></td>
                        <td>TGFFIN + TGFNAT</td>
                        <td><strong style="color: #00ff88;">ALTA</strong></td>
                        <td>Titulos a pagar/receber, naturezas</td>
                    </tr>
                    <tr>
                        <td><span class="badge badge-tgf">Estoque</span></td>
                        <td>TGFEST + TGWEST + TGWEND</td>
                        <td><strong style="color: #00ff88;">ALTA</strong></td>
                        <td>Saldo estoque ERP e WMS por endereco</td>
                    </tr>
                    <tr>
                        <td><span class="badge badge-tgw">WMS</span></td>
                        <td>TGWREC + TGWSEP + TGWEMPE</td>
                        <td><strong style="color: #ffff00;">MEDIA</strong></td>
                        <td>Recebimento, separacao, empenho</td>
                    </tr>
                    <tr>
                        <td><span class="badge badge-tgf">Cotacao</span></td>
                        <td>TGFCOT + TGFITC</td>
                        <td><strong style="color: #ffff00;">MEDIA</strong></td>
                        <td>Processo de cotacao de compras</td>
                    </tr>
                    <tr>
                        <td><span class="badge badge-tgf">Precos</span></td>
                        <td>TGFPRC + TGFCUS</td>
                        <td><strong style="color: #ffff00;">MEDIA</strong></td>
                        <td>Lista de precos e historico de custos</td>
                    </tr>
                    <tr>
                        <td><span class="badge badge-tsi">Sistema</span></td>
                        <td>TSIUSU + TSIEMP + TGFTOP</td>
                        <td><strong style="color: #888;">BAIXA</strong></td>
                        <td>Usuarios, empresas, tipos de operacao (auxiliares)</td>
                    </tr>
                </tbody>
            </table>
        </div>

    </div>

    <script>
        function filterTables() {{
            const input = document.getElementById('searchTable').value.toLowerCase();
            const rows = document.querySelectorAll('#tableDetails tbody tr');
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(input) ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>'''

    # Salvar HTML
    output_file = "relatorio_schema_banco.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] Relatorio gerado: {output_file}")

if __name__ == "__main__":
    gerar_html()
