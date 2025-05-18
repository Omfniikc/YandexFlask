import asyncio
import click
from flask import Flask, g, current_app, request, jsonify
from flask_cors import CORS
from .db import _init_db

def create_app(config_object=None):
    app = Flask(__name__)
    CORS(app)

    # Загрузка конфигурации
    if config_object:
        app.config.from_object(config_object)
    else:
        # fallback: локальные константы
        from config import DB_PATH, JWT_SECRET_KEY
        app.config['DATABASE'] = DB_PATH
        app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

    # Регистрируем инициализацию и закрытие БД
    from .db import init_app as init_db_app
    init_db_app(app)

    # Регистрация команд CLI
    @app.cli.command('init-db')
    def init_db_command():
        """Инициализирует базу данных."""
        asyncio.run(_init_db(current_app.config['DATABASE']))
        click.echo('Initialized database.')

    # Пример эндпоинтов
    from .resources.user import bp as user_bp
    from .resources.food import bp as food_bp
    app.register_blueprint(food_bp, url_prefix='/api/v1/food')
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')

    @app.route('/')
    def index():
        return 'Hello world!'  

    return app
