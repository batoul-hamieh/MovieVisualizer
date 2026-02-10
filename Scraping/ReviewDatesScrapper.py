import pandas as pd
import time
import random
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ------------------- CONFIG -------------------

DATES_PER_MOVIE = 100
MOVIE_CSV = "MovieReviewsBatoul.csv" # You change the name ACCORDING TO YOUR FILE!!!
OUTPUT_CSV = "AllDatesBatoul.csv"
WAIT_BETWEEN_DATES = (3, 7)     # seconds
WAIT_BETWEEN_MOVIES = (15, 30)    # seconds
MAX_RETRIES = 3                   # Max retries for pagination
PAGE_LOAD_WAIT = 5                # Seconds to wait for page load

# ----------------------------------------------

def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    return driver

def get_date_elements(driver):
    return driver.find_elements(By.CSS_SELECTOR, 'span.date')

def extract_date_texts(date_elements, already_collected, movie_name):
    dates = []
    count = len(already_collected)
    
    for date in date_elements:
        try:
            text_elem = date.find_element(By.CSS_SELECTOR, 'span._nobr')
            text = text_elem.text.strip()
            if text and text not in already_collected:
                count += 1
                print(f"{movie_name} ✅ Date {count}")
                date.append(text)
        except NoSuchElementException:
            continue
    return date

def click_next_page(driver, movie_name):
    """Click next page button if available and return True if successful"""
    try:
        next_button = WebDriverWait(driver, PAGE_LOAD_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.next'))
        )
        driver.execute_script("arguments[0].scrollIntoView();", next_button)
        time.sleep(random.uniform(1, 2))
        next_button.click()
        
        # Wait for new page to load
        WebDriverWait(driver, PAGE_LOAD_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'span.date')))
        time.sleep(random.uniform(*WAIT_BETWEEN_DATES))
        return True
    except Exception as e:
        print(f"❌ Could not find/click next page for {movie_name}: {str(e)}")
        return False
    

def collect_all_dates(driver, dates_needed, movie_name):
    collected_dates = set()
    current_page = 1
    retries = 0

    while len(collected_dates) < dates_needed and retries < MAX_RETRIES:
        print(f"📄 Processing page {current_page} for {movie_name}")
        
        # Scroll to trigger potential lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 2))
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(1, 2))

        # Get all date elements on current page
        elements = get_date_elements(driver)
        new_texts = extract_date_texts(elements, collected_dates, movie_name)
        
        if new_texts:
            collected_dates.update(new_texts)
            print(f"📊 Collected {len(collected_dates)}/{dates_needed} dates so far")
            retries = 0  # Reset retries if we found new dates
        else:
            retries += 1
            print(f"⚠ No new dates found on page {current_page}, retry {retries}/{MAX_RETRIES}")

        # If we still need more dates, try to go to next page
        if len(collected_dates) < dates_needed:
            if not click_next_page(driver, movie_name):
                break  # No more pages or error clicking next
            current_page += 1
        else:
            break  # We have enough dates

    return list(collected_dates)[:dates_needed]

def sanitize_movie_title(title):
    """Clean movie title for URL"""
    # Remove special characters and multiple spaces
    title = re.sub(r'[^\w\s-]', '', title.strip())
    # Replace spaces with single hyphens
    title = re.sub(r'[\s-]+', '-', title)
    return title.lower()

def build_date_url(movie_title):
    slug = sanitize_movie_title(movie_title)
    return f"https://letterboxd.com/film/{slug}/reviews/by/activity/"

def save_dates_to_master_csv(movie, dates, output_file=OUTPUT_CSV):
    try:
        # Create DataFrame with the new dates
        new_df = pd.DataFrame({movie: pd.Series(dates)})
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            try:
                # Try to read existing file
                existing_df = pd.read_csv(output_file)
                
                # If movie already exists, skip
                if movie in existing_df.columns:
                    print(f"⚠ Movie '{movie}' already exists in output file. Skipping.")
                    return
                
                # Merge with existing data
                merged_df = pd.concat([existing_df, new_df], axis=1)
                merged_df.to_csv(output_file, index=False)
            except pd.errors.EmptyDataError:
                # If file is corrupt/empty, overwrite it
                new_df.to_csv(output_file, index=False)
        else:
            # Create new file
            new_df.to_csv(output_file, index=False)
            
        print(f"✅ Saved {len(dates)} dates for '{movie}'")
    except Exception as e:
        print(f"❌ Error saving dates for '{movie}': {e}")


def load_movie_list(csv_file):
    df = pd.read_csv(csv_file)
    return df.iloc[:, 0].dropna().tolist()  # Reads values from the first column

def already_scraped(movie, output_file=OUTPUT_CSV):
    if not os.path.exists(output_file):
        return False
    try:
        # Check if file is empty
        if os.path.getsize(output_file) == 0:
            return False
            
        df = pd.read_csv(output_file, nrows=1)
        return movie in df.columns
    except pd.errors.EmptyDataError:
        return False
    except Exception as e:
        print(f"⚠ Error checking if movie exists: {e}")
        return False


def scrape_dates_for_movie(driver, movie):
    url = build_date_url(movie)
    print(f"🎬 Scraping: {movie} → {url}")
    
    try:
        driver.get(url)
        WebDriverWait(driver, PAGE_LOAD_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span.date'))
        )
    except Exception as e:
        print(f"⚠ Initial page load failed for {movie}: {str(e)}")
        return []
    
    time.sleep(random.uniform(2, 4))  # Additional load time
    
    dates = collect_all_dates(driver, DATES_PER_MOVIE, movie)
    print(f"📝 Total collected {len(dates)} dates for '{movie}'")
    return dates

def main():
    driver = init_driver()
    movie_list = load_movie_list(MOVIE_CSV)

    your_movies = movie_list[:16]  # You're scraping 16 movies

    for idx, movie in enumerate(your_movies):
        if already_scraped(movie):
            print(f"⏩ Already scraped: {movie}")
            continue

        try:
            dates = scrape_dates_for_movie(driver, movie)
            if dates:
                save_dates_to_master_csv(movie, dates)
            else:
                print(f"⚠ No dates found for {movie}")
        except Exception as e:
            print(f"❌ Error scraping {movie}: {e}")
            # Save partial results if any
            if 'dates' in locals() and dates:
                save_dates_to_master_csv(movie, dates)

        # Random delay between movies with increasing delay based on progress
        if idx < len(your_movies) - 1:  # No need to wait after last movie
            delay_multiplier = 1 + (idx / len(your_movies))  # Increases from 1 to 2
            delay = random.uniform(*WAIT_BETWEEN_MOVIES) * delay_multiplier
            print(f"⏳ Waiting {delay:.1f} seconds before next movie...")
            time.sleep(delay)

    driver.quit()
    print("\n🎉 Done scraping your 16 movies!")

if __name__ == "__main__":
    main()
