"""Performance tests for Lotto Max Analyzer."""

import pytest
import time
from pathlib import Path
from datetime import datetime, timedelta

from tests.test_utils import MockDataGenerator, PerformanceTimer, create_temp_database, cleanup_temp_database
from lotto_max_analyzer.data.storage import DataStorage
from lotto_max_analyzer.analysis.frequency import FrequencyAnalyzer
from lotto_max_analyzer.analysis.patterns import PatternAnalyzer
from lotto_max_analyzer.analysis.recommendations import RecommendationEngine


class TestStoragePerformance:
    """Test storage performance with various data sizes."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.db_path = create_temp_database()
        self.storage = DataStorage(self.db_path)
        self.mock_generator = MockDataGenerator()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        cleanup_temp_database(self.db_path)
    
    def test_single_draw_save_performance(self):
        """Test performance of saving a single draw."""
        draw = self.mock_generator.generate_draw_result()
        
        with PerformanceTimer() as timer:
            self.storage.save_draw(draw)
        
        # Single draw save should be very fast
        timer.assert_under_threshold(0.1, "Single draw save")
    
    def test_batch_save_performance(self):
        """Test performance of saving multiple draws."""
        draws = self.mock_generator.generate_draw_sequence(100)
        
        with PerformanceTimer() as timer:
            for draw in draws:
                self.storage.save_draw(draw)
        
        # 100 draws should save within reasonable time
        timer.assert_under_threshold(2.0, "100 draw batch save")
    
    def test_large_dataset_save_performance(self):
        """Test performance with large dataset."""
        draws = self.mock_generator.generate_draw_sequence(1000)
        
        with PerformanceTimer() as timer:
            for draw in draws:
                self.storage.save_draw(draw)
        
        # 1000 draws should save within reasonable time
        timer.assert_under_threshold(10.0, "1000 draw save")
    
    def test_load_performance(self):
        """Test performance of loading draws."""
        # First, save some data
        draws = self.mock_generator.generate_draw_sequence(500)
        for draw in draws:
            self.storage.save_draw(draw)
        
        # Test loading all draws
        with PerformanceTimer() as timer:
            loaded_draws = self.storage.load_draws()
        
        assert len(loaded_draws) == 500
        timer.assert_under_threshold(1.0, "Load 500 draws")
    
    def test_filtered_load_performance(self):
        """Test performance of loading with date filters."""
        # Save data spanning 2 years
        draws = self.mock_generator.generate_draw_sequence(200)
        for draw in draws:
            self.storage.save_draw(draw)
        
        # Test filtered loading
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now() - timedelta(days=90)
        
        with PerformanceTimer() as timer:
            filtered_draws = self.storage.load_draws(start_date=start_date, end_date=end_date)
        
        assert len(filtered_draws) < 200  # Should be filtered
        timer.assert_under_threshold(0.5, "Filtered load")


class TestAnalysisPerformance:
    """Test analysis performance with various data sizes."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_generator = MockDataGenerator()
        self.frequency_analyzer = FrequencyAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
        self.recommendation_engine = RecommendationEngine()
    
    def test_frequency_analysis_performance(self):
        """Test frequency analysis performance."""
        # Test with different dataset sizes
        sizes = [50, 100, 500, 1000]
        
        for size in sizes:
            draws = self.mock_generator.generate_realistic_draws(size)
            
            with PerformanceTimer() as timer:
                frequency_stats = self.frequency_analyzer.analyze_frequency(draws)
            
            # Performance should scale reasonably
            expected_time = size * 0.001  # 1ms per draw as rough baseline
            timer.assert_under_threshold(max(expected_time, 0.1), f"Frequency analysis for {size} draws")
            
            assert frequency_stats is not None
            assert frequency_stats.total_draws == size
    
    def test_pattern_analysis_performance(self):
        """Test pattern analysis performance."""
        sizes = [50, 100, 200]  # Pattern analysis is more intensive
        
        for size in sizes:
            draws = self.mock_generator.generate_realistic_draws(size)
            
            with PerformanceTimer() as timer:
                patterns = self.pattern_analyzer.analyze_patterns(draws)
            
            # Pattern analysis is more complex, allow more time
            expected_time = size * 0.01  # 10ms per draw
            timer.assert_under_threshold(max(expected_time, 0.5), f"Pattern analysis for {size} draws")
            
            assert patterns is not None
            assert len(patterns) > 0
    
    def test_recommendation_generation_performance(self):
        """Test recommendation generation performance."""
        draws = self.mock_generator.generate_realistic_draws(100)
        
        strategies = ['hot_numbers', 'cold_numbers', 'balanced']
        
        for strategy in strategies:
            with PerformanceTimer() as timer:
                recommendations = self.recommendation_engine.generate_recommendations(
                    draws, strategy=strategy, count=5
                )
            
            timer.assert_under_threshold(1.0, f"Recommendation generation ({strategy})")
            
            assert len(recommendations) == 5
            for rec in recommendations:
                assert len(rec.numbers) == 7
    
    def test_combined_analysis_performance(self):
        """Test performance of combined analysis workflow."""
        draws = self.mock_generator.generate_realistic_draws(200)
        
        with PerformanceTimer() as timer:
            # Full analysis workflow
            frequency_stats = self.frequency_analyzer.analyze_frequency(draws)
            patterns = self.pattern_analyzer.analyze_patterns(draws)
            recommendations = self.recommendation_engine.generate_recommendations(
                draws, strategy='balanced', count=3
            )
        
        # Complete analysis should finish within reasonable time
        timer.assert_under_threshold(5.0, "Combined analysis workflow")
        
        assert frequency_stats is not None
        assert patterns is not None
        assert len(recommendations) == 3


class TestMemoryUsage:
    """Test memory usage with large datasets."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_generator = MockDataGenerator()
    
    def test_large_dataset_memory_usage(self):
        """Test memory usage with large dataset."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate large dataset
        draws = self.mock_generator.generate_realistic_draws(2000)
        
        # Perform analysis
        frequency_analyzer = FrequencyAnalyzer()
        frequency_stats = frequency_analyzer.analyze_frequency(draws)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 2000 draws)
        assert memory_increase < 100 * 1024 * 1024, \
            f"Memory usage too high: {memory_increase / 1024 / 1024:.1f}MB"
        
        assert frequency_stats is not None
    
    def test_memory_cleanup(self):
        """Test that memory is properly cleaned up."""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and analyze large dataset in a function to ensure cleanup
        def analyze_large_dataset():
            draws = self.mock_generator.generate_realistic_draws(1000)
            frequency_analyzer = FrequencyAnalyzer()
            return frequency_analyzer.analyze_frequency(draws)
        
        # Run analysis
        result = analyze_large_dataset()
        
        # Force garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase significantly after cleanup
        assert memory_increase < 50 * 1024 * 1024, \
            f"Memory not properly cleaned up: {memory_increase / 1024 / 1024:.1f}MB increase"
        
        assert result is not None


class TestConcurrencyPerformance:
    """Test performance under concurrent access."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.db_path = create_temp_database()
        self.mock_generator = MockDataGenerator()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        cleanup_temp_database(self.db_path)
    
    def test_concurrent_read_performance(self):
        """Test performance of concurrent read operations."""
        import threading
        import time
        
        # Setup data
        storage = DataStorage(self.db_path)
        draws = self.mock_generator.generate_draw_sequence(100)
        for draw in draws:
            storage.save_draw(draw)
        
        results = []
        errors = []
        
        def read_worker():
            try:
                worker_storage = DataStorage(self.db_path)
                start_time = time.time()
                loaded_draws = worker_storage.load_draws()
                end_time = time.time()
                
                results.append({
                    'count': len(loaded_draws),
                    'time': end_time - start_time
                })
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple concurrent readers
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=read_worker)
            threads.append(thread)
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Check results
        assert len(errors) == 0, f"Concurrent read errors: {errors}"
        assert len(results) == 5
        assert all(result['count'] == 100 for result in results)
        
        # Concurrent reads should not take much longer than sequential
        assert total_time < 2.0, f"Concurrent reads took too long: {total_time:.2f}s"
    
    def test_mixed_read_write_performance(self):
        """Test performance with mixed read/write operations."""
        import threading
        import time
        
        storage = DataStorage(self.db_path)
        results = []
        errors = []
        
        def writer_worker(worker_id):
            try:
                worker_storage = DataStorage(self.db_path)
                draws = self.mock_generator.generate_draw_sequence(20)
                
                start_time = time.time()
                for i, draw in enumerate(draws):
                    draw.draw_id = f"WORKER_{worker_id}_{i}"
                    worker_storage.save_draw(draw)
                end_time = time.time()
                
                results.append({
                    'type': 'write',
                    'worker_id': worker_id,
                    'time': end_time - start_time
                })
            except Exception as e:
                errors.append(f"Writer {worker_id}: {e}")
        
        def reader_worker(worker_id):
            try:
                worker_storage = DataStorage(self.db_path)
                
                start_time = time.time()
                draws = worker_storage.load_draws()
                end_time = time.time()
                
                results.append({
                    'type': 'read',
                    'worker_id': worker_id,
                    'count': len(draws),
                    'time': end_time - start_time
                })
            except Exception as e:
                errors.append(f"Reader {worker_id}: {e}")
        
        # Start mixed workers
        threads = []
        
        # 2 writers
        for i in range(2):
            thread = threading.Thread(target=writer_worker, args=(i,))
            threads.append(thread)
        
        # 3 readers
        for i in range(3):
            thread = threading.Thread(target=reader_worker, args=(i,))
            threads.append(thread)
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Check results
        assert len(errors) == 0, f"Mixed operation errors: {errors}"
        assert len(results) == 5
        
        # Mixed operations should complete within reasonable time
        assert total_time < 5.0, f"Mixed operations took too long: {total_time:.2f}s"


@pytest.mark.slow
class TestStressTests:
    """Stress tests for extreme conditions."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_generator = MockDataGenerator()
    
    def test_very_large_dataset(self):
        """Test with very large dataset (5000+ draws)."""
        pytest.skip("Skipping stress test - uncomment to run")
        
        draws = self.mock_generator.generate_realistic_draws(5000)
        
        with PerformanceTimer() as timer:
            frequency_analyzer = FrequencyAnalyzer()
            frequency_stats = frequency_analyzer.analyze_frequency(draws)
        
        timer.assert_under_threshold(30.0, "Very large dataset analysis")
        assert frequency_stats.total_draws == 5000
    
    def test_memory_stress(self):
        """Test memory usage under stress."""
        pytest.skip("Skipping memory stress test - uncomment to run")
        
        # Generate multiple large datasets
        for i in range(10):
            draws = self.mock_generator.generate_realistic_draws(1000)
            frequency_analyzer = FrequencyAnalyzer()
            frequency_stats = frequency_analyzer.analyze_frequency(draws)
            
            # Force cleanup
            del draws, frequency_analyzer, frequency_stats
            
        # Should complete without memory errors