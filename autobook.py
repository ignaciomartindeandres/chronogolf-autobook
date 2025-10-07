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
club_url = f"https://www.chronogolf.com/club/miami-beach-golf-club?date={date_str}"

# --- Chrome setup ---
tmpdir = tempfile.mkdtemp()
options = Options()
options.add_argument(f"--user-data-dir={tmpdir}")
options.add_argument(f"--data-path={os.path.join(tmpdir, 'data-path')}")
options.add_argument(f"--disk-cache-dir={os.path.join(tmpdir, 'cache-dir')}")
options.add_argument("--headless=new")  # comment out for local visual debugging
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-features=VizDisplayCompositor")

driver = None
try:
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    # --- LOGIN ---
    driver.get("https://www.chronogolf.com/login")
    wait.until(EC.presence_of_element_located((By.ID, "sessionEmail"))).send_keys(EMAIL)
    driver.find_element(By.ID, "sessionPassword").send_keys(PWD)
    driver.find_element(By.XPATH, "//input[@type='submit' and @value='Log in']").click()
    wait.until(EC.url_contains("chronogolf.com"))
    print("✅ Logged in successfully.")

    # --- LOAD TEE TIMES ---
    driver.get(club_url)
    print(f"⏳ Loading tee times for {date_str} ...")

    try:
        wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//button[contains(., 'AM') or contains(., 'PM')]")
            )
        )
        time.sleep(2)  # grace delay for full render
        print("✅ Tee time buttons detected.")
    except Exception:
        print("⚠️ Tee time buttons not detected — page may still be loading.")

    # Save HTML + screenshot for debugging
    driver.save_screenshot("page_after_load.png")
    with open("tee_times_page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("🧩 Saved HTML + screenshot for debugging.")

    # --- Parse buttons ---
    tee_time_buttons = driver.find_elements(By.TAG_NAME, "button")
    print("🔍 All button texts found:")
    for b in tee_time_buttons:
        if b.text.strip():
            print(repr(b.text))

    available_cards = [
        btn for btn in tee_time_buttons
        if btn.is_displayed() and btn.is_enabled()
        and ("AM" in btn.text or "PM" in btn.text)
        and len(btn.text.strip()) > 2
    ]

    if not available_cards:
        print("❌ No available tee times found.")
        exit(0)

    first_card = available_cards[0]
    print(f"🎯 First available tee time: {first_card.text}")
    first_card.click()

    # --- SELECT 18 HOLES ---
    try:
        hole_button = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[type='button'][role='radio'][value='18']")
            )
        )
        hole_button.click()
        print("✅ Selected 18 holes.")
    except Exception:
        print("⚠️ Could not select 18 holes.")

    # --- ADD PLAYERS ---
    try:
        player_buttons = driver.find_elements(By.CSS_SELECTOR, "button.e5zz781.e5zz780.e5zz782")
        if player_buttons:
            add_button = player_buttons[0]
            for i in range(3):  # Add up to 4 players total
                if add_button.is_enabled():
                    add_button.click()
                    time.sleep(0.3)
                    print(f"👥 Added player #{i + 2}")
        else:
            print("⚠️ No player add button found.")
    except Exception as e:
        print(f"⚠️ Player selection error: {e}")

    # --- RESERVE BUTTON ---
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
        print("⚠️ Could not find or click terms checkbox.")

    # --- CONFIRM RESERVATION ---
    try:
        confirm_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Confirm Reservation')]"))
        )
        confirm_button.click()
        print("🎉 Confirmed reservation!")
    except Exception as e:
        print(f"⚠️ Confirm button not found or disabled: {e}")

    print("✅ Script completed successfully.")
    exit(0)

except Exception as main_error:
    print("❌ Fatal error:", main_error)
    driver.save_screenshot("error_screenshot.png")
    exit(1)

finally:
    if driver:
        driver.quit()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("🧹 Cleaned up temp files and closed Chrome.")
