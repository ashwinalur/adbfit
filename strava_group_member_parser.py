from bs4 import BeautifulSoup
import pandas as pd
import sys

def get_strava_club_members(full_members,html_file):
    """
    Scrapes Strava club member names and links from a saved strata group member page and adds it to a DF

    Args:

    full_members: pandas.DataFrame: A DataFrame containing member names, profile links, and stravaIds or None if an error occurs.
    html_file: a strava member page html file 

    Returns:

    full_members: pandas.DataFrame: A DataFrame containing member names, profile links, and stravaIds or None if an error occurs. 
    """
    try:
        with open(html_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        soup = BeautifulSoup(content, 'html.parser')

#        member_elements = soup.find_all('div', class_='text-headlineavatar avatar-athlete avatar-default')
        member_elements = soup.find_all('div', class_='text-headline')


        for member_element in member_elements:
            
            print(member_element)
            member_link_tag = member_element.find('a')
            strava_url = member_link_tag['href']
            strava_id = strava_url.split('/')[-1]
            member_name = member_link_tag.get_text()

            print(strava_url)
            print(strava_id)
            print(member_name)

            new_member = {'Name': member_name,
                          'Profile Page':strava_url,
                          'Strava ID':strava_id}
            
            if member_name and strava_id not in full_members['Strava ID']:
                full_members = pd.concat([full_members,
                                     pd.DataFrame([new_member])],
                                    ignore_index=True)
                               

        return full_members.drop_duplicates().reset_index(drop=True)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Example usage:
input_file_names = [
    "San Jose, California Club _ ADB FIT Season 6 on Strava_members_1.html",
    "San Jose, California Club _ ADB FIT Season 6 on Strava_members_2.html",
    "San Jose, California Club _ ADB FIT Season 6 on Strava_members_3.html",
    "San Jose, California Club _ ADB FIT Season 6 on Strava_members_4.html"
]

output_filename = "ADB_Fit_6_members_list.csv"

column_names = ['Name',
                'Profile Page',
                'Strava ID']

full_members = pd.DataFrame(columns=column_names)

if (sys.argv[1:]):
    input_file_names = sys.argv[1:]


for filename in input_file_names:
    full_members = get_strava_club_members(full_members, filename)


full_members.drop_duplicates().reset_index(drop=True)

if full_members is not None:
    print(full_members)

full_members.to_csv(output_filename, index=False)
