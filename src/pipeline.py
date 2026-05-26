"""
Pipeline de Datos - Arquitectura Medallion
Bronze (crudo) -> Silver (limpio) -> Gold (metricas)
IU Digital de Antioquia
"""
import duckdb
import json
import os


def ejecutar_pipeline(csv_path, output_dir='output'):
    """Ejecuta el pipeline ETL completo."""
    os.makedirs(output_dir, exist_ok=True)
    env = os.getenv('APP_ENV', 'local')
    print(f'=== Pipeline ejecutandose en: {env} ===')

    con = duckdb.connect(':memory:')

    # ── BRONZE: Cargar datos crudos ──
    print('\n--- BRONZE: Cargando datos crudos ---')
    con.execute(f"""
        CREATE TABLE bronze AS
        SELECT * FROM read_csv_auto('{csv_path}')
    """)
    total_bronze = con.execute('SELECT COUNT(*) FROM bronze').fetchone()[0]
    print(f'Registros cargados: {total_bronze}')

    # ── SILVER: Limpiar datos ──
    print('\n--- SILVER: Limpiando datos ---')
    con.execute("""
        CREATE TABLE silver AS
        SELECT
            fecha::DATE as fecha,
            TRIM(producto) as producto,
            TRIM(categoria) as categoria,
            cantidad,
            precio_unitario,
            TRIM(ciudad) as ciudad,
            TRIM(vendedor) as vendedor,
            (cantidad * precio_unitario) as venta_total
        FROM bronze
        WHERE producto IS NOT NULL
          AND LENGTH(TRIM(producto)) > 0
          AND cantidad > 0
    """)
    total_silver = con.execute('SELECT COUNT(*) FROM silver').fetchone()[0]
    descartados = total_bronze - total_silver
    print(f'Registros validos: {total_silver}')
    print(f'Registros descartados: {descartados}')

    # ── GOLD: Calcular metricas ──
    print('\n--- GOLD: Calculando metricas ---')

    # Ventas por ciudad
    ventas_ciudad = con.execute("""
        SELECT ciudad,
               SUM(venta_total) as total_ventas,
               COUNT(*) as num_transacciones
        FROM silver GROUP BY ciudad ORDER BY total_ventas DESC
    """).fetchdf().to_dict('records')

    # Ventas por categoria
    ventas_categoria = con.execute("""
        SELECT categoria,
               SUM(venta_total) as total_ventas,
               SUM(cantidad) as unidades_vendidas
        FROM silver GROUP BY categoria ORDER BY total_ventas DESC
    """).fetchdf().to_dict('records')

    # Ventas por mes
    ventas_mes = con.execute("""
        SELECT STRFTIME(fecha, '%Y-%m') as mes,
               SUM(venta_total) as total_ventas,
               COUNT(*) as transacciones
        FROM silver GROUP BY mes ORDER BY mes
    """).fetchdf().to_dict('records')

    # Top vendedores
    top_vendedores = con.execute("""
        SELECT vendedor,
               SUM(venta_total) as total_ventas,
               COUNT(*) as transacciones
        FROM silver GROUP BY vendedor ORDER BY total_ventas DESC
    """).fetchdf().to_dict('records')

    # Resumen general
    resumen = con.execute("""
        SELECT
            COUNT(*) as total_transacciones,
            SUM(venta_total) as ingresos_totales,
            AVG(venta_total) as ticket_promedio,
            MIN(fecha) as fecha_inicio,
            MAX(fecha) as fecha_fin
        FROM silver
    """).fetchdf().to_dict('records')[0]

    con.close()

    # Empaquetar resultados Gold
    gold = {
        'ambiente': env,
        'resumen': {
            'total_transacciones': int(resumen['total_transacciones']),
            'ingresos_totales': float(resumen['ingresos_totales']),
            'ticket_promedio': float(resumen['ticket_promedio']),
            'registros_crudos': total_bronze,
            'registros_validos': total_silver,
            'registros_descartados': descartados,
            'fecha_inicio': str(resumen['fecha_inicio']),
            'fecha_fin': str(resumen['fecha_fin']),
        },
        'ventas_ciudad': ventas_ciudad,
        'ventas_categoria': ventas_categoria,
        'ventas_mes': ventas_mes,
        'top_vendedores': top_vendedores,
    }

    # Guardar Gold como JSON
    gold_path = os.path.join(output_dir, 'gold.json')
    with open(gold_path, 'w') as f:
        json.dump(gold, f, indent=2, default=str)
    print(f'\nGold guardado en: {gold_path}')

    # Imprimir resumen
    print(f'\n=== RESUMEN DEL PIPELINE ===')
    print(f'Ambiente:       {env}')
    print(f'Transacciones:  {gold["resumen"]["total_transacciones"]}')
    r = gold['resumen']['ingresos_totales']
    print(f'Ingresos:       ${r:,.0f} COP')
    print(f'Calidad:        {total_silver}/{total_bronze}',
          f'({total_silver/total_bronze*100:.0f}% validos)')

    return gold


if __name__ == '__main__':
    ejecutar_pipeline('data/ventas.csv')
