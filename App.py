import streamlit as st
from PIL import Image
import json
from Classifier import KNearestNeighbours
from bs4 import BeautifulSoup
import requests, io
import PIL.Image
from urllib.request import urlopen

with open('./Data/movie_data.json', 'r+', encoding='utf-8') as f:
    data = json.load(f)
with open('./Data/movie_titles.json', 'r+', encoding='utf-8') as f:
    movie_titles = json.load(f)

hdr = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'
}

def movie_poster_fetcher(imdb_link):
    try:
        url_data = requests.get(imdb_link, headers=hdr)
        url_data.raise_for_status()
        s_data = BeautifulSoup(url_data.text, 'html.parser')
        imdb_dp = s_data.find("meta", property="og:image")
        if imdb_dp is not None:
            movie_poster_link = imdb_dp.attrs['content']
            u = urlopen(movie_poster_link)
            raw_data = u.read()
            image = PIL.Image.open(io.BytesIO(raw_data))
            image = image.resize((220, 301))
            st.image(image, use_column_width=False)
        else:
            st.warning("No movie poster available for this link.")
    except Exception as e:
        st.error(f"An error occurred while fetching movie poster: {e}")

def get_movie_info(imdb_link):
    url_data = requests.get(imdb_link, headers=hdr)
    url_data.raise_for_status()
    s_data = BeautifulSoup(url_data.text, 'html.parser')
    imdb_content = s_data.find("meta", property="og:description")
    if imdb_content is not None:
        movie_descr = imdb_content.attrs['content']
        movie_descr = str(movie_descr).split('.')
        movie_director = movie_descr[0].strip() if len(movie_descr) > 0 else "Director information not available"
    else:
        movie_director = "Director information not available"

    story_element = s_data.find("span", class_="sc-7193fc79-2 kpMXpM")
    if story_element is not None:
        story = story_element.text
        movie_story = 'Story: ' + str(story)
    else:
        movie_story = "Story information not available"
    
    rating_element = s_data.find("div", class_="sc-5f7fb5b4-1 fTREEx")
    if rating_element is not None:
        rating = rating_element.text
        movie_rating = 'Popularity: ' + str(rating) + ' place'
    else:
        movie_rating = "Popularity information not available"

    return movie_director, movie_story, movie_rating

def KNN_Movie_Recommender(test_point, k):
    target = [0 for item in movie_titles]
    model = KNearestNeighbours(data, target, test_point, k=k)
    model.fit()
    table = []
    for i in model.indices:
        table.append([movie_titles[i][0], movie_titles[i][2], data[i][-1]])
    print(table)
    return table

st.set_page_config(
    page_title="Movie Recommender System",
)

def run():
    st.title("Movie Recommender System")
    genres = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family',
              'Fantasy', 'Film-Noir', 'Game-Show', 'History', 'Horror', 'Music', 'Musical', 'Mystery', 'News',
              'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 'Thriller', 'War', 'Western']
    movies = [title[0] for title in movie_titles]
    category = ['--Select--', 'Movie based', 'Genre based']
    cat_op = st.selectbox('Select Recommendation Type', category)
    if cat_op == category[0]:
        st.warning('Please select Recommendation Type!!')
    elif cat_op == category[1]:
        select_movie = st.selectbox('Select movie: (Recommendation will be based on this selection)',
                                    ['--Select--'] + movies)
        dec = st.radio("Want to Fetch Movie Poster?", ('Yes', 'No'))
        st.markdown(
            '''<h4 style='text-align: left; color: #d73b5c;'>Fetching a Movie Posters will take a time.</h4>''',
            unsafe_allow_html=True)
        if dec == 'No':
            if select_movie == '--Select--':
                st.warning('Please select Movie!!')
            else:
                no_of_reco = st.slider('Number of movies you want Recommended:', min_value=5, max_value=20, step=1)
                genres = data[movies.index(select_movie)]
                test_points = genres
                table = KNN_Movie_Recommender(test_points, no_of_reco + 1)
                table.pop(0)
                c = 0
                st.success('Some of the movies from our Recommendation, have a look below')
                for movie, link, ratings in table:
                    c += 1
                    director, story, total_rat = get_movie_info(link)
                    st.markdown(f"({c})[ {movie}]({link})")
                    st.markdown(director)
                    st.markdown(story)
                    st.markdown(total_rat)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')
        else:
            if select_movie == '--Select--':
                st.warning('Please select Movie!!')
            else:
                no_of_reco = st.slider('Number of movies you want Recommended:', min_value=5, max_value=20, step=1)
                genres = data[movies.index(select_movie)]
                test_points = genres
                table = KNN_Movie_Recommender(test_points, no_of_reco + 1)
                table.pop(0)
                c = 0
                st.success('Some of the movies from our Recommendation, have a look below')
                for movie, link, ratings in table:
                    c += 1
                    st.markdown(f"({c})[ {movie}]({link})")
                    movie_poster_fetcher(link)
                    director, story, total_rat = get_movie_info(link)
                    st.markdown(director)
                    st.markdown(story)
                    st.markdown(total_rat)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')
    elif cat_op == category[2]:
        sel_gen = st.multiselect('Select Genres:', genres)
        dec = st.radio("Want to Fetch Movie Poster?", ('Yes', 'No'))
        st.markdown(
            '''<h4 style='text-align: left; color: #d73b5c;'>Fetching a Movie Posters will take a time.</h4>''',
            unsafe_allow_html=True)
        if dec == 'No':
            if sel_gen:
                imdb_score = st.slider('Choose IMDb score:', 1, 10, 8)
                no_of_reco = st.number_input('Number of movies:', min_value=5, max_value=20, step=1)
                test_point = [1 if genre in sel_gen else 0 for genre in genres]
                test_point.append(imdb_score)
                table = KNN_Movie_Recommender(test_point, no_of_reco)
                c = 0
                st.success('Some of the movies from our Recommendation, have a look below')
                for movie, link, ratings in table:
                    c += 1
                    st.markdown(f"({c})[ {movie}]({link})")
                    director, story, total_rat = get_movie_info(link)
                    st.markdown(director)
                    st.markdown(story)
                    st.markdown(total_rat)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')
        else:
            if sel_gen:
                imdb_score = st.slider('Choose IMDb score:', 1, 10, 8)
                no_of_reco = st.number_input('Number of movies:', min_value=5, max_value=20, step=1)
                test_point = [1 if genre in sel_gen else 0 for genre in genres]
                test_point.append(imdb_score)
                table = KNN_Movie_Recommender(test_point, no_of_reco)
                c = 0
                st.success('Some of the movies from our Recommendation, have a look below')
                for movie, link, ratings in table:
                    c += 1
                    st.markdown(f"({c})[ {movie}]({link})")
                    movie_poster_fetcher(link)
                    director, story, total_rat = get_movie_info(link)
                    st.markdown(director)
                    st.markdown(story)
                    st.markdown(total_rat)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')

run()
