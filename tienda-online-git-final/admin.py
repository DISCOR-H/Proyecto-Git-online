from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from pymongo import MongoClient
from bson import ObjectId
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from typing import Optional, List, Dict, Any

class DatabaseConnection:
    _instance: Optional['DatabaseConnection'] = None
    _client: Optional[MongoClient] = None
    _db = None
    _products_collection = None

    def __new__(cls) -> 'DatabaseConnection':
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._client = MongoClient('mongodb+srv://taniamelany2003:admin123@tania.gtqnh.mongodb.net/')
            self._db = self._client['gamerdb']
            self._products_collection = self._db['agregarproductos']

    @property
    def products_collection(self):
        return self._products_collection

class ProductManager:
    _instance: Optional['ProductManager'] = None
    _db: Optional[DatabaseConnection] = None

    def __new__(cls) -> 'ProductManager':
        if cls._instance is None:
            cls._instance = super(ProductManager, cls).__new__(cls)
            cls._instance._db = DatabaseConnection()
        return cls._instance

    def get_all_products(self) -> List[Dict[str, Any]]:
        return list(self._db.products_collection.find())

    def add_product(self, product_data: Dict[str, Any]) -> bool:
        try:
            self._db.products_collection.insert_one(product_data)
            return True
        except Exception as e:
            print(f"Error adding product: {e}")
            return False

    def update_product(self, product_id: str, update_data: Dict[str, Any]) -> bool:
        try:
            result = self._db.products_collection.update_one(
                {'_id': ObjectId(product_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating product: {e}")
            return False

    def delete_product(self, product_id: str) -> bool:
        try:
            result = self._db.products_collection.delete_one({'_id': ObjectId(product_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting product: {e}")
            return False

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        try:
            return self._db.products_collection.find_one({'_id': ObjectId(product_id)})
        except Exception as e:
            print(f"Error getting product: {e}")
            return None

class FileManager:
    _instance: Optional['FileManager'] = None
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    def __new__(cls) -> 'FileManager':
        if cls._instance is None:
            cls._instance = super(FileManager, cls).__new__(cls)
            os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        return cls._instance

    def allowed_file(self, filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def save_file(self, file) -> Optional[str]:
        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(self.UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            return unique_filename
        return None

    def delete_file(self, filename: str) -> bool:
        try:
            file_path = os.path.join(self.UPLOAD_FOLDER, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

# Crear Blueprint
admin = Blueprint('admin', __name__, url_prefix='/admin', template_folder='template')

# Instanciar managers
product_manager = ProductManager()
file_manager = FileManager()

@admin.route('/')
def admin_panel():
    try:
        products = product_manager.get_all_products()
        return render_template('admin/admin.html', products=products)
    except Exception as e:
        flash(f'Error al cargar productos: {str(e)}', 'error')
        return render_template('admin/admin.html', products=[])

@admin.route('/add', methods=['POST'])
def add_product():
    try:
        if 'image' not in request.files:
            flash('No se ha seleccionado ninguna imagen', 'error')
            return redirect(url_for('admin.admin_panel'))

        file = request.files['image']
        if file.filename == '':
            flash('No se ha seleccionado ninguna imagen', 'error')
            return redirect(url_for('admin.admin_panel'))

        unique_filename = file_manager.save_file(file)
        if unique_filename:
            product_data = {
                'title': request.form['title'],
                'price': float(request.form['price']),
                'description': request.form['description'],
                'category': request.form['category'],
                'stock': int(request.form['stock']),
                'image': unique_filename,
                'created_at': datetime.now()
            }

            if product_manager.add_product(product_data):
                flash('Producto agregado exitosamente', 'success')
            else:
                flash('Error al agregar el producto', 'error')
                file_manager.delete_file(unique_filename)

        return redirect(url_for('admin.admin_panel'))

    except Exception as e:
        flash(f'Error al agregar el producto: {str(e)}', 'error')
        return redirect(url_for('admin.admin_panel'))

@admin.route('/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    try:
        if request.method == 'POST':
            update_data = {
                'title': request.form['title'],
                'price': float(request.form['price']),
                'description': request.form['description'],
                'category': request.form['category'],
                'stock': int(request.form['stock'])
            }

            if 'image' in request.files and request.files['image'].filename != '':
                file = request.files['image']
                unique_filename = file_manager.save_file(file)
                if unique_filename:
                    old_product = product_manager.get_product(product_id)
                    if old_product and 'image' in old_product:
                        file_manager.delete_file(old_product['image'])
                    update_data['image'] = unique_filename

            if product_manager.update_product(product_id, update_data):
                flash('Producto actualizado exitosamente', 'success')
            else:
                flash('Error al actualizar el producto', 'error')
            return redirect(url_for('admin.admin_panel'))

        product = product_manager.get_product(product_id)
        if product is None:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('admin.admin_panel'))
        return render_template('admin/edit_product.html', product=product)

    except Exception as e:
        flash(f'Error al editar el producto: {str(e)}', 'error')
        return redirect(url_for('admin.admin_panel'))

@admin.route('/delete/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = product_manager.get_product(product_id)
        if product and 'image' in product:
            file_manager.delete_file(product['image'])

        if product_manager.delete_product(product_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Producto no encontrado'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})