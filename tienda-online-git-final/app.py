from flask import Flask, render_template, redirect, url_for
from admin import admin
from productos import productos_bp
from login import login_bp  # Nuevo blueprint para login
from carrito import carrito_singleton
from flask_mail import Mail
from vista import vista_bp

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'taniamelany2003@gmail.com'  # Cambia esto por tu correo real
app.config['MAIL_PASSWORD'] = 'bjfo wusa afbh mhti'  # Contraseña de aplicación de Gmail

mail = Mail(app)

# Registrar los blueprints
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(productos_bp, url_prefix='/productos')
app.register_blueprint(login_bp)  # Registrar el blueprint de login
app.register_blueprint(vista_bp)

# Ruta principal: Redirigir la ruta principal al login
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)