from flask import Flask
from flask_bootstrap import Bootstrap
from config import Config
from database import init_db
from routes import register_routes
import datetime as dt
import os


def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    Bootstrap(app)
    init_db(app)
    
    # Register routes
    register_routes(app)
    
    # Template global variables
    @app.context_processor
    def inject_globals():
        return {'current_year': dt.datetime.now().year}
    
    return app


if __name__ == "__main__":
    app = create_app()
    debug_mode = os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(host='127.0.0.1', port=5050, debug=debug_mode)
