import pandas as pd
import re
from datetime import datetime

def clean_date(date_str):
    """
    Clean and standardize date strings with various formats.
    Handles cases where months are in letters (full or abbreviated).
    Returns a standardized YYYY-MM-DD format or None if parsing fails.
    """
    if pd.isna(date_str) or date_str == '':
        return None
    
    # Common date patterns to match
    patterns = [
        # Formats with month names (full or abbreviated)
        r'(?P<day>\d{1,2})[-/\.\s](?P<month>[a-zA-Z]{3,})[-/\.\s](?P<year>\d{2,4})',
        r'(?P<month>[a-zA-Z]{3,})[-/\.\s](?P<day>\d{1,2})[-/\.\s](?P<year>\d{2,4})',
        r'(?P<year>\d{2,4})[-/\.\s](?P<month>[a-zA-Z]{3,})[-/\.\s](?P<day>\d{1,2})',
        
        # Numeric formats
        r'(?P<day>\d{1,2})[-/\.](?P<month>\d{1,2})[-/\.](?P<year>\d{2,4})',
        r'(?P<year>\d{2,4})[-/\.](?P<month>\d{1,2})[-/\.](?P<day>\d{1,2})',
        r'(?P<month>\d{1,2})[-/\.](?P<day>\d{1,2})[-/\.](?P<year>\d{2,4})',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, str(date_str), re.IGNORECASE)
        if match:
            try:
                day = match.group('day')
                month = match.group('month')
                year = match.group('year')
                
                # Handle 2-digit years
                if len(year) == 2:
                    year = f'20{year}' if int(year) < 50 else f'19{year}'
                
                # Convert month name to number if needed
                if month.isalpha():
                    try:
                        month_num = datetime.strptime(month[:3], '%b').month
                    except ValueError:
                        try:
                            month_num = datetime.strptime(month, '%B').month
                        except ValueError:
                            return None
                    month = str(month_num)
                
                # Pad single-digit day/month with leading zero
                day = day.zfill(2)
                month = month.zfill(2)
                
                # Validate date components
                if not (1 <= int(month) <= 12):
                    return None
                if not (1 <= int(day) <= 31):
                    return None
                
                # Try to create a date to validate (e.g., catches Feb 30)
                datetime.strptime(f'{year}-{month}-{day}', '%Y-%m-%d')
                
                return f'{year}-{month}-{day}'
            except (ValueError, AttributeError):
                continue
    
    return None

def process_movie_dates(input_file, output_file):
    """
    Process the input CSV file with movie dates and save cleaned version.
    """
    # Read the input CSV
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    # Clean each date in each column
    cleaned_df = df.copy()
    for column in cleaned_df.columns:
        cleaned_df[column] = cleaned_df[column].apply(clean_date)
    
    # Save the cleaned data
    try:
        cleaned_df.to_csv(output_file, index=False)
        print(f"Successfully processed and saved to {output_file}")
    except Exception as e:
        print(f"Error saving output file: {e}")

if __name__ == "__main__":
    input_csv = 'single1.csv'
    output_csv = 'single2.csv'
    
    process_movie_dates(input_csv, output_csv)
