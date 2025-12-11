# pages/3_Top_Rated.py
import streamlit as st
from utils import load_data, fetch_poster
import pandas as pd

st.set_page_config(page_title="Top Rated")
st.title("⭐ Top Rated Movies")

movies, credits, similarity = load_data()

# prepare exploded genres
movies['genres_exploded'] = movies['genres_parsed'].apply(lambda x: x if isinstance(x, list) else [])

all_genres = sorted({g for lst in movies['genres_exploded'] for g in lst})
genre = st.selectbox("Filter by genre (optional)", ["All"] + all_genres)
n = st.slider("How many", 5, 50, 10)

df = movies.copy()
if genre != "All":
    df = df[df['genres_exploded'].apply(lambda gs: genre in gs if isinstance(gs, list) else False)]

top = df.sort_values(['vote_average','vote_count'], ascending=False).head(n)

cols = st.columns(4)
for idx, (_, r) in enumerate(top.iterrows()):
    col = cols[idx % 4]
    with col:
        st.caption(r['title'])
        p = fetch_poster(r.get('movie_id'))
        if p:
            st.image(p, width=160)
        st.write(f"Rating: {r.get('vote_average','N/A')} • Votes: {int(r.get('vote_count') or 0)}")
