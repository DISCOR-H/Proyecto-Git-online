from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
from flask_mail import Mail, Message

login_bp = Blueprint('login', __name__)
mail = Mail()

# Singleton para la colección de usuarios
class UsersDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UsersDB, cls).__new__(cls)
            client = MongoClient("mongodb+srv://taniamelany2003:admin123@tania.gtqnh.mongodb.net/")
            db = client['gamerdb']
            cls._instance.collection = db['users']
        return cls._instance

    def find_one(self, query):
        return self.collection.find_one(query)

    def insert_one(self, data):
        return self.collection.insert_one(data)

    def update_one(self, query, update):
        return self.collection.update_one(query, update)

users_db = UsersDB()

@login_bp.route('/')
def index():
    return render_template('index.html')

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        user = users_db.find_one({'usuario': usuario})
        if user and check_password_hash(user['password'], password):
            session['usuario'] = usuario
            return redirect(url_for('productos.productos'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login/login.html')

@login_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        email = request.form['email']
        password = request.form['password']
        if users_db.find_one({'usuario': usuario}):
            flash('El usuario ya existe', 'error')
        elif users_db.find_one({'email': email}):
            flash('El email ya está registrado', 'error')
        else:
            hash_pass = generate_password_hash(password)
            users_db.insert_one({
                'usuario': usuario,
                'email': email,
                'password': hash_pass
            })
            flash('Registro exitoso, ahora puedes iniciar sesión', 'success')
            return redirect(url_for('login.login'))
    return render_template('login/registro.html')

@login_bp.route('/recuperar-password', methods=['GET', 'POST'])
def recuperacion():
    if request.method == 'POST':
        email = request.form['email']
        user = users_db.find_one({'email': email})
        if user:
            codigo = secrets.token_hex(3)
            users_db.update_one({'email': email}, {'$set': {'codigo_recuperacion': codigo}})
            try:
                msg = Message(
                    'Recuperación de contraseña - NEON GAMING STORE',
                    sender='noreply@neongaming.com',
                    recipients=[email]
                )
                msg.body = f'''
                Hola {user["usuario"]},

                Has solicitado recuperar tu contraseña.
                Tu código de verificación es: {codigo}

                Si no solicitaste este cambio, ignora este mensaje.

                Saludos,
                NEON GAMING STORE
                '''
                mail.send(msg)
                flash('Se ha enviado un código de verificación a tu email', 'success')
                session['recuperacion_email'] = email
                return render_template('login/recuperacion_contraseña.html', codigo_enviado=True)
            except Exception as e:
                flash('Error al enviar el email. Por favor, intenta más tarde.', 'error')
                print(f"Error de correo: {e}")
        else:
            flash('Email no encontrado', 'error')
    return render_template('login/recuperacion_contraseña.html')

@login_bp.route('/verificar-codigo', methods=['POST'])
def verificar_codigo():
    if 'recuperacion_email' not in session:
        return redirect(url_for('login.recuperacion'))

    codigo = request.form['codigo']
    email = session['recuperacion_email']
    user = users_db.find_one({'email': email, 'codigo_recuperacion': codigo})

    if user:
        session['codigo_verificado'] = True
        return render_template('login/recuperacion_contraseña.html', cambiar_password=True)
    else:
        flash('Código incorrecto', 'error')
        return render_template('login/recuperacion_contraseña.html', codigo_enviado=True)

@login_bp.route('/cambiar-password', methods=['POST'])
def cambiar_password():
    if 'recuperacion_email' not in session or 'codigo_verificado' not in session:
        return redirect(url_for('login.recuperacion'))

    new_password = request.form['new_password']
    email = session['recuperacion_email']
    hash_pass = generate_password_hash(new_password)
    users_db.update_one(
        {'email': email},
        {'$set': {'password': hash_pass}, '$unset': {'codigo_recuperacion': ''}}
    )
    session.pop('recuperacion_email', None)
    session.pop('codigo_verificado', None)
    flash('Contraseña actualizada exitosamente', 'success')
    return redirect(url_for('login.login'))

@login_bp.route('/perfil')
def perfil():
    if 'usuario' in session:
        return render_template('login/perfil.html', usuario=session['usuario'])
    return redirect(url_for('login.login'))

@login_bp.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login.login'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Por favor, inicia sesión para acceder', 'error')
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)
    return decorated_function