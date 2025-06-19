document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".token-card");
  cards.forEach(card => {
    card.classList.add("fade-in");
  });
});
