import pandas as pd
from bs4 import BeautifulSoup
import json
import re
import sys

# Constants for season 7
strava_club_names = [
    "San Jose, California Club _ Almaden Fit - Season 7 (Group 1 - Odds) on Strava",
    "San Jose, California Club _ Almaden Fit - Season 7 (Group 2 - Evens) on Strava"
]

output_file = "Almaden Fit - Season 7"+"_output_"


def time_to_minutes(time_str):
    """Convert time duration string to seconds."""
    match = re.match(r"(?:(\d+)h)?(?:\s*(\d+)m)?", time_str.strip())
    if not match:
        raise ValueError(f"Invalid time format: {time_str}")
    hours, minutes = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    return (hours * 60) + (minutes)

def remove_miles(miles_str):
    return miles_str.replace("mi", "").strip()

def remove_feet(feet_str):
    return feet_str.replace("ft", "").strip()
    
# Parse the Strava leaderboard html into a DataFrame
def parse_strava_leaderboard(html_file):

    with open(html_file, 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Find all rows in the table body
    tables = soup.find_all('table')
    # Get the leaderboard table
    table = tables[1]

    data_list = []

    # 1. Extract Headers from <thead>
    header_row = table.find('thead').find_all('th')
    # Get text from headers, but we'll modify them slightly to fit our extra columns
    headers = [th.get_text(strip=True) for th in header_row]
    
    # Insert 'Strava URL' and 'Strava ID' after 'Athlete' (the 2nd column)
    headers.remove("Rank")
    headers.insert(6, "Strava URL")
    headers.insert(7, "Strava ID")

    # 2. Extract Data from <tbody>
    # This automatically skips the header row because headers are in <thead>
    rows = table.find('tbody').find_all('tr')

    
    for row in rows:
        
        # 1. Extract standard columns
    
        # Athlete info is special
        athlete_cell = row.find('td', class_='athlete')
        name_tag = athlete_cell.find('a', class_='athlete-name')
        athlete_name = name_tag.get_text(strip=True)
        strava_url = name_tag['href']
        
        # Extract Numerical ID using Regex (looks for digits at the end of the URL)
        # Example: https://www.strava.com/athletes/110540359 -> 110540359
        strava_id_match = re.search(r'athletes/(\d+)', strava_url)
        strava_id = strava_id_match.group(1) if strava_id_match else "N/A"
    
        # Remaining metrics
        time_str = row.find('td', class_='moving_time').get_text(strip=True)
        time = time_to_minutes(time_str)
        activities = row.find('td', class_='num_activities').get_text(strip=True)
        distance_str = row.find('td', class_='distance').get_text(strip=True)
        distance = remove_miles(distance_str)
        elev_gain_str = row.find('td', class_='elev_gain').get_text(strip=True)
        elev_gain = remove_feet(elev_gain_str)

        # 2. Add to our list
        data_list.append([
            athlete_name, time, activities, distance, elev_gain, strava_url, strava_id
        ])
                      
    return pd.DataFrame(data_list, columns=headers) 


def process_data(week_suffix):
    """Main function to process the data."""
    # Load and prepare data


    # The HTML files on which this script operates
    html_file1 = strava_club_names[0]+"_"+week_suffix+".html"
    html_file2 = strava_club_names[1]+"_"+week_suffix+".html"

    # Parse HTML and create DataFrame
    df1 = parse_strava_leaderboard(html_file1)     
    df2 = parse_strava_leaderboard(html_file2)    
        
    df = pd.concat([df1, df2], ignore_index = True)
    
    df_sorted = df.drop_duplicates().sort_values(by="Athlete")

    # Swap second column with the last column
    #    columns = df.columns.tolist()
    #    columns[1], columns[-1] = columns[-1], columns[1]
    #    df = df[columns]


    # The CSV file that will be created/written out as part of the export process
    CSV_FILE_PATH = output_file+week_suffix+".csv"
    
    # Save DataFrame to CSV
    df_sorted.to_csv(CSV_FILE_PATH, index=False, header=True)
    print("CSV file has been created successfully.")
    print("Final DataFrame:")
    print(df_sorted)

if __name__ == "__main__":

    if(len(sys.argv)>1):
        week_suffix = sys.argv[1]              
        process_data(week_suffix)
    else:
        raise Exception("Enter Week number argument in format MMMDD")
