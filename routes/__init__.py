# routes/__init__.py
from flask import Blueprint

def register_routes(app):
    from .auth import auth_bp
    from .smtp import smtp_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(smtp_bp, url_prefix='/smtp')
