# app.py
import streamlit as st
from utils import load_data, fetch_poster, get_movie_row
import pandas as pd
import pickle

st.set_page_config(page_title="Movie Recommender", layout="wide")
st.title("🎬 Movie Recommender System")

movies, credits, similarity = load_data()

# If similarity is a path to pickle, try load. But load_data should already have returned matrix.
if similarity is None:
    try:
        similarity = pickle.load(open("similarity.pkl", "rb"))
    except Exception:
        similarity = None

if movies is None or movies.empty:
    st.error("Movies dataset not found. Place movies.pkl or movie_dict.pkl in the working directory.")
    st.stop()

selected_movie_name = st.selectbox("Pick a movie and let us recommend more!", movies['title'].values, index=0)

col1, col2 = st.columns([3, 2])

with col1:
    if st.button("Recommend (Content-based)"):
        # content-based recommendations
        try:
            movie_index = movies[movies['title'] == selected_movie_name].index[0]
        except Exception:
            st.error("Selected movie not found in dataset.")
            st.stop()
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

        rec_titles = []
        rec_posters = []
        for i in movies_list:
            mrow = movies.iloc[i[0]]
            rec_titles.append(mrow['title'])
            poster = fetch_poster(mrow.get('movie_id'))
            rec_posters.append(poster)

        # display 5 in a row
        cols = st.columns(5)
        for idx, c in enumerate(cols):
            with c:
                if idx < len(rec_titles):
                    st.caption(rec_titles[idx])
                    if rec_posters[idx]:
                        st.image(rec_posters[idx], use_container_width=True)
                    else:
                        st.write("Poster not found")

with col2:
    # Show selected movie details
    row = get_movie_row(movies, selected_movie_name)
    if row is not None:
        st.subheader(row['title'])
        poster = fetch_poster(row.get('movie_id'))
        if poster:
            st.image(poster)
        st.markdown(f"**Overview:** {row.get('overview', 'N/A')}")
        genres = row.get('genres_parsed', [])
        st.markdown(f"**Genres:** {', '.join(genres) if genres else 'N/A'}")
        st.markdown(f"**Runtime:** {row.get('runtime', 'N/A')}")
        st.markdown(f"**Rating:** {row.get('vote_average', 'N/A')}  ({row.get('vote_count', 'N/A')} votes)")
        st.markdown(f"**Release Year:** {row.get('release_year', 'N/A')}")
        st.markdown(f"**Budget:** {int(row['budget']) if pd.notna(row['budget']) and row['budget'] else 'N/A'}")
        st.markdown(f"**Revenue:** {int(row['revenue']) if pd.notna(row['revenue']) and row['revenue'] else 'N/A'}")
    else:
        st.write("Movie details not found.")

st.markdown("---")
st.info("Use the left sidebar Pages to navigate: Advanced Recommendations, Trending, Top Rated, Dashboard, Search & Filters.")
