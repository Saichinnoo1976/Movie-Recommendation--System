# utils.py
import ast
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st
from functools import lru_cache

API_KEY = "d02874027cdbddce773c6301218af7b7"  # you may replace with env var if preferred
POSTER_BASE = "https://image.tmdb.org/t/p/w500"

@st.cache_data
def load_data():
    """
    Load pickles/csvs. Returns (movies_df, credits_df, similarity_matrix)
    """
    import pickle, os
    # Try pickles first
    movies = None
    similarity = None
    credits = None

    # load movies DataFrame from movies.pkl or movie_dict.pkl
    if os.path.exists("movies.pkl"):
        try:
            movies = pd.read_pickle("movies.pkl")
        except Exception:
            movies = pd.DataFrame()
    if movies is None or movies.empty:
        # try movie_dict.pkl
        try:
            movies_dict = pickle.load(open("movie_dict.pkl", "rb"))
            movies = pd.DataFrame(movies_dict)
        except Exception:
            movies = pd.DataFrame()

    # similarity matrix
    if os.path.exists("similarity.pkl"):
        try:
            similarity = pickle.load(open("similarity.pkl", "rb"))
        except Exception:
            similarity = None

    # credits csv (for actors/directors)
    if os.path.exists("tmdb_5000_credits.csv"):
        try:
            credits = pd.read_csv("tmdb_5000_credits.csv")
        except Exception:
            credits = None
    else:
        credits = None

    # movies csv fallback to enrich data
    if (("genres" not in movies.columns or "runtime" not in movies.columns)
        and os.path.exists("tmdb_5000_movies.csv")):
        try:
            movies_csv = pd.read_csv("tmdb_5000_movies.csv")
            # merge on title if possible to enrich missing cols
            if not movies.empty:
                movies = movies.merge(movies_csv, how="left", left_on="title", right_on="title", suffixes=('', '_csv'))
            else:
                movies = movies_csv
        except Exception:
            pass

    # Clean / normalize columns
    if 'genres' in movies.columns:
        movies['genres_parsed'] = movies['genres'].apply(_parse_column)
    else:
        movies['genres_parsed'] = [[] for _ in range(len(movies))]

    # ensure movie_id column
    if 'movie_id' not in movies.columns and 'id' in movies.columns:
        movies = movies.rename(columns={'id': 'movie_id'})

    # release year column
    if 'release_date' in movies.columns:
        movies['release_year'] = pd.to_datetime(movies['release_date'], errors='coerce').dt.year
    else:
        movies['release_year'] = None

    # ensure numeric columns exist
    for c in ['runtime', 'budget', 'revenue', 'popularity', 'vote_average', 'vote_count']:
        if c not in movies.columns:
            movies[c] = None

    return movies, credits, similarity

def _parse_column(x):
    """
    Robust parsing for columns that are lists/dicts stored as strings.
    e.g. genres field in TMDB is often "[{'id':..,'name':'Action'},...]"
    """
    if pd.isna(x):
        return []
    if isinstance(x, list):
        # maybe already parsed
        try:
            return [ (i['name'] if isinstance(i, dict) and 'name' in i else i) for i in x ]
        except Exception:
            return x
    # if string
    try:
        parsed = ast.literal_eval(x)
        if isinstance(parsed, list):
            return [ (i['name'] if isinstance(i, dict) and 'name' in i else i) for i in parsed ]
        return []
    except Exception:
        # fallback naive split
        s = str(x)
        s = s.replace('[','').replace(']','').replace("'", "")
        parts = [p.strip() for p in s.split(',') if p.strip()]
        return parts

@st.cache_data
def fetch_poster(movie_id):
    if pd.isna(movie_id):
        return None
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    try:
        resp = session.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if data.get('poster_path'):
            return POSTER_BASE + data['poster_path']
    except Exception as e:
        # print(e)  # keep silent in production
        return None
    return None

def get_movie_row(movies, title):
    row = movies[movies['title'] == title]
    if len(row) == 0:
        # try case-insensitive
        row = movies[movies['title'].str.lower() == title.lower()]
    if len(row) > 0:
        return row.iloc[0]
    return None

def extract_top_cast(credits_row, top_n=5):
    """
    credits_row: string representation of cast list or actual list
    """
    import ast
    if pd.isna(credits_row):
        return []
    if isinstance(credits_row, list):
        cast = credits_row
    else:
        try:
            cast = ast.literal_eval(credits_row)
        except Exception:
            # naive parse
            return []
    # cast items may be dicts with 'name'
    names = []
    for c in cast[:top_n]:
        if isinstance(c, dict):
            names.append(c.get('name') or c.get('original_name'))
        else:
            names.append(c)
    return names
