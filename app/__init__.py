import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
talisman = Talisman()


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///twibbon.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['RESULT_EXPIRY_MINUTES'] = int(os.getenv('RESULT_EXPIRY_MINUTES', 60))

    # Ensure upload directories exist
    for folder in ['frames', 'results', 'temp']:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], folder), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    # Security Headers (Talisman)
    csp = {
        'default-src': [
            '\'self\'',
            'fonts.googleapis.com',
            'fonts.gstatic.com',
        ],
        'style-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            'fonts.googleapis.com',
        ],
        'script-src': [
            '\'self\'',
            '\'unsafe-inline\'',
        ],
        'img-src': [
            '\'self\'',
            'data:',
            'blob:',
        ],
    }
    talisman.init_app(app, content_security_policy=csp, force_https=False) # force_https=True in prod

    # Secure Cookie Settings
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = False # Set to True if using HTTPS
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = False # Set to True if using HTTPS

    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
    login_manager.login_message_category = 'warning'

    # Import and register blueprints
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Import models so SQLAlchemy knows about them
    with app.app_context():
        from app.models import frame, user  # noqa: F401
        db.create_all()

    return app
