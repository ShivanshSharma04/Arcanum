# -*- coding: utf-8 -*-
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from colorama import Fore, Back, Style
from pyvirtualdisplay import Display

# --- Configuration ---
TEST_PATH = "/root/beeslab-arcanum/"
RECORDING_PATH = TEST_PATH + 'recordings/linkedin2_interactive.wprgo'
ANNOTATION_PATH = TEST_PATH + 'annotations/linkedin2_interactive.js'
WPR_PATH = '/root/go/pkg/mod/github.com/catapult-project/catapult/web_page_replay_go@v0.0.0-20230901234838-f16ca3c78e46/'
USER_DATA = '/root/userdata/'
RESULTS_DIR = TEST_PATH + 'Results/LinkedIn/'

# Environment specific paths
CHROMEDRIVER_PATH = "/root/chromedriver/chromedriver"
ARCANUM_BIN = "/root/Arcanum/opt/chromium.org/chromium-unstable/chromium-browser-unstable"

def init_environment():
    os.system('pkill Xvfb')
    os.system('pkill chrome')
    os.system('pkill chromedriver')
    os.system('pkill wpr')
    os.system(f'rm -rf {USER_DATA}')
    
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    return display

def start_wpr():
    if not os.path.exists(WPR_PATH):
        print(Fore.RED + f"Error: WPR path not found: {WPR_PATH}" + Fore.RESET)
        return False

    os.chdir(WPR_PATH)
    cmd = (f'nohup /usr/local/go/bin/go run src/wpr.go replay '
           f'--http_port=8080 --https_port=8081 '
           f'--inject_scripts=deterministic.js,{ANNOTATION_PATH} '
           f'{RECORDING_PATH} > /tmp/wprgo.log 2>&1 &')
    
    print(f"Starting WPR: {cmd}")
    os.system(cmd)
    time.sleep(3)
    return True

def launch_arcanum(extension_path=''):
    if not os.path.exists(ARCANUM_BIN):
        print(Fore.RED + f"Error: Arcanum binary not found at {ARCANUM_BIN}" + Fore.RESET)
        exit(1)

    options = webdriver.ChromeOptions()
    options.binary_location = ARCANUM_BIN
    
    options.add_argument(f'--user-data-dir={USER_DATA}')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("--enable-logging")
    options.add_argument("--v=0")
    options.page_load_strategy = 'eager'
    
    if extension_path and os.path.exists(extension_path):
        options.add_extension(extension_path)
    
    rules = ("MAP *.linkedin.com:80 127.0.0.1:8080,"
             "MAP *.linkedin.com:443 127.0.0.1:8081,"
             "MAP *.licdn.com:80 127.0.0.1:8080,"
             "MAP *.licdn.com:443 127.0.0.1:8081,"
             "EXCLUDE localhost")
    options.add_argument(f'--host-resolver-rules={rules}')
    
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=options)
    driver.set_page_load_timeout(15)
    return driver

def check_logs():
    potential_paths = [
        os.path.join(USER_DATA, 'taint_fetch.log'),
        '/ram/analysis/v8logs/taint_fetch.log'
    ]
    
    logs = ""
    found = False
    for path in potential_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    logs += f.read()
                    found = True
            except Exception as e:
                print(f"Warning: Could not read {path}: {e}")

    if not found:
        print(Fore.RED + f"FAIL: Taint fetch log not found in: {potential_paths}" + Fore.RESET)
        return

    if "JohnDoe@gmail.com" in logs or "Netsec123" in logs:
        print(Back.GREEN + "SUCCESS: INTERACTIVE LEAK DETECTED" + Back.RESET)
    else:
        print(Fore.RED + "FAIL: No interactive leakage found" + Fore.RESET)

def run_test():
    display = init_environment()
    
    # Use default extension for single test
    ext_path = '/root/extensions/realworld/oadkgbgppkhoaaoepjbcnjejmkknaobg.crx'
    if not os.path.exists(ext_path):
        print(Fore.YELLOW + "Default extension not found, trying fallback..." + Fore.RESET)
        ext_path = '/root/extensions/realworld/aamfmnhcipnbjjnbfmaoooiohikifefk.crx'

    if not start_wpr():
        display.stop()
        return

    driver = None
    try:
        print(f"Launching Arcanum with: {ext_path}")
        driver = launch_arcanum(ext_path)
        
        target_url = "https://www.linkedin.com/checkpoint/rm/sign-in-another-account?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin"
        print(f"Navigating to {target_url}...")
        
        try:
            driver.get(target_url)
        except TimeoutException:
            print("Page load timed out (Expected). Stopping load and proceeding...")
            driver.execute_script("window.stop();")
        
        print("Interacting...")
        
        username_field = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#username"))
        )
        username_field.send_keys("JohnDoe@gmail.com")
        
        password_field = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#password"))
        )
        password_field.send_keys("Netsec123")
        
        toggle_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#password-visibility-toggle"))
        )
        toggle_btn.click()
        
        print("Clicking Sign In...")
        sign_in_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Sign in']"))
        )
        sign_in_btn.click()
        
        print("Waiting 20s for exfiltration...")
        time.sleep(20)
        
    except Exception as e:
        print(Fore.RED + f"Test Error: {e}" + Fore.RESET)
    finally:
        if driver:
            driver.quit()
        display.stop()
        os.system('pkill wpr')
        
    check_logs()

if __name__ == "__main__":
    run_test()

