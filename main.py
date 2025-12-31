from flask import Flask, render_template, abort
import os
import json
import requests

app = Flask(__name__)

# CONFIGURATION
MEDIA_FOLDER = 'Media'
TMDB_API_KEY = 'b1cfd8833332e9364b059105e2b79d16'
BASE_IMG_URL = "https://image.tmdb.org/t/p/w500"
BASE_BACKDROP_URL = "https://image.tmdb.org/t/p/original"

def get_movie_data(folder_name):
    search_query = folder_name.replace('_', ' ').replace('.', ' ')
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={search_query}"
    
    try:
        response = requests.get(url).json()
        if response.get('results'):
            result = response['results'][0]
            folder_path = os.path.join(MEDIA_FOLDER, folder_name)
            external_videos = []

            # Use log.json if exists
            log_json_path = os.path.join(folder_path, 'log.json')
            if os.path.exists(log_json_path):
                with open(log_json_path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                    external_videos = data.get('videos', [])

            has_video = len(external_videos) > 0
            return {
                "title": result.get("title") or result.get("name"),
                "poster": BASE_IMG_URL + result.get("poster_path") if result.get("poster_path") else "",
                "backdrop": BASE_BACKDROP_URL + result.get("backdrop_path") if result.get("backdrop_path") else "",
                "overview": result.get("overview", "No description available.").replace('"', '&quot;'),
                "rating": round(result.get("vote_average", 0), 1),
                "folder_name": folder_name,
                "has_video": has_video,
                "external_videos": external_videos
            }
    except Exception as e:
        print(f"Error fetching data for {folder_name}: {e}")
    return None

@app.route('/')
def home():
    if not os.path.exists(MEDIA_FOLDER):
        os.makedirs(MEDIA_FOLDER)

    movie_list = []
    folders = [f for f in os.listdir(MEDIA_FOLDER) if os.path.isdir(os.path.join(MEDIA_FOLDER, f))]
    for folder in folders:
        data = get_movie_data(folder)
        if data:
            movie_list.append(data)
    return render_template('index.html', movies=movie_list)

@app.route('/player/<folder_name>')
def player(folder_name):
    folder_path = os.path.join(MEDIA_FOLDER, folder_name)
    if not os.path.exists(folder_path):
        abort(404)

    movie_meta = get_movie_data(folder_name) or {"title": folder_name, "poster": "", "backdrop": "", "overview": "", "external_videos": []}

    # Pass videos array to template
    videos = movie_meta.get('external_videos', [])
    return render_template('player.html', folder=folder_name, videos=videos, movie=movie_meta)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
