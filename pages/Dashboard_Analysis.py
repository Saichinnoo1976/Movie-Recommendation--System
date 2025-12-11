# pages/4_Dashboard_Analysis.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data
import ast

st.set_page_config(page_title="Dashboard & Analysis", layout="wide")
st.title("📊 Dashboard & Analysis")

movies, credits, similarity = load_data()

# Prepare genres exploded
movies['genres_exploded'] = movies['genres_parsed'].apply(lambda x: x if isinstance(x, list) else [])

st.header("Top Genres")
top_n = st.slider("Top N genres", 5, 20, 10)
# count
from collections import Counter
genre_counts = Counter()
for g in movies['genres_exploded']:
    if isinstance(g, list):
        genre_counts.update(g)
top_genres = pd.DataFrame(genre_counts.most_common(top_n), columns=['genre','count'])
fig1 = px.bar(top_genres, x='genre', y='count', title="Top Genres")
st.plotly_chart(fig1, use_container_width=True)

st.header("Most Frequent Actors")
if credits is not None:
    # extract top cast across credits
    def parse_cast_str(x):
        if pd.isna(x): return []
        if isinstance(x, list): cast = x
        else:
            try:
                cast = ast.literal_eval(x)
            except Exception:
                return []
        return [c.get('name') for c in cast if isinstance(c, dict)][:5]
    credits['top_cast'] = credits['cast'].apply(parse_cast_str)
    from collections import Counter
    actor_count = Counter()
    credits['top_cast'].apply(lambda arr: actor_count.update(arr))
    top_actors = pd.DataFrame(actor_count.most_common(20), columns=['actor','count'])
    fig2 = px.bar(top_actors, x='actor', y='count', title="Top Actors (by appearances)")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.write("Credits CSV not found. Place tmdb_5000_credits.csv in the project root.")

st.header("Most Frequent Directors")
if credits is not None:
    def extract_directors(crew_str):
        if pd.isna(crew_str): return []
        try:
            crew = ast.literal_eval(crew_str)
        except Exception:
            return []
        return [c.get('name') for c in crew if c.get('job') == 'Director']
    credits['directors'] = credits['crew'].apply(extract_directors)
    dir_count = Counter()
    credits['directors'].apply(lambda arr: dir_count.update(arr))
    top_dirs = pd.DataFrame(dir_count.most_common(20), columns=['director','count'])
    fig3 = px.bar(top_dirs, x='director', y='count', title="Top Directors")
    st.plotly_chart(fig3, use_container_width=True)

st.header("Runtime Distribution")
if 'runtime' in movies.columns:
    fig4 = px.histogram(movies[movies['runtime'].notna()], x='runtime', nbins=30, title="Runtime Distribution")
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.write("Runtime data not available in dataset.")

st.header("Budget vs Revenue")
if 'budget' in movies.columns and 'revenue' in movies.columns:
    df_br = movies.dropna(subset=['budget','revenue'])
    # filter out zeros and unrealistic outliers optionally
    df_br = df_br[(df_br['budget'] > 0) & (df_br['revenue'] > 0)]
    fig5 = px.scatter(df_br, x='budget', y='revenue', hover_data=['title','release_year','vote_average'], title="Budget vs Revenue (log scale)")
    fig5.update_layout(xaxis_title="Budget", yaxis_title="Revenue")
    fig5.update_xaxes(type="log")
    fig5.update_yaxes(type="log")
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.write("Budget/Revenue data missing.")

st.header("Popularity / Releases Over Time")
if 'release_year' in movies.columns:
    trend = movies.dropna(subset=['release_year']).groupby('release_year').agg({'title':'count','popularity':'mean'}).reset_index()
    fig6 = px.line(trend, x='release_year', y='title', title="Number of Movies Released per Year")
    st.plotly_chart(fig6, use_container_width=True)
    fig7 = px.line(trend, x='release_year', y='popularity', title="Average Popularity per Year")
    st.plotly_chart(fig7, use_container_width=True)
else:
    st.write("Release year data not available.")

st.header("Average Rating by Genre")
# compute average rating per genre
genres = {}
for _, r in movies.iterrows():
    g_list = r['genres_exploded']
    for g in g_list:
        genres.setdefault(g, []).append(r.get('vote_average') or 0)
avg_by_genre = [(g, sum(vals)/len(vals)) for g, vals in genres.items() if len(vals) > 0]
avg_by_genre = pd.DataFrame(avg_by_genre, columns=['genre','avg_rating']).sort_values('avg_rating', ascending=False)
st.plotly_chart(px.bar(avg_by_genre.head(20), x='genre', y='avg_rating', title="Average Rating by Genre"), use_container_width=True)
