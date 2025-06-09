from typing import Any, Dict, List, Optional, Union, Callable
import json
import functools
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

class Cache:
    """Clase para manejo de caché con Redis"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor de caché
        
        Args:
            key: Clave de caché
        
        Returns:
            Any: Valor almacenado o None
        """
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache value: {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Guardar valor en caché
        
        Args:
            key: Clave de caché
            value: Valor a almacenar
            ttl: Tiempo de vida en segundos
        
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            value = json.dumps(value)
            if ttl:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache value: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Eliminar valor de caché
        
        Args:
            key: Clave de caché
        
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache value: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Verificar si existe clave
        
        Args:
            key: Clave de caché
        
        Returns:
            bool: True si existe
        """
        try:
            return await self.redis.exists(key)
        except Exception as e:
            logger.error(f"Error checking cache key: {str(e)}")
            return False
    
    async def ttl(self, key: str) -> Optional[int]:
        """
        Obtener tiempo de vida restante
        
        Args:
            key: Clave de caché
        
        Returns:
            int: Tiempo restante en segundos o None
        """
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Error getting cache TTL: {str(e)}")
            return None
    
    async def clear(self) -> bool:
        """
        Limpiar toda la caché
        
        Returns:
            bool: True si se limpió correctamente
        """
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Incrementar valor numérico
        
        Args:
            key: Clave de caché
            amount: Cantidad a incrementar
        
        Returns:
            int: Nuevo valor o None
        """
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing cache value: {str(e)}")
            return None
    
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Decrementar valor numérico
        
        Args:
            key: Clave de caché
            amount: Cantidad a decrementar
        
        Returns:
            int: Nuevo valor o None
        """
        try:
            return await self.redis.decrby(key, amount)
        except Exception as e:
            logger.error(f"Error decrementing cache value: {str(e)}")
            return None
    
    async def set_many(
        self,
        mapping: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Guardar múltiples valores
        
        Args:
            mapping: Diccionario de clave-valor
            ttl: Tiempo de vida en segundos
        
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            pipeline = self.redis.pipeline()
            for key, value in mapping.items():
                value = json.dumps(value)
                if ttl:
                    pipeline.setex(key, ttl, value)
                else:
                    pipeline.set(key, value)
            await pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"Error setting multiple cache values: {str(e)}")
            return False
    
    async def get_many(self, keys: list) -> dict:
        """
        Obtener múltiples valores
        
        Args:
            keys: Lista de claves
        
        Returns:
            dict: Diccionario de clave-valor
        """
        try:
            values = await self.redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            logger.error(f"Error getting multiple cache values: {str(e)}")
            return {}
    
    async def delete_many(self, keys: list) -> bool:
        """
        Eliminar múltiples valores
        
        Args:
            keys: Lista de claves
        
        Returns:
            bool: True si se eliminaron correctamente
        """
        try:
            await self.redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error deleting multiple cache values: {str(e)}")
            return False
    
    async def set_hash(
        self,
        key: str,
        mapping: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Guardar hash
        
        Args:
            key: Clave de caché
            mapping: Diccionario de campo-valor
            ttl: Tiempo de vida en segundos
        
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            pipeline = self.redis.pipeline()
            pipeline.hmset(key, mapping)
            if ttl:
                pipeline.expire(key, ttl)
            await pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"Error setting cache hash: {str(e)}")
            return False
    
    async def get_hash(self, key: str) -> dict:
        """
        Obtener hash
        
        Args:
            key: Clave de caché
        
        Returns:
            dict: Diccionario de campo-valor
        """
        try:
            return await self.redis.hgetall(key)
        except Exception as e:
            logger.error(f"Error getting cache hash: {str(e)}")
            return {}
    
    async def delete_hash_field(self, key: str, field: str) -> bool:
        """
        Eliminar campo de hash
        
        Args:
            key: Clave de caché
            field: Campo a eliminar
        
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            await self.redis.hdel(key, field)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache hash field: {str(e)}")
            return False

def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generar clave de caché
    
    Args:
        prefix: Prefijo de la clave
        args: Argumentos posicionales
        kwargs: Argumentos nombrados
    
    Returns:
        str: Clave generada
    """
    key_parts = [prefix]
    
    # Agregar argumentos posicionales
    if args:
        key_parts.extend([str(arg) for arg in args])
    
    # Agregar argumentos nombrados
    if kwargs:
        sorted_items = sorted(kwargs.items())
        key_parts.extend([f"{k}:{v}" for k, v in sorted_items])
    
    return ":".join(key_parts)

def get_cached_value(key: str) -> Optional[Any]:
    """
    Obtener valor de caché (síncrono)
    
    Args:
        key: Clave de caché
    
    Returns:
        Any: Valor almacenado o None
    """
    try:
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Error getting cached value: {str(e)}")
        return None

def set_cached_value(key: str, value: Any, ttl: int = 300) -> None:
    """
    Guardar valor en caché (síncrono)
    
    Args:
        key: Clave de caché
        value: Valor a almacenar
        ttl: Tiempo de vida en segundos
    """
    try:
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        value = json.dumps(value)
        redis_client.setex(key, ttl, value)
    except Exception as e:
        logger.error(f"Error setting cached value: {str(e)}")

def delete_cached_value(key: str) -> None:
    """
    Eliminar valor de caché (síncrono)
    
    Args:
        key: Clave de caché
    """
    try:
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_client.delete(key)
    except Exception as e:
        logger.error(f"Error deleting cached value: {str(e)}")

def clear_cache() -> None:
    """Limpiar toda la caché (síncrono)"""
    try:
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_client.flushdb()
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")

def cache(
    ttl: int = 300,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None,
    serializer: Optional[Callable] = None,
    deserializer: Optional[Callable] = None
) -> Callable:
    """
    Decorador para caché
    
    Args:
        ttl: Tiempo de vida en segundos
        key_prefix: Prefijo de la clave
        key_builder: Función para construir clave
        serializer: Función para serializar valor
        deserializer: Función para deserializar valor
    
    Returns:
        Callable: Decorador
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Construir clave de caché
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = get_cache_key(
                    key_prefix or func.__name__,
                    *args,
                    **kwargs
                )
            
            # Intentar obtener de caché
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                if deserializer:
                    return deserializer(cached_value)
                return cached_value
            
            # Ejecutar función
            result = await func(*args, **kwargs)
            
            # Guardar en caché
            if serializer:
                value = serializer(result)
            else:
                value = result
            
            await cache_manager.set(cache_key, value, ttl)
            
            return result
        return wrapper
    return decorator

def cache_key_builder(*args, **kwargs) -> str:
    """
    Constructor de clave de caché por defecto
    
    Args:
        args: Argumentos posicionales
        kwargs: Argumentos nombrados
    
    Returns:
        str: Clave generada
    """
    return get_cache_key("", *args, **kwargs)

def cache_serializer(value: Any) -> str:
    """
    Serializador de caché por defecto
    
    Args:
        value: Valor a serializar
    
    Returns:
        str: Valor serializado
    """
    return json.dumps(value)

def cache_deserializer(value: str) -> Any:
    """
    Deserializador de caché por defecto
    
    Args:
        value: Valor a deserializar
    
    Returns:
        Any: Valor deserializado
    """
    return json.loads(value)

# Instancia global de caché
cache_manager = Cache(redis.Redis.from_url(settings.REDIS_URL)) 