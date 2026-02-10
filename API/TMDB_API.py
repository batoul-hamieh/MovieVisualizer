import requests
import pandas as pd
import time
import re

API_KEY = ''  # <-- Replace with your actual TMDB API key
SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
DETAILS_URL = 'https://api.themoviedb.org/3/movie/{}'
CREDITS_URL = 'https://api.themoviedb.org/3/movie/{}/credits'
IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500'

raw_movies = [
    "Titanic (1997)", "Barbie (2023)", "Furious 7 (2015)", "Jurassic World (2015)", "The Avengers (2012)",
    "Ne Zha 2 (2025)", "Inside Out 2 (2024)", "The Lion King (1994)", "Avengers Endgame (2019)",
    "Avengers Infinity War (2018)", "Avatar The Way Of Water (2022)", "Spider-Man No Way Home (2021)",
    "Star Wars The Force Awakens (2015)", "Top Gun Maverick (2022)", "Avatar (2009)", "Frozen 2 (2019)",
    "Star Wars: Episode I- The Phantom Menace (Unknown)", "The Batman (2022)", "Skyfall (2012)", "Joker (2019)",
    "Toy Story 4 (2019)", "Aladdin (2019)", "Despicable Me 3 (2017)", "Transformers: Age Of Extinction (2014)",
    "The Dark Knight Rises (2012)", "Star Wars: The Rise Of Skywalker (2019)", "Toy Story 3 (2010)",
    "Pirates Of The Caribbean: Dead Man'S Chest (2006)", "Moana 2 (2025)", "Rogue One: A Star Wars Story (2016)",
    "Pirates Of The Caribbean: On Stranger Tides (2011)", "Jurassic Park (1993)", "Finding Dory (2016)",
    "Avengers: Age Of Ultron (2015)", "Super Mario Bros. (2023)", "Star Wars: The Last Jedi (2017)",
    "Black Panther (2018)", "Harry Potter And The Deathly Hallows (2010)", "Jurassic World Fallen Kingdom (2018)",
    "Beauty And The Beast (2017)", "Incredibles 2 (2018)", "The Fate Of The Furious (2017)", "Iron Man 3 (2013)",
    "Minions (2015)", "Captain America Civil War (2016)", "Aquaman (2018)",
    "The Lord Of The Rings The Return Of The King (2003)", "Spider Man Far From Home (2019)", "Captain Marvel (2019)",
    "Transformers Dark Of The Moon (2011)"
]

def extract_title_year(movie_str):
    match = re.match(r'^(.*?)\s+\((\d{4}|Unknown)\)$', movie_str)
    if match:
        title, year = match.group(1).strip(), match.group(2)
        return title, None if year == "Unknown" else year
    return movie_str.strip(), None

def get_movie_info(title, year):
    # Search for movie by title
    search = requests.get(SEARCH_URL, params={'api_key': API_KEY, 'query': title}).json()
    results = search.get('results', [])

    if not results:
        return {'title': title, 'error': 'Not found'}

    # Filter by year if available
    if year:
        results = [r for r in results if r.get('release_date', '').startswith(year)]

    if not results:
        return {'title': title, 'error': 'No match for year'}

    movie = results[0]
    movie_id = movie['id']

    # Get movie details
    details = requests.get(DETAILS_URL.format(movie_id), params={'api_key': API_KEY}).json()
    # Get movie credits to find director
    credits = requests.get(CREDITS_URL.format(movie_id), params={'api_key': API_KEY}).json()

    director = ''
    for crew_member in credits.get('crew', []):
        if crew_member.get('job') == 'Director':
            director = crew_member.get('name')
            break

    return {
        'title': title + f" ({year})" if year else title,
        'poster_url': IMAGE_BASE_URL + movie['poster_path'] if movie.get('poster_path') else None,
        'genres': [genre['name'] for genre in details.get('genres', [])],
        'release_year': details.get('release_date', '')[:4],
        'runtime': details.get('runtime', ''),
        'director': director,
        'user_score': details.get('vote_average', None),          # TMDB user score
        'original_language': details.get('original_language', ''), # Original language ISO code
        'overview': details.get('overview', '')                    # Movie summary/description
    }

# Fetch info for all movies
data = []
for raw_title in raw_movies:
    try:
        title, year = extract_title_year(raw_title)
        info = get_movie_info(title, year)
        data.append(info)
        print(f"✅ Retrieved: {raw_title}")
        time.sleep(0.3)  # polite pause to avoid hitting rate limits
    except Exception as e:
        print(f"❌ Error with {raw_title}: {str(e)}")
        data.append({'title': raw_title, 'error': str(e)})

# Save to CSV
df = pd.DataFrame(data)
df.to_csv("movie_info_1.csv", index=False)
print("✅ Movie data retrieval complete. CSV file saved as 'movie_info_1.csv'.")
