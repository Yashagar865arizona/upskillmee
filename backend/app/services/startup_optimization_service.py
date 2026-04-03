"""
Startup optimization service for managing application initialization and resource usage.
"""

import asyncio
import logging
import time
import psutil
import gc
from typing import Dict, List, Callable, Any, Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
import signal
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ServicePriority(Enum):
    """Service initialization priority levels"""
    CRITICAL = 1    # Database, config, security
    HIGH = 2        # Authentication, core services
    MEDIUM = 3      # AI services, caching
    LOW = 4         # Monitoring, analytics
    BACKGROUND = 5  # Background tasks, cleanup

@dataclass
class ServiceConfig:
    """Configuration for a service during startup"""
    name: str
    init_func: Callable
    priority: ServicePriority
    timeout: float = 30.0
    retry_count: int = 3
    dependencies: List[str] = None
    cleanup_func: Optional[Callable] = None
    health_check: Optional[Callable] = None

class StartupOptimizationService:
    """Manages optimized application startup and shutdown"""
    
    def __init__(self):
        self.services: Dict[str, ServiceConfig] = {}
        self.initialized_services: Dict[str, Any] = {}
        self.startup_metrics: Dict[str, float] = {}
        self.shutdown_handlers: List[Callable] = []
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="startup")
        self._shutdown_event = asyncio.Event()
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.graceful_shutdown())
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def register_service(self, config: ServiceConfig):
        """Register a service for managed initialization"""
        self.services[config.name] = config
        logger.debug(f"Registered service: {config.name} (priority: {config.priority.name})")
    
    async def initialize_services(self) -> Dict[str, Any]:
        """Initialize all registered services in optimal order"""
        logger.info("Starting optimized service initialization...")
        start_time = time.time()
        
        # Log system resources before startup
        self._log_system_resources("startup_begin")
        
        # Group services by priority
        priority_groups = self._group_services_by_priority()
        
        # Initialize services by priority groups
        for priority in ServicePriority:
            if priority in priority_groups:
                await self._initialize_priority_group(priority, priority_groups[priority])
        
        # Verify all services are healthy
        await self._verify_service_health()
        
        total_time = time.time() - start_time
        self.startup_metrics['total_startup_time'] = total_time
        
        # Log system resources after startup
        self._log_system_resources("startup_complete")
        
        logger.info(f"Service initialization completed in {total_time:.2f}s")
        return self.initialized_services
    
    def _group_services_by_priority(self) -> Dict[ServicePriority, List[ServiceConfig]]:
        """Group services by their initialization priority"""
        groups = {}
        for service in self.services.values():
            if service.priority not in groups:
                groups[service.priority] = []
            groups[service.priority].append(service)
        return groups
    
    async def _initialize_priority_group(self, priority: ServicePriority, services: List[ServiceConfig]):
        """Initialize a group of services with the same priority"""
        logger.info(f"Initializing {priority.name} priority services ({len(services)} services)")
        
        # For critical services, initialize sequentially
        if priority == ServicePriority.CRITICAL:
            for service in services:
                await self._initialize_single_service(service)
        else:
            # For other services, initialize concurrently within the group
            tasks = [self._initialize_single_service(service) for service in services]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _initialize_single_service(self, config: ServiceConfig):
        """Initialize a single service with error handling and retries"""
        service_start = time.time()
        
        for attempt in range(config.retry_count):
            try:
                logger.debug(f"Initializing {config.name} (attempt {attempt + 1}/{config.retry_count})")
                
                # Check dependencies
                if config.dependencies:
                    missing_deps = [dep for dep in config.dependencies if dep not in self.initialized_services]
                    if missing_deps:
                        raise RuntimeError(f"Missing dependencies for {config.name}: {missing_deps}")
                
                # Initialize service with timeout
                if asyncio.iscoroutinefunction(config.init_func):
                    result = await asyncio.wait_for(config.init_func(), timeout=config.timeout)
                else:
                    # Run sync function in executor
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(self.executor, config.init_func),
                        timeout=config.timeout
                    )
                
                self.initialized_services[config.name] = result
                init_time = time.time() - service_start
                self.startup_metrics[f"{config.name}_init_time"] = init_time
                
                logger.info(f"✓ {config.name} initialized in {init_time:.2f}s")
                return result
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout initializing {config.name} (attempt {attempt + 1})")
                if attempt == config.retry_count - 1:
                    logger.error(f"Failed to initialize {config.name} after {config.retry_count} attempts")
                    raise
            except Exception as e:
                logger.warning(f"Error initializing {config.name} (attempt {attempt + 1}): {e}")
                if attempt == config.retry_count - 1:
                    logger.error(f"Failed to initialize {config.name}: {e}")
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _verify_service_health(self):
        """Verify all initialized services are healthy"""
        logger.info("Verifying service health...")
        
        health_checks = []
        for name, config in self.services.items():
            if config.health_check and name in self.initialized_services:
                health_checks.append(self._check_service_health(name, config))
        
        if health_checks:
            results = await asyncio.gather(*health_checks, return_exceptions=True)
            failed_checks = [r for r in results if isinstance(r, Exception)]
            if failed_checks:
                logger.warning(f"Some health checks failed: {len(failed_checks)} failures")
    
    async def _check_service_health(self, name: str, config: ServiceConfig):
        """Check health of a single service"""
        try:
            if asyncio.iscoroutinefunction(config.health_check):
                await config.health_check()
            else:
                config.health_check()
            logger.debug(f"✓ {name} health check passed")
        except Exception as e:
            logger.warning(f"✗ {name} health check failed: {e}")
            raise
    
    def _log_system_resources(self, phase: str):
        """Log current system resource usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            logger.info(f"System resources ({phase}):")
            logger.info(f"  Memory: {memory_info.rss / 1024 / 1024:.1f} MB RSS, {memory_info.vms / 1024 / 1024:.1f} MB VMS")
            logger.info(f"  CPU: {cpu_percent:.1f}%")
            logger.info(f"  Open files: {len(process.open_files())}")
            logger.info(f"  Threads: {process.num_threads()}")
            
            # Store metrics
            self.startup_metrics[f"{phase}_memory_rss"] = memory_info.rss
            self.startup_metrics[f"{phase}_memory_vms"] = memory_info.vms
            self.startup_metrics[f"{phase}_cpu_percent"] = cpu_percent
            
        except Exception as e:
            logger.warning(f"Could not collect system metrics: {e}")
    
    def optimize_memory_usage(self):
        """Optimize memory usage after startup"""
        logger.info("Optimizing memory usage...")
        
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
        
        # Log memory usage after optimization
        self._log_system_resources("memory_optimized")
    
    async def graceful_shutdown(self):
        """Perform graceful shutdown of all services"""
        if self._shutdown_event.is_set():
            return  # Already shutting down
        
        self._shutdown_event.set()
        logger.info("Starting graceful shutdown...")
        
        # Run custom shutdown handlers
        for handler in self.shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.error(f"Error in shutdown handler: {e}")
        
        # Shutdown services in reverse priority order
        priority_groups = self._group_services_by_priority()
        for priority in reversed(list(ServicePriority)):
            if priority in priority_groups:
                await self._shutdown_priority_group(priority_groups[priority])
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Graceful shutdown completed")
    
    async def _shutdown_priority_group(self, services: List[ServiceConfig]):
        """Shutdown a group of services"""
        shutdown_tasks = []
        for service in services:
            if service.cleanup_func and service.name in self.initialized_services:
                shutdown_tasks.append(self._shutdown_single_service(service))
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
    
    async def _shutdown_single_service(self, config: ServiceConfig):
        """Shutdown a single service"""
        try:
            logger.debug(f"Shutting down {config.name}")
            if asyncio.iscoroutinefunction(config.cleanup_func):
                await config.cleanup_func()
            else:
                config.cleanup_func()
            logger.debug(f"✓ {config.name} shutdown completed")
        except Exception as e:
            logger.error(f"Error shutting down {config.name}: {e}")
    
    def add_shutdown_handler(self, handler: Callable):
        """Add a custom shutdown handler"""
        self.shutdown_handlers.append(handler)
    
    def get_startup_metrics(self) -> Dict[str, float]:
        """Get startup performance metrics"""
        return self.startup_metrics.copy()

# Global instance
startup_service = StartupOptimizationService()