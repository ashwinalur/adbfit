import pandas as pd
from bs4 import BeautifulSoup
import json
import re
import sys


week_suffix = "Aug18"
strava_club_name = "San Jose, California Club _ ADB FIT Season 6 on Strava"


# The HTML file on which this script operates
HTML_FILE_PATH = strava_club_name+"_"+week_suffix+".html"


# The CSV file that will be created/written out as part of the export process
CSV_FILE_PATH = strava_club_name+"_output_"+week_suffix+".csv"


# You'll need this if you want to maintain the strava ID as the key in your calculations. Members often change their strava names. 
members_dict = {

    '148402534' : 'adarsh bhupalam',
    '24299927' : 'Aditya Belwadi',
    '179651040' : 'Akshay Pavagada',
    '44242365' : 'Amar R',
    '182148829' : 'amit chadha',
    '129588892' : 'Amit Saha',
    '75651763' : 'Amiya Trivedi',
    '491089' : 'Ankit Agarwal',
    '182223099' : 'Ankit Bhargava',
    '25056219' : 'Anshul Sawant',
    '155771560' : 'Anumita Baral',
    '178922621' : 'Aparna Bhatnagar',
    '155402444' : 'Aparna Sundararajan',
    '129438646' : 'Arun V Rao',
    '155404899' : 'Ashish Bhargava',
    '178906827' : 'Ashwath  N',
    '107290125' : 'Ashwin Alur Sreesha',
    '22948013' : 'Ashwin Mysore',
    '67786267' : 'Avi Harsh',
    '114341022' : 'ayush sharma',
    '148218525' : 'Bandhu B',
    '157560406' : 'Bharath P',
    '1918586' : 'Chintan Shah',
    '27782974' : 'Darshan Modani',
    '139163002' : 'D M',
    '131351829' : 'Gayatri Vedula',
    '21393522' : 'Harish Mohan',
    '148402855' : 'haritha vaddi',
    '113469980' : 'Hemang Shah',
    '148900327' : 'jay ramamurthi',
    '33547295' : 'Karthik Krishnan',
    '156127858' : 'Karthik Moulie',
    '138862567' : 'Kav Gupta',
    '125463836' : 'Kishore Chennupati',
    '128028946' : 'Lakshmi Easwaran',
    '117355488' : 'Leela Mandalapu',
    '148282061' : 'Madhuvanthi Radhakrishnan',
    '78417663' : 'Manish Harsh',
    '82016829' : 'Manoj Tuguru',
    '178983428' : 'Manu Menon',
    '179848372' : 'MAYA RAO',
    '157777290' : 'Mini Kapur',
    '60832286' : 'mitesh patel',
    '47238' : 'Moh (Ashraf) Nainar',
    '157700685' : 'Nancy M',
    '113903907' : 'Neeti Berwal',
    '181127322' : 'Neha P',
    '17453581' : 'Nikhil Mahajan',
    '179551449' : 'Nikita Merchant',
    '158149813' : 'Niranjan Vaddi',
    '64167429' : 'Padmanaban Ramsamy',
    '107532498' : 'Parag Mehta',
    '108701392' : 'Parina Tanna',
    '75582596' : 'Preethi Prasad',
    '138915433' : 'Preeti Malik-Kale',
    '180704023' : 'Priti Nayak',
    '99471725' : 'Priya Dhaka',
    '182223472' : 'Priyanka Manjarekar',
    '179513424' : 'Rahul Gupta',
    '143909928' : 'raj desikavinayagompillai',
    '158614021' : 'Ramya Kudithipudi',
    '179551583' : 'rani uppal',
    '179047760' : 'Ranjit M',
    '113508445' : 'Ravi N',
    '179874165' : 'Reeba Thomas',
    '180551655' : 'Rekha Agarwal',
    '95003136' : 'Renuka Harsh',
    '106254233' : 'Ritesh Garg',
    '148808180' : 'Ritesh Kale',
    '113864178' : 'Roshan Rammohan',
    '178921418' : 'Samreen Zafer',
    '179874168' : 'Samuel Chacko',
    '22477449' : 'Sandeep Gangundi',
    '178909942' : 'Santosh G',
    '178913478' : 'Sapna E',
    '117299983' : 'Sateesh Medepalli',
    '3648915' : 'Satish 🚴  💤',
    '69775689' : 'saurin choksi',
    '179875481' : 'Sayanee Chakraborty',
    '86263866' : 'Shafeela Ashraf',
    '112111198' : 'Shaifali Gupta',
    '132735848' : 'Shalini Mukherjee',
    '157769111' : 'Shikha Bhargava',
    '179395559' : 'Shilpa Kumari',
    '60193309' : 'Shishir Gupta',
    '179078666' : 'shivam priyadarshi',
    '105337955' : 'Shobha Shah',
    '110540359' : 'Shweta Menon',
    '157546165' : 'Smitha V',
    '180019811' : 'Smruti Vaidya',
    '148903799' : 'Sneha G',
    '179887486' : 'Sri Keesara',
    '148713878' : 'Sripoorna  Amarnath',
    '42152917' : 'Subha Rajagopalan',
    '114064659' : 'Sujeet Bambawale',
    '148191125' : 'Sulu R',
    '157545267' : 'Sumanth Kubair',
    '179698082' : 'Supriya Patil',
    '180294038' : 'Supriya Sheshu',
    '179549673' : 'Supriya Sudheendra',
    '148809968' : 'Suresh Ayyalsamy',
    '178989316' : 'Swathi N',
    '180221598' : 'Tanushri Arun',
    '60724171' : 'Tejaswini Chadaga',
    '179325841' : 'Vaishali Dubal',
    '31098256' : 'vibhav lohani',
    '45788979' : 'Vikram Rao',
    '148772002' : 'Vishwas Manral',
    '19859082' : 'Vivek Ramanna',
    '179048330' : 'Zarna J'
}

def swap_dict_keys_values(dict_to_swap):
    """Swap keys and values in a dictionary."""
    return {value: key for key, value in dict_to_swap.items()}

def parse_html_to_df(html_file):
    """Parse HTML file and return DataFrame from the table."""
    with open(html_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all('table')
    table = tables[1]

    headers = [header.text.strip() for header in table.find_all('th')]
    rows = [
        [cell.text.strip() for cell in row.find_all('td')]
        for row in table.find_all('tr')[1:]
    ]

    return pd.DataFrame(rows, columns=headers)

def map_athlete_to_id(athlete_name, id_dict):
    """Map athlete name to Strava ID using a dictionary."""
    return id_dict.get(athlete_name, 'ID Not Found')

def time_to_seconds(time_str):
    """Convert time duration string to seconds."""
    match = re.match(r"(?:(\d+)h)?(?:\s*(\d+)m)?", time_str.strip())
    if not match:
        raise ValueError(f"Invalid time format: {time_str}")
    hours, minutes = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    return (hours * 3600) + (minutes * 60)

def process_data():
    """Main function to process the data."""
    # Load and prepare data

    print (sys.argv)
    print(len(members_dict))
    
    swapped_dict = swap_dict_keys_values(members_dict)

    # Parse HTML and create DataFrame
    df = parse_html_to_df(HTML_FILE_PATH)
    print("DataFrame before adding Strava ID:")
    print(df)

    # Add Strava ID column
    df['Strava ID'] = df['Athlete'].apply(lambda name: map_athlete_to_id(name, swapped_dict))

    # Convert time strings to seconds
    df['Time'] = df['Time'].apply(time_to_seconds)

    # Rename columns
    df.rename(columns={'Strava ID': 'athlete_id', 'Time': 'moving_time'}, inplace=True)

    # Swap second column with the last column
    columns = df.columns.tolist()
    columns[1], columns[-1] = columns[-1], columns[1]
    df = df[columns]

    # Save DataFrame to CSV
    df.to_csv(CSV_FILE_PATH, index=False)
    print("CSV file has been created successfully.")
    print("Final DataFrame:")
    print(df)

if __name__ == "__main__":
    process_data()
