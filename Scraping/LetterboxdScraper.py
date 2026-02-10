import pandas as pd
import time
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# ------------------- CONFIG -------------------

REVIEWS_PER_MOVIE = 100
MOVIE_CSV = "Movies.csv" #You change the name ACCORDING TO YOUR fILE!!!
OUTPUT_CSV = "all_reviews.csv"
WAIT_BETWEEN_REVIEWS = (2, 5)     # seconds
WAIT_BETWEEN_MOVIES = (10, 20)    # seconds

# ----------------------------------------------

def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)
    return driver

def get_review_elements(driver):
    return driver.find_elements(By.CSS_SELECTOR, 'div.review')

def extract_review_texts(review_elements, already_collected, movie_name):
    reviews = []
    count = len(already_collected)
    
    for review in review_elements:
        try:
            text_elem = review.find_element(By.CSS_SELECTOR, 'div.truncate')
            text = text_elem.text.strip()
            if text and text not in already_collected:
                count += 1
                print(f"{movie_name} ✅ Review {count}")
                reviews.append(text)
        except NoSuchElementException:
            continue
    return reviews

def scroll_and_collect_reviews(driver, reviews_needed, movie_name):
    collected_reviews = set()

    while len(collected_reviews) < reviews_needed:
        time.sleep(random.uniform(*WAIT_BETWEEN_REVIEWS))

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(*WAIT_BETWEEN_REVIEWS))

        elements = get_review_elements(driver)
        new_texts = extract_review_texts(elements, collected_reviews, movie_name)
        collected_reviews.update(new_texts)

        if len(new_texts) == 0:
            break  # No more new reviews loaded

    return list(collected_reviews)[:reviews_needed]

def build_review_url(movie_title):
    slug = movie_title.lower().replace(' ', '-')
    return f"https://letterboxd.com/film/{slug}/reviews/by/date/"

def save_reviews_to_master_csv(movie, reviews, output_file=OUTPUT_CSV):
    review_col = pd.Series(reviews, name=movie)

    if os.path.exists(output_file):
        df = pd.read_csv(output_file)
        if movie in df.columns:
            print(f"⚠️ Movie '{movie}' already exists in output file. Skipping.")
            return
        df[movie] = pd.Series(reviews)
    else:
        df = pd.DataFrame({movie: review_col})

    df.to_csv(output_file, index=False)
    print(f"✅ Saved {len(reviews)} reviews for '{movie}'")

def load_movie_list(csv_file):
    df = pd.read_csv(csv_file)
    return df.columns.tolist()

def already_scraped(movie, output_file=OUTPUT_CSV):
    if not os.path.exists(output_file):
        return False
    df = pd.read_csv(output_file, nrows=1)
    return movie in df.columns

def scrape_reviews_for_movie(driver, movie):
    url = build_review_url(movie)
    print(f"🎬 Scraping: {movie} → {url}")
    driver.get(url)
    time.sleep(random.uniform(2, 4))  # Let page load
    reviews = scroll_and_collect_reviews(driver, REVIEWS_PER_MOVIE, movie)
    print(f"📝 Collected {len(reviews)} reviews for '{movie}'")
    return reviews

def main():
    driver = init_driver()
    movie_list = load_movie_list(MOVIE_CSV)

    your_movies = movie_list[:16]  # You're scraping 18, others will scrape 16

    for idx, movie in enumerate(your_movies):
        if already_scraped(movie):
            print(f"⏩ Already scraped: {movie}")
            continue

        try:
            reviews = scrape_reviews_for_movie(driver, movie)
            if reviews:
                save_reviews_to_master_csv(movie, reviews)
            else:
                print(f"⚠️ No reviews found for {movie}")
        except Exception as e:
            print(f"❌ Error scraping {movie}: {e}")

        time.sleep(random.uniform(*WAIT_BETWEEN_MOVIES))

    driver.quit()
    print("\n🎉 Done scraping your 16 movies!")

if __name__ == "__main__":
    main()
