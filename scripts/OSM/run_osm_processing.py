#!/usr/bin/env python3
"""
Script principal para procesar datos de OpenStreetMap y extraer sitios turísticos.
Este script ejecuta todo el flujo de trabajo: filtrado y análisis.
"""

import subprocess
import time
from pathlib import Path

def run_command(command, description):
    """Ejecuta un comando y muestra el progreso."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"📝 Comando: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        subprocess.run(command, shell=True, check=True, 
                       capture_output=False, text=True)
        
        duration = time.time() - start_time
        print(f"\n✅ {description} completado en {duration:.2f} segundos")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error ejecutando {description}: {e}")
        return False

def main():
    """Función principal que ejecuta todo el proceso."""
    print("🌍 PROCESAMIENTO COMPLETO DE SITIOS TURÍSTICOS DESDE OPENSTREETMAP")
    print("=" * 80)
    
    # Directorios base
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent  # D:\TravelApp\Project
    data_dir = project_root / "scripts" / "data"
    data_dir.mkdir(exist_ok=True)

    # Verificar que los scripts requeridos existen
    if not (script_dir / "filter_osm_sites.py").exists():
        print("❌ Error: No se encontró filter_osm_sites.py en el directorio actual")
        return

    # Verificar que el archivo OSM existe
    osm_file = Path(r"D:\TravelApp\OSM\planet-250609.osm.pbf")
    if not osm_file.exists():
        print(f"❌ Error: No se encontró el archivo OSM en {osm_file}")
        return

    # Mostrar info del archivo OSM
    file_size_gb = osm_file.stat().st_size / (1024**3)
    print(f"📁 Archivo OSM encontrado: {osm_file}")
    print(f"📏 Tamaño: {file_size_gb:.2f} GB")
    
    if file_size_gb > 5:
        print("⚠️  ADVERTENCIA: El archivo es muy grande (>5GB)")
        response = input("\n¿Deseas continuar? (s/N): ").strip().lower()
        if response not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Procesamiento cancelado")
            return

    # Paso 1: Filtrado de sitios turísticos
    print(f"\n📋 PASO 1: FILTRADO DE SITIOS TURÍSTICOS")
    output_file = data_dir / "sites_filtered.jsonl"
    
    if output_file.exists() and output_file.stat().st_size > 100 * 1024 * 1024:
        print(f"🟡 Archivo de salida ya existe: {output_file}")
        print(f"📏 Tamaño: {output_file.stat().st_size / (1024**2):.2f} MB")
        print("✅ Saltando paso de filtrado")
    else:
        success = run_command(
            "python filter_osm_sites.py",
            "Filtrado de sitios turísticos desde OSM"
        )
        if not success or not output_file.exists():
            print("❌ Error en el filtrado. Deteniendo el proceso.")
            return

    # Paso 2: Análisis
    print(f"\n📋 PASO 2: ANÁLISIS DE RESULTADOS")
    success = run_command(
        f"python {script_dir / 'analyze_sites.py'}",
        "Análisis de sitios filtrados"
    )

    
    if not success:
        print("❌ Error en el análisis. Continuando...")

    # Final
    print(f"\n{'='*80}")
    print("🎉 PROCESAMIENTO COMPLETADO")
    print(f"{'='*80}")
    print(f"📁 Archivo OSM procesado: {osm_file}")
    print(f"📄 Sitios filtrados guardados en: {output_file}")
    print(f"📊 Análisis completado")
    print(f"\n📋 PRÓXIMOS PASOS:")
    print(f"   1. Revisa el archivo {output_file}")
    print(f"   2. Ejecuta 'python load_sites_to_mongodb.py' para cargar en MongoDB")
    print(f"   3. Ejecuta 'python example_sites_usage.py' para probar consultas")
    print(f"\n✅ ¡Todo listo!")

if __name__ == "__main__":
    main()
