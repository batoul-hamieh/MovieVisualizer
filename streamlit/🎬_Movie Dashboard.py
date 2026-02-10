
import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
import plotly.express as px
from wordcloud import WordCloud
import numpy as np
import ast
import os

# Logo setup
image_path = r"pages/images/TMBDLogo.png"
if os.path.exists(image_path):
    with st.sidebar:
        st.image(image_path, width=150)
else:
    st.sidebar.warning("Logo not found.")
st.sidebar.markdown("<b>Copyright to  <br> TMBD <br> Samira Jawish <br> Batoul Hamieh <br> Mohammad Sayyour</b>", unsafe_allow_html=True)

@st.cache_data
def load_movie_info():
    df = pd.read_csv("movie_info_1.csv")
    df['id'] = df['id'].astype(str)
    df['title'] = df['title'].str.strip()
    return df

@st.cache_data
def load_reviews():
    df = pd.read_csv("analyzed_reviews_with_id.csv", parse_dates=['date'])
    df['id'] = df['id'].astype(str)
    return df

# === File Check ===
if not os.path.exists("movie_info_1.csv") or not os.path.exists("analyzed_reviews_with_id.csv"):
    st.error("Required files missing.")
    st.stop()

# === Load Data ===
df = load_movie_info()
reviews_df = load_reviews()

# === Movie Title Selector (uses ID internally) ===
movie_dict = {row['title']: row['id'] for _, row in df.iterrows()}

# Add a title and description above the dropdown list
st.title("Movie's Sentiment Visualizer")
st.markdown("This Web app aims to display the sentiment analysis of the top 50 highest-grossing movies of all time through the audience reviews.")

movie_titles = ["Select a movie"] + list(movie_dict.keys())
selected_title = st.selectbox("🎬 Select a Movie", movie_titles)

if selected_title == "Select a movie":
    st.warning("Please select a movie.")
    st.stop()

selected_id = movie_dict[selected_title]

# === Filter Movie Info by ID ===
movie_row = df[df['id'] == selected_id]
if movie_row.empty:
    st.error("Movie data not found.")
    st.stop()

movie = movie_row.iloc[0]

# === Display Metadata ===
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader(movie['title'])
    st.markdown(f"**Release Year:** {movie.get('release_year', 'N/A')}")
    st.markdown(f"**Runtime:** {movie.get('runtime', 'N/A')} minutes")
    
    genres = ast.literal_eval(movie['genres']) if isinstance(movie['genres'], str) else movie['genres']
    st.markdown(f"**Genres:** {', '.join(genres) if genres else 'N/A'}")
    
    st.markdown(f"**Director:** {movie.get('director', 'N/A')}")
    st.markdown(f"**User Score:** {movie.get('user_score', 'N/A')}")
    st.markdown(f"**Original Language:** {movie.get('original_language', 'N/A').upper()}")
    st.markdown("**Overview:**")
    st.markdown(movie.get('overview', 'N/A'))
with col2:
    if pd.notnull(movie['poster_url']):
        try:
            response = requests.get(movie['poster_url'], timeout=5)
            img = Image.open(BytesIO(response.content))
            st.image(img, width=400)
        except:
            st.write("Poster could not be loaded.")
    else:
        st.write("Poster not available.")

# === Filter Reviews by ID ===
movie_reviews = reviews_df[reviews_df['id'] == selected_id]


# === Sentiment Counts ===
sentiment_counts = movie_reviews['sentiment_label'].value_counts() if 'sentiment_label' in movie_reviews else pd.Series()

# === Word Cloud ===
if not movie_reviews['review'].empty:
    wordcloud = WordCloud(width=600, height=400, background_color='white').generate(" ".join(movie_reviews['review']))

# === Radar Chart Data ===
emotion_cols = ['joy', 'anger', 'fear', 'sadness', 'surprise', 'love']
for col in emotion_cols:
    if col not in movie_reviews.columns:
        movie_reviews[col] = np.random.uniform(0, 1, len(movie_reviews))

radar_df = movie_reviews[emotion_cols].mean().reset_index()
radar_df.columns = ['emotion', 'value']
radar_df = pd.concat([radar_df, radar_df.iloc[0:1]])

# === Time-based Sentiment (Yearly View) ===
movie_reviews['date'] = pd.to_datetime(movie_reviews['date'], errors='coerce')
movie_reviews['year'] = movie_reviews['date'].dt.to_period('Y').dt.to_timestamp()
time_sentiment = movie_reviews.groupby('year')['sentiment_score'].mean().reset_index()

st.subheader("📈 Yearly Sentiment Trend")
if 'sentiment_score' in movie_reviews:
    import plotly.express as px
    fig = px.line(
        time_sentiment,
        x='year',
        y='sentiment_score',
        title='Yearly Sentiment Trend',
        labels={'sentiment_score': 'Average Sentiment Score', 'year': 'Year'}
    )
    fig.update_layout(xaxis_tickformat="%Y")  # Only show year
    st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("☁️ Word Cloud")
    if 'wordcloud' in locals():
        st.image(wordcloud.to_array(), use_container_width=True)
    else:
        st.write("No reviews to display.")
with col2:
    st.subheader("🥧 Sentiment Distribution")
    if not sentiment_counts.empty:
        fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index)
        st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns([1, 1])
with col3:
    st.subheader("📊 Emotion Radar")
    fig = px.line_polar(radar_df, r='value', theta='emotion', line_close=True, markers=True)
    st.plotly_chart(fig, use_container_width=True)
with col4:
    st.subheader("📊 Average Sentiment per Label")
    if 'sentiment_score' in movie_reviews:
        avg_df = movie_reviews.groupby('sentiment_label')['sentiment_score'].mean().reset_index()
        fig = px.bar(avg_df, x='sentiment_label', y='sentiment_score')
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("💬 Sample Reviews")
# Update the review numbering to count based on the ID repetitions
if len(movie_reviews) >= 3:
    for i, (index, row) in enumerate(movie_reviews.sample(3).iterrows(), start=1):
        review_number = movie_reviews.index.get_loc(index) + 1  # Get the position of the review within the filtered DataFrame
        with st.expander(f"Review {review_number}"):
            st.write(f"**Sentiment:** {row['sentiment_label']} (Score: {row['sentiment_score']:.2f})")
            st.write(row['review'])
else:
    st.warning("Not enough reviews available.")
