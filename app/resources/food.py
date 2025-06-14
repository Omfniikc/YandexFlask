from .user import jwt_required
from quart import Blueprint, g, url_for, current_app, request, jsonify, send_from_directory
import datetime
import jwt
import aiosqlite
from werkzeug.utils import secure_filename
from ..db import get_db
import os
from ..services.gpt_scan_food import scan_food
import asyncio

bp = Blueprint('food', __name__)
UPLOAD_FOLDER = os.path.join('instance', 'uploads')

# Убеждаемся, что папка для загрузок существует
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@bp.route('/files/<filename>')
async def get_file(filename):
    """Асинхронная отдача файлов"""
    print(f"Requesting file: {filename}")
    return await send_from_directory('instance/uploads', filename)

@bp.route('/scan_image', methods=['POST'])
@jwt_required
async def upload_image():
    """Асинхронная загрузка и сканирование изображения"""
    try:
        # Получаем файлы из формы (в Quart это асинхронная операция)
        files = await request.files
        form = await request.form
        
        print("Content-Type:", request.content_type)
        print("Headers:", dict(request.headers))
        print("Form:", dict(form))
        print("Files:", list(files.keys()))
        
        if 'image' not in files:
            return jsonify({'msg': 'No image part'}), 400
        
        image = files['image']
        
        if not image or image.filename == '':
            return jsonify({'msg': 'No selected image'}), 400
        
        # Безопасное имя файла
        filename = secure_filename(image.filename)
        if not filename:
            return jsonify({'msg': 'Invalid filename'}), 400
            
        # Добавляем timestamp для уникальности
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Асинхронное сохранение файла
        await image.save(save_path)
        
        # Генерируем URL для файла
        photo_url = url_for('food.get_file', filename=filename, _external=True)
        
        # Асинхронное сканирование изображения
        food_table = await scan_food(photo_url)
        print("food_table:", food_table)
        
        return jsonify({
            'msg': 'Image uploaded and scanned successfully', 
            'filename': filename,
            'photo_url': photo_url,
            'food_data': food_table
        }), 200
        
    except Exception as e:
        print(f"Error in upload_image: {str(e)}")
        return jsonify({'msg': 'Internal server error', 'error': str(e)}), 500

@bp.route('/foods', methods=['GET'])
@jwt_required
async def get_foods():
    """Получение списка продуктов пользователя"""
    try:
        user_id = g.user_id
        db = await get_db()
        
        # Пример запроса к БД (адаптируйте под вашу схему)
        async with db.execute(
            'SELECT * FROM foods WHERE user_id = ?', (user_id,)
        ) as cursor:
            foods = await cursor.fetchall()
        
        # Преобразуем результат в список словарей
        foods_list = [dict(food) for food in foods] if foods else []
        
        return jsonify({'foods': foods_list}), 200
        
    except Exception as e:
        print(f"Error in get_foods: {str(e)}")
        return jsonify({'msg': 'Internal server error'}), 500

@bp.route('/foods', methods=['POST'])
@jwt_required
async def add_food():
    """Добавление нового продукта"""
    try:
        user_id = g.user_id
        data = await request.get_json()
        
        if not data:
            return jsonify({'msg': 'No data provided'}), 400
        
        # Валидация данных
        required_fields = ['name', 'calories_per_100g']
        for field in required_fields:
            if field not in data:
                return jsonify({'msg': f'Missing field: {field}'}), 400
        
        db = await get_db()
        
        # Добавляем продукт в БД
        await db.execute(
            '''INSERT INTO foods (user_id, name, calories_per_100g, proteins, fats, carbs, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                user_id,
                data['name'],
                data['calories_per_100g'],
                data.get('proteins', 0),
                data.get('fats', 0),
                data.get('carbs', 0),
                datetime.datetime.now().isoformat()
            )
        )
        await db.commit()
        
        return jsonify({'msg': 'Food added successfully'}), 201
        
    except Exception as e:
        print(f"Error in add_food: {str(e)}")
        return jsonify({'msg': 'Internal server error'}), 500

@bp.route('/foods/<int:food_id>', methods=['DELETE'])
@jwt_required
async def delete_food(food_id):
    """Удаление продукта"""
    try:
        user_id = g.user_id
        db = await get_db()
        
        # Проверяем, что продукт принадлежит пользователю
        async with db.execute(
            'SELECT id FROM foods WHERE id = ? AND user_id = ?', 
            (food_id, user_id)
        ) as cursor:
            food = await cursor.fetchone()
        
        if not food:
            return jsonify({'msg': 'Food not found'}), 404
        
        # Удаляем продукт
        await db.execute('DELETE FROM foods WHERE id = ?', (food_id,))
        await db.commit()
        
        return jsonify({'msg': 'Food deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error in delete_food: {str(e)}")
        return jsonify({'msg': 'Internal server error'}), 500

# Обработчик ошибок для этого блюпринта
@bp.errorhandler(413)
async def too_large(e):
    return jsonify({'msg': 'File too large'}), 413

@bp.errorhandler(400)
async def bad_request(e):
    return jsonify({'msg': 'Bad request'}), 400