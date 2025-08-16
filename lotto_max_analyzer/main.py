"""Main entry point for Lotto Max Analyzer."""

import argparse
import sys
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from lotto_max_analyzer.config import APP_NAME, VERSION, DEFAULT_ANALYSIS_YEARS, LOG_LEVEL, LOG_FORMAT


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - Analyze historical Lotto Max data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --fetch-data                    # Fetch latest historical data
  %(prog)s --analyze                       # Run comprehensive analysis
  %(prog)s --recommend balanced            # Get balanced number recommendations
  %(prog)s --visualize                     # Generate charts and reports
  %(prog)s --analyze --recommend hot --visualize  # Full analysis workflow
  %(prog)s --start-date 2024-01-01 --end-date 2024-12-31 --analyze  # Custom date range
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'{APP_NAME} {VERSION}'
    )
    
    # Data operations
    data_group = parser.add_argument_group('Data Operations')
    data_group.add_argument(
        '--fetch-data',
        action='store_true',
        help='Fetch latest historical data from sources'
    )
    
    data_group.add_argument(
        '--fetch-all',
        action='store_true',
        help='Fetch complete historical data from Lotto Max beginning (Sept 2009)'
    )
    
    data_group.add_argument(
        '--status',
        action='store_true',
        help='Show database status and available data'
    )
    
    # Analysis operations
    analysis_group = parser.add_argument_group('Analysis Operations')
    analysis_group.add_argument(
        '--analyze',
        action='store_true',
        help='Run comprehensive frequency and pattern analysis'
    )
    
    analysis_group.add_argument(
        '--recommend',
        choices=['hot', 'cold', 'balanced', 'all'],
        help='Generate number recommendations (hot=frequent numbers, cold=overdue numbers, balanced=mixed strategy, all=show all strategies)'
    )
    
    analysis_group.add_argument(
        '--visualize',
        action='store_true',
        help='Generate charts and detailed reports'
    )
    
    # Configuration options
    config_group = parser.add_argument_group('Configuration Options')
    config_group.add_argument(
        '--start-date',
        type=str,
        metavar='YYYY-MM-DD',
        help='Start date for analysis (default: 2 years ago)'
    )
    
    config_group.add_argument(
        '--end-date',
        type=str,
        metavar='YYYY-MM-DD',
        help='End date for analysis (default: today)'
    )
    
    config_group.add_argument(
        '--output-dir',
        type=str,
        metavar='DIR',
        help='Output directory for charts and reports (default: current directory)'
    )
    
    config_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    config_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-essential output'
    )
    
    # Interactive mode
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode with guided workflow'
    )
    
    return parser


def setup_logging(verbose: bool = False, quiet: bool = False):
    """Setup logging configuration."""
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """Validate that date range is reasonable."""
    if start_date >= end_date:
        print("❌ Error: Start date must be before end date")
        return False
    
    # Check if date range is too large (more than 10 years)
    if (end_date - start_date).days > 365 * 10:
        print("⚠️  Warning: Date range is very large (>10 years). This may take a while.")
        response = input("Continue? (y/N): ").strip().lower()
        return response in ['y', 'yes']
    
    # Check if end date is in the future
    if end_date > datetime.now():
        print("⚠️  Warning: End date is in the future. Using today's date instead.")
        return True
    
    return True


def check_database_status() -> dict:
    """Check database status and return information."""
    try:
        from lotto_max_analyzer.data.storage import DataStorage
        
        storage = DataStorage()
        draws = storage.get_all_draws()
        
        if not draws:
            return {
                'status': 'empty',
                'count': 0,
                'message': 'No data available. Run --fetch-data to get historical data.'
            }
        
        latest_draw = storage.get_latest_draw()
        oldest_draw = min(draws, key=lambda d: d.date)
        
        return {
            'status': 'ready',
            'count': len(draws),
            'latest_date': latest_draw.date,
            'oldest_date': oldest_draw.date,
            'message': f'Database contains {len(draws)} draws from {oldest_draw.date.strftime("%Y-%m-%d")} to {latest_draw.date.strftime("%Y-%m-%d")}'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'count': 0,
            'message': f'Database error: {e}'
        }


def interactive_mode():
    """Run the application in interactive mode."""
    print(f"\n🎯 Welcome to {APP_NAME} Interactive Mode!")
    print("=" * 60)
    
    # Check database status
    db_status = check_database_status()
    print(f"📊 Database Status: {db_status['message']}")
    
    if db_status['status'] == 'empty':
        print("\n🔄 You need historical data to perform analysis.")
        print("Choose data fetching option:")
        print("1. Fetch recent data (last 2 years) - Quick")
        print("2. Fetch ALL historical data (since 2009) - Comprehensive")
        print("3. Skip (exit)")
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            print("Fetching recent historical data...")
            success = run_fetch_data()
        elif choice == '2':
            print("Fetching complete historical data...")
            success = run_fetch_all_data()
        else:
            print("❌ Cannot proceed without data. Exiting interactive mode.")
            return
        
        if not success:
            print("❌ Failed to fetch data. Exiting interactive mode.")
            return
    
    # Main interactive loop
    while True:
        print(f"\n🎯 {APP_NAME} - What would you like to do?")
        print("1. 📊 Run Analysis (frequency and patterns)")
        print("2. 🎲 Get Number Recommendations")
        print("3. 📈 Generate Visualizations")
        print("4. 🔄 Fetch Recent Data")
        print("5. 📥 Fetch ALL Historical Data (since 2009)")
        print("6. ℹ️  Show Database Status")
        print("7. 🚪 Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            run_analysis_interactive()
        elif choice == '2':
            run_recommendations_interactive()
        elif choice == '3':
            run_visualizations_interactive()
        elif choice == '4':
            run_fetch_data()
        elif choice == '5':
            run_fetch_all_data()
        elif choice == '6':
            show_status()
        elif choice == '7':
            print("👋 Thank you for using Lotto Max Analyzer!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-7.")


def run_analysis_interactive():
    """Run analysis in interactive mode."""
    print("\n📊 Running Comprehensive Analysis...")
    
    # Get date range
    use_custom_dates = input("Use custom date range? (y/N): ").strip().lower()
    
    if use_custom_dates in ['y', 'yes']:
        start_str = input("Start date (YYYY-MM-DD) or press Enter for default: ").strip()
        end_str = input("End date (YYYY-MM-DD) or press Enter for default: ").strip()
        
        try:
            start_date = parse_date(start_str) if start_str else None
            end_date = parse_date(end_str) if end_str else None
        except argparse.ArgumentTypeError as e:
            print(f"❌ {e}")
            return
    else:
        start_date = None
        end_date = None
    
    # Set defaults if not provided
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=365 * DEFAULT_ANALYSIS_YEARS)
    
    if not validate_date_range(start_date, end_date):
        return
    
    # Run analysis
    success = run_analysis(start_date, end_date)
    
    if success:
        print("✅ Analysis complete!")
        
        # Ask if user wants recommendations too
        get_recs = input("\nWould you like number recommendations based on this analysis? (Y/n): ").strip().lower()
        if get_recs in ['', 'y', 'yes']:
            run_recommendations_interactive()


def run_recommendations_interactive():
    """Run recommendations in interactive mode."""
    print("\n🎲 Generating Number Recommendations...")
    
    print("Available strategies:")
    print("1. 🔥 Hot Numbers (frequently appearing)")
    print("2. ❄️  Cold Numbers (overdue/infrequent)")
    print("3. ⚖️  Balanced (mixed approach)")
    print("4. 📋 All Strategies")
    
    strategy_choice = input("Choose strategy (1-4): ").strip()
    
    strategy_map = {
        '1': 'hot',
        '2': 'cold', 
        '3': 'balanced',
        '4': 'all'
    }
    
    strategy = strategy_map.get(strategy_choice)
    if not strategy:
        print("❌ Invalid choice.")
        return
    
    # Get date range (reuse from previous analysis or ask)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * DEFAULT_ANALYSIS_YEARS)
    
    success = run_recommendations(start_date, end_date, strategy)
    
    if success:
        print("✅ Recommendations complete!")


def run_visualizations_interactive():
    """Run visualizations in interactive mode."""
    print("\n📈 Generating Visualizations and Reports...")
    
    # Ask about output directory
    output_dir = input("Output directory (press Enter for current directory): ").strip()
    if not output_dir:
        output_dir = "."
    
    # Create output directory if it doesn't exist
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        return
    
    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * DEFAULT_ANALYSIS_YEARS)
    
    success = run_visualizations(start_date, end_date, output_dir)
    
    if success:
        print("✅ Visualizations complete!")
        print(f"📁 Files saved to: {os.path.abspath(output_dir)}")


def show_status():
    """Show database and system status."""
    print("\n📊 System Status")
    print("=" * 40)
    
    db_status = check_database_status()
    print(f"Database: {db_status['message']}")
    
    if db_status['status'] == 'ready':
        print(f"Total draws: {db_status['count']}")
        print(f"Date range: {db_status['oldest_date'].strftime('%Y-%m-%d')} to {db_status['latest_date'].strftime('%Y-%m-%d')}")
        
        # Calculate data freshness
        days_old = (datetime.now().date() - db_status['latest_date'].date()).days
        if days_old == 0:
            freshness = "Up to date"
        elif days_old <= 7:
            freshness = f"{days_old} days old"
        else:
            freshness = f"{days_old} days old (consider updating)"
        
        print(f"Data freshness: {freshness}")
    
    # Show configuration
    print(f"\nConfiguration:")
    print(f"App version: {VERSION}")
    print(f"Default analysis period: {DEFAULT_ANALYSIS_YEARS} years")


def run_fetch_data() -> bool:
    """Run data fetching operation."""
    try:
        from lotto_max_analyzer.data.fetcher import DataFetcher
        from lotto_max_analyzer.data.storage import DataStorage
        
        print("🔄 Fetching historical data...")
        fetcher = DataFetcher()
        storage = DataStorage()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * DEFAULT_ANALYSIS_YEARS)
        
        draws = fetcher.fetch_historical_data(start_date, end_date)
        saved_count = storage.save_draws(draws)
        
        print(f"✅ Fetched {len(draws)} draws")
        print(f"✅ Saved {saved_count} new draws to database")
        print(f"✅ Total draws in database: {storage.get_draw_count()}")
        
        if draws:
            latest = max(draws, key=lambda d: d.date)
            print(f"✅ Latest draw: {latest.date.strftime('%Y-%m-%d')} (${latest.jackpot_amount:,.0f})")
        
        fetcher.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return False


def run_fetch_all_data() -> bool:
    """Fetch complete historical Lotto Max data from the beginning."""
    try:
        from lotto_max_analyzer.data.fetcher import DataFetcher
        from lotto_max_analyzer.data.storage import DataStorage
        
        print("🔄 Fetching COMPLETE Lotto Max historical data...")
        print("📅 This includes all draws from September 25, 2009 to present")
        print("⏱️  This may take a few moments...")
        
        fetcher = DataFetcher()
        storage = DataStorage()
        
        # Check current database status
        current_count = storage.get_draw_count()
        print(f"📊 Current database has {current_count} draws")
        
        # Fetch all historical data
        draws = fetcher.fetch_all_historical_data()
        
        print(f"📥 Processing {len(draws)} historical draws...")
        
        # Save in batches for better performance
        batch_size = 100
        saved_count = 0
        
        for i in range(0, len(draws), batch_size):
            batch = draws[i:i + batch_size]
            batch_saved = storage.save_draws(batch)
            saved_count += batch_saved
            
            # Show progress
            progress = min(i + batch_size, len(draws))
            print(f"📊 Progress: {progress}/{len(draws)} draws processed ({progress/len(draws)*100:.1f}%)")
        
        final_count = storage.get_draw_count()
        
        print(f"\n✅ Successfully processed {len(draws)} historical draws")
        print(f"✅ Saved {saved_count} new draws to database")
        print(f"✅ Total draws in database: {final_count}")
        
        if draws:
            earliest = min(draws, key=lambda d: d.date)
            latest = max(draws, key=lambda d: d.date)
            print(f"📅 Date range: {earliest.date.strftime('%Y-%m-%d')} to {latest.date.strftime('%Y-%m-%d')}")
            print(f"💰 Latest jackpot: ${latest.jackpot_amount:,.0f}")
        
        # Calculate some quick stats
        total_years = (latest.date - earliest.date).days / 365.25
        avg_draws_per_year = len(draws) / total_years
        print(f"📈 Coverage: {total_years:.1f} years, ~{avg_draws_per_year:.0f} draws per year")
        
        fetcher.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fetching complete historical data: {e}")
        return False


def run_analysis(start_date: datetime, end_date: datetime) -> bool:
    """Run analysis operation."""
    try:
        from lotto_max_analyzer.data.storage import DataStorage
        from lotto_max_analyzer.analysis.frequency import FrequencyAnalyzer
        from lotto_max_analyzer.analysis.patterns import PatternAnalyzer
        
        print("📊 Running comprehensive analysis...")
        storage = DataStorage()
        freq_analyzer = FrequencyAnalyzer()
        pattern_analyzer = PatternAnalyzer()
        
        draws = storage.load_draws(start_date, end_date)
        
        if len(draws) < 50:
            print(f"⚠️  Warning: Only {len(draws)} draws available. Need at least 50 for reliable analysis.")
            print("   Consider fetching more data or adjusting date range.")
            return False
        
        print(f"✅ Analyzing {len(draws)} draws")
        
        # Run frequency analysis
        print(f"\n📊 FREQUENCY ANALYSIS")
        print(f"{'='*40}")
        
        trends = freq_analyzer.analyze_frequency_trends(draws)
        
        print(f"Period: {trends['date_range']['start'][:10]} to {trends['date_range']['end'][:10]}")
        print(f"Expected frequency per number: {trends['overall_stats']['expected_frequency']:.1f}")
        
        hot_numbers = trends['hot_numbers'][:5]
        cold_numbers = trends['cold_numbers'][:5]
        print(f"🔥 Hot numbers: {hot_numbers}")
        print(f"❄️  Cold numbers: {cold_numbers}")
        
        # Run pattern analysis
        print(f"\n🔍 PATTERN ANALYSIS")
        print(f"{'='*40}")
        
        pattern_summary = pattern_analyzer.get_pattern_summary(draws)
        
        consecutive_patterns = pattern_summary['consecutive_patterns']
        print(f"Consecutive patterns found: {len(consecutive_patterns)}")
        for pattern in consecutive_patterns[:3]:
            print(f"  • {pattern.description}: {pattern.frequency} times (sig: {pattern.significance:.2f})")
        
        odd_even = pattern_summary['odd_even_analysis']
        most_common = odd_even['most_common_pattern']
        print(f"Most common odd/even pattern: {most_common[0]} ({most_common[1]} times)")
        
        range_analysis = pattern_summary['range_analysis']
        balance_score = range_analysis['range_balance_score']
        print(f"Range balance score: {balance_score:.1f}/100")
        
        print(f"Overall pattern complexity: {pattern_summary['pattern_score']:.1f}/100")
        
        # Show overdue numbers
        overdue = freq_analyzer.get_overdue_numbers(draws, threshold_days=30)
        if overdue:
            print(f"\n📅 OVERDUE NUMBERS (30+ days):")
            for i, (num, days) in enumerate(overdue[:5]):
                print(f"   {i+1}. Number {num}: {days} days ago")
        
        print(f"\n✅ Comprehensive analysis complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False


def run_recommendations(start_date: datetime, end_date: datetime, strategy: str) -> bool:
    """Run recommendations operation."""
    try:
        from lotto_max_analyzer.data.storage import DataStorage
        from lotto_max_analyzer.analysis.recommendations import RecommendationEngine
        
        print(f"🎲 Generating {strategy} number recommendations...")
        storage = DataStorage()
        engine = RecommendationEngine()
        
        draws = storage.load_draws(start_date, end_date)
        
        if len(draws) < 50:
            print(f"⚠️  Warning: Only {len(draws)} draws available. Need at least 50 for reliable recommendations.")
            return False
        
        print(f"✅ Generating recommendations from {len(draws)} draws")
        
        if strategy == 'all':
            # Generate all strategies
            recommendations = engine.get_multiple_recommendations(draws)
            
            print(f"\n🎯 ALL STRATEGY RECOMMENDATIONS")
            print(f"{'='*60}")
            
            for strategy_name, recommendation in recommendations.items():
                strategy_title = strategy_name.replace('_', ' ').title()
                print(f"\n{strategy_title}:")
                print(f"Numbers: {recommendation.numbers}")
                print(f"Confidence: {recommendation.confidence:.2f}")
                
                # Show frequency analysis
                frequency = engine.frequency_analyzer.calculate_number_frequency(draws)
                pick_frequencies = [frequency[num] for num in recommendation.numbers]
                avg_pick_freq = sum(pick_frequencies) / len(pick_frequencies)
                overall_avg = sum(frequency.values()) / len(frequency)
                print(f"Frequency ratio: {avg_pick_freq / overall_avg:.2f}x")
        else:
            # Map CLI strategy names to internal names
            strategy_mapping = {
                'hot': 'hot_numbers',
                'cold': 'cold_numbers',
                'balanced': 'balanced'
            }
            
            internal_strategy = strategy_mapping.get(strategy, strategy)
            
            recommendation = engine.generate_recommendation_with_rationale(draws, internal_strategy)
            
            print(f"\n🎯 {strategy.title()} Strategy Recommendation")
            print(f"{'='*60}")
            print(f"Numbers: {recommendation.numbers}")
            print(f"Confidence: {recommendation.confidence:.2f}")
            print(f"\nRationale: {recommendation.rationale}")
            
            # Show additional context
            frequency = engine.frequency_analyzer.calculate_number_frequency(draws)
            pick_frequencies = [frequency[num] for num in recommendation.numbers]
            avg_pick_freq = sum(pick_frequencies) / len(pick_frequencies)
            overall_avg = sum(frequency.values()) / len(frequency)
            
            print(f"\n📊 Pick Analysis:")
            print(f"Average frequency of picks: {avg_pick_freq:.1f}")
            print(f"Overall average frequency: {overall_avg:.1f}")
            print(f"Frequency ratio: {avg_pick_freq / overall_avg:.2f}x")
            
            odd_count = sum(1 for n in recommendation.numbers if n % 2 == 1)
            print(f"Odd/even split: {odd_count}-{7-odd_count}")
        
        print(f"\n✅ Recommendation complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error generating recommendations: {e}")
        return False


def run_visualizations(start_date: datetime, end_date: datetime, output_dir: str = ".") -> bool:
    """Run visualizations operation."""
    try:
        from lotto_max_analyzer.data.storage import DataStorage
        from lotto_max_analyzer.analysis.frequency import FrequencyAnalyzer
        from lotto_max_analyzer.analysis.patterns import PatternAnalyzer
        from lotto_max_analyzer.analysis.recommendations import RecommendationEngine
        from lotto_max_analyzer.visualization.charts import ChartGenerator
        from lotto_max_analyzer.visualization.reports import ReportGenerator
        
        print("📈 Creating visualizations and reports...")
        
        # Initialize components
        storage = DataStorage()
        freq_analyzer = FrequencyAnalyzer()
        pattern_analyzer = PatternAnalyzer()
        rec_engine = RecommendationEngine()
        chart_gen = ChartGenerator()
        report_gen = ReportGenerator()
        
        draws = storage.load_draws(start_date, end_date)
        
        if len(draws) < 50:
            print(f"⚠️  Warning: Only {len(draws)} draws available. Need at least 50 for reliable visualizations.")
            return False
        
        print(f"✅ Creating visualizations from {len(draws)} draws")
        
        # Run analysis
        frequency_data = freq_analyzer.calculate_number_frequency(draws)
        hot_numbers = freq_analyzer.get_hot_numbers(draws)
        cold_numbers = freq_analyzer.get_cold_numbers(draws)
        pattern_summary = pattern_analyzer.get_pattern_summary(draws)
        recommendations = rec_engine.get_multiple_recommendations(draws)
        
        # Generate charts
        print(f"\n📊 Generating Charts:")
        
        freq_chart = chart_gen.create_frequency_chart(frequency_data, hot_numbers, cold_numbers)
        freq_path = chart_gen.save_chart(freq_chart, os.path.join(output_dir, 'lotto_max_frequency'))
        print(f"✅ Frequency chart: {os.path.basename(freq_path)}")
        
        pattern_chart = chart_gen.create_pattern_visualization(pattern_summary)
        pattern_path = chart_gen.save_chart(pattern_chart, os.path.join(output_dir, 'lotto_max_patterns'))
        print(f"✅ Pattern chart: {os.path.basename(pattern_path)}")
        
        rec_numbers = {name: rec.numbers for name, rec in recommendations.items()}
        rec_chart = chart_gen.create_recommendation_comparison_chart(rec_numbers, frequency_data)
        rec_path = chart_gen.save_chart(rec_chart, os.path.join(output_dir, 'lotto_max_recommendations'))
        print(f"✅ Recommendation chart: {os.path.basename(rec_path)}")
        
        dashboard = chart_gen.create_comprehensive_dashboard(
            draws, frequency_data, pattern_summary, rec_numbers
        )
        dashboard_path = chart_gen.save_chart(dashboard, os.path.join(output_dir, 'lotto_max_dashboard'))
        print(f"✅ Dashboard: {os.path.basename(dashboard_path)}")
        
        # Generate reports
        print(f"\n📄 Generating Reports:")
        
        comprehensive_report = report_gen.generate_comprehensive_report(
            draws, frequency_data, pattern_summary, recommendations, hot_numbers, cold_numbers
        )
        report_path = report_gen.save_report(comprehensive_report, os.path.join(output_dir, 'lotto_max_analysis_report'))
        print(f"✅ Analysis report: {os.path.basename(report_path)}")
        
        freq_report = report_gen.generate_frequency_report(draws, frequency_data, hot_numbers, cold_numbers)
        freq_report_path = report_gen.save_report(freq_report, os.path.join(output_dir, 'lotto_max_frequency_report'))
        print(f"✅ Frequency report: {os.path.basename(freq_report_path)}")
        
        pattern_report = report_gen.generate_pattern_report(pattern_summary)
        pattern_report_path = report_gen.save_report(pattern_report, os.path.join(output_dir, 'lotto_max_pattern_report'))
        print(f"✅ Pattern report: {os.path.basename(pattern_report_path)}")
        
        rec_report = report_gen.generate_recommendation_report(recommendations, frequency_data)
        rec_report_path = report_gen.save_report(rec_report, os.path.join(output_dir, 'lotto_max_recommendation_report'))
        print(f"✅ Recommendation report: {os.path.basename(rec_report_path)}")
        
        print(f"\n✅ Visualization complete!")
        print(f"📊 Charts: 4 files generated")
        print(f"📄 Reports: 4 files generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating visualizations: {e}")
        return False


def main():
    """Main application entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose if hasattr(args, 'verbose') else False, 
                  args.quiet if hasattr(args, 'quiet') else False)
    
    # Handle interactive mode
    if hasattr(args, 'interactive') and args.interactive:
        interactive_mode()
        return
    
    # Handle status check
    if hasattr(args, 'status') and args.status:
        show_status()
        return
    
    # Set default date range if not provided
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * DEFAULT_ANALYSIS_YEARS)
    
    if hasattr(args, 'start_date') and args.start_date:
        try:
            start_date = parse_date(args.start_date)
        except argparse.ArgumentTypeError as e:
            print(f"❌ {e}")
            sys.exit(1)
    
    if hasattr(args, 'end_date') and args.end_date:
        try:
            end_date = parse_date(args.end_date)
        except argparse.ArgumentTypeError as e:
            print(f"❌ {e}")
            sys.exit(1)
    
    # Validate date range
    if not validate_date_range(start_date, end_date):
        sys.exit(1)
    
    # Adjust end date if in future
    if end_date > datetime.now():
        end_date = datetime.now()
    
    # Set output directory
    output_dir = getattr(args, 'output_dir', None) or '.'
    if output_dir != '.':
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            print(f"❌ Error creating output directory: {e}")
            sys.exit(1)
    
    # Show header (unless quiet mode)
    if not (hasattr(args, 'quiet') and args.quiet):
        print(f"🎯 {APP_NAME} v{VERSION}")
        print(f"📅 Analysis period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        if output_dir != '.':
            print(f"📁 Output directory: {output_dir}")
        print()
    
    try:
        # Check if any action is specified
        actions = [
            getattr(args, 'fetch_data', False),
            getattr(args, 'fetch_all', False),
            getattr(args, 'analyze', False),
            getattr(args, 'recommend', None) is not None,
            getattr(args, 'visualize', False)
        ]
        
        if not any(actions):
            print("❓ No action specified. Here are some options:")
            print("   --fetch-data          Fetch recent historical data")
            print("   --fetch-all           Fetch ALL historical data (since 2009)")
            print("   --analyze             Run analysis")
            print("   --recommend balanced  Get recommendations")
            print("   --visualize           Create charts and reports")
            print("   --interactive         Interactive mode")
            print("   --status              Show database status")
            print("   --help                Show all options")
            print("\n💡 Try: python -m lotto_max_analyzer.main --interactive")
            return
        
        # Execute requested operations
        success_count = 0
        total_operations = sum(actions)
        
        if getattr(args, 'fetch_data', False):
            print("🔄 Operation 1: Fetching Recent Data")
            if run_fetch_data():
                success_count += 1
            print()
        
        if getattr(args, 'fetch_all', False):
            print(f"🔄 Operation {success_count + 1}: Fetching ALL Historical Data")
            if run_fetch_all_data():
                success_count += 1
            print()
        
        if getattr(args, 'analyze', False):
            print(f"📊 Operation {success_count + 1}: Running Analysis")
            if run_analysis(start_date, end_date):
                success_count += 1
            print()
        
        if getattr(args, 'recommend', None):
            print(f"🎲 Operation {success_count + 1}: Generating Recommendations")
            if run_recommendations(start_date, end_date, args.recommend):
                success_count += 1
            print()
        
        if getattr(args, 'visualize', False):
            print(f"📈 Operation {success_count + 1}: Creating Visualizations")
            if run_visualizations(start_date, end_date, output_dir):
                success_count += 1
            print()
        
        # Show summary
        if not (hasattr(args, 'quiet') and args.quiet):
            if success_count == total_operations:
                print(f"🎉 All operations completed successfully! ({success_count}/{total_operations})")
            else:
                print(f"⚠️  {success_count}/{total_operations} operations completed successfully.")
                if success_count < total_operations:
                    print("   Some operations failed. Check the output above for details.")
    
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.exception("Unexpected error occurred")
        print(f"❌ Unexpected error: {e}")
        print("   Use --verbose for more details or check the logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()