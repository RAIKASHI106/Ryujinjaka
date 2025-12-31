function getQueryParam(name) {
    return new URLSearchParams(window.location.search).get(name);
}

const folder = getQueryParam('folder');
document.body.dataset.folder = folder;

const player = document.getElementById('player');
const epList = document.getElementById('episodesList');

fetch(`Media/${folder}/log.json`)
  .then(res => res.json())
  .then(data => {
    const videos = data.videos || [];
    if(!videos.length) return;

    let currentIdx = 0;

    function loadVideo(idx) {
      currentIdx = idx;
      player.src = videos[idx].url;
      player.play();
      renderEpisodes();
    }

    function renderEpisodes() {
      epList.innerHTML = '';
      videos.forEach((v, i) => {
        const div = document.createElement('div');
        div.className = i === currentIdx ? 'item active' : 'item';
        div.innerText = v.name || `Episode ${i+1}`;
        div.onclick = () => loadVideo(i);
        epList.appendChild(div);
      });
    }

    loadVideo(0);
  });
