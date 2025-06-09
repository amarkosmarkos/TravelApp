import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime, timedelta
from functools import wraps
from app.utils.logging import get_logger, log_background_task

logger = get_logger(__name__)

class TaskManager:
    """Gestor de tareas en segundo plano"""
    
    def __init__(self):
        """Inicializar gestor de tareas"""
        self.tasks: Dict[str, asyncio.Task] = {}
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_task(
        self,
        name: str,
        func: Callable,
        *args: Any,
        **kwargs: Any
    ) -> asyncio.Task:
        """
        Iniciar tarea en segundo plano
        
        Args:
            name: Nombre de la tarea
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
        
        Returns:
            asyncio.Task: Tarea iniciada
        """
        if name in self.tasks:
            raise ValueError(f"Task {name} already exists")
        
        task = asyncio.create_task(
            self._run_task(name, func, *args, **kwargs)
        )
        self.tasks[name] = task
        return task
    
    async def schedule_task(
        self,
        name: str,
        func: Callable,
        interval: Union[int, float],
        *args: Any,
        **kwargs: Any
    ) -> asyncio.Task:
        """
        Programar tarea periódica
        
        Args:
            name: Nombre de la tarea
            func: Función a ejecutar
            interval: Intervalo en segundos
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
        
        Returns:
            asyncio.Task: Tarea programada
        """
        if name in self.scheduled_tasks:
            raise ValueError(f"Scheduled task {name} already exists")
        
        task = asyncio.create_task(
            self._run_scheduled_task(name, func, interval, *args, **kwargs)
        )
        self.scheduled_tasks[name] = task
        return task
    
    async def stop_task(self, name: str) -> bool:
        """
        Detener tarea
        
        Args:
            name: Nombre de la tarea
        
        Returns:
            bool: True si se detuvo correctamente
        """
        task = self.tasks.get(name)
        if not task:
            return False
        
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        del self.tasks[name]
        return True
    
    async def stop_scheduled_task(self, name: str) -> bool:
        """
        Detener tarea programada
        
        Args:
            name: Nombre de la tarea
        
        Returns:
            bool: True si se detuvo correctamente
        """
        task = self.scheduled_tasks.get(name)
        if not task:
            return False
        
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        del self.scheduled_tasks[name]
        return True
    
    async def stop_all_tasks(self) -> None:
        """Detener todas las tareas"""
        for name in list(self.tasks.keys()):
            await self.stop_task(name)
        
        for name in list(self.scheduled_tasks.keys()):
            await self.stop_scheduled_task(name)
    
    async def _run_task(
        self,
        name: str,
        func: Callable,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Ejecutar tarea con logging
        
        Args:
            name: Nombre de la tarea
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
        """
        start_time = datetime.now()
        try:
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
            status = "completed"
        except Exception as e:
            logger.error(f"Task {name} failed: {str(e)}")
            status = "failed"
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            log_background_task(
                logger,
                name,
                status,
                duration
            )
    
    async def _run_scheduled_task(
        self,
        name: str,
        func: Callable,
        interval: Union[int, float],
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Ejecutar tarea programada
        
        Args:
            name: Nombre de la tarea
            func: Función a ejecutar
            interval: Intervalo en segundos
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
        """
        while True:
            await self._run_task(name, func, *args, **kwargs)
            await asyncio.sleep(interval)

def background_task(name: Optional[str] = None):
    """
    Decorador para tareas en segundo plano
    
    Args:
        name: Nombre opcional de la tarea
    
    Returns:
        Callable: Función decorada
    """
    def decorator(func: Callable) -> Callable:
        task_name = name or func.__name__
        
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = datetime.now()
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                status = "completed"
                return result
            except Exception as e:
                logger.error(f"Task {task_name} failed: {str(e)}")
                status = "failed"
                raise
            finally:
                duration = (datetime.now() - start_time).total_seconds()
                log_background_task(
                    logger,
                    task_name,
                    status,
                    duration
                )
        
        return wrapper
    
    return decorator

def scheduled_task(
    interval: Union[int, float],
    name: Optional[str] = None
):
    """
    Decorador para tareas programadas
    
    Args:
        interval: Intervalo en segundos
        name: Nombre opcional de la tarea
    
    Returns:
        Callable: Función decorada
    """
    def decorator(func: Callable) -> Callable:
        task_name = name or func.__name__
        
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> None:
            while True:
                start_time = datetime.now()
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func(*args, **kwargs)
                    else:
                        func(*args, **kwargs)
                    status = "completed"
                except Exception as e:
                    logger.error(f"Scheduled task {task_name} failed: {str(e)}")
                    status = "failed"
                finally:
                    duration = (datetime.now() - start_time).total_seconds()
                    log_background_task(
                        logger,
                        task_name,
                        status,
                        duration
                    )
                await asyncio.sleep(interval)
        
        return wrapper
    
    return decorator

# Instancia global del gestor de tareas
task_manager = TaskManager() 