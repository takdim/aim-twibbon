from app import create_app
from datetime import datetime

import click
from app import db
from app.models.user import AdminUser

app = create_app()

# CLI Command to create admin
@app.cli.command("create-admin")
@click.argument("username")
@click.argument("email")
@click.password_option()
def create_admin(username, email, password):
    """Create a new admin user via terminal."""
    with app.app_context():
        if AdminUser.query.filter_by(username=username).first():
            click.echo(f"Error: Username '{username}' sudah ada.")
            return
        
        user = AdminUser(username=username, email=email, is_superadmin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Berhasil! Admin '{username}' telah dibuat.")

# Inject `now` into all Jinja2 templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
