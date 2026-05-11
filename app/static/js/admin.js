// ─── Admin Panel JavaScript ───────────────────────────

// Sidebar toggle (mobile)
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');
if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });
  // Close sidebar on outside click
  document.addEventListener('click', e => {
    if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

// ─── Frame Toggle (activate/deactivate) ──────────────
document.querySelectorAll('.toggle-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const frameId = btn.dataset.frameId;
    const csrfToken = document.querySelector('meta[name=csrf-token]')?.content
      || document.querySelector('input[name=csrf_token]')?.value || '';

    try {
      const res = await fetch(`/admin/frames/${frameId}/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        }
      });
      const data = await res.json();
      if (data.success) {
        // Update badge
        const card = document.getElementById(`admin-frame-${frameId}`);
        if (card) {
          const badge = card.querySelector('.frame-admin-status-badge .badge');
          if (badge) {
            badge.textContent = data.is_active ? 'Aktif' : 'Nonaktif';
            badge.className = `badge ${data.is_active ? 'badge-green' : 'badge-gray'}`;
          }
        }
        btn.textContent = data.is_active ? 'Nonaktifkan' : 'Aktifkan';
        btn.dataset.isActive = String(data.is_active);
        showAdminToast(data.message, 'success');
      }
    } catch (e) {
      showAdminToast('Terjadi kesalahan.', 'danger');
    }
  });
});

// ─── Admin Toast ──────────────────────────────────────
function showAdminToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:999;max-width:360px;animation:none';
  toast.innerHTML = `
    ${type === 'success' ? '✅' : '❌'} ${message}
    <button onclick="this.parentElement.remove()" style="margin-left:auto;background:none;border:none;cursor:pointer;color:inherit;font-size:1.2rem">×</button>
  `;
  document.body.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 400); }, 4000);
}

// ─── Auto-dismiss flash alerts ────────────────────────
document.querySelectorAll('.admin-alerts .alert').forEach(alert => {
  setTimeout(() => {
    alert.style.opacity = '0';
    alert.style.transition = 'opacity 0.4s';
    setTimeout(() => alert.remove(), 400);
  }, 5000);
});
