#!/usr/bin/env python3
"""
Manual data entry utility for Lotto Max results.
Use this to manually enter the latest real Lotto Max draw results.
"""

from datetime import datetime
from lotto_max_analyzer.data.models import DrawResult
from lotto_max_analyzer.data.storage import DataStorage
from lotto_max_analyzer.utils.validation import DataValidator
from datetime import timedelta

def get_latest_real_draw():
    """Get the latest real Lotto Max draw from user input."""
    print("🎯 Manual Lotto Max Data Entry")
    print("=" * 40)
    print("Enter the latest real Lotto Max draw results:")
    print("(You can find these at: https://www.olg.ca/en/lottery/lotto-max/winning-numbers)")
    print()
    
    validator = DataValidator()
    
    # Get draw date
    while True:
        print("📅 Enter draw date:")
        print("   Format: YYYY-MM-DD (e.g., 2025-08-16)")
        print("   Or press Enter for today's date")
        date_str = input("Date: ").strip()
        
        try:
            if not date_str:
                # Use today's date if nothing entered
                draw_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                print(f"   Using today: {draw_date.strftime('%Y-%m-%d')}")
            else:
                # Try multiple date formats
                formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']
                draw_date = None
                
                for fmt in formats:
                    try:
                        draw_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if draw_date is None:
                    raise ValueError("Could not parse date format")
            
            # Basic validation (don't use the validator that might be too strict)
            if draw_date.year < 2009:
                raise ValueError("Date cannot be before Lotto Max started (2009)")
            if draw_date > datetime.now() + timedelta(days=1):
                raise ValueError("Date cannot be in the future")
            
            print(f"✅ Date accepted: {draw_date.strftime('%Y-%m-%d')}")
            break
            
        except Exception as e:
            print(f"❌ Invalid date: {e}")
            print("   Try formats like: 2025-08-16, 2025/08/16, 08/16/2025")
            print()
    
    # Get winning numbers
    while True:
        print("🎲 Enter the 7 winning numbers:")
        print("   Format: space-separated (e.g., 5 12 18 25 33 41 47)")
        print("   Numbers must be between 1-50 and unique")
        numbers_str = input("Numbers: ").strip()
        
        try:
            # Handle different separators
            numbers_str = numbers_str.replace(',', ' ').replace('-', ' ')
            numbers = [int(x.strip()) for x in numbers_str.split() if x.strip()]
            
            # Basic validation
            if len(numbers) != 7:
                raise ValueError(f"Need exactly 7 numbers, got {len(numbers)}")
            
            for num in numbers:
                if not (1 <= num <= 50):
                    raise ValueError(f"Number {num} must be between 1-50")
            
            if len(set(numbers)) != 7:
                duplicates = [n for n in set(numbers) if numbers.count(n) > 1]
                raise ValueError(f"Numbers must be unique. Duplicates: {duplicates}")
            
            numbers = sorted(numbers)
            print(f"✅ Numbers accepted: {numbers}")
            break
            
        except ValueError as e:
            print(f"❌ Invalid numbers: {e}")
            print("   Example: 5 12 18 25 33 41 47")
            print()
    
    # Get bonus number
    while True:
        print("⭐ Enter the bonus number:")
        print(f"   Must be between 1-50 and not in main numbers: {numbers}")
        bonus_str = input("Bonus: ").strip()
        
        try:
            bonus = int(bonus_str)
            
            if not (1 <= bonus <= 50):
                raise ValueError(f"Bonus number must be between 1-50, got {bonus}")
            
            if bonus in numbers:
                raise ValueError(f"Bonus number {bonus} cannot be the same as a main number")
            
            print(f"✅ Bonus accepted: {bonus}")
            break
            
        except ValueError as e:
            print(f"❌ Invalid bonus: {e}")
            print()
    
    # Get jackpot amount
    while True:
        print("💰 Enter the jackpot amount:")
        print("   You can use: 15000000, 15,000,000, $15,000,000, or 15M")
        jackpot_str = input("Jackpot: ").strip()
        
        try:
            # Clean up the input
            jackpot_str = jackpot_str.replace('$', '').replace(',', '').replace(' ', '')
            
            # Handle millions notation
            if jackpot_str.upper().endswith('M'):
                jackpot = float(jackpot_str[:-1]) * 1_000_000
            else:
                jackpot = float(jackpot_str)
            
            if jackpot < 0:
                raise ValueError("Jackpot cannot be negative")
            
            if jackpot < 1_000_000:
                print(f"⚠️  Warning: Jackpot ${jackpot:,.0f} seems low for Lotto Max")
                confirm = input("   Continue anyway? (y/N): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    continue
            
            print(f"✅ Jackpot accepted: ${jackpot:,.0f}")
            break
            
        except ValueError as e:
            print(f"❌ Invalid jackpot: {e}")
            print("   Examples: 15000000, 15M, $15,000,000")
            print()
    
    # Create draw result
    draw = DrawResult(
        date=draw_date,
        numbers=sorted(numbers),
        bonus=bonus,
        jackpot_amount=jackpot,
        draw_id=f"REAL-{draw_date.strftime('%Y%m%d')}"
    )
    
    print("✅ Draw created successfully!")
    return draw

def save_real_draw():
    """Get and save a real draw to the database."""
    try:
        # Get draw from user
        draw = get_latest_real_draw()
        
        # Show summary
        print(f"\n📋 Draw Summary:")
        print(f"📅 Date: {draw.date.strftime('%Y-%m-%d')}")
        print(f"🎲 Numbers: {draw.numbers}")
        print(f"⭐ Bonus: {draw.bonus}")
        print(f"💰 Jackpot: ${draw.jackpot_amount:,.0f}")
        print(f"🆔 ID: {draw.draw_id}")
        
        # Confirm save
        confirm = input(f"\n💾 Save this draw to database? (Y/n): ").strip().lower()
        
        if confirm in ['', 'y', 'yes']:
            # Save to database
            storage = DataStorage()
            
            # Check if draw already exists
            existing_draws = storage.load_draws(
                start_date=draw.date,
                end_date=draw.date
            )
            
            if existing_draws:
                print(f"⚠️  Found {len(existing_draws)} existing draw(s) for {draw.date.strftime('%Y-%m-%d')}")
                for existing in existing_draws:
                    print(f"   Existing: {existing.numbers} + {existing.bonus} (${existing.jackpot_amount:,.0f})")
                
                overwrite = input("🔄 Overwrite existing draw? (y/N): ").strip().lower()
                if overwrite not in ['y', 'yes']:
                    print("❌ Save cancelled")
                    return False
            
            # Save the draw
            saved_count = storage.save_draws([draw])
            
            if saved_count > 0:
                print(f"✅ Successfully saved real draw to database!")
                
                # Show updated database status
                total_draws = storage.get_draw_count()
                print(f"📊 Total draws in database: {total_draws}")
                
                return True
            else:
                print(f"❌ Failed to save draw (may already exist)")
                return False
        else:
            print("❌ Save cancelled")
            return False
            
    except KeyboardInterrupt:
        print(f"\n❌ Entry cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def show_recent_draws():
    """Show recent draws in the database."""
    print(f"\n📊 Recent Draws in Database")
    print("=" * 40)
    
    try:
        storage = DataStorage()
        draws = storage.load_draws()
        
        if not draws:
            print("📭 No draws in database")
            return
        
        # Show last 5 draws
        recent_draws = sorted(draws, key=lambda d: d.date)[-5:]
        
        for draw in recent_draws:
            date_str = draw.date.strftime('%Y-%m-%d')
            real_indicator = "🟢" if "REAL-" in draw.draw_id else "🔵"
            print(f"{real_indicator} {date_str}: {draw.numbers} + {draw.bonus} (${draw.jackpot_amount:,.0f})")
        
        print(f"\n📈 Total: {len(draws)} draws")
        print("🟢 = Real data, 🔵 = Mock data")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def main():
    """Main function."""
    print("🎯 Lotto Max Manual Data Entry Utility")
    print("=" * 50)
    print("Use this tool to manually enter real Lotto Max draw results.")
    print("Get the latest results from: https://www.olg.ca/en/lottery/lotto-max/winning-numbers")
    print()
    
    while True:
        print("What would you like to do?")
        print("1. 📝 Enter new real draw")
        print("2. 📊 Show recent draws")
        print("3. 🚪 Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            success = save_real_draw()
            if success:
                print("\n🎉 Real draw added successfully!")
            print()
        elif choice == '2':
            show_recent_draws()
            print()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-3.")

if __name__ == "__main__":
    main()