from .user import jwt_required
from flask import Blueprint, g, url_for
import datetime, jwt, aiosqlite
from flask import current_app, request, jsonify
from werkzeug.utils import secure_filename
from ..db import get_db
import os
from ..services.gpt_scan_food import scan_food
import asyncio

bp = Blueprint('food', __name__)
UPLOAD_FOLDER = os.path.join('instance', 'uploads')

from flask import send_from_directory

@bp.route('/files/<filename>')
def get_file(filename):
    return send_from_directory('instance/uploads', filename)


@bp.route('/scan_image', methods=['POST'])
@jwt_required
async def upload_image():
    print(request.content_type)
    print(request.headers)
    print(request.form)
    print(request.files)
    if 'image' not in request.files:
        return jsonify({'msg': 'No image part'}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({'msg': 'No selected image'}), 400

    filename = secure_filename(image.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(save_path)

    photo_url = url_for('food.get_file', filename=filename, _external=True)

    food_table = await scan_food(photo_url)
    print("food_table", food_table)

    return jsonify({'msg': 'Image uploaded successfully', 'filename': filename}), 200