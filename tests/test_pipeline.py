"""Tests del pipeline de datos."""
import os
import sys
import json
import pytest
 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from pipeline import ejecutar_pipeline
 
 
def test_pipeline_ejecuta_correctamente(tmp_path):
    """El pipeline debe correr sin errores."""
    gold = ejecutar_pipeline('data/ventas.csv', str(tmp_path))
    assert gold is not None
    assert 'resumen' in gold
 
 
def test_pipeline_descarta_registros_invalidos(tmp_path):
    """El pipeline debe descartar filas con producto vacio o cantidad <= 0."""
    gold = ejecutar_pipeline('data/ventas.csv', str(tmp_path))
    crudos = gold['resumen']['registros_crudos']
    validos = gold['resumen']['registros_validos']
    assert validos < crudos  # Algunos se descartaron
    assert gold['resumen']['registros_descartados'] > 0
 
 
def test_pipeline_calcula_ingresos(tmp_path):
    """Los ingresos deben ser mayores a cero."""
    gold = ejecutar_pipeline('data/ventas.csv', str(tmp_path))
    assert gold['resumen']['ingresos_totales'] > 0
 
 
def test_pipeline_genera_metricas_por_ciudad(tmp_path):
    """Debe haber al menos una ciudad en los resultados."""
    gold = ejecutar_pipeline('data/ventas.csv', str(tmp_path))
    assert len(gold['ventas_ciudad']) > 0
 
 
def test_pipeline_genera_json_gold(tmp_path):
    """Debe generarse el archivo gold.json."""
    ejecutar_pipeline('data/ventas.csv', str(tmp_path))
    assert os.path.exists(os.path.join(str(tmp_path), 'gold.json'))
