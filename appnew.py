import streamlit as st
import pickle
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import ast

# -----------------------------------------------------------------
# Load datasets
# -----------------------------------------------------------------
movies = pd.read_csv("data/tmdb_5000_movies.csv")
credits = pd.read_csv("data/tmdb_5000_credits.csv")

movies_dict = pickle.load(open("data/movie_dict.pkl", "rb"))
movie_df = pd.DataFrame(movies_dict)
similarity = pickle.load(open("data/similarity.pkl", "rb"))

# Merge movies + credits for details
credits.columns = ["movie_id", "title", "cast", "crew"]
full_df = movies.merge(credits, on="title")


# -----------------------------------------------------------------
# Fetch poster
# -----------------------------------------------------------------
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=d02874027cdbddce773c6301218af7b7&language=en-US"

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, timeout=10)
        data = response.json()
        return "https://image.tmdb.org/t/p/w500" + data['poster_path']
    except:
        return None


# -----------------------------------------------------------------
# Content-Based Recommendation
# -----------------------------------------------------------------
def recommend(movie):
    index = movie_df[movie_df["title"] == movie].index[0]
    distances = similarity[index]
    movies_list = sorted(list(enumerate(distances)), key=lambda x: x[1], reverse=True)[1:6]

    names = []
    posters = []

    for i in movies_list:
        movie_id = movie_df.iloc[i[0]].movie_id
        names.append(movie_df.iloc[i[0]].title)
        posters.append(fetch_poster(movie_id))

    return names, posters


# -----------------------------------------------------------------
# Movie Details Extraction
# -----------------------------------------------------------------
def get_movie_details(title):
    row = full_df[full_df["title"] == title].iloc[0]

    genres = ", ".join([g["name"] for g in ast.literal_eval(row.genres)])
    cast = ", ".join([c["name"] for c in ast.literal_eval(row.cast)[:5]])

    director = [c["name"] for c in ast.literal_eval(row.crew) if c["job"] == "Director"]
    director = director[0] if director else "Unknown"

    return {
        "Overview": row.overview,
        "Genres": genres,
        "Runtime": f"{row.runtime} min",
        "Rating": row.vote_average,
        "Release Year": row.release_date.split("-")[0],
        "Budget": f"${row.budget:,}",
        "Revenue": f"${row.revenue:,}",
        "Cast": cast,
        "Director": director
    }


# -----------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.title("🎬 Movie Recommender System")
st.markdown("Select a movie to get recommendations.")

movie_name = st.selectbox("Choose a movie:", movie_df["title"].values)

if st.button("Recommend"):
    colA, colB = st.columns([1, 2])

    # Movie Details Section
    with colA:
        st.subheader("📌 Movie Details")
        details = get_movie_details(movie_name)
        movie_id = full_df[full_df["title"] == movie_name].iloc[0]["movie_id"]
        poster = fetch_poster(movie_id)
        st.image(poster, use_container_width=True)
        st.write(details)

    # Recommendation Section
    with colB:
        st.subheader("🎯 Recommended Movies")
        names, posters = recommend(movie_name)

        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                st.text(names[i])
                st.image(posters[i], use_container_width=True)

st.markdown("---")
st.write("Navigate more features using the **sidebar pages** →")
