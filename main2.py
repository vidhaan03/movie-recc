import streamlit as st
import streamlit_option_menu
from streamlit_extras.stoggle import stoggle
from processing import preprocess
from processing.display import Main
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("/Users/vidhandubey/Downloads/moviemind-549bc-firebase-adminsdk-fbsvc-6361cc0613.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Streamlit setup
st.set_page_config(layout="wide")

# Session states
if 'movie_number' not in st.session_state:
    st.session_state['movie_number'] = 0
if 'selected_movie_name' not in st.session_state:
    st.session_state['selected_movie_name'] = ""
if 'user_menu' not in st.session_state:
    st.session_state['user_menu'] = ""
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = ""
if 'data_loaded' not in st.session_state:
    st.session_state['data_loaded'] = False
if 'new_df' not in st.session_state:
    st.session_state['new_df'] = None
if 'movies' not in st.session_state:
    st.session_state['movies'] = None
if 'movies2' not in st.session_state:
    st.session_state['movies2'] = None

displayed = []

# Authentication functions
def login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        user_ref = db.collection("users").document(email).get()
        if user_ref.exists and user_ref.to_dict()["password"] == password:
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = email
            st.success("Login successful!")
        else:
            st.error("Invalid email or password.")

def signup():
    st.title("Signup")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    signup_button = st.button("Signup")

    if signup_button:
        user_ref = db.collection("users").document(email).get()
        if user_ref.exists:
            st.error("Email already registered. Please log in.")
        else:
            db.collection("users").document(email).set({"password": password})
            st.success("Signup successful! Please log in.")

# Movie Functions
def recommendation_tags(new_df, selected_movie_name, pickle_file_path, label):
    movies, posters = preprocess.recommend(new_df, selected_movie_name, pickle_file_path)
    st.subheader(f'Best Recommendations {label}...')

    rec_movies, rec_posters = [], []
    cnt = 0
    for i, j in enumerate(movies):
        if cnt == 5:
            break
        if j not in displayed:
            rec_movies.append(j)
            rec_posters.append(posters[i])
            displayed.append(j)
            cnt += 1

    col1, col2, col3, col4, col5 = st.columns(5)
    for idx, (name, poster) in enumerate(zip(rec_movies, rec_posters)):
        with [col1, col2, col3, col4, col5][idx]:
            st.text(name)
            st.image(poster)

def recommend_display():
    st.title('MovieMinds🎥')
    selected_movie_name = st.selectbox('Select a Movie...', st.session_state['new_df']['title'].values)
    if st.button('Recommend'):
        st.session_state['selected_movie_name'] = selected_movie_name
        recommendation_tags(st.session_state['new_df'], selected_movie_name, r'Files/similarity_tags_tags.pkl', "are")
        recommendation_tags(st.session_state['new_df'], selected_movie_name, r'Files/similarity_tags_genres.pkl', "on the basis of genres are")
        recommendation_tags(st.session_state['new_df'], selected_movie_name, r'Files/similarity_tags_tprduction_comp.pkl', "from the same production company are")
        recommendation_tags(st.session_state['new_df'], selected_movie_name, r'Files/similarity_tags_keywords.pkl', "on the basis of keywords are")
        recommendation_tags(st.session_state['new_df'], selected_movie_name, r'Files/similarity_tags_tcast.pkl', "on the basis of cast are")

def display_movie_details():
    selected_movie_name = st.session_state['selected_movie_name']
    info = preprocess.get_details(selected_movie_name)
    image_col, text_col = st.columns((1, 2))
    with image_col:
        st.image(info[0])
    with text_col:
        st.title(selected_movie_name)
        col1, col2, col3 = st.columns(3)
        with col1: st.write("Rating:", info[8])
        with col2: st.write("No. of ratings:", info[9])
        with col3: st.write("Runtime:", info[6])
        st.write("Overview:", info[3])
        col1, col2, col3 = st.columns(3)
        with col1: st.write("Release Date:", info[4])
        with col2: st.write("Budget:", info[1])
        with col3: st.write("Revenue:", info[5])
        col1, col2, col3 = st.columns(3)
        with col1: st.write("Genres:", " . ".join(info[2]))
        with col2: st.write("Available in:", " . ".join(info[13]))
        with col3: st.write("Directed by:", info[12][0])

    st.header('Cast')
    urls, bios = [], []
    for i in info[14][:5]:
        url, bio = preprocess.fetch_person_details(i)
        urls.append(url)
        bios.append(bio)
    cols = st.columns(5)
    for i in range(len(urls)):
        with cols[i]:
            st.image(urls[i])
            stoggle("Show More", bios[i])

def display_all_movies(start):
    i = start
    cols = st.columns(5)
    for _ in range(2):  # display 10 posters, 5 per row
        for col in cols:
            if i >= len(st.session_state['movies']):
                break
            movie = st.session_state['movies'].iloc[i]
            id = movie['movie_id']
            link = preprocess.fetch_posters(id)
            with col:
                st.image(link, caption=movie['title'])
            i += 1

def paging_movies():
    max_pages = len(st.session_state['movies']) // 10
    col1, col2, col3 = st.columns([1, 9, 1])
    with col1:
        if st.button("Prev") and st.session_state['movie_number'] >= 10:
            st.session_state['movie_number'] -= 10
    with col2:
        page = st.slider("Jump to page", 0, max_pages, st.session_state['movie_number'] // 10)
        st.session_state['movie_number'] = page * 10
    with col3:
        if st.button("Next") and st.session_state['movie_number'] + 10 < len(st.session_state['movies']):
            st.session_state['movie_number'] += 10
    display_all_movies(st.session_state['movie_number'])

def initial_options():
    st.session_state.user_menu = streamlit_option_menu.option_menu(
        menu_title='What are you looking for? 👀',
        options=['Recommend me a similar movie', 'Describe me a movie', 'Check all Movies'],
        icons=['film', 'info-circle', 'grid'],
        menu_icon='list',
        orientation="horizontal",
    )
    if st.session_state.user_menu == 'Recommend me a similar movie':
        recommend_display()
    elif st.session_state.user_menu == 'Describe me a movie':
        display_movie_details()
    elif st.session_state.user_menu == 'Check all Movies':
        paging_movies()

# Main function
def main():
    if not st.session_state['logged_in']:
        auth_menu = st.sidebar.radio("Authentication", ["Login", "Signup"])
        if auth_menu == "Login":
            login()
        else:
            signup()
    else:
        if not st.session_state['data_loaded']:
            with Main() as bot:
                bot.main_()
                new_df, movies, movies2 = bot.getter()
                st.session_state['new_df'] = new_df
                st.session_state['movies'] = movies
                st.session_state['movies2'] = movies2
                st.session_state['data_loaded'] = True
        initial_options()

if __name__ == '__main__':
    main()
