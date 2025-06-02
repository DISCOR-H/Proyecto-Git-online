from flask import session

class Carrito:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Carrito, cls).__new__(cls)
        return cls._instance

    def obtener_carrito(self):
        """Devuelve el carrito actual de la sesión, o lo crea si no existe."""
        if 'carrito' not in session:
            session['carrito'] = []
        return session['carrito']

    def agregar_producto(self, producto):
        """Agrega un producto al carrito o aumenta la cantidad si ya existe."""
        carrito = self.obtener_carrito()
        for item in carrito:
            if item['id'] == producto['id']:
                item['cantidad'] += 1
                session.modified = True
                return
        # Si no existe, lo agrega con cantidad 1
        producto_copia = producto.copy()
        producto_copia['cantidad'] = 1
        carrito.append(producto_copia)
        session.modified = True

    def actualizar_cantidad(self, producto_id, cantidad):
        """Actualiza la cantidad de un producto en el carrito."""
        carrito = self.obtener_carrito()
        for item in carrito:
            if item['id'] == producto_id:
                if cantidad < 1:
                    carrito.remove(item)
                else:
                    item['cantidad'] = cantidad
                session.modified = True
                return

    def eliminar_producto(self, producto_id):
        """Elimina un producto del carrito."""
        carrito = self.obtener_carrito()
        for item in carrito:
            if item['id'] == producto_id:
                carrito.remove(item)
                session.modified = True
                return

    def limpiar_carrito(self):
        """Vacía el carrito."""
        session['carrito'] = []
        session.modified = True

    def total_carrito(self):
        """Calcula el total del carrito."""
        carrito = self.obtener_carrito()
        return sum(item['price'] * item['cantidad'] for item in carrito)

    def cantidad_total(self):
        """Devuelve la cantidad total de productos en el carrito."""
        carrito = self.obtener_carrito()
        return sum(item['cantidad'] for item in carrito)

# Instancia global para usar en tus rutas
carrito_singleton = Carrito()