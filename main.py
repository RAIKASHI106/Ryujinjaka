import os
import json
import requests
import re
import zipfile
import io
from flask import Flask, render_template, abort, request, send_from_directory, jsonify, make_response

app = Flask(__name__)

# CONFIGURATION
MEDIA_FOLDER = 'Media'
TMDB_API_KEY = 'b1cfd8833332e9364b059105e2b79d16'
BASE_IMG_URL = "https://image.tmdb.org/t/p/w500"
BASE_BACKDROP_URL = "https://image.tmdb.org/t/p/original"
MANGA_FOLDER = 'Manga'
BASE_MANGA_API_URL = "https://graphql.anilist.co"

# --- HELPER FUNCTIONS ---

def get_movie_data(folder_name):
    search_query = folder_name.replace('_', ' ').replace('.', ' ')
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={search_query}"
    try:
        response = requests.get(url).json()
        result = response['results'][0] if response.get('results') else {}
        folder_path = os.path.join(MEDIA_FOLDER, folder_name)
        videos = []
        if os.path.exists(folder_path):
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(('.mkv', '.mp4', '.webm', '.avi')):
                        rel_path = os.path.relpath(os.path.join(root, file), MEDIA_FOLDER)
                        videos.append({"title": file, "url": f"/stream/{rel_path.replace(os.sep, '/')}", "type": "local"})
        videos.sort(key=lambda x: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', x['title'])])
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
    except: return None

def get_manga_data(folder_name):
    query = """
    query ($search: String, $format: [MediaFormat]) {
        Media(search: $search, type: MANGA, format_in: $format, sort: SEARCH_MATCH) {
            title { english romaji }
            description
            bannerImage
            coverImage { extraLarge }
        }
    }
    """
    search_term = folder_name.replace('_', ' ').replace('.', ' ')
    try:
        variables = {"search": search_term, "format": ["MANGA"]}
        response = requests.post(BASE_MANGA_API_URL, json={"query": query, "variables": variables})
        media = response.json().get("data", {}).get("Media", {})
        if media:
            return {
                "title": media.get("title", {}).get("english") or media.get("title", {}).get("romaji") or folder_name,
                "poster": media.get("coverImage", {}).get("extraLarge", ""),
                "backdrop": media.get("bannerImage") or media.get("coverImage", {}).get("extraLarge", ""),
                "overview": media.get("description", "No description available."),
                "folder_name": folder_name
            }
    except: pass
    return {"title": folder_name, "poster": "", "backdrop": "", "overview": "No metadata found.", "folder_name": folder_name}

# --- ROUTES ---

@app.route('/')
def home():
    movie_list = [get_movie_data(f) for f in os.listdir(MEDIA_FOLDER) if os.path.isdir(os.path.join(MEDIA_FOLDER, f))]
    return render_template('index.html', movies=[m for m in movie_list if m])

@app.route('/manga')
def manga():
    manga_list = [get_manga_data(f) for f in os.listdir(MANGA_FOLDER) if os.path.isdir(os.path.join(MANGA_FOLDER, f)) and not f.startswith('.')]
    return render_template('manga.html', mangas=manga_list)

@app.route('/manga_reader')
def manga_reader():
    folder_name = request.args.get('folder')
    chapter_file = request.args.get('chapter') # e.g. "chapter3.cbz"
    
    manga_path = os.path.join(MANGA_FOLDER, folder_name)
    if not os.path.exists(manga_path): abort(404)
    
    # Get all .cbz files in the series folder
    chapters = sorted([f for f in os.listdir(manga_path) if f.lower().endswith('.cbz')])
    if not chapters: return "No .cbz files found in this folder."
    
    # Default to first chapter if none specified
    if not chapter_file or chapter_file not in chapters:
        chapter_file = chapters[0]
    
    current_idx = chapters.index(chapter_file)
    prev_chapter = chapters[current_idx - 1] if current_idx > 0 else None
    next_chapter = chapters[current_idx + 1] if current_idx < len(chapters) - 1 else None

    # Open zip and list images
    image_names = []
    cbz_path = os.path.join(manga_path, chapter_file)
    with zipfile.ZipFile(cbz_path, 'r') as archive:
        image_names = sorted([n for n in archive.namelist() if n.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])

    return render_template('manga_reader.html', 
                           series=folder_name, 
                           current_chapter=chapter_file,
                           chapters=chapters,
                           image_names=image_names,
                           prev_chapter=prev_chapter,
                           next_chapter=next_chapter)

@app.route('/manga_page/<series>/<chapter>/<path:imagename>')
def serve_cbz_image(series, chapter, imagename):
    """Extracts a single image from a .cbz on the fly."""
    cbz_path = os.path.join(MANGA_FOLDER, series, chapter)
    try:
        with zipfile.ZipFile(cbz_path, 'r') as archive:
            with archive.open(imagename) as file:
                img_data = file.read()
                response = make_response(img_data)
                ext = imagename.split('.')[-1].lower()
                response.headers.set('Content-Type', f'image/{ext}')
                return response
    except Exception as e:
        abort(404)

@app.route('/video_player')
def video_player():
    folder_name = request.args.get('folder')
    movie_meta = get_movie_data(folder_name)
    return render_template('video_player.html', videos=movie_meta['videos'], movie=movie_meta, default_index=0)

@app.route('/stream/<path:filename>')
def stream_video(filename):
    return send_from_directory(MEDIA_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)