import requests
import pandas as pd # -*- coding: utf-8 -*-
from dotenv import dotenv_values
import argparse
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
import os 
import time
config = dotenv_values(".env")
# Initialize a global variable for the WebDriver
driver = ''

def get_username(username):
    driver.get(f"https://twitter.com/{username}/{option}")


# Function to create the WebDriver instance
def create_driver(cookie, option):
    global driver

    # Configure Chrome options, including a custom extension
    options = webdriver.ChromeOptions()
    # Add headless mode and disable GPU
    options.add_argument('--window-position=-32000,-32000')
    # options.add_argument('--headless')
    options.add_extension(r"Old-Twitter-Layout-2023.crx")

    # Create the WebDriver instance with the configured options
    driver = webdriver.Chrome(options=options)

    # Navigate to Twitter and set the authentication cookie
    driver.get('https://twitter.com/')
    driver.add_cookie({'name': 'auth_token', 'value': cookie, 'domain': '.twitter.com',
                       'secure': True, 'path': '/', })
 
    

# Function to scrape followers or following
def scrape_users(option):
    start_time = time.time()
    
    final_located = False
    data = [
        ['Name', 'Username']  # Translated variable names
    ]

    # Get the number of followers or following
    time.sleep(5)
    user_count = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, f'//*[@id="profile-stat-{option}-value"]')))
    user_count = user_count.text

    len_names = 0
    message = True
    count = 0
    # Scroll down until the last user is located
    while not final_located:
       
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight)")

        names = driver.find_elements(By.XPATH, '//div[@class="user-item-text"]')
        # Keep track of how many users remaining
        new_len_names = len(names)
        if len_names != new_len_names:
            print(f'{new_len_names}/{user_count} {option} loaded.')
            len_names = new_len_names
            count = 0
        else:
            message = True
           
        if message and count == 0:
            print(f"Allowing the system some time to load the remaining {option}.")
            message = False
            count = 1

        try:
            element = WebDriverWait(driver, 0.1).until(
                EC.visibility_of_element_located((By.XPATH, "/html/body/div[4]/main/div/div[2]/div[4]"))
            )
            load_located = True
        except TimeoutException:
            load_located = False
        try:
            element_final = WebDriverWait(driver, 0.1).until(
                EC.visibility_of_element_located(
                    (By.XPATH, f'//*[@id="{option}-list"]/div[{user_count}]/div[1]/a/div/span[1]'))
            )  
            final_located = True
        except:
            final_located = False
        if load_located:
            driver.execute_script("arguments[0].click();", element)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Scrolling took {execution_time} seconds to execute.")
    return data

# Function to save followers or following to a CSV file
def save_users(data, username, output_folder, option):
    start_time1 = time.time()

    # Get lists of user names and usernames
    names = driver.find_elements(By.XPATH, '//div[@class="user-item-text"]')
    usernames = driver.find_elements(By.XPATH, '//span[@class="tweet-header-handle"]')

    # Append user data to the existing data list
    for i in range(len(names)):
        data.append([names[i].text, usernames[i].text])

    # Create the specified output folder if it doesn't exist
    
    os.makedirs(output_folder, exist_ok=True)

    # Save data to a CSV file within the specified output folder
    csv_file_path = os.path.join(output_folder, f'{username}_{option}.csv')

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerows(data)

    end_time1 = time.time()
    execution_time = end_time1 - start_time1
    print(f"Writing took {execution_time} seconds to execute.")

def compare_users(username,output_folder):
    data = [
        ['Name', 'Username']  # Translated variable names
    ]
    names = driver.find_elements(By.XPATH, '//div[@class="user-item-text"]')
    usernames = driver.find_elements(By.XPATH, '//span[@class="tweet-header-handle"]')

    # Append user data to the existing data list
    for i in range(len(names)):
        data.append([names[i].text, usernames[i].text])
        # print(usernames[i].text)

    if os.path.exists(os.path.join(output_folder, f'{username}_{option}.csv')):
        new_df = pd.DataFrame(data[1:], columns=data[0])
        csv_file_path = os.path.join(output_folder, f'{username}_{option}.csv')
        old_df = pd.read_csv(csv_file_path)
        # Clean up usernames in both DataFrames
        new_df['Username'] = new_df['Username'].str.replace(r'\r\n', '', regex=True)
        old_df['Username'] = old_df['Username'].str.replace(r'\r\n', '', regex=True)
        # Find new followers (users present in new_df but not in old_df)
        new_followers = new_df[~new_df['Username'].isin(old_df['Username'])]
        # Find unfollowed users (users present in old_df but not in new_df)
        unfollowed_users = old_df[~old_df['Username'].isin(new_df['Username'])]
        return (list(new_followers[['Username']].itertuples(index=False, name=None)),list(unfollowed_users[['Username']].itertuples(index=False, name=None)))
    else:
        print("No Compare , First time scrapping..")
        return False

def send_mess(user_id,compare_res,token):
   response = requests.post(
            url='https://api.telegram.org/bot{0}/{1}'.format(token, 'sendMessage'),
            data={'chat_id': user_id, 'text': compare_res}
        ).json()
   print(response)

def countdown(t):
    if t<1:
        return
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        t -= 1


if __name__ == "__main__":
    cookie = config['cookie']
    usernames = config['username']
    output_folder= config['output_folder']
    option= config['option']
    tg_id=config['tg_id']
    bot_token=config['bot_token']
    time_interval=config['time_interval']
    print("Creating the driver: It may take some time if it's the first time.")
    create_driver(cookie, option)
    print("Driver created successfully.")
    def rerun():
        for username in usernames.split(','):
            get_username(username)
            print(f"Scraping {username} {option}...")
            data = scrape_users(option)
            print(f"{option.capitalize()} scraped successfully.")

            print(f"{option.capitalize()} Comparing.")
            compare = compare_users(username,output_folder)
            if compare:
                message = 'Here is The Details of '+username+'\n'
                new,old = compare[0],compare[1]
                new,old = [i[0] for i in new],[i[0] for i in old]
                if len(new)>0:
                    message+='New '+option+'\n'
                    message+="\n".join(new)
                if len(old)>0:
                    message+='Unfollowed '+option+'\n'
                    message+="\n".join(old)
                if len(new)<1 and len(old)<1:
                    message+="\nNo New "+option.capitalize()
                send_mess(tg_id,message,bot_token)

            print(f"Saving {option} to CSV...")
            save_users(data, username, output_folder, option)
            print(f"{option.capitalize()} saved to CSV successfully.")

    while True:
        start_time = time.time() #0
        rerun()
        end_time = time.time() #580
        print(f"Taken {round(end_time-start_time)} Second to scrap.")
        count_down = int(time_interval) - round(end_time-start_time)
        countdown(int(count_down))
    # driver.quit()
