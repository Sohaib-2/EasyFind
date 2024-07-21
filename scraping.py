from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import socketio

def scrape_companies(category, location, search_type, num_companies, output_file):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    driver.get("https://www.google.com/maps")


    if search_type == "country":
        search_box = driver.find_element(By.ID, "searchboxinput")
        search_box.send_keys(location)
        search_button = driver.find_element(By.ID, "searchbox-searchbutton")
        search_button.click()
        search_query = f"{category} in {location}"
    else:
        search_query = f"{category} in {location}"
    time.sleep(3)
    search_box = driver.find_element(By.ID, "searchboxinput")
    search_box.clear()
    search_box.send_keys(search_query)
    search_button = driver.find_element(By.ID, "searchbox-searchbutton")
    search_button.click()

    companies = set()
    last_element = None
    while len(companies) < num_companies:
        company_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'hfpxzc'))
        )
        
        if not company_elements:
            break

        for company in company_elements:
            if len(companies) >= num_companies:
                break
            name = company.get_attribute('aria-label')
            link = company.get_attribute('href')
            if name and link and (name, link) not in companies:
                companies.add((name, link))
                socketio.emit('update', {'count': len(companies)})

        new_last_element = company_elements[-1]
        if new_last_element == last_element:
            break
        last_element = new_last_element
        driver.execute_script("arguments[0].scrollIntoView();", last_element)
        time.sleep(5)

    detailed_companies = []
    for name, gmap_link in list(companies)[:num_companies]:
        driver.get(gmap_link)
        try:
            website_link_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-item-id="authority"]'))
            )
            website_link = website_link_element.get_attribute('href')
        except:
            website_link = None

        try:
            location_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="Io6YTe fontBodyMedium kR99db "]'))
            )
            location = location_element.text
        except:
            location = None

        try:
            phone_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-item-id^="phone:tel:"]'))
            )
            phone = phone_element.get_attribute('aria-label').replace('Phone: ', '')
        except:
            phone = None

        detailed_company = {
            'Name': name,
            'Link': website_link if website_link else gmap_link,
            'Location': location,
            'Phone': phone
        }
        detailed_companies.append(detailed_company)
        socketio.emit('detailed_update', detailed_company)

    df = pd.DataFrame(detailed_companies)
    df.to_csv(output_file, index=False)

    driver.quit()
    socketio.emit('complete', {'message': 'Scraping completed!'})
