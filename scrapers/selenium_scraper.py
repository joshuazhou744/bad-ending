from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import os
import random
import csv
import requests

import pymongo
import gridfs
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

first_names = [
    "James", "John", "Robert", "Michael", "William", 
    "David", "Richard", "Joseph", "Thomas", "Charles",
    "Christopher", "Daniel", "Matthew", "Anthony", "Mark",
    "Donald", "Steven", "Paul", "Andrew", "Joshua"
]
last_names = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", 
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin"
]

class Person():
    def __init__(self, name, link, img_src):
        self.name = name
        self.link = link
        self.img_src = img_src

    def __str__(self):
        return f"Person(name={self.name}, link={self.link}, img_src={self.img_src})"

def search_and_scrape_nsopw(first_name, last_name, url, length, page_number):
    driver = webdriver.Chrome()
    driver.get(url)

    wait = WebDriverWait(driver, 10)

    # click on the continue button popup
    continue_button = wait.until(EC.element_to_be_clickable((By.ID, "confirmBtn")))
    continue_button.click()

    # input search parameters
    firstname_input = wait.until(EC.element_to_be_clickable((By.ID, "firstname")))
    lastname_input  = wait.until(EC.element_to_be_clickable((By.ID, "lastname")))
    firstname_input.clear()
    firstname_input.send_keys(first_name)
    lastname_input.clear()
    lastname_input.send_keys(last_name)

    search_button = driver.find_element(By.ID, "searchbynamezip")
    search_button.click()

    # select the desired length of entries
    length_dropdown = wait.until(EC.element_to_be_clickable((By.NAME, "nsopwdt_length")))
    select_obj = Select(length_dropdown)
    select_obj.select_by_value(length)
    time.sleep(2)

    # click on the desired page number
    for i in range(page_number - 1):
        try:
            next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.paginate_button.next")))
            next_button.click()
            time.sleep(1)
        except TimeoutException:
            print(f"Pagination 'Next' button is not available on page {i+1}.")
            break

    # wait until the desired table element is present
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.table-wrapper")))
    time.sleep(3)

    html = driver.page_source
    driver.quit()

    # create BeautifulSoup parser
    soup = BeautifulSoup(html, 'html.parser')

    # select the desired elements
    rows = soup.select(
            "div.table-wrapper table tbody tr.odd td.sorting_1.dtr-control, "
            "div.table-wrapper table tbody tr.even td.sorting_1.dtr-control"
        )
    
    results = []
    for row in rows:
        link_tag = row.select_one("a.ext")
        if not link_tag:
            continue # skip if not found

        # extract person link
        link_url = link_tag.get('href', '').strip()

        # extract person name
        name = link_tag.get_text(separator=" ", strip=True)

        # extract image link
        img_tag = link_tag.select_one("img")
        if not img_tag: # if img is outside the link_tag
            img_tag = row.select_one('img')

        if img_tag:
            img_src = img_tag.get('src', '').strip()
            # prepend if image src is a relative path
            if img_src.startswith('/sites'):
                img_src = 'https://nsopw.gov' + img_src
        else:
            img_src = None

        person = Person(name, link_url, img_src)
        results.append(person)

    return results

def save_people_to_csv(people, filename="people.csv"):
    file_exists = os.path.exists(filename)

    with open(filename, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Name", "Link", "Image Source"])
        for person in people:
            writer.writerow([person.name, person.link, person.img_src])
    print(f"Appended {len(people)} records to {filename}")

def save_people_to_mongodb(people, mongo_uri, db_name, collection_name):
    client = pymongo.MongoClient(mongo_uri)
    db = client[db_name]
    fs = gridfs.GridFS(db)
    collection = db[collection_name]

    for person in people:
        image_id = None
        if person.img_src:
            try:
                response = requests.get(person.img_src, timeout=10)
                response.raise_for_status()
                image_data = response.content
                filename = os.path.basename(person.img_src.split("?")[0])
                image_id = fs.put(image_data, filename=filename)
                print("stored image")
            except Exception as e:
                print(f"error downloading/storing image: {e}")
        doc = {
            "name": person.name,
            "link": person.link,
            "image_id": image_id
        }
        collection.insert_one(doc)
    print(f"Inserted {len(people)} records to {db_name}.{collection_name}")

if __name__ == '__main__':
    
    # INPUTS
    first_name = random.choice(first_names) # write names or get random names
    last_name = random.choice(last_names)
    length = "100" # length of search results; 5, 10, 15, 25, 50, 100
    page_number = 1 # page number of search results starting from 1

    if page_number < 1:
        raise ValueError("Page number must be greater than 0")

    url = "https://www.nsopw.gov/search-public-sex-offender-registries"
    person_list = search_and_scrape_nsopw(first_name, last_name, url, length, page_number)
    #for person in person_list:
    #   print(person)

    DB_NAME = "face_recognition_db"
    COLLECTION_NAME = "persons"
    
    # Store the Person objects in MongoDB
    save_people_to_mongodb(person_list, MONGO_URI, DB_NAME, COLLECTION_NAME)
