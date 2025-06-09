from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import re
import logging
from app.utils.pagination import PaginationParams, create_paginated_response

logger = logging.getLogger(__name__)

def build_search_query(
    search_term: Optional[str] = None,
    search_fields: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    date_range: Optional[Dict[str, datetime]] = None,
    numeric_range: Optional[Dict[str, Dict[str, Union[int, float]]]] = None
) -> Dict[str, Any]:
    """
    Construir query de búsqueda
    
    Args:
        search_term: Término de búsqueda
        search_fields: Campos a buscar
        filters: Filtros adicionales
        date_range: Rango de fechas
        numeric_range: Rango numérico
    
    Returns:
        Dict[str, Any]: Query de búsqueda
    """
    query = {}
    
    # Búsqueda por texto
    if search_term and search_fields:
        search_conditions = []
        for field in search_fields:
            search_conditions.append({
                field: {"$regex": search_term, "$options": "i"}
            })
        if search_conditions:
            query["$or"] = search_conditions
    
    # Filtros adicionales
    if filters:
        for field, value in filters.items():
            if value is not None:
                query[field] = value
    
    # Rango de fechas
    if date_range:
        for field, range_dict in date_range.items():
            date_query = {}
            if "start" in range_dict:
                date_query["$gte"] = range_dict["start"]
            if "end" in range_dict:
                date_query["$lte"] = range_dict["end"]
            if date_query:
                query[field] = date_query
    
    # Rango numérico
    if numeric_range:
        for field, range_dict in numeric_range.items():
            numeric_query = {}
            if "min" in range_dict:
                numeric_query["$gte"] = range_dict["min"]
            if "max" in range_dict:
                numeric_query["$lte"] = range_dict["max"]
            if numeric_query:
                query[field] = numeric_query
    
    return query

def build_aggregation_pipeline(
    search_query: Dict[str, Any],
    sort_params: Optional[Dict[str, int]] = None,
    skip: int = 0,
    limit: int = 20,
    facet_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Construir pipeline de agregación
    
    Args:
        search_query: Query de búsqueda
        sort_params: Parámetros de ordenamiento
        skip: Número de documentos a saltar
        limit: Límite de documentos
        facet_fields: Campos para facetas
    
    Returns:
        List[Dict[str, Any]]: Pipeline de agregación
    """
    pipeline = []
    
    # Match stage
    if search_query:
        pipeline.append({"$match": search_query})
    
    # Facet stage
    if facet_fields:
        facet_stage = {}
        for field in facet_fields:
            facet_stage[field] = [
                {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
        pipeline.append({"$facet": facet_stage})
    
    # Sort stage
    if sort_params:
        pipeline.append({"$sort": sort_params})
    
    # Pagination stages
    pipeline.extend([
        {"$skip": skip},
        {"$limit": limit}
    ])
    
    return pipeline

async def search_documents(
    collection: Any,
    search_term: Optional[str] = None,
    search_fields: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    date_range: Optional[Dict[str, Dict[str, datetime]]] = None,
    numeric_range: Optional[Dict[str, Dict[str, Union[int, float]]]] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 20,
    facet_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Buscar documentos
    
    Args:
        collection: Colección de MongoDB
        search_term: Término de búsqueda
        search_fields: Campos a buscar
        filters: Filtros adicionales
        date_range: Rango de fechas
        numeric_range: Rango numérico
        sort_by: Campo para ordenar
        sort_order: Orden de clasificación
        page: Página actual
        page_size: Tamaño de página
        facet_fields: Campos para facetas
    
    Returns:
        Dict[str, Any]: Resultados de búsqueda
    """
    try:
        # Construir query
        search_query = build_search_query(
            search_term=search_term,
            search_fields=search_fields,
            filters=filters,
            date_range=date_range,
            numeric_range=numeric_range
        )
        
        # Construir pipeline
        sort_params = {sort_by: 1 if sort_order == "asc" else -1} if sort_by else None
        skip = (page - 1) * page_size
        
        pipeline = build_aggregation_pipeline(
            search_query=search_query,
            sort_params=sort_params,
            skip=skip,
            limit=page_size,
            facet_fields=facet_fields
        )
        
        # Ejecutar búsqueda
        results = await collection.aggregate(pipeline).to_list(length=page_size)
        
        # Obtener total
        total = await collection.count_documents(search_query)
        
        # Crear respuesta paginada
        return create_paginated_response(
            items=results,
            total_items=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise

def highlight_search_term(text: str, search_term: str) -> str:
    """
    Resaltar término de búsqueda en texto
    
    Args:
        text: Texto original
        search_term: Término de búsqueda
    
    Returns:
        str: Texto con término resaltado
    """
    if not search_term:
        return text
    
    pattern = re.compile(f"({re.escape(search_term)})", re.IGNORECASE)
    return pattern.sub(r"<mark>\1</mark>", text)

async def get_search_suggestions(
    collection: Any,
    field: str,
    prefix: str,
    limit: int = 10
) -> List[str]:
    """
    Obtener sugerencias de búsqueda
    
    Args:
        collection: Colección de MongoDB
        field: Campo para sugerencias
        prefix: Prefijo de búsqueda
        limit: Límite de sugerencias
    
    Returns:
        List[str]: Lista de sugerencias
    """
    try:
        pipeline = [
            {
                "$match": {
                    field: {"$regex": f"^{re.escape(prefix)}", "$options": "i"}
                }
            },
            {
                "$group": {
                    "_id": f"${field}",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": limit
            }
        ]
        
        results = await collection.aggregate(pipeline).to_list(length=limit)
        return [doc["_id"] for doc in results]
    
    except Exception as e:
        logger.error(f"Error getting search suggestions: {str(e)}")
        raise 