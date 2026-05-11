import os
import json
from flask import (Blueprint, render_template, request, jsonify,
                   send_file, abort, current_app, url_for)
from werkzeug.utils import secure_filename
from app import limiter
from app.models.frame import Frame, Category
from app.services.image_processor import (
    allowed_file, check_image_header, generate_twibbon, generate_unique_filename,
    schedule_file_deletion, cleanup_old_results
)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Halaman utama — galeri frame twibbon."""
    category_slug = request.args.get('category', None)
    search_query = request.args.get('q', '').strip()

    query = Frame.query.filter_by(is_active=True)

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if search_query:
        query = query.filter(Frame.name.ilike(f'%{search_query}%'))

    frames = query.order_by(Frame.download_count.desc()).all()
    categories = Category.query.all()

    return render_template('index.html',
                           frames=frames,
                           categories=categories,
                           active_category=category_slug,
                           search_query=search_query)


@main_bp.route('/frame/<int:frame_id>')
def frame_editor(frame_id):
    """Halaman editor twibbon untuk frame tertentu."""
    frame = Frame.query.get_or_404(frame_id)
    if not frame.is_active:
        abort(404)
    return render_template('editor.html', frame=frame)


@main_bp.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload_photo():
    """Upload foto pengguna, simpan sementara di folder temp."""
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'Tidak ada file yang dikirim.'}), 400

    file = request.files['photo']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'Nama file kosong.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Format file tidak didukung. Gunakan JPG, PNG, atau WEBP.'}), 400

    if not check_image_header(file.stream):
        return jsonify({'success': False, 'error': 'File gambar rusak atau tidak valid.'}), 400

    # Check file size (Flask handles MAX_CONTENT_LENGTH but we double-check)
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > current_app.config['MAX_CONTENT_LENGTH']:
        return jsonify({'success': False, 'error': 'Ukuran file melebihi batas 5 MB.'}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = generate_unique_filename(prefix='upload', extension=ext)
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
    filepath = os.path.join(temp_dir, filename)
    file.save(filepath)

    # Schedule deletion after 1 hour
    schedule_file_deletion(filepath, delay_seconds=3600)

    return jsonify({
        'success': True,
        'filename': filename,
        'preview_url': url_for('static', filename=f'uploads/temp/{filename}')
    })


@main_bp.route('/generate', methods=['POST'])
@limiter.limit("5 per minute")
def generate():
    """Proses overlay foto dengan frame, kembalikan URL hasil."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Data tidak valid.'}), 400

    photo_filename = data.get('photo_filename')
    frame_id = data.get('frame_id')
    transform = data.get('transform')  # {x, y, scale}

    if not photo_filename or not frame_id:
        return jsonify({'success': False, 'error': 'Data tidak lengkap.'}), 400

    # Validate frame
    frame = Frame.query.get(frame_id)
    if not frame or not frame.is_active:
        return jsonify({'success': False, 'error': 'Frame tidak ditemukan.'}), 404

    # Build paths
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
    results_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'results')
    frames_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'frames')

    # Sanitize photo filename
    safe_photo = secure_filename(photo_filename)
    photo_path = os.path.join(temp_dir, safe_photo)

    if not os.path.exists(photo_path):
        return jsonify({'success': False, 'error': 'Foto tidak ditemukan. Silakan upload ulang.'}), 404

    frame_path = os.path.join(frames_dir, frame.filename)
    if not os.path.exists(frame_path):
        return jsonify({'success': False, 'error': 'File frame tidak tersedia.'}), 500

    try:
        # Clean up old results
        cleanup_old_results(results_dir, max_age_minutes=current_app.config['RESULT_EXPIRY_MINUTES'])

        # Generate twibbon
        output_filename = generate_twibbon(
            photo_path, frame_path, results_dir, 
            frame_name=frame.name, transform=transform
        )

        # Increment download count
        frame.increment_download()

        result_url = url_for('static', filename=f'uploads/results/{output_filename}')
        download_url = url_for('main.download', filename=output_filename)

        return jsonify({
            'success': True,
            'result_url': result_url,
            'download_url': download_url,
            'filename': output_filename
        })
    except Exception as e:
        current_app.logger.error(f'Error generating twibbon: {e}')
        return jsonify({'success': False, 'error': 'Gagal memproses gambar. Silakan coba lagi.'}), 500


@main_bp.route('/download/<path:filename>')
def download(filename):
    """Unduh gambar hasil twibbon."""
    results_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'results')
    safe_filename = secure_filename(filename)
    filepath = os.path.join(results_dir, safe_filename)

    if not os.path.exists(filepath):
        abort(404)

    return send_file(filepath,
                     mimetype='image/png',
                     as_attachment=True,
                     download_name=safe_filename)
