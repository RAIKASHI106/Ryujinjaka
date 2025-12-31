import os
import json
import requests
import re
from flask import Flask, render_template, abort, request, send_from_directory, jsonify

app = Flask(__name__)

# CONFIGURATION
MEDIA_FOLDER = 'Media'
TMDB_API_KEY = 'b1cfd8833332e9364b059105e2b79d16'
BASE_IMG_URL = "https://image.tmdb.org/t/p/w500"
BASE_BACKDROP_URL = "https://image.tmdb.org/t/p/original"

def get_movie_data(folder_name):
    """Fetches metadata from TMDB and checks for both external and local videos."""
    search_query = folder_name.replace('_', ' ').replace('.', ' ')
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={search_query}"
    
    try:
        response = requests.get(url).json()
        result = response['results'][0] if response.get('results') else {}
        
        folder_path = os.path.join(MEDIA_FOLDER, folder_name)
        videos = []

        # 1. Check for Local Files (Dynamic Scanning)
        if os.path.exists(folder_path):
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(('.mkv', '.mp4', '.webm', '.avi')):
                        # Create relative path for the serving route
                        rel_path = os.path.relpath(os.path.join(root, file), MEDIA_FOLDER)
                        videos.append({
                            "title": file,
                            "url": f"/stream/{rel_path.replace(os.sep, '/')}",
                            "type": "local"
                        })

        # 2. Check for External Links (log.json)
        log_json_path = os.path.join(folder_path, 'log.json')
        if os.path.exists(log_json_path):
            with open(log_json_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                for v in data.get('videos', []):
                    url = v.get('url') if isinstance(v, dict) else v
                    title = v.get('title') if isinstance(v, dict) else os.path.basename(url)
                    if "drive.google.com" in url:
                        match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
                        if match:
                            file_id = match.group(1)
                            url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    videos.append({"title": title, "url": url, "type": "external"})

        # 3. Numerical Sort for all gathered videos
        def extract_number(v_obj):
            nums = re.findall(r'\d+', v_obj['title'])
            return int(nums[0]) if nums else 999

        videos.sort(key=extract_number)

        return {
            "title": result.get("title") or result.get("name") or folder_name,
            "poster": BASE_IMG_URL + result.get("poster_path") if result.get("poster_path") else "",
            "backdrop": BASE_BACKDROP_URL + result.get("backdrop_path") if result.get("backdrop_path") else "",
            "overview": result.get("overview", "No description available.").replace('"', '&quot;'),
            "rating": round(result.get("vote_average", 0), 1),
            "folder_name": folder_name,
            "has_video": len(videos) > 0,
            "videos": videos
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

@app.route('/video_player')
def video_player():
    folder_name = request.args.get('folder')
    if not folder_name:
        abort(404)

    movie_meta = get_movie_data(folder_name)
    if not movie_meta:
        abort(404)

    # Automatically identify episode 1 to be the default video
    default_index = 0
    for i, v in enumerate(movie_meta['videos']):
        if '01' in v['title'] or ' 1 ' in v['title']:
            default_index = i
            break

    return render_template('video_player.html', 
                           folder=folder_name, 
                           videos=movie_meta['videos'], 
                           movie=movie_meta,
                           default_index=default_index)

@app.route('/stream/<path:filename>')
def stream_video(filename):
    """Serves local video files from the Media folder."""
    return send_from_directory(MEDIA_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)