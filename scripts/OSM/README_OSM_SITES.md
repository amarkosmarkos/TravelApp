# Procesamiento de Sitios Turísticos desde OpenStreetMap

Este directorio contiene scripts para procesar datos de OpenStreetMap (OSM) y extraer sitios de interés turístico para tu aplicación de viajes.

## 🎯 Configuración Inicial

El script está configurado para usar tu archivo OSM específico:
- **Archivo OSM**: `D:\TravelApp\OSM\planet-250609.osm.pbf`
- **Salida**: `scripts/data/sites_filtered.json`

## 📁 Archivos Incluidos

### 1. `run_osm_processing.py` ⭐ **PRINCIPAL**
Script principal que ejecuta todo el proceso automáticamente.

**Funcionalidades:**
- Verifica que el archivo OSM existe
- Ejecuta el filtrado de sitios turísticos
- Ejecuta el análisis de resultados
- Muestra estadísticas completas

**Uso:**
```bash
cd scripts
python run_osm_processing.py
```

### 2. `filter_osm_sites.py`
Script para filtrar sitios turísticos desde un archivo OSM (.pbf).

**Funcionalidades:**
- Procesa archivos OSM (.pbf) usando la librería `osmium`
- Filtra elementos con tags de interés turístico:
  - `tourism` (hoteles, museos, atracciones, etc.)
  - `amenity` (restaurantes, cafés, servicios, etc.)
  - `historic` (monumentos, castillos, sitios históricos, etc.)
  - `leisure` (parques, instalaciones deportivas, etc.)
  - `natural` (puntos naturales, vistas, etc.)
  - `man_made` (estructuras artificiales, etc.)
  - `shop` (tiendas, centros comerciales, etc.)

**Datos extraídos:**
- ID único de OSM
- Tipo de elemento (node, way, relation)
- Coordenadas geográficas (para nodes)
- Tags completos de OSM
- Información específica: nombre, Wikidata, sitio web, teléfono, horarios, etc.

### 3. `analyze_sites.py`
Script para analizar el archivo JSON resultante y mostrar estadísticas detalladas.

**Funcionalidades:**
- Estadísticas por tipo de OSM
- Distribución por países y ciudades
- Análisis de tags de turismo por categoría
- Información sobre completitud de datos
- Ejemplos de sitios interesantes

### 4. `load_sites_to_mongodb.py`
Script para cargar los sitios filtrados en MongoDB (para uso posterior).

### 5. `example_sites_usage.py`
Script de ejemplo que muestra cómo consultar los sitios desde MongoDB.

## 🚀 Uso Rápido

### Opción 1: Procesamiento completo (Recomendado)
```bash
cd scripts
python run_osm_processing.py
```

### Opción 2: Procesamiento paso a paso
```bash
cd scripts

# Paso 1: Filtrar sitios turísticos
python filter_osm_sites.py

# Paso 2: Analizar resultados
python analyze_sites.py
```

## 📊 Resultados Esperados

Después del procesamiento, tendrás:

1. **Archivo JSON**: `scripts/data/sites_filtered.json`
   - Contiene todos los sitios turísticos filtrados
   - Formato: Un JSON por línea (JSONL)

2. **Estadísticas detalladas**:
   - Total de sitios encontrados
   - Distribución por tipo de OSM
   - Top países y ciudades
   - Análisis por categorías de turismo
   - Información sobre completitud de datos

## 📋 Estructura de Datos

Cada sitio en el JSON tiene la siguiente estructura:

```json
{
  "_id": "osm_node_123456",
  "osm_id": 123456,
  "osm_type": "node",
  "location": {
    "lat": 40.4168,
    "lon": -3.7038
  },
  "name": "Museo del Prado",
  "wikidata": "Q160112",
  "website": "https://www.museodelprado.es",
  "phone": "+34 913 30 28 00",
  "opening_hours": "Mo-Su 10:00-20:00",
  "description": "Museo nacional español",
  "addr_street": "Calle de Ruiz de Alarcón",
  "addr_city": "Madrid",
  "addr_country": "ES",
  "addr_postcode": "28014",
  "tags": {
    "tourism": "museum",
    "name": "Museo del Prado",
    "wikidata": "Q160112"
  }
}
```

## ⚠️ Notas Importantes

1. **Tamaño del archivo**: Tu archivo OSM (`planet-250609.osm.pbf`) es muy grande. El procesamiento puede tomar varias horas.

2. **Memoria**: El script está optimizado para manejar archivos grandes, pero asegúrate de tener suficiente RAM disponible.

3. **Progreso**: El script muestra el progreso cada 100,000 elementos procesados.

4. **Interrupción**: Si necesitas interrumpir el proceso, puedes usar Ctrl+C. Los datos procesados hasta ese momento se guardarán.

## 🔧 Personalización

### Cambiar la ruta del archivo OSM
Edita la variable `OSM_FILE` en `filter_osm_sites.py`:
```python
OSM_FILE = Path(r"tu/ruta/al/archivo.osm.pbf")
```

### Agregar más tags de interés
Edita la variable `INTERESTING_TAGS` en `filter_osm_sites.py`:
```python
INTERESTING_TAGS = {
    "tourism",
    "amenity", 
    "historic",
    "leisure",
    "natural",
    "man_made",
    "shop",
}
```

### Extraer información adicional
Modifica la función `extract_data()` en `filter_osm_sites.py` para extraer más campos.

## 📈 Próximos Pasos

Una vez que tengas el archivo JSON:

1. **Revisar resultados**: Ejecuta `python analyze_sites.py` para ver estadísticas
2. **Cargar en MongoDB**: Ejecuta `python load_sites_to_mongodb.py`
3. **Probar consultas**: Ejecuta `python example_sites_usage.py`

## 🛠️ Instalación de Dependencias

```bash
cd scripts
pip install -r requirements.txt
```

**Dependencias incluidas:**
- `osmium>=3.6.0` - Procesamiento de archivos OSM
- `pandas>=2.0.0` - Análisis de datos
- `requests>=2.31.0` - Peticiones HTTP
- `SQLAlchemy>=2.0.0` - ORM para bases de datos
- `psycopg2-binary>=2.9.0` - Driver PostgreSQL 