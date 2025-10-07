import os
import time
import datetime
import tempfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configuration ---
EMAIL = os.environ.get("CHRONO_EMAIL")
PWD = os.environ.get("CHRONO_PWD")

if not EMAIL or not PWD:
    raise ValueError("Missing environment variables: CHRONO_EMAIL or CHRONO_PWD")

today = datetime.date.today()
saturday = today + datetime.timedelta((5 - today.weekday()) % 7)
date_str = saturday.strftime("%Y-%m-%d")

club_url = (
    f"https://www.chronogolf.com/club/miami-beach-golf-club"
    f"?date={date_str}&step=teetimes&holes=&coursesIds=&deals=false&groupSize=0"
)

# --- Chrome setup ---
tmpdir = tempfile.mkdtemp()
options = Options()
options.add_argument(f"--user-data-dir={tmpdir}")
options.add_argument(f"--data-path={os.path.join(tmpdir, 'data-path')}")
options.add_argument(f"--disk-cache-dir={os.path.join(tmpdir, 'cache-dir')}")
options.add_argument("--headless=chrome")  # change to False for local debugging
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-features=VizDisplayCompositor")

driver = None
try:
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 40)  # increased wait time for React

    # --- LOGIN ---
    driver.get("https://www.chronogolf.com/login")
    wait.until(EC.presence_of_element_located((By.ID, "sessionEmail"))).send_keys(EMAIL)
    driver.find_element(By.ID, "sessionPassword").send_keys(PWD)
    driver.find_element(By.XPATH, "//input[@type='submit' and @value='Log in']").click()
    wait.until(EC.url_contains("chronogolf.com"))
    print("✅ Logged in successfully.")

    # --- LOAD TEE TIMES PAGE ---
    driver.get(f"https://www.chronogolf.com/club/miami-beach-golf-club?date={date_str}")
    driver.get(club_url)
    time.sleep(5)  # initial wait for React

    # Scroll to bottom to trigger lazy rendering
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

    # --- WAIT FOR TEE TIME ELEMENTS ---
    tee_time_cards = []
    for _ in range(5):  # retry 5 times
        try:
            tee_time_cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid="tee-time-card"]')
            tee_time_cards = [c for c in tee_time_cards if c.is_displayed()]
            if tee_time_cards:
                break
        except:
            pass
        time.sleep(2)

    if not tee_time_cards:
        print("❌ No tee times detected.")
        driver.save_screenshot("no_tee_times.png")
        with open("no_tee_times.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        exit(0)

    print(f"🎯 Found {len(tee_time_cards)} tee time cards.")

    # --- SELECT FIRST AVAILABLE TEE TIME ---
    first_card = tee_time_cards[0]
    first_card.click()
    print(f"✅ Selected first tee time.")

    # --- SELECT 18 HOLES ---
    try:
        hole_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='button'][role='radio'][value='18']"))
        )
        hole_button.click()
        print("✅ Selected 18 holes.")
    except Exception:
        print("⚠️ Could not select 18 holes.")

    # --- ADD PLAYERS ---
    try:
        add_buttons = driver.find_elements(By.CSS_SELECTOR, "button.e5zz781.e5zz780.e5zz782")
        if add_buttons:
            for i in range(3):  # add 3 players
                if add_buttons[0].is_enabled():
                    add_buttons[0].click()
                    time.sleep(0.3)
                    print(f"👥 Added player #{i + 2}")
    except Exception as e:
        print(f"⚠️ Player selection error: {e}")

    # --- RESERVE ---
    try:
        reserve_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[span[contains(text(),'Reserve')] or contains(text(),'Reserve')]")
            )
        )
        reserve_button.click()
        print("✅ Clicked Reserve button.")
    except Exception as e:
        print(f"⚠️ Reserve button not found: {e}")

    # --- ACCEPT TERMS ---
    try:
        terms_checkbox = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[type='checkbox'][ng-model='vm.acceptTermsAndConditions']")
            )
        )
        if not terms_checkbox.is_selected():
            terms_checkbox.click()
        print("✅ Accepted terms and conditions.")
    except Exception:
        print("⚠️ Terms checkbox not found.")

    # --- CONFIRM RESERVATION ---
    try:
        confirm_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Confirm Reservation')]"))
        )
        confirm_button.click()
        print("🎉 Confirmed reservation!")
    except Exception as e:
        print(f"⚠️ Confirm button not found or disabled: {e}")

    # --- SAVE DEBUG ---
    driver.save_screenshot("page_after_booking.png")
    with open("page_after_booking.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    print("✅ Script completed successfully.")

except Exception as main_error:
    print("❌ Fatal error:", main_error)
    if driver:
        driver.save_screenshot("error_screenshot.png")
finally:
    if driver:
        driver.quit()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("🧹 Cleaned up temp files and closed Chrome.")
