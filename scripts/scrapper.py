from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.firefox.options import Options
from tqdm import tqdm
from fake_useragent import UserAgent

import csv
import pandas as pd
from time import sleep
import os
from bs4 import BeautifulSoup

from utils import sections_to_row

def parse_content_with_bullets(html, verbose=False):
    """
    Extract text content from HTML, including both paragraphs and bullet points,
    and returns them as a list of text fragments.
    """
    soup = BeautifulSoup(html, "html.parser")
    # Find both paragraph and list item elements not to leave some bulleted texts out of the data collection
    elements = soup.find_all(["p", "li"])
    # Join inline elements to preserve sentence continuity and preserve the logic of paragraphs to be individually annotated
    text_fragments = [el.get_text(separator=" ", strip=True) for el in elements if el.get_text(strip=True)]
    if verbose:
        print("Extracted content fragments:", text_fragments)
    return text_fragments

def main_page_extract(url, driver_path='driver/geckodriver', save=False, output_path='report_urls.csv', verbose=False):
    """
    Extracts report URLs from the main page of the ENB website.
    """
    options = Options()
    options.add_argument("-headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(driver_path)
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)
    sleep(3)

    # Accept cookies if the button exists.
    try:
        driver.find_element(By.XPATH, "//button[@class='agree-button eu-cookie-compliance-secondary-button']").click()
    except NoSuchElementException:
        pass

    # Expand all relevant accordion sections.
    buttons = driver.find_elements(By.XPATH, "//button[@class='o-accordion__heading js-accordion__heading']")
    for button in buttons[:-1]:
        try:
            driver.execute_script("arguments[0].scrollIntoView();", button)
            if button.is_displayed() and button.is_enabled():
                button.click()
        except ElementNotInteractableException:
            if verbose:
                print(f"Button {button} not interactable.")

    # Extract report links.
    report_links = driver.find_elements(By.XPATH, "//a[@class='o-accordion-item__heading-link']")
    report_urls = list(set(link.get_attribute("href") for link in report_links))
    # Select report URLs that include 'summary' or 'report'.
    report_urls_selected = [u for u in report_urls if 'summary' in u or 'report' in u]
    report_urls_selected.sort()
    data = [(url_, "daily-report" in str(url_)) for url_ in report_urls_selected]

    if verbose:
        print("Report URLs:", *report_urls_selected, sep='\n')

    if save:
        df = pd.DataFrame(data, columns=['url', "is_daily_report"])
        df.to_csv(output_path, index=False)
        if verbose:
            print(f'Links saved in {output_path}')

    driver.quit()
    return report_urls_selected

def report_page_extract(csv_path, url_col_name, driver_path='driver/geckodriver', save=False, output_path='report.csv', verbose=False):
    """
    Scrape report details from given URLs.
    """
    data = pd.read_csv(csv_path)
    if url_col_name not in data.columns:
        raise ValueError(f"La colonne '{url_col_name}' n'existe pas dans le fichier CSV.")

    urls = data[url_col_name].dropna().tolist()
    scraped_data = []
    user_agent = UserAgent().random

    options = Options()
    options.add_argument('--headless')
    options.add_argument(f"user-agent={user_agent}")
    service = Service(driver_path)

    for url in urls:
        try:
            driver = webdriver.Firefox(service=service, options=options)
            driver.get(url)
            sleep(3)

            # Attempt to click the cookie consent button.
            try:
                driver.find_element(By.XPATH, "//button[@class='agree-button eu-cookie-compliance-secondary-button']").click()
            except NoSuchElementException:
                if verbose:
                    print("Cookie consent button not found.")

            # Get the title and extract the first line if title is multi-line.
            title = driver.find_element(By.CLASS_NAME, 'c-node__title').text.split('\n')
            # Locate the article container with the report content.
            article_element = driver.find_element(By.XPATH, "//article[@class='o-section o-section--small-margin']")
            html_content = article_element.get_attribute('innerHTML')

            # Use the parsing function to extract text fragments and join them to form one continuous string.
            text_content = parse_content_with_bullets(html_content, verbose=verbose)
            #text_content = " ".join(text_fragments)

            scraped_data.append({"url": url, "title": title, "content": text_content})
            if verbose:
                print(f"Scraped data for {url}")
            driver.quit()
        except Exception as e:
            if verbose:
                print(f"Error while scraping {url}: {e}")

    if save:
        df_scrape = pd.DataFrame(scraped_data)
        df_data = pd.merge(data, df_scrape, on='url', how='inner')
        # If the title field is a list, take its first element.
        df_data['title'] = df_data['title'].apply(lambda x: x[0] if isinstance(x, list) else x)
        # Assuming sections_to_row is defined in your utils module.
        df_data = sections_to_row(df_data)
        df_data.to_csv(output_path, index=False, encoding='utf-8')
    return scraped_data

if __name__ == '__main__':
    urls_main = [
        'https://enb.iisd.org/bonn-climate-change-conference-sbi58-sbsta58',
        'https://enb.iisd.org/united-arab-emirates-climate-change-conference-cop28',
        'https://enb.iisd.org/bonn-climate-change-conference-sbi60-sbsta60',
        "https://enb.iisd.org/baku-un-climate-change-conference-cop29"
    ]
    csv_dir = 'csv/'
    driver_path = '/Users/rolly/Documents/10-19_Université_et_scolarité/18.Projets/columbia_scrapping/driver/geckodriver'

    for url in urls_main:
        output_path = os.path.join(csv_dir, url.split('/')[-1] + '.csv')
        main_page_extract(url, save=True, output_path=output_path, driver_path=driver_path, verbose=True)
        report_page_extract(output_path, url_col_name='url', driver_path=driver_path, save=True, output_path=output_path, verbose=True)
