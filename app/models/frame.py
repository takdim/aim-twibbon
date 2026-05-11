from app import db
from datetime import datetime, timezone


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    frames = db.relationship('Frame', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Frame(db.Model):
    __tablename__ = 'frames'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    filename = db.Column(db.String(300), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    download_count = db.Column(db.Integer, default=0, nullable=False)
    active_from = db.Column(db.DateTime, nullable=True)
    active_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    category = db.relationship('Category', back_populates='frames')

    @property
    def is_currently_active(self):
        now = datetime.now(timezone.utc)
        if not self.is_active:
            return False
        if self.active_from and now < self.active_from.replace(tzinfo=timezone.utc):
            return False
        if self.active_until and now > self.active_until.replace(tzinfo=timezone.utc):
            return False
        return True

    @property
    def frame_url(self):
        return f'/static/uploads/frames/{self.filename}'

    def increment_download(self):
        self.download_count += 1
        db.session.commit()

    def __repr__(self):
        return f'<Frame {self.name}>'
