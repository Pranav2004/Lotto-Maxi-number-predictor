"""Performance monitoring and optimization utilities."""

import time
import psutil
import logging
import functools
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    execution_time: float
    memory_usage: float
    cpu_usage: float
    timestamp: datetime
    function_name: str
    parameters: Dict[str, Any]


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.logger = logging.getLogger(__name__)
        self.metrics_history = []
        self.function_stats = defaultdict(list)
        self.start_time = time.time()
    
    def measure_execution_time(self, func: Callable) -> Callable:
        """
        Decorator to measure function execution time.
        
        Args:
            func: Function to measure
            
        Returns:
            Decorated function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            start_cpu = psutil.cpu_percent()
            
            try:
                result = func(*args, **kwargs)
                
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                end_cpu = psutil.cpu_percent()
                
                execution_time = end_time - start_time
                memory_delta = end_memory - start_memory
                cpu_usage = (start_cpu + end_cpu) / 2
                
                # Create metrics
                metrics = PerformanceMetrics(
                    execution_time=execution_time,
                    memory_usage=memory_delta,
                    cpu_usage=cpu_usage,
                    timestamp=datetime.now(),
                    function_name=func.__name__,
                    parameters={'args_count': len(args), 'kwargs_count': len(kwargs)}
                )
                
                # Store metrics
                self.metrics_history.append(metrics)
                self.function_stats[func.__name__].append(metrics)
                
                # Log performance if significant
                if execution_time > 1.0:  # Log if takes more than 1 second
                    self.logger.info(
                        f"Performance: {func.__name__} took {execution_time:.2f}s, "
                        f"memory delta: {memory_delta:.1f}MB"
                    )
                
                return result
                
            except Exception as e:
                # Log error with timing info
                error_time = time.time() - start_time
                self.logger.error(
                    f"Function {func.__name__} failed after {error_time:.2f}s: {e}"
                )
                raise
        
        return wrapper
    
    def check_memory_usage(self, threshold_mb: float = 500.0) -> Dict[str, Any]:
        """
        Check current memory usage and warn if high.
        
        Args:
            threshold_mb: Memory threshold in MB to warn at
            
        Returns:
            Dictionary with memory information
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        system_memory = psutil.virtual_memory()
        memory_percent = process.memory_percent()
        
        memory_data = {
            'current_mb': memory_mb,
            'threshold_mb': threshold_mb,
            'system_total_gb': system_memory.total / 1024 / 1024 / 1024,
            'system_available_gb': system_memory.available / 1024 / 1024 / 1024,
            'process_percent': memory_percent,
            'warning': memory_mb > threshold_mb
        }
        
        if memory_mb > threshold_mb:
            self.logger.warning(
                f"High memory usage: {memory_mb:.1f}MB "
                f"({memory_percent:.1f}% of system memory)"
            )
        
        return memory_data
    
    def check_disk_space(self, path: str = ".", threshold_gb: float = 1.0) -> Dict[str, Any]:
        """
        Check available disk space.
        
        Args:
            path: Path to check disk space for
            threshold_gb: Minimum free space threshold in GB
            
        Returns:
            Dictionary with disk space information
        """
        disk_usage = psutil.disk_usage(path)
        
        total_gb = disk_usage.total / 1024 / 1024 / 1024
        free_gb = disk_usage.free / 1024 / 1024 / 1024
        used_gb = disk_usage.used / 1024 / 1024 / 1024
        used_percent = (disk_usage.used / disk_usage.total) * 100
        
        disk_data = {
            'total_gb': total_gb,
            'free_gb': free_gb,
            'used_gb': used_gb,
            'used_percent': used_percent,
            'threshold_gb': threshold_gb,
            'warning': free_gb < threshold_gb
        }
        
        if free_gb < threshold_gb:
            self.logger.warning(
                f"Low disk space: {free_gb:.1f}GB free "
                f"({used_percent:.1f}% used)"
            )
        
        return disk_data
    
    def get_function_stats(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance statistics for functions.
        
        Args:
            function_name: Specific function to get stats for (None for all)
            
        Returns:
            Dictionary with performance statistics
        """
        if function_name and function_name in self.function_stats:
            metrics_list = self.function_stats[function_name]
        elif function_name:
            return {'error': f'No metrics found for function: {function_name}'}
        else:
            # Aggregate all functions
            metrics_list = self.metrics_history
        
        if not metrics_list:
            return {'error': 'No metrics available'}
        
        execution_times = [m.execution_time for m in metrics_list]
        memory_usages = [m.memory_usage for m in metrics_list]
        
        stats = {
            'call_count': len(metrics_list),
            'execution_time': {
                'total': sum(execution_times),
                'average': sum(execution_times) / len(execution_times),
                'min': min(execution_times),
                'max': max(execution_times)
            },
            'memory_usage': {
                'average': sum(memory_usages) / len(memory_usages),
                'min': min(memory_usages),
                'max': max(memory_usages)
            },
            'first_call': metrics_list[0].timestamp.isoformat(),
            'last_call': metrics_list[-1].timestamp.isoformat()
        }
        
        return stats
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get current system information.
        
        Returns:
            Dictionary with system information
        """
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        uptime = time.time() - self.start_time
        
        return {
            'cpu': {
                'count': cpu_count,
                'usage_percent': cpu_percent
            },
            'memory': {
                'total_gb': memory.total / 1024 / 1024 / 1024,
                'available_gb': memory.available / 1024 / 1024 / 1024,
                'used_percent': memory.percent
            },
            'disk': {
                'total_gb': disk.total / 1024 / 1024 / 1024,
                'free_gb': disk.free / 1024 / 1024 / 1024,
                'used_percent': (disk.used / disk.total) * 100
            },
            'uptime_seconds': uptime
        }
    
    def optimize_for_large_dataset(self, dataset_size: int) -> Dict[str, Any]:
        """
        Provide optimization recommendations for large datasets.
        
        Args:
            dataset_size: Size of the dataset to process
            
        Returns:
            Dictionary with optimization recommendations
        """
        memory_info = self.check_memory_usage()
        system_info = self.get_system_info()
        
        recommendations = []
        
        # Memory recommendations
        estimated_memory_mb = dataset_size * 0.001  # Rough estimate
        if estimated_memory_mb > memory_info['system_available_gb'] * 1024 * 0.8:
            recommendations.append(
                "Consider processing data in smaller chunks to avoid memory issues"
            )
        
        # CPU recommendations
        if system_info['cpu']['count'] > 1 and dataset_size > 1000:
            recommendations.append(
                "Consider using parallel processing for better performance"
            )
        
        # Disk space recommendations
        disk_info = self.check_disk_space()
        estimated_output_gb = dataset_size * 0.00001  # Rough estimate for output files
        if estimated_output_gb > disk_info['free_gb'] * 0.5:
            recommendations.append(
                "Ensure sufficient disk space for output files and temporary data"
            )
        
        # Performance recommendations
        if dataset_size > 10000:
            recommendations.extend([
                "Use database indexing for faster queries",
                "Consider caching frequently accessed data",
                "Monitor memory usage during processing"
            ])
        
        return {
            'dataset_size': dataset_size,
            'estimated_memory_mb': estimated_memory_mb,
            'estimated_output_gb': estimated_output_gb,
            'recommendations': recommendations,
            'system_resources': {
                'memory_available_gb': memory_info['system_available_gb'],
                'cpu_count': system_info['cpu']['count'],
                'disk_free_gb': disk_info['free_gb']
            }
        }
    
    def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        self.metrics_history.clear()
        self.function_stats.clear()
        self.logger.info("Performance metrics cleared")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(func: Callable) -> Callable:
    """Convenience decorator for performance monitoring."""
    return performance_monitor.measure_execution_time(func)


def check_system_resources() -> Dict[str, Any]:
    """Convenience function to check system resources."""
    return {
        'memory': performance_monitor.check_memory_usage(),
        'disk': performance_monitor.check_disk_space(),
        'system': performance_monitor.get_system_info()
    }