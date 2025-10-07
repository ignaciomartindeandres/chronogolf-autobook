import os
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Read credentials from GitHub Actions secrets
EMAIL = os.environ.get("CHRONO_EMAIL")
PWD = os.environ.get("CHRONO_PWD")

# Calculate next Saturday
today = datetime.date.today()
saturday = today + datetime.timedelta((5 - today.weekday()) % 7)
date_str = saturday.strftime("%Y-%m-%d")
club_url = f"https://www.chronogolf.com/club/miami-beach-golf-club?date={date_str}"

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Start the browser
driver = webdriver.Chrome(options=options)

# Step 1: Go to ChronoGolf login
driver.get("https://www.chronogolf.com/login")

# Step 2: Enter login details
time.sleep(2)
driver.find_element(By.ID, "sessionEmail").send_keys(EMAIL)
driver.find_element(By.ID, "sessionPassword").send_keys(PWD)
driver.find_element(By.XPATH, "//input[@type='submit' and @value='Log in']").click()

time.sleep(3)  # Wait for login

# Step 3: Go to Miami Beach Golf Club for next Saturday
driver.get(club_url)
time.sleep(4)

# Step 4: Find the earliest available tee time button
buttons = driver.find_elements(By.CSS_SELECTOR, ".booking-times .btn")
booked = False
for button in buttons:
    if "Book" in button.text:
        button.click()
        booked = True
        break

# Step 5: Confirm booking steps, if button click is successful
if booked:
    time.sleep(3)
    # Page may ask to confirm # of players, or confirm booking
    # You may need to update the selectors below depending on any changes
    try:
        confirm = driver.find_element(By.CSS_SELECTOR, "button[data-qa='confirm-booking']")
        confirm.click()
        print("Booking confirmed!")
    except Exception as e:
        print("Booking possible, but could not auto-confirm:", e)
else:
    print("No available tee times found.")

driver.quit()
