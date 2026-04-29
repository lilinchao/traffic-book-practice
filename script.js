const header = document.querySelector(".site-header");

window.addEventListener("scroll", () => {
  const elevated = window.scrollY > 12;
  header.style.boxShadow = elevated ? "0 10px 28px rgba(31, 48, 43, 0.08)" : "none";
});
