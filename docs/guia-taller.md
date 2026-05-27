# 🚀 Guía: Pipeline de Datos con DuckDB, CI/CD y GitHub Pages

**Institución:** IU Digital de Antioquia  
**Instructora:** Darkanita  
**Nivel:** Básico–Intermedio  
**Duración:** 4–5 horas

---

> ### 🎯 Convención de esta guía
>
> Cada operación se explica de dos formas:
>
> 🖱️ **Interfaz gráfica** — Pasos en la web de GitHub  
> ⌨️ **Línea de comandos** — El comando equivalente con `git` + `gh`
>
> Ambas hacen lo mismo. Usa la que prefieras.

---

## 0. Antes de empezar: Estandarizar la rama principal

Dependiendo de la versión de Git y cuándo creaste tu cuenta, tu rama principal puede llamarse `master` o `main`. Vamos a estandarizar en `main`.

> ⚠️ **¿Por qué existen dos nombres?** Antes de 2020, Git creaba la rama principal como `master`. En octubre de 2020, GitHub cambió el nombre por defecto a `main`. Ambos funcionan igual, pero es importante que todo el grupo use el mismo.

### 0.1 Verificar qué nombre tienes configurado

```bash
git config --global init.defaultBranch
# Si no muestra nada o muestra 'master', necesitas cambiarlo.
# Si muestra 'main', ya estás bien.
```

### 0.2 Configurar `main` como estándar

```bash
git config --global init.defaultBranch main
```

### 0.3 Si ya tienes un repositorio con `master`, renombrarlo

#### 🖱️ Interfaz gráfica

1. En tu repositorio, ve a **Settings** → **General**.
2. En **Default branch**, haz clic en el lápiz junto a `master`.
3. Escribe `main` y confirma.

#### ⌨️ Línea de comandos

```bash
git branch -m master main
git push -u origin main
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
gh api repos/$REPO --method PATCH --field default_branch=main
git push origin --delete master
```

### 0.4 Configurar GitHub para repos nuevos

#### 🖱️ Interfaz gráfica

1. Ve a [github.com/settings/repositories](https://github.com/settings/repositories).
2. En **Repository default branch**, cambia `master` a `main`.
3. Clic en **Update**.

> 🚨 **Todo esta guía usa `main`**. Si tu repo usa `master`, sigue estos pasos antes de continuar.

---

## 1. Visión general: ¿Qué vamos a construir?

Un pipeline de datos real con arquitectura Medallion que se ejecuta con GitHub Actions y publica un dashboard en GitHub Pages.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   BRONZE     │ ─▶ │   SILVER     │ ─▶ │    GOLD      │ ─▶ │  DASHBOARD   │
│  datos.csv   │    │  limpieza    │    │  métricas    │    │  HTML+Plotly │
│  (crudo)     │    │  (DuckDB)    │    │  (DuckDB)    │    │  (Pub. Web)  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

**Flujo CI/CD:**

```
feature/* ─▶ PR a dev ─▶ CI (lint+tests) ─▶ merge ─▶ CD: pipeline + preview
dev       ─▶ PR a qa  ─▶ CI              ─▶ merge ─▶ CD: pipeline + validación
qa        ─▶ PR a main─▶ CI              ─▶ merge ─▶ CD: pipeline + publica dashboard
                                                               │
                                           https://usuario.github.io/repo/
```

**Tecnologías:**

| Herramienta | Para qué | Costo |
|---|---|---|
| DuckDB | SQL sobre archivos CSV | Gratis |
| pandas | Manipulación de datos | Gratis |
| Plotly | Gráficas interactivas | Gratis |
| GitHub Actions | Pipeline automático | Gratis (repos públicos) |
| GitHub Pages | Publicar dashboard | Gratis |

---

## 2. Crear el repositorio

#### 🖱️ Interfaz gráfica

1. En GitHub, clic en **"+"** → **"New repository"**.
2. Nombre: `pipeline-datos-duckdb`, público, con README.
3. Clic en **"Create repository"**.

#### ⌨️ Línea de comandos

```bash
mkdir pipeline-datos-duckdb && cd pipeline-datos-duckdb
git init
echo "# Pipeline de Datos con DuckDB" > README.md
git add . && git commit -m "feat: crear repositorio"
gh repo create pipeline-datos-duckdb --public --source=. --push
```

---

## 3. Crear los datos de ejemplo (Bronze)

El CSV incluye errores intencionales para demostrar la limpieza de datos.

#### 🖱️ Interfaz gráfica

Crea `data/ventas.csv` con **Add file → Create new file**.

#### ⌨️ Línea de comandos

```bash
mkdir -p data

cat > data/ventas.csv << 'EOF'
fecha,producto,categoria,cantidad,precio_unitario,ciudad,vendedor
2026-01-15,Laptop Dell,Tecnologia,3,2500000,Medellin,Ana Torres
2026-01-15,Mouse Logitech,Tecnologia,10,85000,Bogota,Carlos Ruiz
2026-01-20,Escritorio,Muebles,2,450000,Cali,Diana Lopez
2026-01-22,Laptop HP,Tecnologia,5,2800000,Medellin,Ana Torres
2026-02-01,Silla Ergonomica,Muebles,8,380000,Bogota,Carlos Ruiz
2026-02-05,Monitor Samsung,Tecnologia,4,1200000,Medellin,Luis Garcia
2026-02-10,Teclado Mecanico,Tecnologia,15,250000,Cali,Diana Lopez
2026-02-14,Laptop Lenovo,Tecnologia,2,3200000,Bogota,Ana Torres
2026-02-20,Lampara LED,Muebles,12,95000,Medellin,Luis Garcia
2026-03-01,Laptop Dell,Tecnologia,7,2500000,Cali,Carlos Ruiz
2026-03-05,Webcam HD,Tecnologia,20,180000,Bogota,Diana Lopez
2026-03-10,Escritorio,Muebles,3,450000,Medellin,Ana Torres
2026-03-15,Laptop HP,Tecnologia,4,2800000,Cali,Luis Garcia
2026-03-20,Silla Ergonomica,Muebles,6,380000,Bogota,Carlos Ruiz
2026-03-25,,Tecnologia,5,150000,Medellin,Ana Torres
2026-03-28,Monitor Samsung,Tecnologia,-2,1200000,Bogota,Luis Garcia
2026-03-30,Teclado Mecanico,Tecnologia,0,250000,Cali,Diana Lopez
EOF
```

> 💡 Los datos incluyen errores a propósito: producto vacío (línea 15), cantidad negativa (línea 16) y cantidad cero (línea 17). El pipeline Silver los detectará y limpiará.

---

## 4. Crear el pipeline ETL

Crea `src/pipeline.py`:

```python
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

    ventas_ciudad = con.execute("""
        SELECT ciudad, SUM(venta_total) as total_ventas,
               COUNT(*) as num_transacciones
        FROM silver GROUP BY ciudad ORDER BY total_ventas DESC
    """).fetchdf().to_dict('records')

    ventas_categoria = con.execute("""
        SELECT categoria, SUM(venta_total) as total_ventas,
               SUM(cantidad) as unidades_vendidas
        FROM silver GROUP BY categoria ORDER BY total_ventas DESC
    """).fetchdf().to_dict('records')

    ventas_mes = con.execute("""
        SELECT STRFTIME(fecha, '%Y-%m') as mes,
               SUM(venta_total) as total_ventas,
               COUNT(*) as transacciones
        FROM silver GROUP BY mes ORDER BY mes
    """).fetchdf().to_dict('records')

    top_vendedores = con.execute("""
        SELECT vendedor, SUM(venta_total) as total_ventas,
               COUNT(*) as transacciones
        FROM silver GROUP BY vendedor ORDER BY total_ventas DESC
    """).fetchdf().to_dict('records')

    resumen = con.execute("""
        SELECT COUNT(*) as total_transacciones,
               SUM(venta_total) as ingresos_totales,
               AVG(venta_total) as ticket_promedio,
               MIN(fecha) as fecha_inicio,
               MAX(fecha) as fecha_fin
        FROM silver
    """).fetchdf().to_dict('records')[0]

    con.close()

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

    gold_path = os.path.join(output_dir, 'gold.json')
    with open(gold_path, 'w') as f:
        json.dump(gold, f, indent=2, default=str)
    print(f'\nGold guardado en: {gold_path}')

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
```

---

## 5. Crear el generador de dashboard

Crea `src/dashboard.py`:

```python
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

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Ventas por Ciudad', 'Ventas por Categoria',
            'Tendencia Mensual', 'Top Vendedores'
        ),
        specs=[
            [{'type': 'bar'}, {'type': 'pie'}],
            [{'type': 'scatter'}, {'type': 'bar'}]
        ]
    )

    # 1. Ventas por ciudad
    ciudades = gold['ventas_ciudad']
    fig.add_trace(go.Bar(
        x=[c['ciudad'] for c in ciudades],
        y=[c['total_ventas'] for c in ciudades],
        marker_color=['#2E75B6', '#1F4E79', '#71A6D2'],
        name='Ventas'
    ), row=1, col=1)

    # 2. Ventas por categoria
    cats = gold['ventas_categoria']
    fig.add_trace(go.Pie(
        labels=[c['categoria'] for c in cats],
        values=[c['total_ventas'] for c in cats],
        marker_colors=['#2E75B6', '#E65100'],
    ), row=1, col=2)

    # 3. Tendencia mensual
    meses = gold['ventas_mes']
    fig.add_trace(go.Scatter(
        x=[m['mes'] for m in meses],
        y=[m['total_ventas'] for m in meses],
        mode='lines+markers',
        line=dict(color='#2E75B6', width=3),
        name='Tendencia'
    ), row=2, col=1)

    # 4. Top vendedores
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
        .header {{ background: #1F4E79; color: white; padding: 20px; text-align: center; }}
        .header h1 {{ margin: 0; }}
        .env-badge {{ background: #2E75B6; padding: 5px 15px; border-radius: 15px;
                      font-size: 14px; display: inline-block; margin-top: 8px; }}
        .kpis {{ display: flex; justify-content: center; gap: 20px;
                 padding: 20px; flex-wrap: wrap; }}
        .kpi {{ background: white; padding: 20px 30px; border-radius: 10px;
               text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
               min-width: 180px; }}
        .kpi .valor {{ font-size: 28px; font-weight: bold; color: #1F4E79; }}
        .kpi .label {{ color: #666; font-size: 13px; margin-top: 5px; }}
        .chart {{ padding: 20px; max-width: 1200px; margin: 0 auto; }}
        .footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; }}
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
```

---

## 6. Crear los tests

Crea `tests/test_pipeline.py`:

```python
"""Tests del pipeline de datos."""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from pipeline import ejecutar_pipeline


def test_pipeline_ejecuta_correctamente(tmp_path):
    """El pipeline debe correr sin errores."""
    gold = ejecutar_pipeline('data/ventas.csv', str(tmp_path))
    assert gold is not None
    assert 'resumen' in gold


def test_pipeline_descarta_registros_invalidos(tmp_path):
    """Debe descartar filas con producto vacío o cantidad <= 0."""
    gold = ejecutar_pipeline('data/ventas.csv', str(tmp_path))
    crudos = gold['resumen']['registros_crudos']
    validos = gold['resumen']['registros_validos']
    assert validos < crudos
    assert gold['resumen']['registros_descartados'] > 0


def test_pipeline_calcula_ingresos(tmp_path):
    """Los ingresos deben ser mayores a cero."""
    gold = ejecutar_pipeline('data/ventas.csv', str(tmp_path))
    assert gold['resumen']['ingresos_totales'] > 0


def test_pipeline_genera_metricas_por_ciudad(tmp_path):
    """Debe haber al menos una ciudad."""
    gold = ejecutar_pipeline('data/ventas.csv', str(tmp_path))
    assert len(gold['ventas_ciudad']) > 0


def test_pipeline_genera_json_gold(tmp_path):
    """Debe generarse el archivo gold.json."""
    ejecutar_pipeline('data/ventas.csv', str(tmp_path))
    assert os.path.exists(os.path.join(str(tmp_path), 'gold.json'))
```

---

## 6.1 Requirements y .gitignore

```bash
cat > requirements.txt << 'EOF'
duckdb==1.2.1
pandas==2.2.3
plotly==6.0.1
pytest==8.3.4
flake8==7.1.1
EOF

cat > .gitignore << 'EOF'
__pycache__/
*.pyc
output/
.venv/
.env
.pytest_cache/
EOF
```

---

## 7. Crear los pipelines CI y CD

### 7.1 Pipeline CI (`.github/workflows/ci.yml`)

```yaml
name: "CI - Validacion"
on:
  pull_request:
    branches: [dev, qa, main]
jobs:
  ci:
    name: "Lint + Tests"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - name: Lint
        run: flake8 src/ --max-line-length=100
      - name: Tests
        run: pytest tests/ -v
      - name: Pipeline de prueba
        run: |
          python src/pipeline.py
          echo "Pipeline ejecutado correctamente en CI"
```

### 7.2 Pipeline CD (`.github/workflows/cd.yml`)

```yaml
name: "CD - Pipeline + Deploy"
on:
  push:
    branches: [dev, qa, main]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  pipeline-dev:
    name: "Pipeline Development"
    if: github.ref == 'refs/heads/dev'
    runs-on: ubuntu-latest
    environment: { name: development }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - name: Ejecutar pipeline
        env: { APP_ENV: development }
        run: |
          python src/pipeline.py
          echo "=== Pipeline DEV completado ==="

  pipeline-qa:
    name: "Pipeline QA"
    if: github.ref == 'refs/heads/qa'
    runs-on: ubuntu-latest
    environment: { name: qa }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - name: Ejecutar pipeline + validacion
        env: { APP_ENV: qa }
        run: |
          python src/pipeline.py
          python src/dashboard.py
          echo "=== Pipeline QA + Dashboard generado ==="

  pipeline-prod:
    name: "Pipeline Production"
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production
      url: ${{ steps.deploy.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - name: Ejecutar pipeline completo
        env: { APP_ENV: production }
        run: |
          python src/pipeline.py
          python src/dashboard.py
          echo "=== Pipeline PRODUCTION completado ==="
      - name: Configurar Pages
        uses: actions/configure-pages@v5
      - name: Subir artefacto
        uses: actions/upload-pages-artifact@v3
        with: { path: output }
      - name: Deploy a GitHub Pages
        id: deploy
        uses: actions/deploy-pages@v4
```

> ⚠️ **Si tu rama principal es `master`**, cambia `main` por `master` en ambos archivos YAML (en `branches:` y en `refs/heads/main`).

### 7.3 Activar GitHub Pages

#### 🖱️ Interfaz gráfica

1. Ve a **Settings** → **Pages**.
2. En **Source**, selecciona **GitHub Actions**.

#### ⌨️ Línea de comandos

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
gh api repos/$REPO/pages --method POST \
  --input - << 'EOF'
{ "build_type": "workflow" }
EOF
```

---

## 8. Configurar ramas, protecciones y ambientes

### 8.1 Crear ramas

#### 🖱️ Interfaz gráfica

Desde el selector de ramas, crear `dev` y `qa` desde `main`.

#### ⌨️ Línea de comandos

```bash
git checkout -b dev && git push -u origin dev
git checkout main
git checkout -b qa && git push -u origin qa
git checkout main
```

### 8.2 Proteger ramas y crear ambientes

#### 🖱️ Interfaz gráfica

Para cada rama (`dev`, `qa`, `main`):

1. **Settings** → **Branches** → **Add branch protection rule**.
2. Branch name pattern: nombre de la rama.
3. Marcar:
   - ☑ Require a pull request before merging (1 aprobación)
   - ☑ Dismiss stale pull request approvals
4. **Desmarcar** "Do not allow bypassing the above settings" (para poder usar `--admin` si trabajas solo).
5. Crear.

Para los ambientes:

1. **Settings** → **Environments** → **New environment**.
2. Crear: `development`, `qa`, `production`.

#### ⌨️ Línea de comandos

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

for BRANCH in dev qa main; do
  gh api repos/$REPO/branches/$BRANCH/protection \
    --method PUT \
    --input - << EOF
{
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "enforce_admins": false,
  "required_status_checks": null,
  "restrictions": null
}
EOF
done

gh api repos/$REPO/environments/development --method PUT
gh api repos/$REPO/environments/qa --method PUT
gh api repos/$REPO/environments/production --method PUT
```

> ⚠️ **`enforce_admins: false`** permite que el owner haga merge con `--admin` sin necesidad de aprobación. GitHub NO permite aprobar tu propio PR, así que este bypass es necesario para practicar en solitario.

---

## 9. Flujo completo: Feature → Dev → QA → Main

### Paso 1: Subir el código a dev vía PR

```bash
git checkout dev
git checkout -b feature/pipeline-inicial

git add .
git commit -m "feat: agregar pipeline de datos con DuckDB y dashboard"
git push origin feature/pipeline-inicial

gh pr create --base dev \
  --title "feat: pipeline de datos DuckDB" \
  --body "Pipeline ETL con medallion architecture + dashboard Plotly"

gh pr checks --watch
gh pr merge --squash --delete-branch --admin
```

### Paso 2: Promover a QA

```bash
gh pr create --base qa --head dev \
  --title "release: promover a QA" \
  --body "Cambios validados en dev."

gh pr checks --watch
gh pr merge --merge --admin
```

### Paso 3: Promover a Producción (publica el dashboard)

```bash
gh pr create --base main --head qa \
  --title "release: publicar dashboard" \
  --body "Validado en QA. Publicar dashboard en GitHub Pages."

gh pr checks --watch
gh pr merge --merge --admin
```

> 🎉 **Resultado:** El pipeline corre en modo production, genera el dashboard y lo publica en `https://TU_USUARIO.github.io/pipeline-datos-duckdb/`

### Verificar el dashboard

#### 🖱️ Interfaz gráfica

Ve a **Settings → Pages**. La URL aparecerá ahí. También en **Deployments → production**.

#### ⌨️ Línea de comandos

```bash
gh api repos/$REPO/pages --jq '.html_url'
```

---

## 10. Criterios de evaluación

| Criterio | Puntos |
|---|---|
| Repositorio con estructura correcta (data/, src/, tests/) | 10 |
| Datos Bronze con errores intencionales | 5 |
| Pipeline ETL funcional (Bronze→Silver→Gold) | 20 |
| Silver descarta registros inválidos | 10 |
| Gold genera métricas correctas | 10 |
| Dashboard HTML generado con Plotly | 10 |
| Tests automatizados que pasen | 10 |
| CI ejecuta lint + tests en PRs | 5 |
| CD despliega al ambiente correcto | 10 |
| Dashboard publicado en GitHub Pages | 10 |
| **Total** | **100** |

---

## 11. Qué aprendimos

| Concepto | Qué hicimos |
|---|---|
| Medallion Architecture | Bronze (CSV crudo) → Silver (limpio) → Gold (métricas) |
| DuckDB | SQL sobre archivos CSV directamente en Python |
| ETL | Extract (leer CSV), Transform (limpiar con SQL), Load (generar JSON) |
| Data Quality | Filtrar registros inválidos (nulos, negativos, ceros) |
| Plotly | Gráficas interactivas embebidas en HTML |
| GitHub Actions | Automatizar pipeline en cada merge |
| GitHub Pages | Publicar dashboard accesible por URL |
| Environments | Diferentes comportamientos por ambiente (dev/qa/prod) |
| Branch Protection | Todo cambio pasa por PR + CI + aprobación |

---

*Taller diseñado para la IU Digital de Antioquia por Darkanita* 🐧
