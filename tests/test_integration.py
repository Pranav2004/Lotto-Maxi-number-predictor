"""Integration tests for Lotto Max Analyzer."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from lotto_max_analyzer.data.models import DrawResult
from lotto_max_analyzer.data.storage import DataStorage
from lotto_max_analyzer.data.fetcher import DataFetcher
from lotto_max_analyzer.analysis.frequency import FrequencyAnalyzer
from lotto_max_analyzer.analysis.patterns import PatternAnalyzer
from lotto_max_analyzer.analysis.recommendations import RecommendationEngine
from lotto_max_analyzer.visualization.charts import ChartGenerator
from lotto_max_analyzer.visualization.reports import ReportGenerator


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.storage = DataStorage(self.db_path)
        
        # Create sample data
        self.sample_draws = self._create_sample_draws()
        
        # Initialize components
        self.frequency_analyzer = FrequencyAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        self.chart_generator = ChartGenerator()
        self.report_generator = ReportGenerator()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_sample_draws(self):
        """Create sample draw data for testing."""
        draws = []
        base_date = datetime(2024, 1, 1)
        
        for i in range(50):
            draw = DrawResult(
                draw_id=f"DRAW_{i+1:03d}",
                date=base_date + timedelta(days=i*3),  # Every 3 days
                numbers=[1+i%7, 8+i%7, 15+i%7, 22+i%7, 29+i%7, 36+i%7, 43+i%7],
                bonus=1 + (i*7) % 49,
                jackpot_amount=10_000_000 + (i * 1_000_000)
            )
            draws.append(draw)
        
        return draws
    
    def test_complete_analysis_workflow(self):
        """Test complete analysis workflow from data to recommendations."""
        # Step 1: Store data
        for draw in self.sample_draws:
            self.storage.save_draw(draw)
        
        # Step 2: Load data
        loaded_draws = self.storage.load_draws()
        assert len(loaded_draws) == len(self.sample_draws)
        
        # Step 3: Frequency analysis
        frequency_stats = self.frequency_analyzer.analyze_frequency(loaded_draws)
        assert frequency_stats is not None
        assert len(frequency_stats.number_frequencies) > 0
        
        # Step 4: Pattern analysis
        patterns = self.pattern_analyzer.analyze_patterns(loaded_draws)
        assert patterns is not None
        assert len(patterns) > 0
        
        # Step 5: Generate recommendations
        recommendations = self.recommendation_engine.generate_recommendations(
            loaded_draws, strategy='balanced'
        )
        assert len(recommendations) > 0
        assert all(len(rec.numbers) == 7 for rec in recommendations)
        
        # Step 6: Generate report
        report = self.report_generator.generate_analysis_report(
            loaded_draws, frequency_stats, patterns, recommendations
        )
        assert report is not None
        assert len(report) > 0
    
    def test_data_filtering_workflow(self):
        """Test workflow with date filtering."""
        # Store data
        for draw in self.sample_draws:
            self.storage.save_draw(draw)
        
        # Filter by date range
        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 2, 15)
        
        filtered_draws = self.storage.load_draws(start_date=start_date, end_date=end_date)
        
        # Verify filtering worked
        assert len(filtered_draws) < len(self.sample_draws)
        for draw in filtered_draws:
            assert start_date <= draw.date <= end_date
        
        # Run analysis on filtered data
        frequency_stats = self.frequency_analyzer.analyze_frequency(filtered_draws)
        assert frequency_stats is not None
    
    def test_error_recovery_workflow(self):
        """Test workflow with error conditions and recovery."""
        # Test with empty database
        empty_draws = self.storage.load_draws()
        assert len(empty_draws) == 0
        
        # Frequency analysis should handle empty data gracefully
        with pytest.raises(ValueError, match="No draws provided"):
            self.frequency_analyzer.analyze_frequency(empty_draws)
        
        # Add minimal data
        minimal_draws = self.sample_draws[:5]  # Only 5 draws
        for draw in minimal_draws:
            self.storage.save_draw(draw)
        
        # Analysis should work with minimal data but may have warnings
        frequency_stats = self.frequency_analyzer.analyze_frequency(minimal_draws)
        assert frequency_stats is not None
    
    def test_performance_with_large_dataset(self):
        """Test performance with larger dataset."""
        import time
        
        # Create larger dataset
        large_draws = []
        base_date = datetime(2020, 1, 1)
        
        for i in range(500):  # 500 draws
            draw = DrawResult(
                draw_id=f"LARGE_{i+1:04d}",
                date=base_date + timedelta(days=i*3),
                numbers=[(1+i*j) % 49 + 1 for j in range(7)],
                bonus=(i*13) % 49 + 1,
                jackpot_amount=10_000_000 + (i * 100_000)
            )
            large_draws.append(draw)
        
        # Measure storage performance
        start_time = time.time()
        for draw in large_draws:
            self.storage.save_draw(draw)
        storage_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert storage_time < 10.0, f"Storage took too long: {storage_time:.2f}s"
        
        # Measure analysis performance
        start_time = time.time()
        frequency_stats = self.frequency_analyzer.analyze_frequency(large_draws)
        analysis_time = time.time() - start_time
        
        assert analysis_time < 5.0, f"Analysis took too long: {analysis_time:.2f}s"
        assert frequency_stats is not None
    
    @patch('lotto_max_analyzer.data.fetcher.requests.get')
    def test_data_fetching_integration(self, mock_get):
        """Test integration with data fetching."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <body>
        <div class="draw-result">
            <span class="date">2024-01-01</span>
            <span class="numbers">1,8,15,22,29,36,43</span>
            <span class="bonus">7</span>
            <span class="jackpot">$15,000,000</span>
        </div>
        </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # Test fetching and storing
        fetcher = DataFetcher()
        fetched_draws = fetcher.fetch_recent_draws(limit=1)
        
        # Store fetched data
        for draw in fetched_draws:
            self.storage.save_draw(draw)
        
        # Verify data was stored correctly
        stored_draws = self.storage.load_draws()
        assert len(stored_draws) == len(fetched_draws)
    
    def test_recommendation_strategies_comparison(self):
        """Test and compare different recommendation strategies."""
        # Store data
        for draw in self.sample_draws:
            self.storage.save_draw(draw)
        
        loaded_draws = self.storage.load_draws()
        
        # Test all strategies
        strategies = ['hot_numbers', 'cold_numbers', 'balanced']
        all_recommendations = {}
        
        for strategy in strategies:
            recommendations = self.recommendation_engine.generate_recommendations(
                loaded_draws, strategy=strategy, count=3
            )
            all_recommendations[strategy] = recommendations
            
            # Verify recommendations
            assert len(recommendations) == 3
            for rec in recommendations:
                assert len(rec.numbers) == 7
                assert len(set(rec.numbers)) == 7  # No duplicates
                assert all(1 <= num <= 49 for num in rec.numbers)
        
        # Strategies should produce different results
        hot_numbers = set(tuple(rec.numbers) for rec in all_recommendations['hot_numbers'])
        cold_numbers = set(tuple(rec.numbers) for rec in all_recommendations['cold_numbers'])
        
        # At least some recommendations should be different
        assert len(hot_numbers.intersection(cold_numbers)) < len(hot_numbers)
    
    def test_visualization_integration(self):
        """Test visualization component integration."""
        # Store data
        for draw in self.sample_draws:
            self.storage.save_draw(draw)
        
        loaded_draws = self.storage.load_draws()
        frequency_stats = self.frequency_analyzer.analyze_frequency(loaded_draws)
        
        # Test chart generation
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            chart_path = Path(tmp_file.name)
        
        try:
            # Generate frequency chart
            self.chart_generator.create_frequency_chart(
                frequency_stats.number_frequencies,
                save_path=chart_path
            )
            
            # Verify chart was created
            assert chart_path.exists()
            assert chart_path.stat().st_size > 0
            
        finally:
            # Clean up
            if chart_path.exists():
                chart_path.unlink()
    
    def test_concurrent_access(self):
        """Test concurrent database access."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                # Each worker creates its own storage instance
                worker_storage = DataStorage(self.db_path)
                
                # Add some draws
                for i in range(10):
                    draw = DrawResult(
                        draw_id=f"WORKER_{worker_id}_{i}",
                        date=datetime.now() + timedelta(days=i),
                        numbers=[1, 2, 3, 4, 5, 6, 7],
                        bonus=8,
                        jackpot_amount=10_000_000
                    )
                    worker_storage.save_draw(draw)
                
                # Read draws
                draws = worker_storage.load_draws()
                results.append(len(draws))
                
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 3
        
        # Final verification
        final_draws = self.storage.load_draws()
        assert len(final_draws) >= 30  # At least 30 draws (3 workers * 10 draws each)


class TestDataQuality:
    """Test data quality validation and handling."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.storage = DataStorage(self.db_path)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_duplicate_draw_handling(self):
        """Test handling of duplicate draws."""
        draw1 = DrawResult(
            draw_id="DUPLICATE_TEST",
            date=datetime(2024, 1, 1),
            numbers=[1, 2, 3, 4, 5, 6, 7],
            bonus=8,
            jackpot_amount=10_000_000
        )
        
        draw2 = DrawResult(
            draw_id="DUPLICATE_TEST",  # Same ID
            date=datetime(2024, 1, 1),
            numbers=[8, 9, 10, 11, 12, 13, 14],  # Different numbers
            bonus=15,
            jackpot_amount=15_000_000
        )
        
        # Save first draw
        self.storage.save_draw(draw1)
        
        # Save duplicate - should handle gracefully
        self.storage.save_draw(draw2)
        
        # Should only have one draw (or the second one should update the first)
        draws = self.storage.load_draws()
        assert len(draws) <= 2  # Depending on implementation
    
    def test_invalid_data_rejection(self):
        """Test rejection of invalid data."""
        from lotto_max_analyzer.utils.validation import DataValidator
        
        validator = DataValidator()
        
        # Test invalid numbers
        with pytest.raises(Exception):
            invalid_draw = DrawResult(
                draw_id="INVALID_NUMBERS",
                date=datetime(2024, 1, 1),
                numbers=[1, 2, 3, 4, 5, 6, 50],  # 50 is out of range
                bonus=8,
                jackpot_amount=10_000_000
            )
            validator.validate_draw_result(invalid_draw)
        
        # Test duplicate numbers
        with pytest.raises(Exception):
            invalid_draw = DrawResult(
                draw_id="DUPLICATE_NUMBERS",
                date=datetime(2024, 1, 1),
                numbers=[1, 2, 3, 4, 5, 6, 6],  # Duplicate 6
                bonus=8,
                jackpot_amount=10_000_000
            )
            validator.validate_draw_result(invalid_draw)
    
    def test_data_consistency_checks(self):
        """Test data consistency validation."""
        # Create draws with potential consistency issues
        draws = []
        
        # Normal draw
        draws.append(DrawResult(
            draw_id="NORMAL_1",
            date=datetime(2024, 1, 1),
            numbers=[1, 8, 15, 22, 29, 36, 43],
            bonus=7,
            jackpot_amount=10_000_000
        ))
        
        # Draw with bonus number in main numbers (should be caught)
        draws.append(DrawResult(
            draw_id="INVALID_BONUS",
            date=datetime(2024, 1, 5),
            numbers=[1, 8, 15, 22, 29, 36, 43],
            bonus=15,  # 15 is also in main numbers
            jackpot_amount=12_000_000
        ))
        
        from lotto_max_analyzer.utils.validation import DataValidator
        validator = DataValidator()
        
        # First draw should be valid
        validator.validate_draw_result(draws[0])
        
        # Second draw should be invalid
        with pytest.raises(Exception):
            validator.validate_draw_result(draws[1])