# 📊 Pipeline de Datos con DuckDB + GitHub Pages

Pipeline ETL automatizado que procesa datos de ventas, aplica arquitectura Medallion (Bronze → Silver → Gold) y publica un dashboard interactivo en GitHub Pages — todo orquestado con GitHub Actions.

🔗 **Dashboard en vivo:** [https://darkanita.github.io/pipeline-datos-duckdb/](https://darkanita.github.io/pipeline-datos-duckdb/)

---

## ¿Qué hace este proyecto?

```
ventas.csv → DuckDB limpia y transforma → Métricas Gold → Dashboard HTML con Plotly
                                                                    │
                                                    Publicado automáticamente en GitHub Pages
```

| Capa | Qué hace | Herramienta |
|------|----------|-------------|
| **Bronze** | Carga datos crudos desde CSV | DuckDB `read_csv_auto` |
| **Silver** | Filtra registros inválidos, normaliza texto, calcula totales | DuckDB SQL |
| **Gold** | Agrega métricas por ciudad, categoría, mes y vendedor | DuckDB SQL |
| **Dashboard** | Genera gráficas interactivas (barras, pie, línea, ranking) | Plotly |

## Arquitectura CI/CD

El proyecto usa tres ramas protegidas con tres ambientes de GitHub:

```
feature/* ──► PR a dev ──► CI (lint + tests) ──► merge ──► CD: pipeline en Development
dev        ──► PR a qa  ──► CI                ──► merge ──► CD: pipeline en QA
qa         ──► PR a main ─► CI                ──► merge ──► CD: pipeline + publica dashboard
                                                                     │
                                                     GitHub Pages (producción)
```

| Rama | Ambiente | Qué ejecuta el CD |
|------|----------|--------------------|
| `dev` | development | Pipeline ETL |
| `qa` | qa | Pipeline + genera dashboard (sin publicar) |
| `main` | production | Pipeline + dashboard + deploy a GitHub Pages |

**Reglas:**
- No se permite push directo a `dev`, `qa` ni `main`
- Todo cambio entra por Pull Request
- CI (lint + tests) debe pasar antes de poder fusionar
- Aprobación de un reviewer requerida

## Tecnologías

| Herramienta | Uso |
|-------------|-----|
| [DuckDB](https://duckdb.org/) | Base de datos analítica (SQL sobre archivos) |
| [pandas](https://pandas.pydata.org/) | Manipulación de datos |
| [Plotly](https://plotly.com/python/) | Gráficas interactivas |
| [GitHub Actions](https://docs.github.com/es/actions) | CI/CD automatizado |
| [GitHub Pages](https://pages.github.com/) | Hosting del dashboard |
| [flake8](https://flake8.pycqa.org/) | Linter para Python |
| [pytest](https://pytest.org/) | Tests automatizados |

## Estructura del proyecto

```
.
├── data/
│   └── ventas.csv                 # Bronze: datos crudos de ventas
├── src/
│   ├── pipeline.py                # ETL: Bronze → Silver → Gold
│   └── dashboard.py               # Genera HTML interactivo con Plotly
├── tests/
│   └── test_pipeline.py           # Tests automatizados del pipeline
├── docs/
│   └── guia-taller.md             # Guía paso a paso para replicar el proyecto
├── .github/
│   └── workflows/
│       ├── ci.yml                 # CI: lint + tests en cada PR
│       └── cd.yml                 # CD: deploy por ambiente
├── requirements.txt
├── .gitignore
└── README.md
```

## Ejecutar localmente

```bash
# Clonar el repositorio
git clone https://github.com/darkanita/pipeline-datos-duckdb.git
cd pipeline-datos-duckdb

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el pipeline
python src/pipeline.py

# Generar el dashboard
python src/dashboard.py

# Abrir el dashboard en el navegador
open output/index.html    # macOS
# o: start output/index.html    # Windows
# o: xdg-open output/index.html # Linux
```

## Ejecutar los tests

```bash
# Lint
flake8 src/ --max-line-length=100

# Tests
pytest tests/ -v
```

## ¿Cómo replicar este proyecto?

La guía completa paso a paso está en [`docs/guia-taller.md`](docs/guia-taller.md). Incluye:

- Configuración del entorno (Git + GitHub CLI)
- Creación del repositorio y las ramas
- Configuración de branch protection y environments
- Creación de los pipelines CI/CD
- Flujo completo feature → dev → qa → main
- Todo explicado con interfaz gráfica (GitHub web) y línea de comandos

## Datos de ejemplo

El archivo `data/ventas.csv` contiene datos simulados de ventas con errores intencionales para demostrar la limpieza de datos:

| Tipo de error | Ejemplo | Qué hace Silver |
|---------------|---------|-----------------|
| Producto vacío | Fila sin nombre de producto | Lo descarta |
| Cantidad negativa | cantidad = -2 | Lo descarta |
| Cantidad cero | cantidad = 0 | Lo descarta |

El pipeline reporta cuántos registros se descartaron y el porcentaje de calidad.

## Dashboard

El dashboard incluye 4 visualizaciones interactivas:

- **Ventas por ciudad** — Gráfica de barras
- **Ventas por categoría** — Gráfica de pie
- **Tendencia mensual** — Línea de tiempo
- **Top vendedores** — Barras horizontales

Además muestra KPIs: total de transacciones, ingresos totales, ticket promedio y calidad de datos.

---

**IU Digital de Antioquia** — Taller de Pipeline de Datos con CI/CD  
Instructora: Darkanita 🐧
