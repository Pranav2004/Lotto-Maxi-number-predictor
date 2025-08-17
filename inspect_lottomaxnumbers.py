#!/usr/bin/env python3
"""
Inspect the HTML structure of lottomaxnumbers.com to build a better parser.
"""

import requests
import urllib3
from bs4 import BeautifulSoup
import re
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def inspect_site():
    """Inspect the lottomaxnumbers.com site structure."""
    print("🔍 Inspecting LottoMaxNumbers.com Structure")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    session.verify = False
    
    url = "https://www.lottomaxnumbers.com/"
    
    try:
        response = session.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"✅ Successfully loaded page")
        print(f"📏 Content length: {len(response.text)} characters")
        
        # Look for specific elements that might contain lottery data
        print("\n🔍 Searching for lottery data containers...")
        
        # Check for common lottery result patterns
        selectors_to_check = [
            'table',
            '.result', '.draw', '.winning', '.numbers',
            '.latest', '.recent', '.current',
            '[class*="lotto"]', '[class*="max"]', '[class*="draw"]',
            '[class*="number"]', '[class*="result"]',
            'div[data-*]', 'span[data-*]'
        ]
        
        found_elements = {}
        
        for selector in selectors_to_check:
            try:
                elements = soup.select(selector)
                if elements:
                    found_elements[selector] = len(elements)
                    print(f"   {selector}: {len(elements)} elements")
            except:
                continue
        
        # Look for the most promising elements
        print(f"\n📊 Most promising selectors:")
        for selector, count in sorted(found_elements.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {selector}: {count} elements")
        
        # Examine tables specifically
        tables = soup.find_all('table')
        print(f"\n📋 Found {len(tables)} tables:")
        
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            print(f"   Table {i+1}: {len(rows)} rows")
            
            # Show first few rows of each table
            for j, row in enumerate(rows[:3]):
                cells = row.find_all(['td', 'th'])
                if cells:
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    print(f"      Row {j+1}: {cell_texts}")
        
        # Look for divs with lottery-related classes
        print(f"\n🎲 Looking for lottery number containers...")
        
        lottery_divs = soup.find_all('div', class_=re.compile(r'(number|ball|draw|result|lotto|max)', re.I))
        print(f"Found {len(lottery_divs)} lottery-related divs")
        
        for i, div in enumerate(lottery_divs[:5]):
            text = div.get_text(strip=True)
            if text and len(text) < 100:
                print(f"   Div {i+1} ({div.get('class', [])}): {text}")
        
        # Look for spans with numbers
        print(f"\n🔢 Looking for number spans...")
        
        number_spans = soup.find_all('span', string=re.compile(r'^\d{1,2}$'))
        print(f"Found {len(number_spans)} spans with single/double digits")
        
        if number_spans:
            numbers = [span.get_text(strip=True) for span in number_spans[:20]]
            print(f"   Sample numbers: {numbers}")
        
        # Look for specific lottery max patterns
        print(f"\n🎯 Looking for 'Lotto Max' specific content...")
        
        lotto_max_text = soup.find_all(string=re.compile(r'lotto.?max', re.I))
        print(f"Found {len(lotto_max_text)} 'Lotto Max' text references")
        
        # Look for date patterns
        print(f"\n📅 Looking for date patterns...")
        
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, response.text, re.I)
            if matches:
                print(f"   Pattern {pattern}: {len(matches)} matches")
                print(f"      Sample: {matches[:5]}")
        
        # Look for jackpot amounts
        print(f"\n💰 Looking for jackpot amounts...")
        
        jackpot_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'[\d,]+\s*million',
            r'jackpot.*?\$?[\d,]+'
        ]
        
        for pattern in jackpot_patterns:
            matches = re.findall(pattern, response.text, re.I)
            if matches:
                print(f"   Pattern {pattern}: {len(matches)} matches")
                print(f"      Sample: {matches[:5]}")
        
        # Save a sample of the HTML for manual inspection
        print(f"\n💾 Saving HTML sample for manual inspection...")
        
        with open('lottomaxnumbers_sample.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"✅ Saved to 'lottomaxnumbers_sample.html'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inspecting site: {e}")
        return False
    
    finally:
        session.close()

def find_latest_draw_manually():
    """Try to manually find the latest draw using various approaches."""
    print(f"\n🎯 Manual Latest Draw Detection")
    print("=" * 40)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    session.verify = False
    
    url = "https://www.lottomaxnumbers.com/"
    
    try:
        response = session.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strategy 1: Look for the most recent date
        print("📅 Strategy 1: Finding recent dates...")
        
        # Find all text that looks like dates
        date_regex = r'(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})'
        
        all_text = soup.get_text()
        date_matches = re.findall(date_regex, all_text, re.I)
        
        print(f"Found {len(date_matches)} potential dates")
        
        # Parse and sort dates
        parsed_dates = []
        for match in date_matches:
            date_str = match[0] if isinstance(match, tuple) else match
            try:
                for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%b %d, %Y', '%B %d, %Y']:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        parsed_dates.append((parsed_date, date_str))
                        break
                    except ValueError:
                        continue
            except:
                continue
        
        if parsed_dates:
            # Sort by date and show most recent
            parsed_dates.sort(key=lambda x: x[0], reverse=True)
            print(f"Most recent dates found:")
            for date_obj, date_str in parsed_dates[:5]:
                print(f"   {date_str} ({date_obj.strftime('%Y-%m-%d')})")
        
        # Strategy 2: Look for number sequences
        print(f"\n🎲 Strategy 2: Finding number sequences...")
        
        # Look for sequences of 7 numbers
        number_sequences = re.findall(r'(\d{1,2})\s*[-,\s]\s*(\d{1,2})\s*[-,\s]\s*(\d{1,2})\s*[-,\s]\s*(\d{1,2})\s*[-,\s]\s*(\d{1,2})\s*[-,\s]\s*(\d{1,2})\s*[-,\s]\s*(\d{1,2})', all_text)
        
        print(f"Found {len(number_sequences)} potential 7-number sequences")
        
        for i, seq in enumerate(number_sequences[:3]):
            numbers = [int(n) for n in seq]
            if all(1 <= n <= 50 for n in numbers):
                print(f"   Sequence {i+1}: {numbers}")
        
        # Strategy 3: Look in specific HTML structures
        print(f"\n🏗️  Strategy 3: Checking HTML structures...")
        
        # Check for common lottery result containers
        containers = [
            soup.find('div', class_=re.compile(r'latest|recent|current', re.I)),
            soup.find('table'),
            soup.find('div', {'id': re.compile(r'result|draw|latest', re.I)}),
        ]
        
        for i, container in enumerate(containers):
            if container:
                text = container.get_text(strip=True)
                print(f"   Container {i+1}: {text[:100]}...")
                
                # Look for numbers in this container
                numbers = re.findall(r'\b(\d{1,2})\b', text)
                lottery_numbers = [int(n) for n in numbers if 1 <= int(n) <= 50]
                if len(lottery_numbers) >= 7:
                    print(f"      Potential numbers: {lottery_numbers[:10]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in manual detection: {e}")
        return False
    
    finally:
        session.close()

def main():
    """Main inspection function."""
    print("🔍 LottoMaxNumbers.com Site Inspector")
    print("=" * 70)
    
    success1 = inspect_site()
    success2 = find_latest_draw_manually()
    
    if success1 or success2:
        print(f"\n✅ Inspection completed!")
        print(f"📄 Check 'lottomaxnumbers_sample.html' for the full HTML")
        print(f"🔧 Use this information to improve the parser")
    else:
        print(f"\n❌ Inspection failed")

if __name__ == "__main__":
    main()