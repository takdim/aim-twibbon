import os
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, abort, current_app, jsonify)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from app import db, limiter
from app.models.user import AdminUser
from app.models.frame import Frame, Category

admin_bp = Blueprint('admin', __name__)

FRAME_ALLOWED_EXTENSIONS = {'png'}


def frame_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in FRAME_ALLOWED_EXTENSIONS


# ─── Auth ────────────────────────────────────────────────────────────────────

@admin_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Selamat datang, {user.username}!', 'success')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Username atau password salah.', 'danger')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('admin.login'))


# ─── Dashboard ───────────────────────────────────────────────────────────────

@admin_bp.route('/')
@login_required
def dashboard():
    total_frames = Frame.query.count()
    active_frames = Frame.query.filter_by(is_active=True).count()
    total_downloads = db.session.query(db.func.sum(Frame.download_count)).scalar() or 0
    total_categories = Category.query.count()

    top_frames = Frame.query.filter_by(is_active=True)\
        .order_by(Frame.download_count.desc()).limit(5).all()
    recent_frames = Frame.query.order_by(Frame.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           total_frames=total_frames,
                           active_frames=active_frames,
                           total_downloads=total_downloads,
                           total_categories=total_categories,
                           top_frames=top_frames,
                           recent_frames=recent_frames)


# ─── Frame Management ────────────────────────────────────────────────────────

@admin_bp.route('/frames')
@login_required
def frames():
    all_frames = Frame.query.order_by(Frame.created_at.desc()).all()
    categories = Category.query.all()
    return render_template('admin/frames.html', frames=all_frames, categories=categories)


@admin_bp.route('/frames/add', methods=['GET', 'POST'])
@login_required
def add_frame():
    categories = Category.query.all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id') or None
        is_active = bool(request.form.get('is_active'))
        active_from_str = request.form.get('active_from', '').strip()
        active_until_str = request.form.get('active_until', '').strip()

        if not name:
            flash('Nama frame wajib diisi.', 'danger')
            return render_template('admin/frame_form.html', categories=categories)

        if 'frame_file' not in request.files or request.files['frame_file'].filename == '':
            flash('File frame wajib diunggah.', 'danger')
            return render_template('admin/frame_form.html', categories=categories)

        file = request.files['frame_file']
        if not frame_allowed_file(file.filename):
            flash('Hanya file PNG yang diperbolehkan untuk frame.', 'danger')
            return render_template('admin/frame_form.html', categories=categories)

        filename = secure_filename(file.filename)
        # Make filename unique
        import time
        base, ext = os.path.splitext(filename)
        filename = f"{base}_{int(time.time())}{ext}"
        frames_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'frames')
        file.save(os.path.join(frames_dir, filename))

        active_from = None
        active_until = None
        if active_from_str:
            try:
                active_from = datetime.strptime(active_from_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                pass
        if active_until_str:
            try:
                active_until = datetime.strptime(active_until_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                pass

        frame = Frame(
            name=name,
            description=description,
            filename=filename,
            category_id=int(category_id) if category_id else None,
            is_active=is_active,
            active_from=active_from,
            active_until=active_until
        )
        db.session.add(frame)
        db.session.commit()
        flash(f'Frame "{name}" berhasil ditambahkan.', 'success')
        return redirect(url_for('admin.frames'))

    return render_template('admin/frame_form.html', categories=categories, frame=None)


@admin_bp.route('/frames/<int:frame_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_frame(frame_id):
    frame = Frame.query.get_or_404(frame_id)
    categories = Category.query.all()

    if request.method == 'POST':
        frame.name = request.form.get('name', '').strip()
        frame.description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id') or None
        frame.category_id = int(category_id) if category_id else None
        frame.is_active = bool(request.form.get('is_active'))

        active_from_str = request.form.get('active_from', '').strip()
        active_until_str = request.form.get('active_until', '').strip()
        if active_from_str:
            try:
                frame.active_from = datetime.strptime(active_from_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                frame.active_from = None
        else:
            frame.active_from = None
        if active_until_str:
            try:
                frame.active_until = datetime.strptime(active_until_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                frame.active_until = None
        else:
            frame.active_until = None

        # Optional: replace frame file
        if 'frame_file' in request.files and request.files['frame_file'].filename:
            file = request.files['frame_file']
            if frame_allowed_file(file.filename):
                import time
                # Delete old file
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'frames', frame.filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
                filename = secure_filename(file.filename)
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{int(time.time())}{ext}"
                frames_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'frames')
                file.save(os.path.join(frames_dir, filename))
                frame.filename = filename

        db.session.commit()
        flash(f'Frame "{frame.name}" berhasil diperbarui.', 'success')
        return redirect(url_for('admin.frames'))

    return render_template('admin/frame_form.html', frame=frame, categories=categories)


@admin_bp.route('/frames/<int:frame_id>/delete', methods=['POST'])
@login_required
def delete_frame(frame_id):
    frame = Frame.query.get_or_404(frame_id)
    # Delete file from disk
    frame_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'frames', frame.filename)
    if os.path.exists(frame_path):
        os.remove(frame_path)
    db.session.delete(frame)
    db.session.commit()
    flash(f'Frame "{frame.name}" berhasil dihapus.', 'success')
    return redirect(url_for('admin.frames'))


@admin_bp.route('/frames/<int:frame_id>/toggle', methods=['POST'])
@login_required
def toggle_frame(frame_id):
    frame = Frame.query.get_or_404(frame_id)
    frame.is_active = not frame.is_active
    db.session.commit()
    status = 'diaktifkan' if frame.is_active else 'dinonaktifkan'
    return jsonify({'success': True, 'is_active': frame.is_active, 'message': f'Frame {status}.'})


# ─── Category Management ──────────────────────────────────────────────────────

@admin_bp.route('/categories')
@login_required
def categories():
    all_cats = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=all_cats)


@admin_bp.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Nama kategori wajib diisi.', 'danger')
        return redirect(url_for('admin.categories'))
    slug = name.lower().replace(' ', '-')
    if Category.query.filter_by(slug=slug).first():
        flash('Kategori dengan nama tersebut sudah ada.', 'warning')
        return redirect(url_for('admin.categories'))
    cat = Category(name=name, slug=slug)
    db.session.add(cat)
    db.session.commit()
    flash(f'Kategori "{name}" berhasil ditambahkan.', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    # Unlink frames from this category
    Frame.query.filter_by(category_id=cat_id).update({'category_id': None})
    db.session.delete(cat)
    db.session.commit()
    flash(f'Kategori "{cat.name}" berhasil dihapus.', 'success')
    return redirect(url_for('admin.categories'))


# No setup route here for security. Use 'flask create-admin' instead.
