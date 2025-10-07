import os
import time
import datetime
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

EMAIL = os.environ.get("CHRONO_EMAIL")
PWD = os.environ.get("CHRONO_PWD")

today = datetime.date.today()
saturday = today + datetime.timedelta((5 - today.weekday()) % 7)
date_str = saturday.strftime("%Y-%m-%d")
club_url = f"https://www.chronogolf.com/club/miami-beach-golf-club?date={date_str}"

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# Always use a unique profile directory for every run (avoids all session/create errors)
options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

# --- Login ---
driver.get("https://www.chronogolf.com/login")
time.sleep(2)
driver.find_element(By.ID, "sessionEmail").send_keys(EMAIL)
driver.find_element(By.ID, "sessionPassword").send_keys(PWD)
driver.find_element(By.XPATH, "//input[@type='submit' and @value='Log in']").click()
time.sleep(3)

# --- Load Tee Times ---
driver.get(club_url)
wait.until(lambda d: "AM" in d.page_source or "PM" in d.page_source)

# Save HTML for debugging
with open("tee_times_page_source.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
print("Saved tee times page source for debugging.")

# Print all button texts for debugging
tee_time_buttons = driver.find_elements(By.TAG_NAME, "button")
print("All button texts found:")
for b in tee_time_buttons:
    print(repr(b.text))

# Select available tee time card (first AM/PM button)
available_cards = []
for btn in tee_time_buttons:
    if btn.is_displayed() and btn.is_enabled() and ("AM" in btn.text or "PM" in btn.text) and len(btn.text.strip()) > 2:
        available_cards.append(btn)
if not available_cards:
    print("No available tee times found.")
    driver.quit()
    exit()

first_card = available_cards[0]
print(f"First available tee time: {first_card.text}")
first_card.click()
time.sleep(2)

# --- Select 18 holes ---
hole_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='button'][role='radio']")
for button in hole_buttons:
    if button.get_attribute("value") == "18":
        button.click()
        print("Selected 18 holes.")
        break
time.sleep(1)

# --- Select 4 players (if possible) ---
player_buttons = driver.find_elements(By.CSS_SELECTOR, "button.e5zz781.e5zz780.e5zz782")
if player_buttons:
    add_button = player_buttons[0]
    for i in range(3):  # Already 1 selected, click 3 more times for 4 total
        if add_button.is_enabled():
            add_button.click()
            time.sleep(0.5)
            print(f"Clicked to select player #{i+2}")
        else:
            print(f"Button disabled after {i+2} players (max available players selected).")
            break
else:
    print("Could not find player add button.")
time.sleep(1)

# --- Reserve button ---
try:
    reserve_button = driver.find_element(By.XPATH, "//button[span[contains(text(),'Reserve')] or contains(text(),'Reserve')]")
    if reserve_button.is_enabled():
        reserve_button.click()
        print("Clicked Reserve button!")
    else:
        print("Reserve button is disabled.")
except Exception:
    try:
        reserve_span = driver.find_element(By.XPATH, "//span[contains(text(), 'Reserve')]")
        reserve_span.click()
        print("Clicked Reserve span!")
    except Exception as e:
        print("Reserve button not found:", e)
time.sleep(2)

# --- Accept terms ---
try:
    terms_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][ng-model='vm.acceptTermsAndConditions']")
    if not terms_checkbox.is_selected():
        terms_checkbox.click()
        print("Accepted terms and conditions!")
    else:
        print("Checkbox already checked.")
except Exception as e:
    print("Could not find or click the terms and conditions checkbox:", e)
time.sleep(1)

# --- Confirm reservation ---
try:
    confirm_button = driver.find_element(By.XPATH, "//button[contains(text(),'Confirm Reservation')]")
    if confirm_button.is_enabled():
        confirm_button.click()
        print("Clicked Confirm Reservation!")
    else:
        print("Button is disabled and cannot be clicked.")
except Exception as e:
    print("Could not find or click Confirm Reservation button:", e)
time.sleep(3)

driver.quit()
