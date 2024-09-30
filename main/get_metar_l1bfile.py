from datetime import datetime, timedelta
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def bmkg_metar_scrapping(year=2022, month=10, day=10, hour=13, min=30, output_location_path='', display_full=False, display_link=True, make_output=False):
    link_temp = ("https://aviation.bmkg.go.id/web/metar_speci.php?icao=W%25&sa=yes&fd={day}%2F{month}%2F{year}&fh={hour}&fm={min}&ud={day}%2F{month}%2F{year}&uh={hour}&um={min}&f=raw_format")
    day_str = str(day).zfill(2)
    month_str = str(month).zfill(2)
    link_target = link_temp.format(day=day_str, month=month_str, year=year, hour=hour, min=min)
    
    if display_full or display_link:
        print(f"Get To {day_str}/{month_str}/{year} {hour}:{min} : {link_target}")
    
    if output_location_path == '':
        output_location_path = f"metar_{day}_{month}_{year}_{hour}_{min}.txt"
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    wd = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        wd.get(link_target)
        if wd.find_element(By.ID, "agreement"):
            wd.find_element(By.ID, "agreement").click()
            wd.find_element(By.ID, "submit").click()
            wd.save_screenshot('ss.png')
            wd.get(link_target)
    except Exception as e:
        print(f"Error: {e}")
        wd.quit()
        return

    try:
        WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'data_text')))
        if display_full:
            print("Page is Ready")
    except TimeoutException:
        if display_full:
            print("Loading took too much time!")
        wd.quit()
        return

    select_elements = wd.find_elements(By.TAG_NAME, 'select')
    option_elements = select_elements[4].find_elements(By.TAG_NAME, 'option')
    
    if display_full:
        print(f"Banyak Select Element: {len(select_elements)}")
        print(f"Banyak Halaman: {len(option_elements)}")
    
    if make_output:
        if os.path.isfile(output_location_path):
            os.remove(output_location_path)
    
    for page_number in range(len(option_elements)):
        link_target_2 = f"{link_target}&pn={page_number}"
        if display_full or display_link:
            print(f"Get To {page_number} : {link_target_2}")
        
        wd.get(link_target_2)
        
        try:
            WebDriverWait(wd, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'data_text')))
            if display_full:
                print("Page is Ready")
        except TimeoutException:
            if display_full:
                print("Loading took too much time!")
            wd.quit()
            return
        
        if display_full:
            print(f"Banyak Select Halaman METAR: {len(option_elements)}")
        
        if make_output:
            with open(output_location_path, "a") as f:
                raw_metar = wd.find_elements(By.CLASS_NAME, 'data_text')
                for i in raw_metar:
                    if display_full:
                        print(i.text)
                    f.write(i.text + "\n")
    
    wd.quit()

output_dataset = '1_ProjectSatteliteData/dataset_out/'

def get_metar_l1bfile(filename, dataoutput='', display_process=True):
    t_path = filename.split('/')
    filename = t_path[-1]
    
    date_str = filename[0:10]
    date_arr = date_str.split('-')
    filename = filename.replace('.', '_')

    year = int(date_arr[2])
    month = int(date_arr[1])
    day = int(date_arr[0])
    time_arr = filename.split(' ')[1]
    hour = int(time_arr[0:2])
    min = 0 if int(time_arr[2:4]) < 15 else 30
    req_date = datetime(year, month, day, hour=hour, minute=min) - timedelta(hours=7)
    
    if display_process:
        print(f"Processing: {filename}")
        print(f"L1B File Datetime: {day}-{month}-{year} {hour}:{min}")
        print(f"Requested Time: {req_date.day}-{req_date.month}-{req_date.year} {req_date.hour}:{req_date.minute}")
    
    bmkg_metar_scrapping(year=year, month=month, day=day, hour=hour, min=min, output_location_path=dataoutput, display_full=False, display_link=True, make_output=True)
