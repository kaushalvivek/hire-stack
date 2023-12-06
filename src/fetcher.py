'''
Approach:
- read details from a row-wise export of candidates to construct URL
- for each candidate:
-   open application page
-   open resume
-   download resume
'''
import os
import time
import redis
import getpass
import pandas as pd
from tqdm import tqdm
from src.config import FetcherConfig
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_URL="https://app3.greenhouse.io"

class ResumeFetcher:
    def __init__(self, use_cache, browser="chrome", is_headless=True):
        self.config = FetcherConfig()
        if use_cache:
            self.cache = redis.Redis(host='localhost', port=6379, db=0)
        else:
            self.cache = None
        self.password = getpass.getpass('Enter your greenhouse password: ')
        self.browser = browser
        if self.browser == "chrome":
            chrome_options = Options()
            if is_headless:
                chrome_options.add_argument("--headless")
                self.is_headless = True
                prefs = {
                "download.default_directory": self.config.resume_folder,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
                }
                chrome_options.add_experimental_option("prefs", prefs)
            self.driver = webdriver.Chrome(options=chrome_options)
        else:
            self.driver = webdriver.Safari()
        

    def _sign_in(self, driver):
        print("Initiating sign in...")
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

        password_field.send_keys(self.password)

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
        print("Successfully signed in!")
        return

    def _get_candidates(self):
        # Extract the file extension
        _, file_extension = os.path.splitext(self.config.candidate_file)

        # Check the file extension and read the file accordingly
        if file_extension in ['.csv']:
            df = pd.read_csv(self.config.candidate_file)
        elif file_extension in ['.xls', '.xlsx']:
            df = pd.read_excel(self.config.candidate_file)
        else:
            raise ValueError("Unsupported file format")

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
        if self.browser == "safari" or (self.browser == "chrome" and self.is_headless):
            self.driver.close()

        # Switch back to the original window
        self.driver.switch_to.window(original_window)
        return


    def fetch(self):
        self._sign_in(self.driver)
        candidates = self._get_candidates()
        for candidate in tqdm(candidates):
            try:
                if self.cache is not None:
                    if self.cache.get(candidate['Candidate ID']) is not None:
                        continue
                    self._fetch_resume(candidate)
                    self.cache.set(candidate['Candidate ID'], "true")
                else:
                    self._fetch_resume(candidate)
            except:
                continue
        self.driver.close()