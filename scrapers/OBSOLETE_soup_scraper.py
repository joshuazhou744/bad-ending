# DOESN'T WORK BECAUSE THE WEBSITE REQUIRES A SEARCH THAT DOESN'T UPDATE THE URL

import requests
from bs4 import BeautifulSoup
import os

class Person():
    def __init__(self, name, link, img_src):
        self.name = name
        self.link = link
        self.img_src = img_src

    def __str__(self):
        return f"Person(name={self.name}, link={self.link}, img_src={self.img_src})"

def scrape_url(url):
    response = requests.get(url)
    response.raise_for_status()

    # create BeautifulSoup parser
    soup = BeautifulSoup(response.text, 'html.parser')

    # select the desired elements
    rows = soup.select("div.table-wrapper table tbody tr.odd td.sorting_1.dtr-control, div.table-wrapper table tbody tr.even td.sorting_1.dtr-control")

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

        results.append(Person(name, link_url, img_src))

        return results

if __name__ == '__main__':
    url = 'https://www.nsopw.gov/en/Search/Results'
    results = scrape_url(url)
    for person in results:
        print(person)