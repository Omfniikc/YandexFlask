from quart import Blueprint, g, current_app, request, jsonify
import datetime
import jwt
import aiosqlite
from ..db import get_db
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

bp = Blueprint('users', __name__)

# JWT Helpers
def encode_token(user_id):
    """Создание JWT токена"""
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=10),
        'iat': datetime.datetime.utcnow(),
        'sub': str(user_id),  # обязательно строкой
        'user_id': user_id    # добавляем для удобства
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return int(payload['sub'])  # возвращаем user_id как число
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None

# Декоратор авторизации для Quart
def jwt_required(fn):
    """Декоратор для проверки JWT токена в асинхронных функциях"""
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'msg': 'Missing or invalid Authorization header'}), 401
        
        try:
            token = auth.split()[1]
        except IndexError:
            return jsonify({'msg': 'Invalid token format'}), 401
        
        user_id = decode_token(token)
        if not user_id:
            return jsonify({'msg': 'Invalid or expired token'}), 401
        
        g.user_id = user_id
        # Важно: вызываем асинхронную функцию с await
        return await fn(*args, **kwargs)
    
    return wrapper

# Регистрация
@bp.route('/register', methods=['POST'])
async def register():
    """Регистрация нового пользователя"""
    try:
        # В Quart нужно использовать await для получения JSON
        data = await request.get_json() or {}
        
        email = data.get('email', '').strip().lower()
        pw = data.get('password', '')
        name = data.get('name', '').strip()
        
        # Валидация входных данных
        if not email or not pw or not name:
            return jsonify({'msg': 'Email, password and name are required'}), 400
        
        if len(pw) < 6:
            return jsonify({'msg': 'Password must be at least 6 characters long'}), 400
        
        # Простая валидация email
        if '@' not in email or '.' not in email:
            return jsonify({'msg': 'Invalid email format'}), 400
        
        db = await get_db()
        
        try:
            # Вставляем нового пользователя
            await db.execute(
                'INSERT INTO users (email, password, name) VALUES (?, ?, ?)',
                (email, generate_password_hash(pw), name)
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            return jsonify({'msg': 'Email already registered'}), 409
        
        # Получаем созданного пользователя
        async with db.execute('SELECT id, email, name FROM users WHERE email = ?', (email,)) as cursor:
            user = await cursor.fetchone()
        
        if not user:
            return jsonify({'msg': 'Registration failed'}), 500
        
        print(f"User registered: {dict(user)}")
        
        # Создаем токен
        token = encode_token(user['id'])
        
        return jsonify({
            'access_token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name']
            }
        }), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'msg': 'Internal server error'}), 500

# Логин
@bp.route('/login', methods=['POST'])
async def login():
    """Авторизация пользователя"""
    try:
        data = await request.get_json() or {}
        
        email = data.get('email', '').strip().lower()
        pw = data.get('password', '')
        
        if not email or not pw:
            return jsonify({'msg': 'Email and password are required'}), 400
        
        db = await get_db()
        
        # Получаем пользователя из БД
        async with db.execute(
            'SELECT id, email, name, password FROM users WHERE email = ?', 
            (email,)
        ) as cursor:
            user = await cursor.fetchone()
        
        if not user or not check_password_hash(user['password'], pw):
            return jsonify({'msg': 'Invalid email or password'}), 401
        
        # Создаем токен
        token = encode_token(user['id'])
        
        return jsonify({
            'access_token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name']
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'msg': 'Internal server error'}), 500

@bp.route('/complete-profile', methods=['POST'])
@jwt_required
async def complete_profile():
    """Завершение профиля пользователя"""
    try:
        data = await request.get_json()
        
        if not data:
            return jsonify({'msg': 'No data provided'}), 400
        
        # Валидация данных
        gender = data.get('gender')
        weight = data.get('weight')
        height = data.get('height')
        
        if not all([gender, weight, height]):
            return jsonify({'msg': 'Gender, weight and height are required'}), 400
        
        # Проверяем типы данных
        try:
            weight = float(weight)
            height = float(height)
        except (ValueError, TypeError):
            return jsonify({'msg': 'Weight and height must be numbers'}), 400
        
        if weight <= 0 or height <= 0:
            return jsonify({'msg': 'Weight and height must be positive numbers'}), 400
        
        if gender not in ['male', 'female']:
            return jsonify({'msg': 'Gender must be "male" or "female"'}), 400
        
        db = await get_db()
        
        # Обновляем профиль пользователя
        await db.execute(
            '''UPDATE users 
               SET sex = ?, weight = ?, height = ?, updated_at = ?
               WHERE id = ?''',
            (gender, weight, height, datetime.datetime.now().isoformat(), g.user_id)
        )
        await db.commit()
        
        return jsonify({'msg': 'Profile completed successfully'}), 200
        
    except Exception as e:
        print(f"Complete profile error: {str(e)}")
        return jsonify({'msg': 'Internal server error'}), 500

# Получение профиля
@bp.route('/profile', methods=['GET'])
@jwt_required
async def profile():
    """Получение профиля текущего пользователя"""
    try:
        db = await get_db()
        
        # Получаем полную информацию о пользователе
        async with db.execute(
            '''SELECT id, email, name, sex, weight, height 
               FROM users WHERE id = ?''', 
            (g.user_id,)
        ) as cursor:
            user = await cursor.fetchone()
        
        if not user:
            return jsonify({'msg': 'User not found'}), 404
        
        user_data = dict(user)
        # Убираем чувствительные данные
        user_data.pop('password', None)
        
        return jsonify(user_data), 200
        
    except Exception as e:
        print(f"Profile error: {str(e)}")
        return jsonify({'msg': 'Internal server error'}), 500

# Обновление профиля
@bp.route('/profile', methods=['PUT'])
@jwt_required
async def update_profile():
    """Обновление профиля пользователя"""
    try:
        data = await request.get_json()
        
        if not data:
            return jsonify({'msg': 'No data provided'}), 400
        
        db = await get_db()
        
        # Поля, которые можно обновить
        updatable_fields = ['name', 'sex', 'weight', 'height']
        update_fields = []
        update_values = []
        
        for field in updatable_fields:
            if field in data:
                update_fields.append(f'{field} = ?')
                update_values.append(data[field])
        
        if not update_fields:
            return jsonify({'msg': 'No valid fields to update'}), 400
        
        # Добавляем updated_at
        update_fields.append('updated_at = ?')
        update_values.append(datetime.datetime.now().isoformat())
        update_values.append(g.user_id)
        
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        
        await db.execute(query, update_values)
        await db.commit()
        
        return jsonify({'msg': 'Profile updated successfully'}), 200
        
    except Exception as e:
        print(f"Update profile error: {str(e)}")
        return jsonify({'msg': 'Internal server error'}), 500

# Смена пароля
@bp.route('/change-password', methods=['POST'])
@jwt_required
async def change_password():
    """Смена пароля пользователя"""
    try:
        data = await request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'msg': 'Current and new passwords are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'msg': 'New password must be at least 6 characters long'}), 400
        
        db = await get_db()
        
        # Проверяем текущий пароль
        async with db.execute(
            'SELECT password FROM users WHERE id = ?', 
            (g.user_id,)
        ) as cursor:
            user = await cursor.fetchone()
        
        if not user or not check_password_hash(user['password'], current_password):
            return jsonify({'msg': 'Current password is incorrect'}), 401
        
        # Обновляем пароль
        await db.execute(
            'UPDATE users SET password = ?, updated_at = ? WHERE id = ?',
            (generate_password_hash(new_password), datetime.datetime.now().isoformat(), g.user_id)
        )
        await db.commit()
        
        return jsonify({'msg': 'Password changed successfully'}), 200
        
    except Exception as e:
        print(f"Change password error: {str(e)}")
        return jsonify({'msg': 'Internal server error'}), 500