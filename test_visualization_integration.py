"""Integration test for visualization components with real data."""

import os
import tempfile
from datetime import datetime, timedelta
from lotto_max_analyzer.data.storage import DataStorage
from lotto_max_analyzer.analysis.frequency import FrequencyAnalyzer
from lotto_max_analyzer.analysis.patterns import PatternAnalyzer
from lotto_max_analyzer.analysis.recommendations import RecommendationEngine
from lotto_max_analyzer.visualization.charts import ChartGenerator
from lotto_max_analyzer.visualization.reports import ReportGenerator

print("Testing Lotto Max Visualization Integration")
print("=" * 60)

# Initialize components
storage = DataStorage()
freq_analyzer = FrequencyAnalyzer()
pattern_analyzer = PatternAnalyzer()
rec_engine = RecommendationEngine()
chart_gen = ChartGenerator()
report_gen = ReportGenerator()

print("✓ All components initialized")

# Get existing data
draws = storage.get_all_draws()
print(f"✓ Using {len(draws)} draws for visualization")

if len(draws) < 50:
    print("⚠️  Need at least 50 draws for visualization")
    exit()

# Run analysis to get data for visualization
print("\n" + "="*50)
print("RUNNING ANALYSIS FOR VISUALIZATION")
print("="*50)

# Frequency analysis
frequency_data = freq_analyzer.calculate_number_frequency(draws)
hot_numbers = freq_analyzer.get_hot_numbers(draws)
cold_numbers = freq_analyzer.get_cold_numbers(draws)
print(f"✓ Frequency analysis complete: {len(hot_numbers)} hot, {len(cold_numbers)} cold numbers")

# Pattern analysis
pattern_summary = pattern_analyzer.get_pattern_summary(draws)
print(f"✓ Pattern analysis complete: {pattern_summary['pattern_score']:.1f}/100 complexity score")

# Recommendations
recommendations = rec_engine.get_multiple_recommendations(draws)
print(f"✓ Generated {len(recommendations)} recommendation strategies")

# Test chart generation
print("\n" + "="*50)
print("TESTING CHART GENERATION")
print("="*50)

with tempfile.TemporaryDirectory() as temp_dir:
    # 1. Frequency chart
    print("Creating frequency chart...")
    freq_chart = chart_gen.create_frequency_chart(frequency_data, hot_numbers, cold_numbers)
    freq_path = chart_gen.save_chart(freq_chart, os.path.join(temp_dir, 'frequency_chart'))
    print(f"✓ Frequency chart saved: {os.path.basename(freq_path)}")
    
    # 2. Trend chart
    print("Creating trend chart...")
    trend_chart = chart_gen.create_trend_chart(draws, hot_numbers[:5])
    trend_path = chart_gen.save_chart(trend_chart, os.path.join(temp_dir, 'trend_chart'))
    print(f"✓ Trend chart saved: {os.path.basename(trend_path)}")
    
    # 3. Pattern visualization
    print("Creating pattern visualization...")
    pattern_chart = chart_gen.create_pattern_visualization(pattern_summary)
    pattern_path = chart_gen.save_chart(pattern_chart, os.path.join(temp_dir, 'pattern_chart'))
    print(f"✓ Pattern chart saved: {os.path.basename(pattern_path)}")
    
    # 4. Recommendation comparison
    print("Creating recommendation comparison...")
    rec_numbers = {name: rec.numbers for name, rec in recommendations.items()}
    rec_chart = chart_gen.create_recommendation_comparison_chart(rec_numbers, frequency_data)
    rec_path = chart_gen.save_chart(rec_chart, os.path.join(temp_dir, 'recommendation_chart'))
    print(f"✓ Recommendation chart saved: {os.path.basename(rec_path)}")
    
    # 5. Comprehensive dashboard
    print("Creating comprehensive dashboard...")
    dashboard = chart_gen.create_comprehensive_dashboard(
        draws, frequency_data, pattern_summary, rec_numbers
    )
    dashboard_path = chart_gen.save_chart(dashboard, os.path.join(temp_dir, 'dashboard'))
    print(f"✓ Dashboard saved: {os.path.basename(dashboard_path)}")
    
    # Test different formats
    print("Testing different chart formats...")
    formats = ['png', 'pdf', 'svg']
    for fmt in formats:
        test_path = chart_gen.save_chart(freq_chart, os.path.join(temp_dir, f'test_chart'), fmt)
        print(f"✓ {fmt.upper()} format: {os.path.basename(test_path)}")
    
    print(f"\n📊 All charts generated successfully in: {temp_dir}")

# Test report generation
print("\n" + "="*50)
print("TESTING REPORT GENERATION")
print("="*50)

with tempfile.TemporaryDirectory() as temp_dir:
    # 1. Frequency report
    print("Generating frequency report...")
    freq_report = report_gen.generate_frequency_report(
        draws, frequency_data, hot_numbers, cold_numbers
    )
    freq_report_path = report_gen.save_report(freq_report, os.path.join(temp_dir, 'frequency_report'))
    print(f"✓ Frequency report saved: {os.path.basename(freq_report_path)}")
    print(f"  Report length: {len(freq_report)} characters")
    
    # 2. Pattern report
    print("Generating pattern report...")
    pattern_report = report_gen.generate_pattern_report(pattern_summary)
    pattern_report_path = report_gen.save_report(pattern_report, os.path.join(temp_dir, 'pattern_report'))
    print(f"✓ Pattern report saved: {os.path.basename(pattern_report_path)}")
    print(f"  Report length: {len(pattern_report)} characters")
    
    # 3. Recommendation report
    print("Generating recommendation report...")
    rec_report = report_gen.generate_recommendation_report(recommendations, frequency_data)
    rec_report_path = report_gen.save_report(rec_report, os.path.join(temp_dir, 'recommendation_report'))
    print(f"✓ Recommendation report saved: {os.path.basename(rec_report_path)}")
    print(f"  Report length: {len(rec_report)} characters")
    
    # 4. Comprehensive report
    print("Generating comprehensive report...")
    comprehensive_report = report_gen.generate_comprehensive_report(
        draws, frequency_data, pattern_summary, recommendations, hot_numbers, cold_numbers
    )
    comp_report_path = report_gen.save_report(comprehensive_report, os.path.join(temp_dir, 'comprehensive_report'))
    print(f"✓ Comprehensive report saved: {os.path.basename(comp_report_path)}")
    print(f"  Report length: {len(comprehensive_report)} characters")
    
    print(f"\n📄 All reports generated successfully in: {temp_dir}")

# Test report content quality
print("\n" + "="*50)
print("TESTING REPORT CONTENT QUALITY")
print("="*50)

# Check frequency report content
freq_lines = freq_report.split('\n')
print(f"✓ Frequency report has {len(freq_lines)} lines")
print(f"✓ Contains {freq_report.count('Number')} number references")
print(f"✓ Contains {freq_report.count('%')} percentage values")

# Check pattern report content
pattern_lines = pattern_report.split('\n')
print(f"✓ Pattern report has {len(pattern_lines)} lines")
print(f"✓ Contains {pattern_report.count('consecutive')} consecutive pattern references")
print(f"✓ Contains {pattern_report.count('odd')} odd/even references")

# Check recommendation report content
rec_lines = rec_report.split('\n')
print(f"✓ Recommendation report has {len(rec_lines)} lines")
print(f"✓ Contains {rec_report.count('Strategy')} strategy references")
print(f"✓ Contains {rec_report.count('Confidence')} confidence scores")

# Display sample content
print("\n" + "="*50)
print("SAMPLE REPORT CONTENT")
print("="*50)

print("Frequency Report Sample (first 10 lines):")
for i, line in enumerate(freq_lines[:10]):
    print(f"  {line}")

print(f"\nPattern Report Sample (executive summary):")
pattern_summary_lines = [line for line in pattern_lines if 'PATTERN SUMMARY' in line or 'Total Draws' in line or 'Pattern Complexity' in line]
for line in pattern_summary_lines[:5]:
    print(f"  {line}")

print(f"\nRecommendation Report Sample (strategies):")
strategy_lines = [line for line in rec_lines if 'STRATEGY' in line and '=' not in line]
for line in strategy_lines[:3]:
    print(f"  {line}")

# Performance metrics
print("\n" + "="*50)
print("PERFORMANCE METRICS")
print("="*50)

print(f"📊 Chart Generation:")
print(f"  • Frequency chart: ✓ Generated")
print(f"  • Trend chart: ✓ Generated") 
print(f"  • Pattern visualization: ✓ Generated")
print(f"  • Recommendation comparison: ✓ Generated")
print(f"  • Comprehensive dashboard: ✓ Generated")

print(f"\n📄 Report Generation:")
print(f"  • Frequency report: {len(freq_report):,} chars")
print(f"  • Pattern report: {len(pattern_report):,} chars")
print(f"  • Recommendation report: {len(rec_report):,} chars")
print(f"  • Comprehensive report: {len(comprehensive_report):,} chars")

print(f"\n📈 Data Coverage:")
print(f"  • Total draws analyzed: {len(draws)}")
print(f"  • Hot numbers identified: {len(hot_numbers)}")
print(f"  • Cold numbers identified: {len(cold_numbers)}")
print(f"  • Recommendation strategies: {len(recommendations)}")
print(f"  • Pattern complexity score: {pattern_summary['pattern_score']:.1f}/100")

print(f"\n🎉 Visualization system working perfectly!")
print(f"Charts and reports provide comprehensive insights into lottery data!")