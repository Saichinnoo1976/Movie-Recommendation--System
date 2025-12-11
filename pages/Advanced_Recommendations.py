import streamlit as st
import pandas as pd
import ast
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

st.set_page_config(page_title="Advanced Recommendations", layout="wide")
st.title("🎬 Advanced Movie Recommendations")


# -------------------------------------------------------------------------
# TMDB Poster Fetch Function
# -------------------------------------------------------------------------
def fetch_poster(movie_id):
    api_key = "d02874027cdbddce773c6301218af7b7"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["GET"])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("poster_path"):
            return "https://image.tmdb.org/t/p/w500" + data["poster_path"]
    except:
        return "https://via.placeholder.com/500x750?text=No+Image"
    return "https://via.placeholder.com/500x750?text=No+Image"


# -------------------------------------------------------------------------
# Load datasets
# -------------------------------------------------------------------------
movies = pd.read_csv("tmdb_5000_movies.csv")
credits = pd.read_csv("tmdb_5000_credits.csv")

# Credits movie_id → id
credits.rename(columns={"movie_id": "id"}, inplace=True)

# Merge
movies = movies.merge(credits, on="id", how="left")

# Fix missing title column
if "title" not in movies.columns:
    if "original_title" in movies:
        movies.rename(columns={"original_title": "title"}, inplace=True)
    else:
        st.error("❌ Neither 'title' nor 'original_title' was found.")
        st.stop()

# Convert JSON-like columns safely
json_cols = ["genres", "cast", "crew"]
for col in json_cols:
    movies[col] = movies[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])


# -------------------------------------------------------------------------
# Helper Functions for Recommendations
# -------------------------------------------------------------------------
def get_genres(movie_title):
    row = movies[movies["title"] == movie_title]
    if row.empty:
        return []
    return [g["name"] for g in row.iloc[0]["genres"]]


def get_cast(movie_title):
    row = movies[movies["title"] == movie_title]
    if row.empty:
        return []
    return [c["name"] for c in row.iloc[0]["cast"]]


def get_director(movie_title):
    row = movies[movies["title"] == movie_title]
    if row.empty:
        return None
    crew = row.iloc[0]["crew"]
    directors = [c["name"] for c in crew if c.get("job") == "Director"]
    return directors[0] if directors else None


# -------------------------------------------------------------------------
# Recommendation Logic
# -------------------------------------------------------------------------
def recommend_by_genre(movie_title):
    genres = set(get_genres(movie_title))
    if not genres:
        return []

    movies["genre_match"] = movies["genres"].apply(
        lambda gen_list: len(genres.intersection(set(g["name"] for g in gen_list)))
    )

    result = movies[movies["title"] != movie_title].sort_values("genre_match", ascending=False).head(5)
    return result


def recommend_by_cast(movie_title):
    cast = set(get_cast(movie_title))
    if not cast:
        return []

    movies["cast_score"] = movies["cast"].apply(
        lambda c_list: len(cast.intersection(set(c["name"] for c in c_list)))
    )

    result = movies[movies["title"] != movie_title].sort_values("cast_score", ascending=False).head(5)
    return result


def recommend_by_director(movie_title):
    director = get_director(movie_title)
    if not director:
        return []

    # Safe mask (no NaN issues)
    movies["has_director"] = movies["crew"].apply(
        lambda crew_list: any(c.get("job") == "Director" and c.get("name") == director for c in crew_list)
    )

    result = movies[(movies["has_director"]) & (movies["title"] != movie_title)].head(5)
    return result


# -------------------------------------------------------------------------
# UI Component — Display Movie Grid
# -------------------------------------------------------------------------
def show_movies(df):
    cols = st.columns(5)
    for idx, row in enumerate(df.itertuples()):
        with cols[idx % 5]:
            st.image(fetch_poster(row.id), use_container_width=True)
            st.write(f"**{row.title}**")
            st.caption(f"⭐ {row.vote_average} | {row.release_date}")


# -------------------------------------------------------------------------
# MAIN UI
# -------------------------------------------------------------------------
movie_list = movies["title"].dropna().unique()
movie_choice = st.selectbox("🎥 Select a Movie", sorted(movie_list))

st.subheader(f"📌 Selected Movie: **{movie_choice}**")

selected_movie = movies[movies["title"] == movie_choice].iloc[0]
st.image(fetch_poster(selected_movie.id), width=300)

# Movie details
st.write("### 🎞 Movie Details")
st.write(f"**Genres:** {', '.join(get_genres(movie_choice))}")
st.write(f"**Rating:** {selected_movie.vote_average}")
st.write(f"**Popularity:** {selected_movie.popularity}")
st.write(f"**Release Date:** {selected_movie.release_date}")
st.write(f"**Budget:** ${selected_movie.budget:,}")
st.write(f"**Revenue:** ${selected_movie.revenue:,}")
st.write(f"**Director:** {get_director(movie_choice)}")

st.markdown("---")

# -------------------------------------------------------------------------
# Recommendation Sections
# -------------------------------------------------------------------------
st.header("🎯 Recommendations Based on Genre")
df1 = recommend_by_genre(movie_choice)
show_movies(df1)

st.header("🎭 Recommendations Based on Cast")
df2 = recommend_by_cast(movie_choice)
show_movies(df2)

st.header("🎬 Recommendations Based on Director")
df3 = recommend_by_director(movie_choice)
show_movies(df3)
