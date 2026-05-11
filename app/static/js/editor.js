/* ─── Editor JavaScript ─────────────────────────────── */
(function () {
  'use strict';

  const cfg = window.TWIBBON_DATA;
  if (!cfg) { console.error('TWIBBON_DATA not set'); return; }

  // DOM refs
  const uploadArea       = document.getElementById('upload-area');
  const photoInput       = document.getElementById('photo-input');
  const uploadPlaceholder= document.getElementById('upload-placeholder');
  const uploadPreview    = document.getElementById('upload-preview');
  const changePhotoBtn   = document.getElementById('change-photo-btn');

  const generateBtn      = document.getElementById('generate-btn');
  const generateLabel    = document.getElementById('generate-label');
  const generateLoader   = document.getElementById('generate-loader');
  const generateNote     = document.getElementById('generate-note');

  const downloadActions  = document.getElementById('download-actions');
  const downloadBtn      = document.getElementById('download-btn');
  const makeAnotherBtn   = document.getElementById('make-another-btn');
  const step3Note        = document.getElementById('step3-note');

  const canvasWrap      = document.getElementById('canvas-wrap');
  const canvasEmpty      = document.getElementById('canvas-empty');
  const canvasPhoto      = document.getElementById('canvas-photo');
  const canvasResult     = document.getElementById('canvas-result');
  const editorControls   = document.getElementById('editor-controls');
  const zoomSlider       = document.getElementById('zoom-slider');

  const badge1 = document.getElementById('badge-1');
  const badge2 = document.getElementById('badge-2');
  const badge3 = document.getElementById('badge-3');
  const step2Panel = document.getElementById('step-2-panel');
  const step3Panel = document.getElementById('step-3-panel');

  let currentPhotoFilename = null;
  const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

  // ─── Interaction State ─────────────────────────────
  let state = {
    scale: 1,
    x: 0,
    y: 0,
    isDragging: false,
    startX: 0,
    startY: 0
  };

  function updateTransform() {
    canvasPhoto.style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
  }

  // ─── Drag Logic ────────────────────────────────────
  canvasWrap.addEventListener('mousedown', e => {
    if (!currentPhotoFilename || canvasResult.classList.contains('hidden') === false) return;
    state.isDragging = true;
    state.startX = e.clientX - state.x;
    state.startY = e.clientY - state.y;
  });

  window.addEventListener('mousemove', e => {
    if (!state.isDragging) return;
    state.x = e.clientX - state.startX;
    state.y = e.clientY - state.startY;
    updateTransform();
  });

  window.addEventListener('mouseup', () => state.isDragging = false);

  // ─── Zoom Logic ────────────────────────────────────
  zoomSlider.addEventListener('input', () => {
    state.scale = parseFloat(zoomSlider.value);
    updateTransform();
  });

  // ─── Step helpers ──────────────────────────────────
  function unlockStep(panel, badge) {
    panel.classList.remove('step-panel-locked');
    badge.classList.add('active');
  }
  function markDone(badge) {
    badge.classList.add('done');
  }

  // ─── Upload Flow ───────────────────────────────────
  uploadArea.addEventListener('click', () => photoInput.click());

  uploadArea.addEventListener('dragover', e => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
  });
  uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
  uploadArea.addEventListener('drop', e => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  photoInput.addEventListener('change', () => {
    if (photoInput.files[0]) handleFile(photoInput.files[0]);
  });

  changePhotoBtn.addEventListener('click', () => {
    photoInput.value = '';
    photoInput.click();
  });

  function handleFile(file) {
    // Validate type
    const allowed = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowed.includes(file.type)) {
      showToast('Format file tidak didukung. Gunakan JPG, PNG, atau WEBP.', 'danger');
      return;
    }
    // Validate size
    if (file.size > MAX_FILE_SIZE) {
      showToast('Ukuran file melebihi batas 5 MB.', 'danger');
      return;
    }

    // Show local preview immediately
    const reader = new FileReader();
    reader.onload = e => {
      canvasPhoto.src = e.target.result;
      canvasPhoto.classList.remove('hidden');
      canvasEmpty.style.display = 'none';
      
      uploadPreview.src = e.target.result;
      uploadPreview.classList.remove('hidden');
      uploadPlaceholder.classList.add('hidden');
      changePhotoBtn.style.display = '';
      editorControls.classList.remove('hidden');
      
      // Reset transform state
      state = { scale: 1, x: 0, y: 0, isDragging: false, startX: 0, startY: 0 };
      zoomSlider.value = 1;

      // Wait for image to load to set initial size matching backend "fit" logic
      canvasPhoto.onload = () => {
        const wrapWidth = canvasWrap.offsetWidth;
        const imgAspect = canvasPhoto.naturalWidth / canvasPhoto.naturalHeight;
        
        if (imgAspect > 1) {
          // Wide image: set height to 100% and width auto
          canvasPhoto.style.height = wrapWidth + 'px';
          canvasPhoto.style.width = 'auto';
        } else {
          // Tall or square: set width to 100% and height auto
          canvasPhoto.style.width = wrapWidth + 'px';
          canvasPhoto.style.height = 'auto';
        }
        updateTransform();
      };
    };
    reader.readAsDataURL(file);

    // Upload to server
    uploadToServer(file);
  }

  function uploadToServer(file) {
    generateBtn.disabled = true;
    generateNote.textContent = 'Mengunggah foto…';

    const formData = new FormData();
    formData.append('photo', file);

    fetch(cfg.uploadUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': cfg.csrfToken },
      body: formData
    })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        currentPhotoFilename = data.filename;
        generateBtn.disabled = false;
        generateNote.textContent = 'Foto berhasil diunggah. Atur posisi lalu klik tombol!';
        unlockStep(step2Panel, badge2);
        markDone(badge1);
      } else {
        showToast(data.error || 'Gagal mengunggah foto.', 'danger');
        generateNote.textContent = 'Upload foto terlebih dahulu.';
      }
    })
    .catch(() => {
      showToast('Terjadi kesalahan jaringan. Coba lagi.', 'danger');
      generateNote.textContent = 'Upload foto terlebih dahulu.';
    });
  }

  // ─── Generate Flow ─────────────────────────────────
  generateBtn.addEventListener('click', () => {
    if (!currentPhotoFilename) return;

    // UI loading state
    generateLabel.classList.add('hidden');
    generateLoader.classList.remove('hidden');
    generateBtn.disabled = true;

    // Calculate relative transform for backend
    // Backend uses 1000x1000. Frontend preview is canvasWrap.offsetWidth
    const displaySize = canvasWrap.offsetWidth;
    const ratio = 1000 / displaySize;

    fetch(cfg.generateUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': cfg.csrfToken
      },
      body: JSON.stringify({
        photo_filename: currentPhotoFilename,
        frame_id: cfg.frameId,
        transform: {
          x: state.x * ratio,
          y: state.y * ratio,
          scale: state.scale
        }
      })
    })
    .then(r => r.json())
    .then(data => {
      generateLabel.classList.remove('hidden');
      generateLoader.classList.add('hidden');

      if (data.success) {
        // Show result on canvas
        canvasResult.src = data.result_url;
        canvasResult.classList.remove('hidden');

        // Setup download
        downloadBtn.href = data.download_url;
        downloadBtn.download = data.filename || 'twibbon.png';

        // Setup WhatsApp share (share result URL)
        const waBtn = document.getElementById('share-wa-btn');
        if (waBtn) {
          const shareText = encodeURIComponent(`Yuk buat twibbon bareng!\n${window.location.href}`);
          waBtn.onclick = () => window.open(`https://wa.me/?text=${shareText}`, '_blank');
          waBtn.style.display = '';
        }

        // Unlock step 3
        unlockStep(step3Panel, badge3);
        markDone(badge2);
        downloadActions.style.display = '';
        step3Note.style.display = 'none';

        showToast('Twibbon berhasil dibuat! 🎉', 'success');
      } else {
        generateBtn.disabled = false;
        showToast(data.error || 'Gagal membuat twibbon.', 'danger');
      }
    })
    .catch(() => {
      generateLabel.classList.remove('hidden');
      generateLoader.classList.add('hidden');
      generateBtn.disabled = false;
      showToast('Terjadi kesalahan. Coba lagi.', 'danger');
    });
  });

  // ─── Make Another ──────────────────────────────────
  if (makeAnotherBtn) {
    makeAnotherBtn.addEventListener('click', () => window.location.reload());
  }

  // ─── Toast Notification ────────────────────────────
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:999;max-width:360px;animation:slideDown 0.3s ease';
    toast.innerHTML = `
      <span>${type === 'success' ? '✅' : type === 'danger' ? '❌' : 'ℹ️'}</span>
      <span>${message}</span>
      <button onclick="this.parentElement.remove()" style="margin-left:auto;background:none;border:none;cursor:pointer;color:inherit;font-size:1.1rem">×</button>
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.4s ease';
      setTimeout(() => toast.remove(), 400);
    }, 5000);
  }
})();
