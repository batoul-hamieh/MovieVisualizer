import streamlit as st
import time
import pandas as pd
import plotly.express as px
import os

# ✅ Set page config first, only once
st.set_page_config(page_title="Movie Dashboard",layout="wide", page_icon="🎬")

# Logo setup
image_path = r"pages/images/TMBDLogo.png"
if os.path.exists(image_path):
    with st.sidebar:
        st.image(image_path, width=150)
else:
    st.sidebar.warning("Logo not found.")

st.sidebar.markdown("<b>Copyright to  <br> TMBD <br> Samira Jawish <br> Batoul Hamieh <br> Mohammad Sayyour</b>", unsafe_allow_html=True)

st.title("🎬 Welcome to the Movie Sentiment Visualizer")
st.markdown("Use the **sidebar** to select the Movie Dashboard.")

# === FUNCTION: Animated Stat Box ===
def animated_stat_box(value_text_func, label, duration=0.05, max_value=50, box_color="#ff4d4d"):
    placeholder = st.empty()
    for i in range(1, max_value + 1):
        text = value_text_func(i)
        placeholder.markdown(
            f"""
            <div style="
                background-color:{box_color};
                color:white;
                padding:15px 30px;
                border-radius:10px;
                width:100%;
                box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
                display:flex;
                align-items:center;
                font-size:26px;
                font-weight:bold;
                margin-bottom: 15px;">
                <span style='margin-right:10px;'>{text}</span>
                <span>{label}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        time.sleep(duration)

# === BOX 1: 50 Movies ===
animated_stat_box(lambda i: f"{i}", "Movies")

# === Spacer between boxes ===
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# === BOX 2: 5,000+ Reviews ===
animated_stat_box(lambda i: f"{i * 100}", "Reviews")


# Load data
df_info = pd.read_csv("movie_info_1.csv")
df_info['release_year'] = pd.to_numeric(df_info['release_year'], errors='coerce')
df_info['user_score'] = pd.to_numeric(df_info['user_score'], errors='coerce')

# Sort by title just for consistent ordering
df_info = df_info.sort_values(by="title")

col1, col2 = st.columns(2)

# === Chart 1: User Scores Bar Chart ===
with col1:
    st.subheader("⭐ Top 10 Movies by User Score")
    st.markdown("<br>", unsafe_allow_html=True)

    # Sort by user score and take top 10
    df_sorted = df_info.sort_values("user_score", ascending=False).head(10)

    fig_scores = px.bar(
        df_sorted,
        x="title",
        y="user_score",
        title="User Ratings",
        labels={"user_score": "Score", "title": "Movie"},
        color="user_score",
        color_continuous_scale="Blues",
        text="user_score"  # Add score labels on bars
    )

    fig_scores.update_traces(textposition="outside")

    fig_scores.update_layout(
        xaxis_tickangle=-45,
        bargap=0.4,
        height=500,
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )

    st.plotly_chart(fig_scores, use_container_width=True)


# === Chart 2: Release Years Chart (Horizontal) ===
with col2:
    st.subheader("📆 Movie Release Years")

    fig_years = px.bar(
        df_info,
        x="release_year",
        y="title",
        orientation="h",
        title="Release Timeline",
        labels={"release_year": "Year", "title": "Movie"},
        color="release_year",
        color_continuous_scale="Viridis"
    )
    fig_years.update_layout(
        height=500,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(range=[1990, 2030])
    )
    st.plotly_chart(fig_years, use_container_width=True)

# Manual worldwide gross in billions USD
worldwide_gross = {
    "Titanic (1997)": 2.264,
    "Barbie (2023)": 1.446,
    "Furious 7 (2015)": 1.515,
    "Jurassic World (2015)": 1.671,
    "The Avengers (2012)": 1.519,
    "Ne Zha 2 (2025)": 0.0,
    "Inside Out 2 (2024)": 0.0,
    "The Lion King (1994)": 0.968,
    "Avengers Endgame (2019)": 2.799,
    "Avengers Infinity War (2018)": 2.048,
    "Avatar The Way Of Water (2022)": 2.320,
    "Spider-Man No Way Home (2021)": 1.921,
    "Star Wars The Force Awakens (2015)": 2.068,
    "Top Gun Maverick (2022)": 1.495,
    "Avatar (2009)": 2.923,
    "Frozen 2 (2019)": 1.453,
    "Star Wars: Episode I- The Phantom Menace": 1.027,
    "The Batman (2022)": 0.772,
    "Skyfall (2012)": 1.109,
    "Joker (2019)": 1.074,
    "Toy Story 4 (2019)": 1.073,
    "Aladdin (2019)": 1.054,
    "Despicable Me 3 (2017)": 1.035,
    "Transformers: Age Of Extinction (2014)": 1.104,
    "The Dark Knight Rises (2012)": 1.081,
    "Star Wars: The Rise Of Skywalker (2019)": 1.077,
    "Toy Story 3 (2010)": 1.067,
    "Pirates Of The Caribbean: Dead Man'S Chest (2006)": 1.066,
    "Moana 2": 0.0,
    "Rogue One: A Star Wars Story (2016)": 1.058,
    "Pirates Of The Caribbean: On Stranger Tides (2011)": 1.045,
    "Jurassic Park (1993)": 1.046,
    "Finding Dory (2016)": 1.029,
    "Avengers: Age Of Ultron (2015)": 1.403,
    "Super Mario Bros. (2023)": 1.361,
    "Star Wars: The Last Jedi (2017)": 1.334,
    "Black Panther (2018)": 1.347,
    "Harry Potter And The Deathly Hallows (2010)": 1.342,
    "Jurassic World Fallen Kingdom (2018)": 1.309,
    "Beauty And The Beast (2017)": 1.266,
    "Incredibles 2 (2018)": 1.243,
    "The Fate Of The Furious (2017)": 1.236,
    "Iron Man 3 (2013)": 1.215,
    "Minions (2015)": 1.159,
    "Captain America Civil War (2016)": 1.155,
    "Aquaman (2018)": 1.152,
    "The Lord Of The Rings The Return Of The King (2003)": 1.146,
    "Spider Man Far From Home (2019)": 1.131,
    "Captain Marvel (2019)": 1.131,
    "Transformers Dark Of The Moon (2011)": 1.123
}

gross_df = pd.DataFrame(list(worldwide_gross.items()), columns=["title", "gross"])
gross_df = gross_df.sort_values(by="gross", ascending=False)

st.subheader("🌍 Worldwide Gross Revenue")
fig_gross = px.bar(gross_df, x="title", y="gross", title="Global Box Office (Billion USD)", labels={"gross": "Billions USD"})
fig_gross.update_layout(xaxis_tickangle=-45, height=600)
st.plotly_chart(fig_gross, use_container_width=True)


# Load data
reviews_df = pd.read_csv("analyzed_reviews_with_id.csv")


# Ensure id columns are strings for safe matching
reviews_df['id'] = reviews_df['id'].astype(str)
df_info['id'] = df_info['id'].astype(str)

# Count positive and negative sentiments by movie id
positive_counts = reviews_df[reviews_df['sentiment_label'] == 'Positive'].groupby('id').size()
negative_counts = reviews_df[reviews_df['sentiment_label'] == 'Negative'].groupby('id').size()

# Find movie id with highest positive count and highest negative count
most_positive_id = positive_counts.idxmax()
most_negative_id = negative_counts.idxmax()

# Sample one positive review from the most positive movie
sample_positive_review = reviews_df[(reviews_df['id'] == most_positive_id) & (reviews_df['sentiment_label'] == 'Positive')].iloc[0]

# Sample one negative review from the most negative movie
sample_negative_review = reviews_df[(reviews_df['id'] == most_negative_id) & (reviews_df['sentiment_label'] == 'Negative')].iloc[0]

# Get movie metadata
most_positive_movie = df_info[df_info['id'] == most_positive_id].iloc[0]
most_negative_movie = df_info[df_info['id'] == most_negative_id].iloc[0]

# Display in Streamlit side by side
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🟢 Movie with Most Positive Reviews")
    st.image(most_positive_movie['poster_url'], width=300)
    st.markdown(f"**{most_positive_movie['title']}**")
    st.markdown(f"**Director:** {most_positive_movie['director']}")
    st.markdown(f"**Number of Positive Reviews:** {positive_counts[most_positive_id]}")
    st.markdown("**Sample Positive Review:**")
    st.success(sample_positive_review['review'])

with col2:
    st.markdown("### 🔴 Movie with Most Negative Reviews")
    st.image(most_negative_movie['poster_url'], width=300)
    st.markdown(f"**{most_negative_movie['title']}**")
    st.markdown(f"**Director:** {most_negative_movie['director']}")
    st.markdown(f"**Number of Negative Reviews:** {negative_counts[most_negative_id]}")
    st.markdown("**Sample Negative Review:**")
    st.error(sample_negative_review['review'])
