from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import logging
from flask import send_file, Blueprint
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import uuid  # Importa la librería para generar UUIDs
from carrito import carrito_singleton  # Añade esta línea
import uuid
from flask import url_for, jsonify
from login import login_required  # Importa el decorador

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear el Blueprint
productos_bp = Blueprint('productos', __name__, template_folder='template')

class ProductosDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProductosDB, cls).__new__(cls)
            try:
                # Conexión a MongoDB
                cls._instance.client = MongoClient('mongodb+srv://taniamelany2003:admin123@tania.gtqnh.mongodb.net/')
                cls._instance.db = cls._instance.client['gamerdb']
                cls._instance.collection = cls._instance.db['agregarproductos']
                logger.info("Conexión a MongoDB establecida exitosamente")
            except Exception as e:
                logger.error(f"Error al conectar a MongoDB: {e}")
                raise
        return cls._instance

    def get_all_products(self):
        """Obtiene todos los productos de la base de datos."""
        try:
            productos = list(self.collection.find())
            logger.info(f"Productos recuperados: {len(productos)}")
            if productos:
                for producto in productos:
                    logger.info(f"Producto encontrado: {producto.get('title', 'Sin título')} - "
                              f"Precio: {producto.get('price', 'Sin precio')}")
            else:
                logger.warning("No se encontraron productos en la colección")
            return productos
        except Exception as e:
            logger.error(f"Error al obtener productos: {e}")
            return []

    def get_product_by_id(self, producto_id):
        """Obtiene un producto específico por su ID."""
        try:
            if not ObjectId.is_valid(producto_id):
                logger.warning(f"ID de producto inválido: {producto_id}")
                return None

            producto = self.collection.find_one({'_id': ObjectId(producto_id)})
            if producto:
                logger.info(f"Producto encontrado por ID: {producto.get('title', 'Sin título')}")
            else:
                logger.warning(f"No se encontró producto con ID: {producto_id}")
            return producto
        except Exception as e:
            logger.error(f"Error al obtener producto por ID: {e}")
            return None

def calcular_total_carrito():
    """Calcula el total del carrito desde la sesión."""
    try:
        if 'carrito' not in session:
            return 0

        total = sum(
            float(item.get('price', 0)) * item.get('cantidad', 1)
            for item in session['carrito']
        )
        logger.info(f"Total del carrito calculado: ${total:.2f}")
        return total
    except Exception as e:
        logger.error(f"Error al calcular total del carrito: {e}")
        return 0

@productos_bp.route('/')
@productos_bp.route('/productos')
@login_required  # Agrega este decorador a las rutas que requieran login
def productos():
    """Ruta principal que muestra todos los productos y el total del carrito."""
    try:
        db = ProductosDB()
        productos_list = db.get_all_products()
        total_carrito = calcular_total_carrito()

        logger.info(f"Número de productos encontrados: {len(productos_list)}")
        if productos_list:
            logger.info("Nombres de productos encontrados:")
            for producto in productos_list:
                logger.info(f"- {producto.get('title', 'Sin título')}")

        return render_template(
            'productos.html',
            productos=productos_list,
            total_carrito=total_carrito
        )
    except Exception as e:
        logger.error(f"Error en la ruta /productos: {e}")
        flash('Error al cargar los productos', 'error')
        return render_template(
            'productos.html',
            productos=[],
            total_carrito=0
        )

@productos_bp.route('/agregar_carrito/<producto_id>', methods=['POST'])
@login_required  # Agrega este decorador
def agregar_carrito(producto_id):
    """Agrega un producto al carrito."""
    try:
        db = ProductosDB()
        producto = db.get_product_by_id(producto_id)

        if not producto:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('productos.productos'))

        if 'carrito' not in session:
            session['carrito'] = []

        producto_en_carrito = next(
            (item for item in session['carrito'] if item['id'] == str(producto['_id'])),
            None
        )

        if producto_en_carrito:
            producto_en_carrito['cantidad'] = producto_en_carrito.get('cantidad', 1) + 1
            logger.info(f"Incrementada cantidad de {producto.get('title')} en carrito")
        else:
            session['carrito'].append({
                'id': str(producto['_id']),
                'title': producto.get('title', ''),
                'price': float(producto.get('price', 0)),
                'image': producto.get('image', ''),
                'cantidad': 1
            })
            logger.info(f"Nuevo producto agregado al carrito: {producto.get('title')}")

        session.modified = True
        flash('Producto agregado al carrito', 'success')

    except Exception as e:
        logger.error(f"Error al agregar al carrito: {e}")
        flash('Error al agregar al carrito', 'error')

    return redirect(url_for('productos.productos'))

@productos_bp.route('/carrito')
@login_required
def carrito():
    """Muestra la página del carrito."""
    try:
        total_carrito = calcular_total_carrito()
        return render_template(
            'carrito.html',
            carrito=session.get('carrito', []),
            total_carrito=total_carrito
        )
    except Exception as e:
        logger.error(f"Error en la ruta /carrito: {e}")
        flash('Error al cargar el carrito', 'error')
        return render_template(
            'carrito.html',
            carrito=[],
            total_carrito=0
        )

@productos_bp.route('/actualizar_cantidad/<producto_id>', methods=['POST'])
def actualizar_cantidad(producto_id):
    """Actualiza la cantidad de un producto en el carrito."""
    try:
        cantidad = int(request.form.get('cantidad', 1))
        if cantidad < 1:
            cantidad = 1

        if 'carrito' in session:
            for item in session['carrito']:
                if item['id'] == producto_id:
                    item['cantidad'] = cantidad
                    session.modified = True
                    break

        return redirect(url_for('productos.carrito'))
    except Exception as e:
        logger.error(f"Error al actualizar cantidad: {e}")
        flash('Error al actualizar cantidad', 'error')
        return redirect(url_for('productos.carrito'))

@productos_bp.route('/eliminar_producto/<producto_id>', methods=['POST'])
def eliminar_producto(producto_id):
    """Elimina un producto del carrito."""
    try:
        if 'carrito' in session:
            session['carrito'] = [item for item in session['carrito'] if item['id'] != producto_id]
            session.modified = True
            flash('Producto eliminado del carrito', 'success')
        return redirect(url_for('productos.carrito'))
    except Exception as e:
        logger.error(f"Error al eliminar producto: {e}")
        flash('Error al eliminar producto', 'error')
        return redirect(url_for('productos.carrito'))

def verificar_producto(producto):
    """Verifica que un producto tenga todos los campos necesarios."""
    campos_requeridos = ['title', 'price', 'image', 'description']
    campos_faltantes = [campo for campo in campos_requeridos if campo not in producto]
    
    if campos_faltantes:
        logger.warning(f"Producto incompleto. Faltan campos: {campos_faltantes}")
        return False
    return True


# Diccionario para almacenar temporalmente los datos de las facturas (¡NO USAR EN PRODUCCIÓN!)
facturas_temporales = {}

@productos_bp.route('/generar_url_factura')
def generar_url_factura():
    carrito = carrito_singleton.obtener_carrito()
    total = carrito_singleton.total_carrito()
    factura_id = str(uuid.uuid4())
    facturas_temporales[factura_id] = {
        'carrito': carrito,
        'total': total
    }
    url_factura = url_for('productos.factura_pdf', factura_id=factura_id, _external=True)
    return url_factura

@productos_bp.route('/factura_pdf/<factura_id>')
@login_required
def factura_pdf(factura_id):
    # Verificar si la factura existe en el diccionario temporal
    if factura_id not in facturas_temporales:
        return "Factura no encontrada", 404

    # Obtener los datos de la factura del diccionario temporal
    datos_factura = facturas_temporales[factura_id]
    carrito = datos_factura['carrito']
    total = datos_factura['total']

    # Crear buffer para el PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Configurar estilos
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor('#ff00c8'))  # Color neón rosa

    # Encabezado
    p.drawString(100, 750, "NEON GAMING STORE")

    # Información de la factura
    p.setFont("Helvetica", 12)
    p.setFillColor(colors.black)
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    p.drawString(100, 720, f"Fecha: {fecha_actual}")
    p.drawString(100, 700, "Factura #: " + datetime.now().strftime("%Y%m%d%H%M"))

    # Línea separadora
    p.line(100, 680, 500, 680)

    # Encabezados de la tabla
    y = 650
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Producto")
    p.drawString(300, y, "Cantidad")
    p.drawString(400, y, "Precio Unit.")
    p.drawString(480, y, "Total")

    # Línea separadora
    y -= 15
    p.line(100, y, 500, y)

    # Productos
    y -= 25
    p.setFont("Helvetica", 11)
    for item in carrito:
        p.drawString(100, y, item['title'][:30])  # Limitar título a 30 caracteres
        p.drawString(300, y, str(item['cantidad']))
        p.drawString(400, y, f"${item['price']:.2f}")
        subtotal = item['price'] * item['cantidad']
        p.drawString(480, y, f"${subtotal:.2f}")
        y -= 20

    # Línea separadora antes del total
    y -= 10
    p.line(100, y, 500, y)

    # Total
    y -= 25
    p.setFont("Helvetica-Bold", 14)
    p.drawString(380, y, f"Total: ${total:.2f}")

    # Pie de página
    p.setFont("Helvetica", 10)
    p.drawString(100, 50, "¡Gracias por tu compra!")
    p.drawString(100, 35, "NEON GAMING STORE - Tu tienda de juegos favorita")

    # Guardar PDF
    p.save()
    buffer.seek(0)

    # Eliminar la factura del diccionario temporal (opcional, para limitar el uso de memoria)
    del facturas_temporales[factura_id]

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"factura_neon_gaming_{datetime.now().strftime('%Y%m%d%H%M')}.pdf",
        mimetype='application/pdf'
    )