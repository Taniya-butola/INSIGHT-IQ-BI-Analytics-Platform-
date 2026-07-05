import os

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db, bcrypt, jwt


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    cors_origins = os.getenv("CORS_ORIGINS", app.config["FRONTEND_ORIGIN"])
    if isinstance(cors_origins, str):
        cors_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    from routes.auth import auth_bp
    from routes.profile import profile_bp
    from routes.datasets import datasets_bp
    from routes.chat import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(datasets_bp)
    app.register_blueprint(chat_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "insight-iq-backend"}), 200

    @app.errorhandler(404)
    def not_found(_err):
        return jsonify({"errors": ["Resource not found."]}), 404

    @app.errorhandler(413)
    def too_large(_err):
        mb = app.config["MAX_UPLOAD_MB"]
        return jsonify({"errors": [f"File exceeds the {mb}MB upload limit."]}), 413

    @app.errorhandler(500)
    def server_error(_err):
        return jsonify({"errors": ["Internal server error."]}), 500

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True, port=5000)
