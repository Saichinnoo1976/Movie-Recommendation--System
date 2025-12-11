# pages/2_Trending_Movies.py
import streamlit as st
from utils import load_data, fetch_poster
import pandas as pd

st.set_page_config(page_title="Trending Movies")
st.title("🔥 Trending Movies")

movies, credits, similarity = load_data()

metric = st.selectbox("Trending by", ["popularity", "vote_count", "revenue"], index=0)
top_n = st.slider("How many to show", min_value=5, max_value=20, value=10)

if metric not in movies.columns:
    st.warning(f"{metric} not in dataset; switching to popularity.")
    metric = "popularity"

trending = movies.sort_values(metric, ascending=False).head(top_n)

# Show a horizontal gallery
for idx, row in trending.iterrows():
    c1, c2 = st.columns([1,4])
    with c1:
        p = fetch_poster(row.get('movie_id'))
        if p:
            st.image(p, width=120)
        else:
            st.write("No poster")
    with c2:
        st.subheader(row['title'])
        st.write(f"Year: {row.get('release_year','N/A')} • Rating: {row.get('vote_average','N/A')} • {metric}: {row.get(metric,'N/A')}")
        st.write(row.get('overview',''))
    st.markdown("---")
