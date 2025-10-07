import os
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------- Setup ----------
EMAIL = os.environ.get("CHRONO_EMAIL")
PWD = os.environ.get("CHRONO_PWD")

today = datetime.date.today()
saturday = today + datetime.timedelta((5 - today.weekday()) % 7)
date_str = saturday.strftime("%Y-%m-%d")
club_url = f"https://www.chronogolf.com/club/miami-beach-golf-club?date={date_str}"

options = Options()
# options.add_argument("--headless")  # REMOVE for debugging/viewing browser
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

# ---------- Login ----------
driver.get("https://www.chronogolf.com/login")
time.sleep(2)
driver.find_element(By.ID, "sessionEmail").send_keys(EMAIL)
driver.find_element(By.ID, "sessionPassword").send_keys(PWD)
driver.find_element(By.XPATH, "//input[@type='submit' and @value='Log in']").click()
time.sleep(3)  # Wait for login to complete

# ---------- Search for Tee Time ----------
driver.get(club_url)

# Wait for tee times to load (wait until "AM"/"PM" appears in page)
wait.until(lambda d: "AM" in d.page_source or "PM" in d.page_source)

# Save the HTML to inspect it
with open("tee_times_page_source.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
print("Saved page source after loading tee times. Please inspect this file manually to compare with what you see in your browser.")

# Find all buttons on the page and print their text
tee_time_buttons = driver.find_elements(By.TAG_NAME, "button")
print("All button texts on tee times page:")
for btn in tee_time_buttons:
    print(repr(btn.text))

# Filter for tee time buttons specifically
available_cards = []
for btn in tee_time_buttons:
    if (
        btn.is_displayed()
        and btn.is_enabled()
        and ("PM" in btn.text or "AM" in btn.text)
        and len(btn.text.strip()) > 2
    ):
        available_cards.append(btn)

if not available_cards:
    print("No available tee times found (per script). Use button print, page source, or browser view to debug why!")
    driver.quit()
    exit()

first_card = available_cards[0]
print(f"First available tee time button says: {first_card.text}")
first_card.click()
print("Clicked first available tee time card.")
time.sleep(2)

# The rest of your booking flow goes here...
# ---------- Select 18 Holes ----------
hole_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='button'][role='radio']")
for button in hole_buttons:
    if button.get_attribute("value") == "18":
        button.click()
        print("Selected 18 holes.")
        break
time.sleep(1)

# ---------- Select 4 Players (if possible) ----------
player_buttons = driver.find_elements(By.CSS_SELECTOR, "button.e5zz781.e5zz780.e5zz782")
if player_buttons:
    add_button = player_buttons[0]
    for i in range(3):  # Already 1 selected, click 3 more times for 4 total
        if add_button.is_enabled():
            add_button.click()
            time.sleep(0.5)
            print(f"Clicked
