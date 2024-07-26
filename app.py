from flask import Flask
from config import Config
from extensions import mail, jwt, cors
from routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    mail.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    
    # Register routes
    register_routes(app)
    
    return app

app = create_app()

if __name__ == '__main__':
    import ssl
    ssl_cert = '/etc/letsencrypt/live/gentai.instamart.ai/fullchain.pem'
    ssl_key = '/etc/letsencrypt/live/gentai.instamart.ai/privkey.pem'
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=ssl_cert, keyfile=ssl_key)
    app.run(debug=True, port=8446, host='gentai.instamart.ai', ssl_context=ssl_context)
