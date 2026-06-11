const menuButton = document.querySelector('.menu-button');
const sidebar = document.querySelector('.sidebar');
menuButton.addEventListener('click', () => {
  const open = sidebar.classList.toggle('open');
  menuButton.setAttribute('aria-expanded', String(open));
});

document.querySelectorAll('.sidebar a').forEach((link) => {
  link.addEventListener('click', () => sidebar.classList.remove('open'));
});

document.querySelectorAll('[data-copy-target]').forEach((button) => {
  button.addEventListener('click', async () => {
    const target = document.getElementById(button.dataset.copyTarget);
    await navigator.clipboard.writeText(target.innerText);
    const original = button.textContent;
    button.textContent = '已复制';
    setTimeout(() => { button.textContent = original; }, 1400);
  });
});

const sections = [...document.querySelectorAll('main [id]')];
const navLinks = [...document.querySelectorAll('.sidebar a')];
const observer = new IntersectionObserver((entries) => {
  const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
  if (!visible) return;
  navLinks.forEach((link) => link.classList.toggle('active', link.hash === `#${visible.target.id}`));
}, { rootMargin: '-20% 0px -65% 0px', threshold: [0, 0.2, 0.6] });
sections.forEach((section) => observer.observe(section));

