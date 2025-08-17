#!/usr/bin/env python3
"""
Test script to fetch real Lotto Max data from legitimate online sources.
This script attempts to connect to official lottery websites and extract current results.
"""

import sys
import logging
from datetime import datetime, timedelta
from lotto_max_analyzer.data.fetcher import DataFetcher
from lotto_max_analyzer.data.storage import DataStorage

def setup_logging():
    """Setup logging for debugging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_real_data_sources():
    """Test fetching from real Lotto Max data sources."""
    print("🔍 Testing Real Lotto Max Data Sources")
    print("=" * 50)
    
    fetcher = DataFetcher()
    
    # Test recent data (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"📅 Attempting to fetch data from {start_date.date()} to {end_date.date()}")
    print("🌐 Trying official lottery websites...")
    
    try:
        # This will attempt to fetch from real sources
        draws = fetcher.fetch_historical_data(start_date, end_date)
        
        if draws:
            print(f"✅ Successfully fetched {len(draws)} real draws!")
            
            # Show the most recent draw
            latest = max(draws, key=lambda d: d.date)
            print(f"\n🎰 Latest Real Draw:")
            print(f"📅 Date: {latest.date.strftime('%Y-%m-%d')}")
            print(f"🎲 Numbers: {latest.numbers}")
            print(f"⭐ Bonus: {latest.bonus}")
            print(f"💰 Jackpot: ${latest.jackpot_amount:,.0f}")
            
            # Save to database
            storage = DataStorage()
            saved_count = storage.save_draws(draws)
            print(f"\n💾 Saved {saved_count} real draws to database")
            
            return True
            
        else:
            print("❌ No draws fetched from real sources")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching real data: {e}")
        print("\n🔧 This is expected if:")
        print("   • Websites have changed their structure")
        print("   • Anti-scraping measures are in place")
        print("   • Network connectivity issues")
        print("   • Sites require JavaScript rendering")
        return False
    
    finally:
        fetcher.close()

def test_individual_sources():
    """Test each data source individually."""
    print("\n🔍 Testing Individual Data Sources")
    print("=" * 50)
    
    fetcher = DataFetcher()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    sources = [
        ("OLG (Ontario Lottery)", fetcher._fetch_from_olg_site),
        ("Lotto649.com", fetcher._fetch_from_lotto649_site),
        ("Atlantic Lottery", fetcher._fetch_from_atlantic_lottery_site),
    ]
    
    for source_name, source_func in sources:
        print(f"\n🌐 Testing {source_name}...")
        try:
            draws = source_func(start_date, end_date)
            if draws:
                print(f"✅ {source_name}: Found {len(draws)} draws")
                latest = max(draws, key=lambda d: d.date)
                print(f"   Latest: {latest.date.strftime('%Y-%m-%d')} - ${latest.jackpot_amount:,.0f}")
            else:
                print(f"⚠️  {source_name}: No draws found")
        except Exception as e:
            print(f"❌ {source_name}: Failed - {e}")
    
    fetcher.close()

def show_current_database_status():
    """Show what's currently in the database."""
    print("\n📊 Current Database Status")
    print("=" * 50)
    
    try:
        storage = DataStorage()
        draws = storage.load_draws()
        
        if draws:
            print(f"📈 Total draws in database: {len(draws)}")
            
            latest = max(draws, key=lambda d: d.date)
            oldest = min(draws, key=lambda d: d.date)
            
            print(f"📅 Date range: {oldest.date.strftime('%Y-%m-%d')} to {latest.date.strftime('%Y-%m-%d')}")
            
            # Check if we have any real data (vs mock data)
            real_data_indicators = [
                any("LM-" not in draw.draw_id for draw in draws[-10:]),  # Non-mock IDs
                any(draw.jackpot_amount % 1000000 != 0 for draw in draws[-10:]),  # Non-round jackpots
            ]
            
            if any(real_data_indicators):
                print("✅ Database appears to contain some real data")
            else:
                print("⚠️  Database contains mock/simulated data")
                
            print(f"\n🎰 Latest draw in database:")
            print(f"📅 Date: {latest.date.strftime('%Y-%m-%d')}")
            print(f"🎲 Numbers: {latest.numbers}")
            print(f"⭐ Bonus: {latest.bonus}")
            print(f"💰 Jackpot: ${latest.jackpot_amount:,.0f}")
            print(f"🆔 ID: {latest.draw_id}")
            
        else:
            print("📭 Database is empty")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

def main():
    """Main test function."""
    setup_logging()
    
    print("🎯 Lotto Max Real Data Fetcher Test")
    print("=" * 60)
    print("This script tests fetching real Lotto Max data from official sources.")
    print("Note: Success depends on website availability and structure.")
    print()
    
    # Show current status
    show_current_database_status()
    
    # Test real data fetching
    success = test_real_data_sources()
    
    # Test individual sources for debugging
    test_individual_sources()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Real data fetching test completed successfully!")
        print("💡 You can now use the analyzer with real Lotto Max data.")
    else:
        print("⚠️  Real data fetching failed - using mock data for now.")
        print("💡 The analyzer still works fully with simulated data for testing.")
    
    print("\n🔧 To improve real data fetching:")
    print("   • Check website structures and update parsing logic")
    print("   • Add more data sources")
    print("   • Implement JavaScript rendering (Selenium)")
    print("   • Use official APIs if available")

if __name__ == "__main__":
    main()