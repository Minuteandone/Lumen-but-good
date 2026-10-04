const video = document.querySelector("#episode");

video.addEventListener("play", () => {
  document.body.classList.add("watching");
});

video.addEventListener("pause", () => {
  document.body.classList.remove("watching");
});

document.addEventListener("keydown", (event) => {
  if (event.target.matches("input, textarea, select, button")) return;

  if (event.code === "Space") {
    event.preventDefault();
    video.paused ? video.play() : video.pause();
  }

  if (event.key === "ArrowLeft") {
    video.currentTime = Math.max(0, video.currentTime - 5);
  }

  if (event.key === "ArrowRight") {
    video.currentTime = Math.min(video.duration || Infinity, video.currentTime + 5);
  }
});