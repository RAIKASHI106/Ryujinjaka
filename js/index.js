const mediaRoot = 'Media'; // GitHub Pages root folder

// Hardcode your movie folders and metadata (or load from a JSON file)
const movies = [
  {
    folder: 'Movie_Folder_1',
    title: 'Movie 1',
    poster: 'Media/Movie_Folder_1/poster.jpg',
    backdrop: 'Media/Movie_Folder_1/backdrop.jpg',
    overview: 'Description for Movie 1'
  },
  {
    folder: 'Movie_Folder_2',
    title: 'Movie 2',
    poster: 'Media/Movie_Folder_2/poster.jpg',
    backdrop: 'Media/Movie_Folder_2/backdrop.jpg',
    overview: 'Description for Movie 2'
  }
];

const grid = document.getElementById('movieGrid');
movies.forEach(m => {
  const div = document.createElement('div');
  div.className = 'movie-card';
  div.innerHTML = `<img src="${m.poster}" alt="${m.title}">`;
  div.onclick = () => window.location.href = `player.html?folder=${m.folder}`;
  grid.appendChild(div);
});
