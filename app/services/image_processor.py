import os
import uuid
import time
import threading
from PIL import Image
from flask import current_app


ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
OUTPUT_SIZE = (1000, 1000)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def check_image_header(file_stream):
    """Verify if the file content is actually a supported image."""
    try:
        img = Image.open(file_stream)
        img.verify() # Verify it's an image
        file_stream.seek(0) # Reset stream for later use
        img = Image.open(file_stream) # Re-open to check format
        format_name = img.format.lower()
        file_stream.seek(0)
        return format_name in ALLOWED_EXTENSIONS or (format_name == 'jpeg' and 'jpg' in ALLOWED_EXTENSIONS)
    except Exception:
        return False


def generate_unique_filename(prefix='photo', extension='png'):
    timestamp = int(time.time())
    unique_id = uuid.uuid4().hex[:8]
    return f"{prefix}_{timestamp}_{unique_id}.{extension}"


def generate_twibbon(user_photo_path, frame_path, output_dir, frame_name='twibbon', transform=None):
    """
    Overlay user photo with frame and save result.
    transform: dict with 'x', 'y', 'scale'
    """
    # Open and convert
    base = Image.open(user_photo_path).convert("RGBA")
    frame = Image.open(frame_path).convert("RGBA")

    target_size = OUTPUT_SIZE # (1000, 1000)
    
    # 1. Initial Scale: Fit photo to fill target size
    base_aspect = base.width / base.height
    if base_aspect > 1:
        new_h = target_size[1]
        new_w = int(new_h * base_aspect)
    else:
        new_w = target_size[0]
        new_h = int(new_w / base_aspect)
    
    base = base.resize((new_w, new_h), Image.LANCZOS)
    
    # 2. User Transform
    scale = transform.get('scale', 1) if transform else 1
    offset_x = transform.get('x', 0) if transform else 0
    offset_y = transform.get('y', 0) if transform else 0
    
    # Apply user scale
    if scale != 1:
        base = base.resize((int(base.width * scale), int(base.height * scale)), Image.LANCZOS)
    
    # 3. Composition
    # Create final image canvas
    final_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    
    # Calculate centering + user offset
    # Frontend centers by default in the viewport, then adds translate(x, y)
    paste_x = (target_size[0] - base.width) // 2 + int(offset_x)
    paste_y = (target_size[1] - base.height) // 2 + int(offset_y)
    
    final_img.paste(base, (paste_x, paste_y))
    
    # Resize frame to target size and composite
    frame = frame.resize(target_size, Image.LANCZOS)
    final_img = Image.alpha_composite(final_img, frame)

    # Save
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in frame_name)
    output_filename = f"twibbon_{safe_name}_{int(time.time())}.png"
    output_path = os.path.join(output_dir, output_filename)
    final_img.convert("RGB").save(output_path, "PNG", quality=95, optimize=True)

    return output_filename


def schedule_file_deletion(filepath, delay_seconds=3600):
    """Delete a file after delay_seconds (default: 1 hour)."""
    def _delete():
        time.sleep(delay_seconds)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

    thread = threading.Thread(target=_delete, daemon=True)
    thread.start()


def cleanup_old_results(results_dir, max_age_minutes=60):
    """Remove result files older than max_age_minutes."""
    max_age_seconds = max_age_minutes * 60
    now = time.time()
    if not os.path.exists(results_dir):
        return
    for filename in os.listdir(results_dir):
        filepath = os.path.join(results_dir, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                except Exception:
                    pass
