from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import config as Info
import time
import os

from EdoParseService.NCALayerParse import Start as NCALayer_work_start


fill = False
def Start(url):
    options = webdriver.FirefoxOptions()
    # options.add_argument("--headless")
    service = webdriver.FirefoxService(executable_path=Info.gecko_driver)
    global driver 
    driver = webdriver.Firefox(options=options, service=service)
    driver.get(url)


def End():
    print('ending')
    driver.quit()


def Login():
    print('login')
    username_input = WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="__layout"]/div/div[4]/div/div[3]/div[1]/div/div/div/input')))
    username_input.send_keys(Info.login)

    password_input = WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="password-input-area"]/div/div/input')))
    password_input.send_keys(Info.password)
    time.sleep(1)
    submit_button = WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div/div[4]/div/div[3]/button')))
    
    driver.execute_script("arguments[0].click();", submit_button)

    time.sleep(10)


def Fill(data):
    submit_button = WebDriverWait(driver, 100).until(
        EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="send-doc-select-button"]')))
    driver.execute_script("arguments[0].click();", submit_button)

    submit_button = WebDriverWait(driver, 100).until(
        EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="nav-collapse"]/div/div[7]/ul/li[1]')))
    driver.execute_script("arguments[0].click();", submit_button)

    ## Input send
    time.sleep(10)

    username_input = WebDriverWait(driver, 100).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '//*[@id="__layout"]/div/div[5]/div[2]/div/div[2]/div/div[2]/div[1]/div/div/input')))
    username_input.send_keys(Info.document_name)

    username_input = WebDriverWait(driver, 100).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '//*[@id="__layout"]/div/div[5]/div[2]/div/div[2]/div/div[2]/div[2]/div/div/input')))
    username_input.send_keys(data.get('iin'))

    username_input = driver.find_element(By.XPATH, '/html/body/div[2]/div/div/div[5]/div[2]/div/div[2]/div/div[2]/div[5]/div/div/div/input')
    username_input.send_keys(data.get('email'))

    ## send file to input
    try:
        button_element = driver.find_element(By.CSS_SELECTOR, '.custom-file-input.is-invalid')
        button_element.send_keys(Info.pdf)
    except:
        button_element = driver.find_element(By.XPATH, '//*[@id="__BVID__82"]')
        button_element.send_keys(Info.pdf)

    ## ncalayerBtn
    try:
        button_element = driver.find_element(By.XPATH, '/html/body/div[7]')
        driver.execute_script("arguments[0].click();", button_element)
    except:
        button_element = driver.find_element(By.XPATH, '/html/body/div[3]')
        driver.execute_script("arguments[0].click();", button_element)

    time.sleep(3)
    btn = WebDriverWait(driver, 100).until(
        EC.element_to_be_clickable((By.XPATH,
                                    '/html/body/div[2]/div/div/div[5]/div[2]/div/div[2]/div[2]/div/button')))
    
    actions = ActionChains(driver)
    while True:
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        actions.move_to_element(btn).click().perform()

        time.sleep(5)
        current_url = driver.current_url
        NCALayer_work_start()
        try:
            WebDriverWait(driver, 100).until(EC.url_changes(current_url))
            break
        except:
            continue


def Test():
    global fill
    if fill:
        driver.get('https://edo.uchet.kz/cabinet/category_list?id=5&page=1')
    time.sleep(10)
    fill=True

    rows = driver.find_elements(By.CSS_SELECTOR, 'table > tbody > tr')
    driver.execute_script('arguments[0].click();', rows[0])

    time.sleep(5)
    try:                               
        button_element = driver.find_element(By.XPATH, '/html/body/div[2]/div/div/div[4]/div[2]/div[2]/div/div[3]/div/div/label')
    except: 
        button_element = driver.find_element(By.XPATH, '/html/body/div[2]/div/div/div[5]/div[2]/div[2]/div/div[3]/div/div/label')
    driver.execute_script("arguments[0].click();", button_element)
      
    try:                                                                                        
        button_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div/div[4]/div[2]/div[2]/div/div[3]/div/div/div[2]')))
    except:
        button_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div/div[5]/div[2]/div[2]/div/div[3]/div/div/div[2]')))
    driver.execute_script("arguments[0].click();", button_element)
                                                                                     
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="doc_temp_link_value"]')))
    return element.text


def ReadData(username):
    data={}
    with open(f'{Info.PATHS["data"]}{username}.data', 'r') as f:
        file = f.read()
        for i in file.split('||'):
            data[i.split('=')[0]] = str(i.split('=')[1])
    return data
    
def Main(username):
    data = ReadData(username)
    os.remove(f'{Info.PATHS["data"]}{username}.data')
    while True:
        try:
            Start("https://edo.uchet.kz/login")

            Login()
            if not fill:
                Fill(data)
            return Test()
        except:
            pass
        finally:
            End()
            

def Check(iin):
    driver.get('https://edo.uchet.kz/cabinet/category_list?id=5&page=1')
    time.sleep(5)
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="__BVID__82"]')))
        rows = driver.find_elements(By.CSS_SELECTOR, '#__BVID__82 > tbody > tr')
    except:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="__BVID__72"]')))
        rows = driver.find_elements(By.CSS_SELECTOR, '#__BVID__72 > tbody > tr')

    for i in rows:
        if i.find_element(By.XPATH, './td[2]/div/div[2]').text == iin:
            return i.find_element(By.XPATH, './td[3]/div/div/div/div').text
            
                


def CheckStatus(data):
    iin=data['ИИН']
    while True:
        try:
            Start("https://edo.uchet.kz/login")
            Login()
            return Check(iin)
        except:
            pass
        finally:
            End()
