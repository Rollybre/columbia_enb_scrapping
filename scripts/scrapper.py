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

def main_page_extract(url, driver_path='driver/geckodriver', save=False, output_path='report_urls.csv', verbose=False):
    """
    Extracts report URLs from the main page of a conference website.

    Args:
        url (str): The URL of the conference main page.
        driver_path (str): Path to the GeckoDriver.
        save (bool): Whether to save the URLs to a CSV file.
        output_path (str): Path to save the CSV file.
        verbose (bool): Whether to print extracted URLs.

    Returns:
        list: A list of unique report URLs.
    """
    options = Options() 
    options.add_argument("-headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(driver_path)
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)
    sleep(3)

    # Accept cookies if the button exists
    try:
        driver.find_element(By.XPATH, "//button[@class='agree-button eu-cookie-compliance-secondary-button']").click()
    except NoSuchElementException:
        pass

    # Expand all relevant sections
    buttons = driver.find_elements(By.XPATH, "//button[@class='o-accordion__heading js-accordion__heading']")
    for button in buttons[:-1]:
        try:
            driver.execute_script("arguments[0].scrollIntoView();", button)
            if button.is_displayed() and button.is_enabled():
                button.click()
        except ElementNotInteractableException:
            if verbose:
                print(f"Le bouton {button} n'est pas interactif.")

    # Extract report links
    report_links = driver.find_elements(By.XPATH, "//a[@class='o-accordion-item__heading-link']")
    report_urls = list(set(link.get_attribute("href") for link in report_links))

    report_urls_selected = [u for u in report_urls if('summary' in u) or ('report' in u) ]
    report_urls_selected.sort()
    data = [(url_, "daily-report" in str(url_)) for url_ in report_urls_selected]

    if verbose:
        print("Report URLs:", *report_urls_selected, sep='\n')

    if save:
        ## save as a df + csv
        df= pd.DataFrame(data, columns=['url', "is_daily_report"])
        df.to_csv(output_path)
        if verbose :
            print(f'Links saved in {output_path}')


    driver.quit()
    return report_urls_selected

def report_page_extract(csv_path, url_col_name, driver_path='driver/geckodriver', save=False, output_path='report.csv', verbose=False):
    """
    Scrape report details from given URLs.

    Args:
        csv_path (str): Path to the CSV file containing URLs.
        url_col_name (str): Column name containing the URLs.
        driver_path (str): Path to the GeckoDriver.
        save (bool): Whether to save the scraped data to a CSV file.
        output_path (str): Path to save the output CSV file.
        verbose (bool): Whether to print logs.

    Returns:
        list: A list of dictionaries containing scraped data.
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
            driver = webdriver.Firefox(service=service, 
                            options=options
                            )
            driver.get(url)
            sleep(3)

            try:
                driver.find_element(By.XPATH, "//button[@class='agree-button eu-cookie-compliance-secondary-button']").click()
            except NoSuchElementException:
                if verbose:
                    print("Bouton d'acceptation des cookies non trouvé.")

            title = driver.find_element(By.CLASS_NAME, 'c-node__title').text
            text_content = driver.find_element(By.XPATH, "//article[@class='o-section o-section--small-margin']").text

            scraped_data.append({"url": url, "title": title, "content": text_content,})
            if verbose:
                print(f"Scraped data for {url}")
            driver.quit()
        except Exception as e:
            if verbose:
                print(f"Erreur lors du scraping de {url}: {e}")
                
    
    
    
    if save:
        df_scrape = pd.DataFrame(scraped_data)
        df_data= pd.merge(data, df_scrape, on= 'url', how= 'inner')
        df_data.to_csv(output_path, index=False, encoding='utf-8')
    return scraped_data


if __name__ == '__main__' :
    urls_main = ['https://enb.iisd.org/bonn-climate-change-conference-sbi58-sbsta58',
                'https://enb.iisd.org/united-arab-emirates-climate-change-conference-cop28',
                'https://enb.iisd.org/bonn-climate-change-conference-sbi60-sbsta60',
                "https://enb.iisd.org/baku-un-climate-change-conference-cop29"]
    
    csv_dir= 'csv/'
    driver_path = '/Users/rolly/Documents/10-19_Université_et_scolarité/18.Projets/columbia_scrapping/driver/geckodriver'
    for url in urls_main: 
        output_path = os.path.join(csv_dir, url.split('/')[-1] + '.csv')
        main_page_extract(url,save=True,output_path=output_path,driver_path=driver_path, verbose=True)
        report_page_extract(output_path, url_col_name='url',driver_path=driver_path,save=True, output_path=output_path, verbose= True)

