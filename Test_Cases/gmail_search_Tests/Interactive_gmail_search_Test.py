import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from colorama import Fore, Back
from pyvirtualdisplay import Display

PAGE_NAME = "gmail_search"
TEST_PATH = "/root/"
TARGET_URL = "https://mail.google.com/mail/u/0/#inbox"
RECORDING_PATH = os.path.join(TEST_PATH, "recordings", "gmail_search.wprgo")
ANNOTATION_PATH = os.path.join(TEST_PATH, "annotations", "gmail_search_interactive.js")
RESULTS_DIR = os.path.join(TEST_PATH, "Results", PAGE_NAME)
WPR_PATH = "/root/go/pkg/mod/github.com/catapult-project/catapult/web_page_replay_go@v0.0.0-20230901234838-f16ca3c78e46/"
USER_DATA = "/root/userdata/"
REALWORLD_EXT_DIR = "/root/extensions/realworld/"
CHROMEDRIVER_PATH = "/root/chromedriver/chromedriver"
ARCANUM_BIN = "/root/Arcanum/opt/chromium.org/chromium-unstable/chromium-browser-unstable"
EXPECTED_STRINGS = [
    "This is a test message"
]
DEFAULT_EXTENSION = "oadkgbgppkhoaaoepjbcnjejmkknaobg"
FALLBACK_EXTENSION = "pjmfidajplecneclhdghcgdefnmhhlca"


def ensure_results_dir():
    os.makedirs(RESULTS_DIR, exist_ok=True)


def init_environment():
    os.system("pkill Xvfb")
    os.system("pkill chrome")
    os.system("pkill chromedriver")
    os.system("pkill wpr")
    os.system(f"rm -rf {USER_DATA}")

    display = Display(visible=0, size=(1920, 1080))
    display.start()
    return display


def resolve_extension():
    preferred = os.path.join(REALWORLD_EXT_DIR, DEFAULT_EXTENSION + ".crx")
    fallback = os.path.join(REALWORLD_EXT_DIR, FALLBACK_EXTENSION + ".crx")

    if os.path.exists(preferred):
        print(Fore.CYAN + f"Using DEFAULT extension: {DEFAULT_EXTENSION}" + Fore.RESET)
        print(Fore.CYAN + f"Path: {preferred}" + Fore.RESET)
        return preferred

    if os.path.exists(fallback):
        print(Fore.YELLOW + f"Default extension {DEFAULT_EXTENSION} not found. Checking fallback..." + Fore.RESET)
        print(Fore.CYAN + f"Using FALLBACK extension: {FALLBACK_EXTENSION}" + Fore.RESET)
        print(Fore.CYAN + f"Path: {fallback}" + Fore.RESET)
        return fallback

    print(Fore.RED + f"Error: No suitable extension found in {REALWORLD_EXT_DIR}. Available files:" + Fore.RESET)
    os.system(f"ls {REALWORLD_EXT_DIR}")
    raise FileNotFoundError(
        f"Neither default ({DEFAULT_EXTENSION}) nor fallback ({FALLBACK_EXTENSION}) extensions were found in {REALWORLD_EXT_DIR}"
    )


def start_wpr():
    """Start Web Page Replay in background"""
    if not os.path.exists(WPR_PATH):
        print(Fore.RED + f"Error: WPR path not found: {WPR_PATH}" + Fore.RESET)
        return False
    
    # Verify annotation file exists
    if not os.path.exists(ANNOTATION_PATH):
        print(Fore.RED + f"Error: Annotation file not found: {ANNOTATION_PATH}" + Fore.RESET)
        return False
    
    print(Fore.CYAN + f"Annotation file found: {ANNOTATION_PATH}" + Fore.RESET)

    os.chdir(WPR_PATH)
    # Note: Using deterministic.js + our new annotation file
    cmd = (
        "nohup /usr/local/go/bin/go run src/wpr.go replay "
        "--http_port=8080 --https_port=8081 "
        f"--inject_scripts=deterministic.js,{os.path.abspath(ANNOTATION_PATH)} "
        f"{os.path.abspath(RECORDING_PATH)} > /tmp/wprgo.log 2>&1 &"
    )
    
    print(f"Starting WPR: {cmd}")
    os.system(cmd)
    time.sleep(3)  # Allow startup time
    return True


def launch_arcanum(extension_path):
    """Launch the custom Chromium browser with Selenium"""
    if not os.path.exists(ARCANUM_BIN):
        print(Fore.RED + f"Error: Arcanum binary not found at {ARCANUM_BIN}" + Fore.RESET)
        raise FileNotFoundError(f"Arcanum binary not found at {ARCANUM_BIN}")

    options = webdriver.ChromeOptions()
    options.binary_location = ARCANUM_BIN
    options.add_argument(f"--user-data-dir={USER_DATA}")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--enable-logging")
    options.add_argument("--v=0")
    
    # Load the extension
    options.add_extension(extension_path)

    # Network Rules for WPR
    rules = (
        "MAP mail.google.com:80 127.0.0.1:8080,"
        "MAP mail.google.com:443 127.0.0.1:8081,"
        "MAP *.google.com:80 127.0.0.1:8080,"
        "MAP *.google.com:443 127.0.0.1:8081,"
        "MAP *.gstatic.com:80 127.0.0.1:8080,"
        "MAP *.gstatic.com:443 127.0.0.1:8081,"
        "MAP *.googleusercontent.com:80 127.0.0.1:8080,"
        "MAP *.googleusercontent.com:443 127.0.0.1:8081,"
        "EXCLUDE localhost"
    )
    options.add_argument(f"--host-resolver-rules={rules}")

    return webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=options)


def clear_log_files():
    for path in [os.path.join(USER_DATA, "taint_fetch.log"), "/ram/analysis/v8logs/taint_fetch.log"]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


def read_log_data():
    logs = ""
    for path in [os.path.join(USER_DATA, "taint_fetch.log"), "/ram/analysis/v8logs/taint_fetch.log"]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as logfile:
                    logs += logfile.read()
            except Exception as exc:
                print(Fore.YELLOW + f"Warning: Unable to read {path}: {exc}" + Fore.RESET)
    return logs


def check_element_taint(driver, selector, name):
    """Check if a specific element has been tainted"""
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        taint_value = element.get_attribute("data-taint")
        
        if taint_value == "1":
            print(Fore.GREEN + f"  [TAINTED] {name}" + Fore.RESET)
            return True
        else:
            print(Fore.RED + f"  [NOT TAINTED] {name} (value: {taint_value})" + Fore.RESET)
            return False
    except Exception as e:
        print(Fore.YELLOW + f"  [NOT FOUND] {name}: {e}" + Fore.RESET)
        return False


def verify_tainting(driver):
    """Verify that the search bar has been tainted"""
    print("\n" + "="*60)
    print("TAINT VERIFICATION")
    print("="*60)
    
    # Give JavaScript time to apply taint
    time.sleep(2)
    
    # Check if annotation script was injected
    script_check = driver.execute_script("""
        var scripts = document.getElementsByTagName('script');
        var found = false;
        for (var i = 0; i < scripts.length; i++) {
            if (scripts[i].textContent.includes('waitForElm')) {
                found = true;
                break;
            }
        }
        return found;
    """)
    print(f"Annotation script injected: {script_check}")
    
    # Debug: Check all input elements on page
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"\nFound {len(all_inputs)} input elements on page")
    for idx, inp in enumerate(all_inputs[:5]):  # Show first 5
        try:
            print(f"  Input {idx}: name={inp.get_attribute('name')}, "
                  f"aria-label={inp.get_attribute('aria-label')}, "
                  f"class={inp.get_attribute('class')[:50] if inp.get_attribute('class') else 'None'}")
        except:
            pass
    
    # Try multiple selectors for the search bar
    selectors = [
        ("input[aria-label='Search mail'][name='q']", "Search bar (aria-label + name)"),
        ("input[name='q']", "Search bar (name only)"),
        ("input.gb_ze.aJh.afOp8c", "Search bar (class)"),
        ("input[placeholder='Search mail']", "Search bar (placeholder)")
    ]
    
    print("\nChecking search bar tainting:")
    tainted = False
    for selector, name in selectors:
        if check_element_taint(driver, selector, name):
            tainted = True
            break
    
    print("="*60)
    if tainted:
        print(Fore.GREEN + "SUCCESS: Search bar is tainted!" + Fore.RESET)
    else:
        print(Fore.RED + "FAILURE: Search bar is NOT tainted!" + Fore.RESET)
    print("="*60 + "\n")
    
    return tainted


def perform_interaction(driver):
    print("Navigating to Gmail search...")
    driver.get(TARGET_URL)

    # Wait for search bar to be available
    print("Waiting for search bar...")
    search_bar = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[aria-label='Search mail'][name='q']"))
    )

    print(f"Search bar found")
    print(f"Search bar visible: {search_bar.is_displayed()}")
    print(f"Search bar enabled: {search_bar.is_enabled()}")

    # After the verify_tainting() call, try manually tainting via Selenium
    print("\nManually applying taint via Selenium execute_script...")
    manual_taint_result = driver.execute_script("""
        var searchBar = document.querySelector("input[name='q']");
        if (searchBar) {
            searchBar.setAttribute("data-taint", "1");
            searchBar.style.border = "3px solid red";
            return {
                success: true,
                taint: searchBar.getAttribute("data-taint")
            };
        }
        return {success: false, error: "Element not found"};
    """)
    print(f"Manual taint result: {manual_taint_result}")

    #Now check if it's tainted
    taint_value = search_bar.get_attribute("data-taint")
    print(f"Taint value after manual application: {taint_value}")
    
    # Verify tainting
    verify_tainting(driver)

    # Click and enter search text
    print("Entering search query...")
    search_bar.click()
    time.sleep(1)  # Small delay after clicking
    search_bar.send_keys("This is a test message")
    
    # Take screenshot after entering text
    driver.save_screenshot('/tmp/after_search_entry.png')
    
    # Press Enter to submit search
    print("Submitting search...")
    search_bar.send_keys(Keys.RETURN)
    
    # Wait for search results to load
    time.sleep(5)
    driver.save_screenshot('/tmp/after_search_submit.png')

    print("Waiting 20s for potential exfiltration...")
    time.sleep(20)


def check_logs_for_expected_strings():
    """Check for leakage in logs, handling multiple potential paths"""
    potential_paths = [
        os.path.join(USER_DATA, "taint_fetch.log"),
        "/ram/analysis/v8logs/taint_fetch.log"
    ]
    
    found_path = None
    logs = ""

    for path in potential_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    logs = f.read()
                    found_path = path
                    break
            except Exception as e:
                print(f"Warning: Could not read {path}: {e}")

    if not found_path:
        print(Fore.RED + f"FAIL: Taint fetch log not found in: {potential_paths}" + Fore.RESET)
        return False

    print(f"Analyzing logs from: {found_path}")
    
    if all(value in logs for value in EXPECTED_STRINGS):
        print(Back.GREEN + "SUCCESS: INTERACTIVE LEAK DETECTED" + Back.RESET)
        return True

    print(Fore.RED + "FAIL: No interactive leakage found" + Fore.RESET)
    return False


def run():
    ensure_results_dir()
    display = init_environment()
    ext_path = resolve_extension()
    
    if not start_wpr():
        display.stop()
        return

    driver = None
    try:
        clear_log_files()
        print(f"Launching Arcanum with extension: {ext_path}")
        driver = launch_arcanum(ext_path)
        perform_interaction(driver)
    except Exception as exc:
        print(Fore.RED + f"Test Execution Error: {str(exc)}" + Fore.RESET)
        import traceback
        print(Fore.RED + f"Traceback: {traceback.format_exc()}" + Fore.RESET)
    finally:
        if driver:
            driver.quit()
        display.stop()
        os.system("pkill wpr")
        
    # Verification
    check_logs_for_expected_strings()


if __name__ == "__main__":
    run()