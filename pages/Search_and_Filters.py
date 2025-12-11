# pages/5_Search_and_Filters.py
import streamlit as st
from utils import load_data, fetch_poster
import pandas as pd
from difflib import get_close_matches

st.set_page_config(page_title="Search & Filters")
st.title("🔎 Search & Filters")

movies, credits, similarity = load_data()

query = st.text_input("Search a movie (type and press Enter)", "")
if query:
    titles = movies['title'].tolist()
    matches = get_close_matches(query, titles, n=10, cutoff=0.4)
    if matches:
        sel = st.selectbox("Did you mean:", matches)
        if sel:
            r = movies[movies['title'] == sel].iloc[0]
            st.subheader(r['title'])
            p = fetch_poster(r.get('movie_id'))
            if p: st.image(p, width=220)
            st.write("Overview:", r.get('overview','N/A'))
            st.write("Genres:", ', '.join(r.get('genres_parsed',[])))
            st.write("Runtime:", r.get('runtime','N/A'))
            st.write("Rating:", r.get('vote_average','N/A'))
            st.write("Budget:", r.get('budget','N/A'))
            st.write("Revenue:", r.get('revenue','N/A'))
    else:
        st.write("No matches found.")
# Filters
st.markdown("---")
st.subheader("Filter dataset")
# genre filter
genres = sorted({g for lst in movies['genres_parsed'] for g in (lst or [])})
gsel = st.multiselect("Select genres", genres)
min_year, max_year = int(movies['release_year'].dropna().min() or 1900), int(movies['release_year'].dropna().max() or 2025)
yr = st.slider("Release year range", min_year, max_year, (min_year, max_year))
df = movies.copy()
if gsel:
    df = df[df['genres_parsed'].apply(lambda gs: any(g in gs for g in gsel) if isinstance(gs, list) else False)]
df = df[df['release_year'].between(yr[0], yr[1], inclusive="both")]
st.dataframe(df[['title','release_year','vote_average','popularity','runtime']].sort_values('vote_average', ascending=False).head(200))
