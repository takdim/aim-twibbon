// ─── Navbar scroll effect ──────────────────────────────
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.style.boxShadow = window.scrollY > 20 ? '0 2px 20px rgba(0,0,0,0.5)' : '';
  }, { passive: true });
}

// ─── Auto-dismiss flash messages ──────────────────────
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.opacity = '0';
    alert.style.transition = 'opacity 0.4s ease';
    setTimeout(() => alert.remove(), 400);
  }, 5000);
});
