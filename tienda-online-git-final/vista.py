from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import logging
from productos import calcular_total_carrito
from login import login_required

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear el Blueprint
vista_bp = Blueprint('vista', __name__)

class VistaProductoDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VistaProductoDB, cls).__new__(cls)
            try:
                # Conexión a MongoDB
                cls._instance.client = MongoClient('mongodb+srv://taniamelany2003:admin123@tania.gtqnh.mongodb.net/')
                cls._instance.db = cls._instance.client['gamerdb']
                cls._instance.collection = cls._instance.db['agregarproductos']
                logger.info("Conexión a MongoDB establecida exitosamente en VistaProductoDB")
            except Exception as e:
                logger.error(f"Error al conectar a MongoDB: {e}")
                raise
        return cls._instance

    def get_product_by_id(self, producto_id):
        try:
            if not ObjectId.is_valid(producto_id):
                logger.warning(f"ID de producto inválido: {producto_id}")
                return None
            producto = self.collection.find_one({'_id': ObjectId(producto_id)})
            if producto:
                logger.info(f"Producto encontrado: {producto.get('title', 'Sin título')}")
            else:
                logger.warning(f"No se encontró producto con ID: {producto_id}")
            return producto
        except Exception as e:
            logger.error(f"Error al obtener producto por ID: {e}")
            return None

    def get_related_products(self, producto_id, categoria, limit=4):
        try:
            productos_relacionados = list(
                self.collection.find({
                    '_id': {'$ne': ObjectId(producto_id)},
                    'category': categoria
                }).limit(limit)
            )
            if len(productos_relacionados) < limit:
                faltantes = limit - len(productos_relacionados)
                otros_productos = list(
                    self.collection.find({
                        '_id': {'$ne': ObjectId(producto_id)},
                        'category': {'$ne': categoria}
                    }).limit(faltantes)
                )
                productos_relacionados.extend(otros_productos)
            logger.info(f"Productos relacionados encontrados: {len(productos_relacionados)}")
            return productos_relacionados
        except Exception as e:
            logger.error(f"Error al obtener productos relacionados: {e}")
            return []

    def get_comentarios(self, producto_id):
        try:
            comentarios = list(
                self.db['comentarios_productos'].find(
                    {'producto_id': ObjectId(producto_id)}
                ).sort('fecha', -1)
            )
            return comentarios
        except Exception as e:
            logger.error(f"Error al obtener comentarios: {e}")
            return []

    def agregar_comentario(self, producto_id, usuario, texto):
        try:
            self.db['comentarios_productos'].insert_one({
                'producto_id': ObjectId(producto_id),
                'usuario': usuario,
                'texto': texto,
                'fecha': datetime.utcnow()
            })
            logger.info("Comentario agregado exitosamente")
        except Exception as e:
            logger.error(f"Error al agregar comentario: {e}")


@vista_bp.route('/producto/<producto_id>')
@login_required
def detalle_producto(producto_id):
    try:
        db = VistaProductoDB()
        producto = db.get_product_by_id(producto_id)

        if not producto:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('productos.productos'))

        productos_relacionados = db.get_related_products(
            producto_id,
            producto.get('category', ''),
            limit=4
        )

        total_carrito = calcular_total_carrito()
        comentarios = db.get_comentarios(producto_id)

        return render_template(
            'vista_producto.html',
            producto=producto,
            productos_relacionados=productos_relacionados,
            total_carrito=total_carrito,
            comentarios=comentarios
        )
    except Exception as e:
        logger.error(f"Error en la ruta /producto/{producto_id}: {e}")
        flash('Error al cargar el producto', 'error')
        return redirect(url_for('productos.productos'))


@vista_bp.route('/comentario/<producto_id>', methods=['POST'])
@login_required
def agregar_comentario(producto_id):
    comentario = request.form.get('comentario')
    usuario = session.get('usuario')

    if comentario and usuario:
        db = VistaProductoDB()
        db.agregar_comentario(producto_id, usuario, comentario)

    return redirect(url_for('vista.detalle_producto', producto_id=producto_id))
