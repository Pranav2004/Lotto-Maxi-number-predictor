"""Complete system integration test."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from lotto_max_analyzer.main import LottoMaxAnalyzer
from tests.test_utils import MockDataGenerator, TestAssertions


class TestCompleteSystem:
    """Test the complete system integration."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test.db"
        self.mock_generator = MockDataGenerator()
        self.assertions = TestAssertions()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_workflow_from_scratch(self):
        """Test complete workflow starting from empty database."""
        # Initialize analyzer
        analyzer = LottoMaxAnalyzer(db_path=self.db_path)
        
        # Generate and add mock data (simulating data fetching)
        mock_draws = self.mock_generator.generate_realistic_draws(100)
        
        # Save mock data to database
        for draw in mock_draws:
            analyzer.storage.save_draw(draw)
        
        # Load data
        loaded_draws = analyzer.load_data()
        assert len(loaded_draws) == 100
        
        # Verify all draws are valid
        for draw in loaded_draws:
            self.assertions.assert_valid_draw_result(draw)
        
        # Perform frequency analysis
        frequency_stats = analyzer.analyze_frequency()
        self.assertions.assert_valid_frequency_stats(frequency_stats)
        assert frequency_stats.total_draws == 100
        
        # Perform pattern analysis
        patterns = analyzer.analyze_patterns()
        assert len(patterns) > 0
        for pattern in patterns:
            self.assertions.assert_valid_pattern(pattern)
        
        # Generate recommendations for all strategies
        strategies = ['hot_numbers', 'cold_numbers', 'balanced']
        for strategy in strategies:
            recommendations = analyzer.generate_recommendations(strategy=strategy, count=3)
            assert len(recommendations) == 3
            
            for rec in recommendations:
                self.assertions.assert_valid_recommendation(rec)
                assert rec.strategy == strategy
        
        # Generate report
        report = analyzer.generate_report()
        assert isinstance(report, str)
        assert len(report) > 0
        assert "Frequency Analysis" in report
        assert "Pattern Analysis" in report
        assert "Recommendations" in report
        
        # Create visualization
        chart_path = self.temp_dir / "frequency_chart.png"
        created_path = analyzer.create_frequency_chart(save_path=chart_path)
        assert created_path.exists()
        assert created_path.stat().st_size > 0
    
    def test_filtered_analysis_workflow(self):
        """Test workflow with date filtering."""
        analyzer = LottoMaxAnalyzer(db_path=self.db_path)
        
        # Generate data spanning 6 months
        base_date = datetime(2024, 1, 1)
        mock_draws = []
        
        for i in range(60):  # 60 draws over 6 months
            draw = self.mock_generator.generate_draw_result(
                draw_id=f"FILTERED_{i:03d}",
                date=base_date + timedelta(days=i*3)
            )
            mock_draws.append(draw)
            analyzer.storage.save_draw(draw)
        
        # Test filtering by date range
        start_date = base_date + timedelta(days=30)  # 1 month in
        end_date = base_date + timedelta(days=120)   # 4 months in
        
        filtered_draws = analyzer.load_data(start_date=start_date, end_date=end_date)
        
        # Verify filtering worked
        assert len(filtered_draws) < len(mock_draws)
        for draw in filtered_draws:
            assert start_date <= draw.date <= end_date
        
        # Perform analysis on filtered data
        frequency_stats = analyzer.analyze_frequency(filtered_draws)
        assert frequency_stats.total_draws == len(filtered_draws)
        
        patterns = analyzer.analyze_patterns(filtered_draws)
        assert len(patterns) >= 0  # May be empty for small datasets
        
        recommendations = analyzer.generate_recommendations(
            draws=filtered_draws, strategy='balanced', count=2
        )
        assert len(recommendations) == 2
    
    def test_error_handling_workflow(self):
        """Test system behavior with various error conditions."""
        analyzer = LottoMaxAnalyzer(db_path=self.db_path)
        
        # Test with empty database
        empty_draws = analyzer.load_data()
        assert len(empty_draws) == 0
        
        # Analysis should handle empty data gracefully
        with pytest.raises(ValueError):
            analyzer.analyze_frequency(empty_draws)
        
        # Add minimal data
        minimal_draws = self.mock_generator.generate_realistic_draws(5)
        for draw in minimal_draws:
            analyzer.storage.save_draw(draw)
        
        # Should work with minimal data
        loaded_draws = analyzer.load_data()
        assert len(loaded_draws) == 5
        
        frequency_stats = analyzer.analyze_frequency(loaded_draws)
        assert frequency_stats.total_draws == 5
        
        # Recommendations should still work
        recommendations = analyzer.generate_recommendations(
            draws=loaded_draws, strategy='balanced', count=1
        )
        assert len(recommendations) == 1
    
    def test_data_persistence_workflow(self):
        """Test data persistence across analyzer instances."""
        # First analyzer instance
        analyzer1 = LottoMaxAnalyzer(db_path=self.db_path)
        
        # Add data
        mock_draws = self.mock_generator.generate_realistic_draws(50)
        for draw in mock_draws:
            analyzer1.storage.save_draw(draw)
        
        # Verify data is saved
        draws1 = analyzer1.load_data()
        assert len(draws1) == 50
        
        # Create second analyzer instance with same database
        analyzer2 = LottoMaxAnalyzer(db_path=self.db_path)
        
        # Should load the same data
        draws2 = analyzer2.load_data()
        assert len(draws2) == 50
        
        # Data should be identical
        for d1, d2 in zip(draws1, draws2):
            assert d1.draw_id == d2.draw_id
            assert d1.date == d2.date
            assert d1.numbers == d2.numbers
            assert d1.bonus == d2.bonus
            assert d1.jackpot_amount == d2.jackpot_amount
        
        # Add more data with second instance
        additional_draws = self.mock_generator.generate_realistic_draws(25)
        for draw in additional_draws:
            draw.draw_id = f"ADDITIONAL_{draw.draw_id}"
            analyzer2.storage.save_draw(draw)
        
        # Both instances should see all data
        final_draws1 = analyzer1.load_data()
        final_draws2 = analyzer2.load_data()
        
        assert len(final_draws1) == 75
        assert len(final_draws2) == 75
        assert len(final_draws1) == len(final_draws2)
    
    def test_recommendation_consistency(self):
        """Test that recommendations are consistent for the same data."""
        analyzer = LottoMaxAnalyzer(db_path=self.db_path)
        
        # Use fixed seed for reproducible data
        generator = MockDataGenerator(seed=12345)
        mock_draws = generator.generate_realistic_draws(100)
        
        for draw in mock_draws:
            analyzer.storage.save_draw(draw)
        
        draws = analyzer.load_data()
        
        # Generate recommendations multiple times
        recommendations1 = analyzer.generate_recommendations(
            draws=draws, strategy='balanced', count=3
        )
        recommendations2 = analyzer.generate_recommendations(
            draws=draws, strategy='balanced', count=3
        )
        
        # Should be identical for same input data
        assert len(recommendations1) == len(recommendations2)
        for rec1, rec2 in zip(recommendations1, recommendations2):
            assert rec1.numbers == rec2.numbers
            assert rec1.strategy == rec2.strategy
            assert abs(rec1.confidence - rec2.confidence) < 0.001
    
    def test_performance_with_realistic_data(self):
        """Test system performance with realistic data size."""
        import time
        
        analyzer = LottoMaxAnalyzer(db_path=self.db_path)
        
        # Generate realistic dataset (2 years of draws, ~300 draws)
        mock_draws = self.mock_generator.generate_realistic_draws(300)
        
        # Measure data loading performance
        start_time = time.time()
        for draw in mock_draws:
            analyzer.storage.save_draw(draw)
        save_time = time.time() - start_time
        
        # Should save within reasonable time
        assert save_time < 5.0, f"Data saving took too long: {save_time:.2f}s"
        
        # Measure analysis performance
        start_time = time.time()
        draws = analyzer.load_data()
        frequency_stats = analyzer.analyze_frequency(draws)
        patterns = analyzer.analyze_patterns(draws)
        recommendations = analyzer.generate_recommendations(draws=draws, count=5)
        analysis_time = time.time() - start_time
        
        # Complete analysis should finish within reasonable time
        assert analysis_time < 10.0, f"Analysis took too long: {analysis_time:.2f}s"
        
        # Verify results
        assert len(draws) == 300
        assert frequency_stats.total_draws == 300
        assert len(patterns) > 0
        assert len(recommendations) == 5
    
    def test_system_robustness(self):
        """Test system robustness with edge cases."""
        analyzer = LottoMaxAnalyzer(db_path=self.db_path)
        
        # Test with draws having same numbers (edge case)
        duplicate_numbers_draws = []
        for i in range(10):
            draw = self.mock_generator.generate_draw_result(
                draw_id=f"DUP_{i}",
                numbers=[1, 2, 3, 4, 5, 6, 7],  # Same numbers
                bonus=8
            )
            duplicate_numbers_draws.append(draw)
            analyzer.storage.save_draw(draw)
        
        # System should handle this gracefully
        draws = analyzer.load_data()
        frequency_stats = analyzer.analyze_frequency(draws)
        
        # All frequency should be on the same numbers
        assert frequency_stats.number_frequencies[1] == 10
        assert frequency_stats.number_frequencies[7] == 10
        assert frequency_stats.bonus_frequencies[8] == 10
        
        # Recommendations should still work
        recommendations = analyzer.generate_recommendations(draws=draws, count=1)
        assert len(recommendations) == 1
        
        # Test with very recent dates
        recent_draws = []
        for i in range(5):
            draw = self.mock_generator.generate_draw_result(
                draw_id=f"RECENT_{i}",
                date=datetime.now() - timedelta(days=i)
            )
            recent_draws.append(draw)
            analyzer.storage.save_draw(draw)
        
        # Should handle recent dates correctly
        all_draws = analyzer.load_data()
        assert len(all_draws) >= 15  # Previous 10 + new 5
        
        # Filter to only recent draws
        recent_only = analyzer.load_data(
            start_date=datetime.now() - timedelta(days=7)
        )
        assert len(recent_only) >= 5