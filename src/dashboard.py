"""Genera un dashboard HTML interactivo con Plotly."""
import json
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime


def generar_dashboard(gold_path, output_dir='output'):
    """Genera el dashboard HTML desde los datos Gold."""
    with open(gold_path) as f:
        gold = json.load(f)
 
    resumen = gold['resumen']
    env = gold['ambiente']
 
    # Crear subplots: 2x2
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Ventas por Ciudad',
            'Ventas por Categoria',
            'Tendencia Mensual',
            'Top Vendedores'
        ),
        specs=[
            [{'type': 'bar'}, {'type': 'pie'}],
            [{'type': 'scatter'}, {'type': 'bar'}]
        ]
    )
 
    # 1. Ventas por ciudad (barras)
    ciudades = gold['ventas_ciudad']
    fig.add_trace(go.Bar(
        x=[c['ciudad'] for c in ciudades],
        y=[c['total_ventas'] for c in ciudades],
        marker_color=['#2E75B6', '#1F4E79', '#71A6D2'],
        name='Ventas'
    ), row=1, col=1)
 
    # 2. Ventas por categoria (pie)
    cats = gold['ventas_categoria']
    fig.add_trace(go.Pie(
        labels=[c['categoria'] for c in cats],
        values=[c['total_ventas'] for c in cats],
        marker_colors=['#2E75B6', '#E65100'],
    ), row=1, col=2)
 
    # 3. Tendencia mensual (linea)
    meses = gold['ventas_mes']
    fig.add_trace(go.Scatter(
        x=[m['mes'] for m in meses],
        y=[m['total_ventas'] for m in meses],
        mode='lines+markers',
        line=dict(color='#2E75B6', width=3),
        name='Tendencia'
    ), row=2, col=1)
 
    # 4. Top vendedores (barras horizontales)
    vends = gold['top_vendedores']
    fig.add_trace(go.Bar(
        y=[v['vendedor'] for v in vends],
        x=[v['total_ventas'] for v in vends],
        orientation='h',
        marker_color='#1F4E79',
        name='Vendedores'
    ), row=2, col=2)
 
    fig.update_layout(
        title_text=f'Dashboard de Ventas | Ambiente: {env.upper()}',
        height=700, showlegend=False,
        template='plotly_white'
    )
 
    # Generar HTML completo
    chart_html = fig.to_html(include_plotlyjs='cdn', full_html=False)
 
    ing = resumen['ingresos_totales']
    ticket = resumen['ticket_promedio']
    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Dashboard de Ventas - {env}</title>
    <style>
        body {{ font-family: Arial; margin: 0; background: #f5f5f5; }}
        .header {{ background: #1F4E79; color: white; padding: 20px;
                   text-align: center; }}
        .header h1 {{ margin: 0; }}
        .env-badge {{ background: #2E75B6; padding: 5px 15px;
                      border-radius: 15px; font-size: 14px;
                      display: inline-block; margin-top: 8px; }}
        .kpis {{ display: flex; justify-content: center; gap: 20px;
                 padding: 20px; flex-wrap: wrap; }}
        .kpi {{ background: white; padding: 20px 30px;
               border-radius: 10px; text-align: center;
               box-shadow: 0 2px 4px rgba(0,0,0,0.1);
               min-width: 180px; }}
        .kpi .valor {{ font-size: 28px; font-weight: bold;
                       color: #1F4E79; }}
        .kpi .label {{ color: #666; font-size: 13px;
                       margin-top: 5px; }}
        .chart {{ padding: 20px; max-width: 1200px;
                  margin: 0 auto; }}
        .footer {{ text-align: center; padding: 20px;
                   color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Dashboard de Ventas</h1>
        <div class="env-badge">{env.upper()}</div>
    </div>
    <div class="kpis">
        <div class="kpi">
            <div class="valor">{resumen['total_transacciones']}</div>
            <div class="label">Transacciones</div>
        </div>
        <div class="kpi">
            <div class="valor">${ing:,.0f}</div>
            <div class="label">Ingresos Totales (COP)</div>
        </div>
        <div class="kpi">
            <div class="valor">${ticket:,.0f}</div>
            <div class="label">Ticket Promedio</div>
        </div>
        <div class="kpi">
            <div class="valor">{resumen['registros_validos']}/{resumen['registros_crudos']}</div>
            <div class="label">Calidad de Datos</div>
        </div>
    </div>
    <div class="chart">{chart_html}</div>
    <div class="footer">
        Generado automaticamente por GitHub Actions |
        Pipeline de Datos - IU Digital de Antioquia |
        {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</body></html>'''
 
    html_path = os.path.join(output_dir, 'index.html')
    with open(html_path, 'w') as f:
        f.write(html)
    print(f'Dashboard generado: {html_path}')
    return html_path


if __name__ == '__main__':
    generar_dashboard('output/gold.json')
