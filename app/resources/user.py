from flask import Blueprint, g
import datetime, jwt, aiosqlite
from flask import current_app, request, jsonify
from ..db import get_db
from werkzeug.security import check_password_hash, generate_password_hash


bp = Blueprint('users', __name__)

# JWT Helpers


def encode_token(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=10),
        'iat': datetime.datetime.utcnow(),
        'sub': str(user_id)  # 👈 обязательно строкой
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return int(payload['sub'])  # 👈 если ожидаешь user_id как число
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        print(f"Token error: {e}")
        return None


# Декоратор авторизации
def jwt_required(fn):
    from functools import wraps
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'msg': 'Missing token'}), 401
        token = auth.split()[1]
        user_id = decode_token(token)
        if not user_id:
            return jsonify({'msg': 'Invalid or expired token'}), 401
        g.user_id = user_id
        return fn(*args, **kwargs)
    return wrapper

# Регистрация
@bp.route('/register', methods=['POST'])
async def register():
    data = request.get_json() or {}
    email = data.get('email')
    pw    = data.get('password')
    name  = data.get('name')
    if not email or not pw or not name:
        return jsonify({'msg': 'Email and password and name required'}), 400

    db = await get_db()
    try:
        await db.execute(
            'INSERT INTO users (email, password, name) VALUES (?, ?, ?)',
            (email, generate_password_hash(pw), name)
        )
        await db.commit()
    except aiosqlite.IntegrityError:
        return jsonify({'msg': 'Email already registered'}), 409

    cur = await db.execute('SELECT id, email FROM users WHERE email = ?', (email,))
    user = await cur.fetchone()
    print(user)
    token = encode_token(user['id'])
    return jsonify({'access_token': token}), 200

# Логин
@bp.route('/login', methods=['POST'])
async def login():
    data = request.get_json() or {}
    email = data.get('email'); pw = data.get('password')
    if not email or not pw:
        return jsonify({'msg': 'Email and password required'}), 400

    db = await get_db()
    cur = await db.execute('SELECT id, password FROM users WHERE email = ?', (email,))
    user = await cur.fetchone()
    if not user or not check_password_hash(user['password'], pw):
        return jsonify({'msg': 'Bad credentials'}), 401

    token = encode_token(user['id'])
    return jsonify({'access_token': token}), 200

@bp.route('/complete-profile', methods=['POST'])
@jwt_required
async def complete_profile():
    data = request.get_json()
    db = await get_db()
    await db.execute(
        '''UPDATE users
            SET sex = ?, weight = ?, height = ?
           WHERE id = ?'''
           ,
        (data['gender'], data['weight'], data['height'], g.user_id)
    )
    await db.commit()
    return jsonify({'msg': 'Profile completed'}), 200

# Профиль
@bp.route('/profile', methods=['GET'])
@jwt_required
async def profile():
    db = await get_db()
    cur = await db.execute('SELECT id, email, name FROM users WHERE id = ?', (g.user_id,))
    user = await cur.fetchone()
    if not user:
        return jsonify({'msg': 'Not found'}), 404
    return jsonify(dict(user)), 200
