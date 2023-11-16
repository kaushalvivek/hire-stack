'''
Approach:
- read details from a row-wise export of candidates to construct URL
- for each candidate:
-   open application page
-   open resume
-   download resume
'''
import time
import redis
import getpass
import pandas as pd
from src.config import FetcherConfig
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL="https://app3.greenhouse.io"

class ResumeFetcher:
    def __init__(self):
        self.config = FetcherConfig()
        self.cache = redis.Redis(host='localhost', port=6379, db=0)
        self.driver = webdriver.Safari()

    def _sign_in(self, driver):
        driver.get(f'{BASE_URL}/dashboard')
        time.sleep(3)
        email_field = driver.find_element(By.ID, 'user_email')
        email_field.send_keys(self.config.email)
        next_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "submit_email_button"))
        )
        next_button.click()

        time.sleep(3)
        # Find the password input field and send the password
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "user_password"))
        )

        # Scroll the password field into view
        driver.execute_script("arguments[0].scrollIntoView(true);", password_field)

        # Wait for the password field to be interactable
        password_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "user_password"))
        )

        password_field.send_keys(getpass.getpass('Enter your greenhouse password: '))

        # Find and click the "Keep me signed in" checkbox
        keep_me_signed_in_checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "user_remember_me"))
        )
        keep_me_signed_in_checkbox.click()

        # Find and click the "Sign in" button
        sign_in_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "submit_password_button"))
        )
        sign_in_button.click()
        time.sleep(3)
        return

    def _get_candidates(self):
        df = pd.read_csv(self.config.candidates_file)
        return df.to_dict(orient='records')

    def _fetch_resume(self, candidate):
        original_window = self.driver.current_window_handle
        assert len(self.driver.window_handles) == 1
        self.driver.get(f'{BASE_URL}/people/{candidate["Candidate ID"]}?application_id={candidate["Application ID"]}')
        time.sleep(1)
        resume_preview_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "preview_resume_button"))
        )
        resume_preview_button.click()
        download_button = self.driver.find_element(By.CLASS_NAME, "download")
        download_button.click()
        # Wait for the new tab to appear
        WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) == 2)

        # Switch to the new tab
        new_window = [window for window in self.driver.window_handles if window != original_window][0]
        self.driver.switch_to.window(new_window)

        # Close the new tab
        time.sleep(2)
        self.driver.close()

        # Switch back to the original window
        self.driver.switch_to.window(original_window)
        return


    def fetch(self):
        self._sign_in(self.driver)
        candidates = self._get_candidates()
        for candidate in candidates:
            if self.cache.get(candidate['Candidate ID']) is not None:
                continue
            self._fetch_resume(candidate)
            self.cache.set(candidate['Candidate ID'], "true")
        self.driver.close()