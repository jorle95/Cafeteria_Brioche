from flask import Flask, render_template, request, redirect, url_for, Response,make_response,session,redirect
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_login import LoginManager, UserMixin,login_user,login_required,current_user,logout_user
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta, date, datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from flask.helpers import flash


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bd/cafeteria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']='secret'
app.config['REMEMBER_COOKIE_DURATION']=timedelta(seconds=20)
app.config['DEBUG'] = True 
app.config['TESTING'] = False
app.config['MAIL_SERVER'] ='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
#app.config['MAIL_DEBUG'] = True
app.config['MAIL_USERNAME'] = 'cafbrioche@gmail.com'
app.config['MAIL_PASSWORD'] = '123456789@#'
app.config['MAIL_DEFAULT_SENDER'] = ('Cafetería Brioche', 'cafbrioche@gmail.com')
app.config['MAIL_MAX_EMAILS'] = None
#app.config['MAIL_SUPPRESS_SEND'] = False
app.config['MAIL_ASCII_ATTACHMENTS'] = False

cajeros=[("cajero1","456"), ("cajero2","abc"), ("cajero3","789"), ("cajero4","aaaa")]
mail=Mail(app)
limiter=Limiter(app, key_func=get_remote_address)
db = SQLAlchemy(app)
login_manager=LoginManager(app)

#//////////////////////////////////////////////////////////////////
#///////////////////TABLAS DE LA BASE DE DATOS/////////////////////
#//////////////////////////////////////////////////////////////////

class Producto (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.Text(200))
    Precio_Unidad= db.Column(db.Integer)
    Cantidad= db.Column(db.Integer)
    Categoria= db.Column(db.Text(200))
    img = db.Column(db.Text)
    name = db.Column(db.Text)
    mimetype = db.Column(db.Text)

class Usuario(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.Text(200))
    Correo= db.Column(db.Text(200),unique=True)
    Contraseña=db.Column(db.Text(200))
    Usuario=db.Column(db.Text(200),unique=True)
    Telefono=db.Column(db.Integer)

class prods_venta(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    idProducto= db.Column(db.Integer)
    idVenta=db.Column(db.Integer)
    cantVenta=db.Column(db.Integer)

class carrito_venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idProducto=db.Column(db.Integer)
    nombreProducto=db.Column(db.Integer)
    precioProducto=db.Column(db.Integer)
    idUsuario= db.Column(db.Integer)
    precioVenta=db.Column(db.Integer)
    cantidadProducto=db.Column(db.Integer)

class Venta(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    Fecha=db.Column(db.Text(200))
    valorVenta=db.Column(db.Integer)

login_manager.session_protection = "strong"
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

#//////////////////////////////////////////////////////////////////
#//////////////////////////PAGINAS/////////////////////////////////
#//////////////////////////////////////////////////////////////////

@app.route('/mailCrd', methods=['POST'])
def mailCrd():
    if request.method == 'POST':
        correoPsw=request.form.get('correoCrd')
        us=Usuario.query.filter_by(Correo=correoPsw).first()
        if us:            
            msg = Message("Link para modificar la contraseña del usuario: "+us.Usuario)
            msg.add_recipient(correoPsw)
            msg.body = 'A continuacion se mostrara el link con el cual puede acceder el usuario :'+us.Usuario+'\nTenga en cuenta que la solicitud de cambio de contraseña solo se puede hacer una vez por dia, independientemente del usuario que solicite la recuperacion .'+'\n https://54.91.198.18/Modificacion'
            mail.send(msg)
            return render_template('index.html', mensaje='Correo con Credenciales enviado')
        else:
            return render_template('RecupeContra.html', mensaje='Correo no registrado')

@app.route('/Modificacion/', methods=["GET","POST"])
@limiter.limit("2/day")
def ModificarContra():
    if request.method == 'POST':
        Usu=request.form.get('Usuario')
        Contraseña=request.form.get('contra')
        us=Usuario.query.filter_by(Usuario=Usu).first()
        if us:            
            us.Contraseña =generate_password_hash(Contraseña, method='sha256')
            db.session.commit()
            return render_template('index.html', mensaje='Contraseña Actualizada')
        else:
            return render_template('ModContra.html', mensaje='Usuario no registrado')
    else:
    	return render_template('ModContra.html') 


@app.route('/')
def inicio():
    return render_template('index2.html')

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

#//////////////////////////////////////////////////////////////////
#////////////////////////////LOGIN/////////////////////////////////
#//////////////////////////////////////////////////////////////////

@app.route('/login',methods=["GET","POST"])
def login():
    logout_user()
    if request.method == 'POST':
        u=request.form.get('usuario')
        psw=request.form.get('password')
        us=Usuario.query.filter_by(Usuario=u).first()
        if us:
            if us.Usuario=='Administrador'and check_password_hash(us.Contraseña,psw):
                login_user(us,remember=True)
                return redirect (url_for('Abienvenida'))
            else:
                if check_password_hash(us.Contraseña,psw):
                    login_user(us, remember=True)
                    return render_template('Cbienvenida.html')
                return render_template('index.html', mensaje='Usuario o Contraseña incorrecta')
        else: 
            return render_template('index.html', mensaje='Usuario o Contraseña incorrecta')
    else:
        return render_template('index.html')


@app.route('/Abienvenida',methods=["GET","POST"])
def Abienvenida():
    return render_template('Abienvenida.html')  
    

@app.route('/recuperacion')
def recuperacion():
    return render_template('RecupeContra.html')




#//////////////////////////////////////////////////////////////////
#////////////////////////PRODUCTOS/////////////////////////////////
#//////////////////////////////////////////////////////////////////

@app.route('/productos/crear/agregar',methods=["GET","POST"])
@login_required
def agregar():
    #Agregar imagenes
    pic = request.files['pic']
    if not pic:
        return 'No se selecciono una imagen!', 400

    filename = secure_filename(pic.filename)
    mimetype = pic.mimetype
    if not filename or not mimetype:
        return 'Archivo no soportado!', 400

    #Agregar texto
    ref=request.form.get('referencia')
    nombre=request.form.get('Nombre')
    precio=request.form.get('Precio')
    categoria=request.form.get('Categoria')
    cantidad=request.form.get('Cantidad')
    if ref=="":
        nuevo_producto = Producto(Nombre=nombre, Precio_Unidad=precio, Cantidad=cantidad, Categoria=categoria, img=pic.read(), name=filename, mimetype=mimetype)
        db.session.add(nuevo_producto)
        db.session.commit()
        return redirect (url_for('crear'))
    else:
        nuevo_producto = Producto(id=int(ref), Nombre=nombre, Precio_Unidad=precio, Cantidad=cantidad, Categoria=categoria, img=pic.read(), name=filename, mimetype=mimetype)
        db.session.add(nuevo_producto)
        db.session.commit()
        return redirect (url_for('crear'))

#Cargar imagen del link en tabla

@app.route('/productos/crear/<int:id>')
@login_required
def get_img(id):
    img = Producto.query.filter_by(id=id).first()
    if not img:
        return 'Img Not Found!', 404

    return Response(img.img, mimetype=img.mimetype)


@app.route('/productos/crear', methods=["GET", "POST"])
@login_required
def crear():
    productos = Producto.query.all()
    return render_template('Crear.html', productos = productos)
 

@app.route('/productos/modificar', methods=["GET", "POST"])
@login_required
def modificar():
    idp=request.form.get('idp')
    nombre=request.form.get('Nombre')
    precio=request.form.get('Precio')
    categoria=request.form.get('Categoria')
    cantidad=request.form.get('Cantidad')

    prod = Producto.query.filter_by(id=int(idp)).first()
    if prod.Nombre != nombre or prod.Precio_Unidad != precio or prod.Categoria != categoria or prod.Cantidad != cantidad:
        prod.Nombre = nombre
        prod.Precio_Unidad = precio
        prod.Categoria = categoria
        prod.Cantidad = cantidad
    
        #Cambiar imagen
    pict = request.files['pict']
    if pict:
        prod.img=pict.read()
        prod.name = secure_filename(pict.filename)
        prod.mimetype = pict.mimetype
        db.session.commit()
    else:
        db.session.commit()
        return redirect (url_for('crear'))        

    return redirect (url_for('crear'))
    

@app.route('/productos/modificar/<int:id>', methods=["GET", "POST"])
@login_required
def modificarTb(id):
    prod = Producto.query.filter_by(id=id).first()
    return render_template('Modificar.html', id=id, Nombre=prod.Nombre, Precio=prod.Precio_Unidad, Categoria=prod.Categoria, Cantidad=prod.Cantidad)








#//////////////////////////////////////////////////////////////////
#/////////////////////////USUARIOS/////////////////////////////////
#//////////////////////////////////////////////////////////////////

@app.route('/registro', methods=["GET", "POST"])
@login_required
def registro():    
    empleados = Usuario.query.all()
    return render_template('Registro.html',empleados=empleados)  

@app.route('/registro/agregar',methods=["GET","POST"])
@login_required
def registro_creado():
    id=request.form.get('id')
    nombre=request.form.get('Nomb')
    usu=request.form.get('Usua')
    Correo=request.form.get('Correo')
    Telefono=request.form.get('Telefono')
    hashed_pss=generate_password_hash(request.form.get('Contra'), method='sha256')
    us=Usuario.query.filter_by(Usuario=usu).first()
    corr=Usuario.query.filter_by(Correo=Correo).first()
    if us or corr:
        empleados = Usuario.query.all()
        return render_template('Registro.html', mensaje='Usuario Existente',empleados=empleados)
    else:
        nuevo_producto = Usuario(Nombre=nombre, Usuario=usu,id=id, Correo=Correo,Telefono=Telefono,Contraseña=hashed_pss)
        db.session.add(nuevo_producto)
        db.session.commit()
        empleados = Usuario.query.all()
        return render_template('Registro.html', mensaje='Usuario Registrado',empleados=empleados)

#Boton eliminar en tabla productos
@app.route('/productos/eliminar/<int:id>',methods=["GET","POST"])
@login_required
def delete(id):
    producto = Producto.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect (url_for('crear'))

@app.route('/usuarios/modificar', methods=["GET", "POST"])
@login_required
def modificar_us():
    id=request.form.get('id')
    Nombre=request.form.get('Nombre')
    Correo=request.form.get('Correo')
    Contraseña=request.form.get('Contraseña')
    Usua=request.form.get('Usuario')
    Telefono=request.form.get('Telefono')
   
    us = Usuario.query.filter_by(id=id).first()
    if us.Nombre != Nombre or us.Correo !=  Correo or us.Usuario!=Usua or us.Telefono!=Telefono:
        us.id = id
        us.Nombre = Nombre 
        us.Correo =  Correo
        us.Contraseña =generate_password_hash(Contraseña, method='sha256')
        
        us.Usuario=Usua
        us.Telefono=Telefono
        db.session.commit()    
        return redirect (url_for('registro'))     
    return redirect (url_for('registro'))     


@app.route('/usuario/Empleados/<int:id>', methods=["GET", "POST"])
@login_required
def modificarEMP(id):
    us = Usuario.query.filter_by(id=id).first()
    return render_template('ModficacionUsu.html' , id=id, Nombre = us.Nombre , Correo= us.Correo , Contraseña= us.Contraseña, Usuario=us.Usuario, Telefono= us.Telefono)


@app.route('/usuario/eliminar/<int:id>',methods=["GET","POST"])
@login_required
def deleteEMP(id):
    us = Usuario.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect (url_for('registro'))

#//////////////////////////////////////////////////////////////////
#////////////////////////////CAJA//////////////////////////////////
#//////////////////////////////////////////////////////////////////

@app.route('/caja', methods=['GET'])
@login_required
def caja():
    productos = Producto.query.all()
    prodscarrito = carrito_venta.query.all()
    subtotal=0
    for prodcarrito in prodscarrito:
        subtotal=subtotal + prodcarrito.precioVenta
    iva = int(subtotal * 0.19)
    total= int(subtotal + iva)
    return render_template('caja.html',productos=productos,prodscarrito=prodscarrito,subtotalcarrito=int(subtotal),ivacarrito=iva,totalcarrito=total)

@app.route('/caja/agregar', methods=["POST"])
@login_required
def caja_agregar():
    idProducto=request.form.get('agregar')
    cantidadseleccion=request.form.get('cantidad')
    productoseleccionado=Producto.query.filter_by(id=idProducto).first()
    if productoseleccionado != None and (productoseleccionado.Cantidad-int(cantidadseleccion))>=0:
        nombreProducto=productoseleccionado.Nombre
        precioProducto=productoseleccionado.Precio_Unidad
        precioVenta=int(cantidadseleccion)*precioProducto
        cantidadProducto=cantidadseleccion
        nuevo_producto_carrito = carrito_venta(idProducto=idProducto, nombreProducto=nombreProducto, precioProducto=precioProducto, precioVenta=precioVenta,cantidadProducto=cantidadProducto)
        db.session.add(nuevo_producto_carrito)
        db.session.commit()
    else:
        if (productoseleccionado == None):
            flash("No tenemos productos en el inventario con esa referencia")
        else:
            flash("No tenemos cantidades suficientes para su pedido")
    return redirect (url_for('caja'))

@app.route('/caja/limpiar', methods=["GET"])
@login_required
def caja_Limpiar():
    items = carrito_venta.query.all()
    for item in items:
        carrito_venta.query.filter_by(id=item.id).delete()
        db.session.commit()
    return redirect (url_for('caja'))

@app.route('/caja/eliminar/<int:id>', methods=["GET"])
@login_required
def cajaEliminar(id):
    item = carrito_venta.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect (url_for('caja'))

@app.route('/caja/modificarcant/<int:id>', methods=["GET","POST"])
@login_required
def modificarcant(id):
    item = carrito_venta.query.filter_by(id=id).first()
    item.cantidadProducto=cantidadseleccion=request.form.get('cantidad')
    item.precioVenta=int(item.cantidadProducto)*item.precioProducto
    db.session.commit()
    return redirect (url_for('caja'))

@app.route('/caja/checkout')
@login_required
def checkout():
    prodscarrito = carrito_venta.query.all()
    subtotal=0
    for prodcarrito in prodscarrito:
        subtotal=subtotal + prodcarrito.precioVenta
    iva = int(subtotal * 0.19)
    total = int(subtotal + iva)
    hoy=date.today()
    fecha=hoy.strftime("%Y-%m-%d")
    nueva_venta = Venta(Fecha=fecha, valorVenta=total)
    db.session.add(nueva_venta)
    db.session.commit()
    for prodcarrito in prodscarrito:
        nuevoprodventa=prods_venta(idProducto=prodcarrito.idProducto,idVenta=nueva_venta.id,cantVenta=prodcarrito.cantidadProducto)
        db.session.add(nuevoprodventa)
        productoupdate=Producto.query.filter_by(id=prodcarrito.idProducto).first()
        productoupdate.Cantidad=productoupdate.Cantidad-prodcarrito.cantidadProducto
        db.session.commit()
    return render_template('checkout.html', prodscarrito = prodscarrito, subtotal=subtotal, iva=iva, totalcarrito=total)

#//////////////////////////////////////////////////////////////////
#////////////////////////////BUSQUEDA//////////////////////////////
#//////////////////////////////////////////////////////////////////

@app.route('/busqueda')
@login_required
def busqueda():
    path=urlparse(request.referrer).path
    print (path)
    if path == "/login":
        items = carrito_venta.query.all()
        for item in items:
            carrito_venta.query.filter_by(id=item.id).delete()
            db.session.commit()
    productos = Producto.query.all()
    return render_template('busqueda.html', productos = productos)

#//////////////////////////////////////////////////////////////////
#////////////////////////////REPORTE///////////////////////////////
#//////////////////////////////////////////////////////////////////

@app.route('/reporteventas', methods=['GET','POST'])
@login_required
def reporteventas():
    if request.method == 'POST':
        fecha=request.form.get('fechareporte')
    else:
        fecha=date.today()
    ventas = Venta.query.filter_by(Fecha=fecha).all()
    totalventas=0
    for venta in ventas:
        totalventas=totalventas + venta.valorVenta
    return render_template('reporteventas.html',ventas=ventas,totalventas=totalventas)

if __name__=='__main__':
    app.run(debug=True)

