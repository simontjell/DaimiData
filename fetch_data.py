#!/usr/bin/env python3
"""
Script to fetch and clean PhD data from AU CS website.
Fixes date errors and normalizes names for consistency.
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def fix_year(date_str):
    """Fix common year errors in dates"""
    if not date_str:
        return date_str
    
    # Fix specific known errors
    date_fixes = {
        "13-03-20015": "13-03-2015",
        "08-12-20017": "08-12-2017", 
        "19-05-215": "19-05-2015"
    }
    
    if date_str in date_fixes:
        return date_fixes[date_str]
    
    # Check for 3-digit years (like 215 instead of 2015)
    match = re.match(r'(\d{2}-\d{2}-)(\d{3})$', date_str)
    if match:
        day_month = match.group(1)
        year = match.group(2)
        if year.startswith('21'):
            fixed_year = '20' + year[1:]
            return day_month + fixed_year
    
    # Check for 5-digit years (like 20015 instead of 2015)
    match = re.match(r'(\d{2}-\d{2}-)(\d{5})$', date_str)
    if match:
        day_month = match.group(1)
        year = match.group(2)
        if year.startswith('200'):
            fixed_year = '20' + year[3:]
            return day_month + fixed_year
    
    return date_str

def parse_date(date_str):
    """Parse date string to ISO format"""
    if not date_str:
        return None
    
    # Fix year errors first
    date_str = fix_year(date_str)
    
    try:
        # Parse DD-MM-YYYY format
        dt = datetime.strptime(date_str, "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d")
    except:
        return date_str  # Return original if parsing fails

def normalize_name(name):
    """Normalize names to handle variations"""
    name_map = {
        'Clemens Klokmose': 'Clemens Nylandsted Klokmose',
        'Christian N. S. Pedersen': 'Christian N. Storm Pedersen',
        'Christian Nørgaard Storm Pedersen': 'Christian N. Storm Pedersen',
        'Christian Storm Pedersen': 'Christian N. Storm Pedersen',
        'Jesper Buus': 'Jesper Buus Nielsen',
        'Ivan Damgaard': 'Ivan Bjerre Damgård',
        'Ivan Damgård': 'Ivan Bjerre Damgård',
        'Gerth S. Brodal': 'Gerth Stølting Brodal',
        'Peter Mosses': 'Peter D. Mosses',
        'Michael Schwartzbach': 'Michael I. Schwartzbach',
        'Marianne Graves': 'Marianne Graves Petersen',
        'Jakob Bardram': 'Jakob Eyvind Bardram',
    }
    return name_map.get(name, name)

def fetch_phd_data():
    """Fetch and parse PhD data from AU CS department"""
    url = "https://cs.au.dk/education/phd/phds-produced/"
    
    print("Fetching data from:", url)
    response = requests.get(url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the table with PhD data
    table = soup.find('table')
    if not table:
        raise ValueError("Could not find PhD data table")
    
    phd_list = []
    
    # Process all rows (skip header)
    rows = table.find_all('tr')[1:]  # Skip header row
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 5:
            try:
                # Extract data from cells
                number = cells[0].get_text(strip=True)
                name = normalize_name(cells[1].get_text(strip=True))
                supervisors = cells[2].get_text(strip=True)
                date_raw = cells[3].get_text(strip=True)
                title = cells[4].get_text(strip=True)
                
                # Parse the date
                date_iso = parse_date(date_raw)
                
                # Extract year from date
                year = None
                if date_iso:
                    try:
                        year = int(date_iso.split('-')[0])
                    except:
                        pass
                
                phd_entry = {
                    "number": int(number) if number.isdigit() else number,
                    "name": name,
                    "supervisors": supervisors,
                    "date_raw": date_raw,
                    "date": date_iso,
                    "year": year,
                    "title": title
                }
                
                phd_list.append(phd_entry)
                
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
    
    return phd_list

def main():
    """Main function to fetch and save PhD data"""
    try:
        # Fetch the data
        phd_data = fetch_phd_data()
        
        print(f"Successfully fetched {len(phd_data)} PhD entries")
        
        # Save to JSON file
        output_file = "data/phd_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(phd_data, f, ensure_ascii=False, indent=2)
        
        print(f"Data saved to {output_file}")
        
        # Print some statistics
        if phd_data:
            years = [p['year'] for p in phd_data if p['year']]
            if years:
                print(f"PhD dissertations from {min(years)} to {max(years)}")
                print(f"Total PhDs: {len(phd_data)}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
