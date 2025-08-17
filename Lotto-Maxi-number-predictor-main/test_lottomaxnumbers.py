#!/usr/bin/env python3
"""
Test script specifically for fetching data from lottomaxnumbers.com
"""

import sys
import logging
from datetime import datetime
from lotto_max_analyzer.data.real_data_sources import RealDataFetcher
from lotto_max_analyzer.data.storage import DataStorage

def setup_logging():
    """Setup detailed logging for debugging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_lottomaxnumbers_specifically():
    """Test fetching specifically from lottomaxnumbers.com"""
    print("Testing LottoMaxNumbers.com Specifically")
    print("=" * 60)
    
    fetcher = RealDataFetcher()
    
    try:
        print("Attempting to fetch from lottomaxnumbers.com...")
        
        # Test the specific method
        results = fetcher._fetch_from_lottomaxnumbers()
        
        if results:
            print(f"SUCCESS! Found {len(results)} real draws from lottomaxnumbers.com")
            print()
            
            # Show all results
            for i, draw in enumerate(sorted(results, key=lambda d: d.date), 1):
                print(f"Draw {i}:")
                print(f"   Date: {draw.date.strftime('%Y-%m-%d')}")
                print(f"   Numbers: {draw.numbers}")
                print(f"   Bonus: {draw.bonus}")
                print(f"   Jackpot: ${draw.jackpot_amount:,.0f}")
                print(f"   ID: {draw.draw_id}")
                print()
            
            # Save to database
            print("Saving to database...")
            storage = DataStorage()
            saved_count = storage.save_draws(results)
            
            print(f"Saved {saved_count} new draws to database")
            
            # Show database status
            total_draws = storage.get_draw_count()
            print(f"Total draws in database: {total_draws}")
            
            return True
            
        else:
            print("No results found from lottomaxnumbers.com")
            return False
            
    except Exception as e:
        print(f"Error fetching from lottomaxnumbers.com: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Show more details for debugging
        import traceback
        print("\nDetailed error information:")
        traceback.print_exc()
        
        return False
    
    finally:
        fetcher.close()

def test_manual_url_fetch():
    """Test fetching the raw HTML to see what we get."""
    print("\nManual URL Test")
    print("=" * 40)
    
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    session.verify = False
    
    url = "https://www.lottomaxnumbers.com/"
    
    try:
        print(f"Fetching: {url}")
        response = session.get(url, timeout=15)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)} characters")
        print(f"Content Type: {response.headers.get('content-type', 'Unknown')}")
        
        if response.status_code == 200:
            # Show first 500 characters
            preview = response.text[:500]
            print(f"\nContent Preview:")
            print("-" * 40)
            print(preview)
            print("-" * 40)
            
            # Look for lottery-related keywords
            keywords = ['lotto', 'max', 'draw', 'winning', 'numbers', 'jackpot', 'bonus']
            found_keywords = []
            
            content_lower = response.text.lower()
            for keyword in keywords:
                if keyword in content_lower:
                    count = content_lower.count(keyword)
                    found_keywords.append(f"{keyword}({count})")
            
            print(f"\nKeywords found: {', '.join(found_keywords)}")
            
            # Look for number patterns
            import re
            number_patterns = re.findall(r'\b\d{1,2}\b', response.text)
            lottery_numbers = [int(n) for n in number_patterns if 1 <= int(n) <= 50]
            
            if lottery_numbers:
                print(f"Potential lottery numbers found: {len(lottery_numbers)} numbers")
                print(f"   Sample: {lottery_numbers[:20]}")
            
            return True
            
        else:
            print(f"HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Request failed: {e}")
        return False
    
    finally:
        session.close()

def show_current_database():
    """Show what's currently in the database."""
    print("\nCurrent Database Status")
    print("=" * 40)
    
    try:
        storage = DataStorage()
        draws = storage.load_draws()
        
        if draws:
            print(f"Total draws: {len(draws)}")
            
            # Show recent draws
            recent = sorted(draws, key=lambda d: d.date)[-5:]
            print(f"\nRecent draws:")
            for draw in recent:
                real_indicator = "Real" if "REAL-" in draw.draw_id or "LMNUM-" in draw.draw_id else "Mock"
                print(f"   {real_indicator} {draw.date.strftime('%Y-%m-%d')}: {draw.numbers} + {draw.bonus}")
            
            print("\nReal = Real data, Mock = Mock data")
            
        else:
            print("Database is empty")
            
    except Exception as e:
        print(f"Database error: {e}")

def main():
    """Main test function."""
    setup_logging()
    
    print("LottoMaxNumbers.com Data Fetcher Test")
    print("=" * 70)
    print("Testing data fetching from: https://www.lottomaxnumbers.com/")
    print()
    
    # Show current database
    show_current_database()
    
    # Test manual URL fetch first
    manual_success = test_manual_url_fetch()
    
    if manual_success:
        # Test the specific fetcher
        fetch_success = test_lottomaxnumbers_specifically()
        
        if fetch_success:
            print("\nSUCCESS! Real Lotto Max data fetched successfully!")
            print("You can now run the analyzer with real data.")
        else:
            print("\nFetching failed, but the site is accessible.")
            print("The HTML structure might need adjustment in the parser.")
    else:
        print("\nCould not access lottomaxnumbers.com")
        print("Check internet connection or try again later.")
    
    print("\n" + "=" * 70)
    print("Next steps:")
    print("   • If successful: Run 'python -m lotto_max_analyzer.main --analyze'")
    print("   • If failed: Check the HTML structure and update the parser")
    print("   • Alternative: Use 'python manual_data_entry.py' to enter data manually")

if __name__ == "__main__":
    main()