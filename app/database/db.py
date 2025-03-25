from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def get_db():
    from flask import current_app
    if not hasattr(current_app, 'db_session'):
        current_app.db_session = db.session
    yield current_app.db_session
