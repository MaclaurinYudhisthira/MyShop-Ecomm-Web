# env-1\Scripts\activate
# Set-ExecutionPolicy Unrestricted -Scope Process
# python app.py
from flask import Flask,render_template, redirect, url_for, request, session, flash, abort, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import pyotp
import os
import dotenv
from cryptography.fernet import Fernet
from twilio.rest import Client
import datetime

# loading .env
dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)


# global variables
hotp = pyotp.HOTP(pyotp.random_base32())


# app object
app=Flask(__name__)

# secret key for session
app.secret_key=os.getenv("SECRET_KEY")

# password encryption key
pass_key=bytes(os.getenv("PASS_KEY"), 'utf-8')

# email setup
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv("MAIL")
app.config['MAIL_PASSWORD'] = os.getenv("PASSWORD")
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# OTP SMS Setup
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')

# mail object
mail = Mail(app)

# database setup
app.config['SQLALCHEMY_DATABASE_URI']=f'mysql://{os.getenv("DB_USERNAME")}:{os.getenv("DB_PASSWORD")}@localhost:3306/ecomm'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=True

# db object
db=SQLAlchemy(app)

# DB Models
class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False )
    price = db.Column(db.Float, nullable=False)
    description=db.Column(db.String(500), nullable=False)
    category=db.Column(db.String(30), nullable=False)
    image=db.Column(db.String(500), nullable=False)
    def __init__(self,title,price,description,category,image): 
        self.title = title
        self.price = price
        self.description = description
        self.category = category
        self.image = image

class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    first_name=db.Column(db.String(50), nullable=False)
    last_name=db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120),unique=True, nullable=False)
    password=db.Column(db.String(150), nullable=False)
    phone_number=db.Column(db.String(13),unique=True, nullable=False)
    def __init__(self,first_name,last_name,email,phone_number,password):
        self.first_name=first_name
        self.last_name=last_name
        self.email = email
        self.password = password
        self.phone_number = phone_number

class Address(db.Model):
    addr_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),nullable=False)
    add_line_1=db.Column(db.String(200), nullable=False)
    add_line_2=db.Column(db.String(200),nullable=True)
    city=db.Column(db.String(50), nullable=False)
    state=db.Column(db.String(50), nullable=False)
    zip_code=db.Column(db.String(10), nullable=False)
    def __init__(self,user_id,add_line_1, add_line_2, city , state, zip_code):
        self.user_id=user_id
        self.add_line_1 = add_line_1
        self.add_line_2 = add_line_2
        self.city = city
        self.state = state
        self.zip_code = zip_code

class CartItems(db.Model):
    ci_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'),nullable=False)
    quantity=db.Column(db.Integer,nullable=False)
    def __init__(self,user_id, product_id, quantity):
        self.user_id=user_id
        self.product_id = product_id
        self.quantity = quantity

class SavedItems(db.Model):
    si_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'),nullable=False)
    def __init__(self,user_id, product_id):
        self.user_id=user_id
        self.product_id = product_id

class Orders(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('product.product_id'),nullable=False)
    time_placed = db.Column(db.String(20),nullable=False)
    amount = db.Column(db.Float, nullable=False)
    def __init__(self,user_id,address_id,time_placed,amount):
        self.user_id=user_id
        self.address_id=address_id
        self.time_placed=time_placed
        self.amount=amount

class OrderItems(db.Model):
    oi_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'),nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'),nullable=False)
    quantity=db.Column(db.Integer,nullable=False)
    def __init__(self,order_id,product_id, quantity):
        self.order_id=order_id
        self.product_id = product_id
        self.quantity = quantity

class Reviews(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'),nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'),nullable=False)
    text=db.Column(db.String(500), nullable=False)
    rating=db.Column(db.Integer,nullable=False)
    def __init__(self,user_id,product_id,text,rating):
        self.user_id = user_id
        self.product_id = product_id
        self.text = text
        self.rating = rating

class Admin(db.Model):
    adm_id = db.Column(db.Integer, primary_key=True)
    first_name=db.Column(db.String(50), nullable=False)
    last_name=db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120),unique=True, nullable=False)
    password=db.Column(db.String(150), nullable=False)
    phone_number=db.Column(db.String(13),unique=True, nullable=False)
    def __init__(self,first_name,last_name,email,phone_number,password):
        self.first_name=first_name
        self.last_name=last_name
        self.email = email
        self.password = password
        self.phone_number = phone_number

class Otp(db.Model):
    otp_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120),unique=True, nullable=False)
    def __init__(self,email):
        self.email = email

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categories = db.Column(db.String(500),nullable=False)
    def __init__(self,categories): 
        self.categories = categories

# Creating Database
db.create_all()

# Routes
# Product navigation and Display routes
@app.route("/")
@app.route("/home")
def home():
    _store=Store.query.all()[0]
    data={}
    categories=_store.categories.split(',')
    for category in categories:
        data[category]=Product.query.filter_by(category=category).all()[:4]
    return render_template("index.html",data=data,categories=categories)

@app.route("/category/<category>")
def category(category):
    data=Product.query.filter_by(category=category).all() 
    categories=Store.query.all()[0].categories.split(',')
    return render_template("category.html",data=data,categories=categories)

@app.route("/search",methods=['GET','POST'])
def search():
    if request.method=='POST':
        if request.form['query'].strip()=='':
            return redirect('/')
        data=Product.query.all()
        def mySearch(pro):
            query=request.form['query'].lower()
            if (query in pro.title.lower().split()) \
                or (query in pro.category.lower().split()) \
                or (query in pro.description.lower().split()) \
                or (query == pro.title.lower()) \
                or (query == pro.category.lower()):
                return True
            else:
                return False
        data=list(filter(mySearch,data))
    categories=Store.query.all()[0].categories.split(',')
    return render_template("search.html",data=data,categories=categories,searchterm=request.form['query'])
    
@app.route("/product/<product_id>")
def product(product_id):
    user_rev=None
    product=Product.query.filter_by(product_id=product_id).first()
    reviews=[]
    for rev in Reviews.query.filter_by(product_id=product_id).all():
        if 'user_id' in session and rev.user_id==session['user_id']:
            usr=Users.query.filter_by(user_id=rev.user_id).first()
            user_rev=(rev,usr.first_name+' '+usr.last_name)
        else:
            usr=Users.query.filter_by(user_id=rev.user_id).first()
            reviews.append((rev,usr.first_name+' '+usr.last_name))
    categories=Store.query.all()[0].categories.split(',')
    return render_template("showproduct.html",item=product,reviews=reviews,user_rev=user_rev,categories=categories)

# Cart routes
@app.route("/cart")
def cart():
    cart=None
    total=0
    cats=Store.query.all()[0].categories.split(',')
    if 'cart' in session:
        cart=[]
        for product_id,quantity in session['cart'].items():
            item=Product.query.filter_by(product_id=product_id).first()
            cart.append((item,quantity))
            total+=(item.price*int(quantity))
    return render_template("cart.html",cart=cart,categories=cats,total=total)

@app.route("/addToCart",methods=['POST'])
def addToCart():
    if request.method=='POST':
        if 'cart' in session:
            di=session['cart']
            if request.form['product_id'] in di:
                di[request.form['product_id']]+=1
                if 'user_id' in session:
                    item=CartItems.query.filter_by(user_id=session['user_id']).filter_by(product_id=request.form['product_id']).first()
                    item.quantity=item.quantity+1
                    db.session.commit()
                session['cartlen']+=1
            else:
                di[request.form['product_id']]=1
                if 'user_id' in session:
                    db.session.add(CartItems(session['user_id'],int(request.form['product_id']),1))
                    db.session.commit()
                session['cartlen']+=1
        else:
            di={}
            di[request.form['product_id']]=1
            if 'user_id' in session:
                db.session.add(CartItems(session['user_id'],int(request.form['product_id']),1))
                db.session.commit()
            session['cart']=di
            session['cartlen']=1
        return redirect(request.referrer)

@app.route("/updateCart",methods=['POST'])
def updateCart():
    if request.method=='POST':
        if 'cart' in session:
            di=session['cart']
            if request.form['product_id'] in di:
                if request.form['quantity']=='0':
                    session['cartlen']=int(session['cartlen'])-int(di[request.form['product_id']])
                    del di[request.form['product_id']]
                    if 'user_id' in session:
                        item=CartItems.query.filter_by(user_id=session['user_id']).filter_by(product_id=request.form['product_id']).first()
                        db.session.delete(item)
                        db.session.commit()
                else:
                    session['cartlen']=int(session['cartlen'])-(int(di[request.form['product_id']])-int(request.form['quantity']))
                    di[request.form['product_id']]=int(request.form['quantity'])
                    if 'user_id' in session:
                        item=CartItems.query.filter_by(user_id=session['user_id']).filter_by(product_id=request.form['product_id']).first()
                        item.quantity=int(request.form['quantity'])
                        db.session.commit()
                session['cart']=di
                if int(session['cartlen'])==0:
                    session.pop('cart')
                    session.pop('cartlen')  
            return redirect(url_for("cart"))

# User auth routes
@app.route("/userSignIn",methods=['GET','POST'])
def userSignIn():
    if 'user_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        if request.method=="POST":
            if Users.query.filter_by(email=request.form['email'].lower()).first():
                found_user=Users.query.filter_by(email=request.form['email'].lower()).first()
            else:
                found_user=Users.query.filter_by(phone_number=request.form['email'].lower()).first()
            if found_user:
                f=Fernet(pass_key)
                Myword=f.decrypt(found_user.password.encode()).decode()
                if request.form['password']==Myword:
                    cart=None
                    if 'cart' in session:
                        cart=session['cart']
                    session.clear()
                    session['user_id']=found_user.user_id
                    session['first_name']=found_user.first_name
                    di={}
                    for item in CartItems.query.filter_by(user_id=session['user_id']).all():
                        di[f"{item.product_id}"]=item.quantity
                    if cart:
                        for key in [key for key in cart.keys() if key in di.keys()]:
                            di[key]+=cart[key]
                            item=CartItems.query.filter_by(product_id=int(key)).first()
                            item.quantity=item.quantity+cart[key]
                            db.session.commit()
                        for key in [key for key in cart.keys() if key not in di.keys()]:
                            di[key]=cart[key]
                            db.session.add(CartItems(session['user_id'],int(key),cart[key]))
                            db.session.commit()
                        found_user.cartlen=sum(di.values())
                    session['cart']=di
                    session['cartlen']=sum(di.values())
                    db.session.commit()
                    flash('You have logged in Successfully','success')
                    return redirect(url_for("home"))
            flash('Incorrect Email or Password','error')
            return redirect(url_for("userSignIn"))
        else:
            return render_template("user/signin.html")

@app.route("/userSignUp",methods=['GET','POST'])
def userSignUp():
    if 'user_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        if request.method=="POST":
            if Users.query.filter_by(email=request.form['email'].lower()).first():
                flash('This Email address is already registerd','error')
                return render_template("user/signup/signup.html")
            else:
                if Otp.query.filter_by(email=request.form['email'].lower()).first():
                    db.session.delete(Otp.query.filter_by(email=request.form['email'].lower()).first())
                    db.session.commit()
                db.session.add(Otp(email=request.form['email'].lower()))
                db.session.commit()
                msg = Message('Sign OTP | MyShop', sender=app.config.get("MAIL_USERNAME"), recipients = [request.form['email'].lower()])
                msg.body = f"Your OTP is {hotp.at(Otp.query.filter_by(email=request.form['email'].lower()).first().otp_id)}"
                mail.send(msg)
                session['xmail']=request.form['email'].lower()
                return render_template("user/signup/signupotp.html",email=request.form['email'].lower())
        else:
            return render_template("user/signup/signup.html")

@app.route("/validateSignUpOTP", methods=['POST'])
def validateSignUpOTP():
    if 'user_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        if request.method=="POST":
            if hotp.verify(request.form['otp'], Otp.query.filter_by(email=session['xmail'].lower()).first().otp_id):
                db.session.delete(Otp.query.filter_by(email=session['xmail'].lower()).first())
                db.session.commit()
                return render_template("user/signup/signupgetphone.html")
            else:
                db.session.delete(Otp.query.filter_by(email=session['xmail'].lower()).first())
                db.session.commit()
                session.pop('xmail')
                flash('OTP was wrong','info')
                return redirect(url_for("userSignUp"))

@app.route("/registerUser", methods=['POST'])
def registerUser():
    if 'user_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        if request.method=="POST":
            Myword=request.form['password'].encode()
            f=Fernet(pass_key)
            Myword=f.encrypt(Myword).decode()
            adm=Users(request.form['first_name'].lower().capitalize(),request.form['last_name'].lower().capitalize(),session['xmail'].lower(),session['xnum'].lower(),Myword)
            db.session.add(adm)
            db.session.commit()
            cart=None
            if 'cart' in session:
                cart=session['cart']
            xmail=session['xmail'].lower()
            session.clear()
            session['user_id']=Users.query.filter_by(email=xmail).first().user_id
            session['first_name']=Users.query.filter_by(email=xmail).first().first_name
            add=Address(session['user_id'],request.form['add_line_1'], request.form['add_line_2'], request.form['city'], request.form['state'], request.form['zip_code'])
            db.session.add(add)
            db.session.commit()
            if cart:
                for key in cart.keys():
                    db.session.add(CartItems(session['user_id'],int(key),cart[key]))
                    db.session.commit()
                session['cart']=cart
            flash('Registered successfully','success')
            return redirect(url_for("home"))

@app.route("/sendPhoneOTP",methods=['POST'])
def sendPhoneOTP():
    if 'user_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        if request.method=="POST":
            if Users.query.filter_by(phone_number=request.form['phone_number'].lower()).first():
                flash('This Phone Number address is already registerd','error')
                return redirect(url_for("userSignUp"))
            else:
                if Otp.query.filter_by(email=request.form['phone_number'].lower()).first():
                    db.session.delete(Otp.query.filter_by(email=request.form['phone_number'].lower()).first())
                    db.session.commit()
                db.session.add(Otp(email=request.form['phone_number'].lower()))
                db.session.commit()
                client = Client(account_sid, auth_token)
                message = client.messages.create(
                                    body=f"Your OTP is {hotp.at(Otp.query.filter_by(email=request.form['phone_number'].lower()).first().otp_id)}",
                                    from_='+13197747814',
                                    to=request.form['phone_number']
                                )
                session['xnum']=request.form['phone_number']
                return render_template("user/signup/signupotpphone.html",email=request.form['phone_number'])

@app.route("/validatePhoneOTP", methods=['POST'])
def validatePhoneOTP():
    if 'user_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        if request.method=="POST":
            if hotp.verify(request.form['otp'], Otp.query.filter_by(email=session['xnum'].lower()).first().otp_id):
                db.session.delete(Otp.query.filter_by(email=session['xnum'].lower()).first())
                db.session.commit()
                return render_template("user/signup/signupsetpass.html")
            else:
                db.session.delete(Otp.query.filter_by(email=session['xnum'].lower()).first())
                db.session.commit()
                session.pop('xmail')
                session.pop('xnum')
                flash('OTP was wrong','info')
                return redirect(url_for("userSignUp"))

@app.route("/signout")
def signout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/userForgotPassword")
def userForgotPassword():
    if 'user_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        return render_template("user/resetpassword/takemail.html")

@app.route("/userFPOTP", methods=['POST'])
def userFPOTP():
    if 'user_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        if request.method=="POST":
            if Users.query.filter_by(email=request.form['email'].lower()).first():
                if Otp.query.filter_by(email=request.form['email'].lower()).first():
                    db.session.delete(Otp.query.filter_by(email=request.form['email'].lower()).first())
                    db.session.commit()
                db.session.add(Otp(email=request.form['email'].lower()))
                db.session.commit()
                msg = Message('Sign OTP | MyShop', sender=app.config.get("MAIL_USERNAME"), recipients = [request.form['email'].lower()])
                msg.body = f"Your OTP is {hotp.at(Otp.query.filter_by(email=request.form['email'].lower()).first().otp_id)}"
                mail.send(msg)
                session['xmail']=request.form['email'].lower()
                return render_template("user/resetpassword/otp.html",email=session['xmail'])
            else:
                flash("This email is not registered.",'error')
                return redirect(url_for('userForgotPassword'))

@app.route("/validateFPOTP", methods=['POST'])
def validateFPOTP():
    if 'user_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        if request.method=="POST":
            if hotp.verify(request.form['otp'],Otp.query.filter_by(email=session['xmail'].lower()).first().otp_id):
                db.session.delete(Otp.query.filter_by(email=session['xmail'].lower()).first())
                db.session.commit()
                return render_template("user/resetpassword/resetpassword.html")
            else:
                db.session.delete(Otp.query.filter_by(email=session['xmail'].lower()).first())
                db.session.commit()
                session.pop('xmail')
                flash('OTP was wrong','info')
                return redirect(url_for("userSignUp"))

@app.route("/userResetPassword", methods=['POST'])
def userResetPassword():
    if 'user_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        if request.method=='POST':
            if 'xmail' in session:
                adm=Users.query.filter_by(email=session['xmail'].lower()).first()
                Myword=request.form['password'].encode()
                f=Fernet(pass_key)
                Myword=f.encrypt(Myword).decode()
                adm.password=Myword
                db.session.commit()
                session.clear()
                flash("Password updated successfully")
                return redirect(url_for("home"))
        else:
            abort(404)
    abort(404)

@app.route("/userProfile", methods=['POST','GET'])
def userProfile():
    if 'user_id' in session:
        user=Users.query.filter_by(user_id=session['user_id']).first()
        adds=Address.query.filter_by(user_id=session['user_id']).all()
        if request.method=="POST":
            # flash("userProfile updated successfully")
            pass
        cartlen=None
        return render_template("user/userProfile.html",user=user,adds=adds)
    else:
        flash('You are not logged in','info')
        return redirect(url_for("signin"))

@app.route("/saveItem/<product_id>",methods=['GET'])
def saveItem(product_id):
    if 'user_id' in session:
        session['cartlen']=int(session['cartlen'])-int(session['cart'][f'{product_id}'])
        del session['cart'][f'{product_id}']
        item=CartItems.query.filter_by(user_id=session['user_id']).filter_by(product_id=product_id).first()
        db.session.delete(item)
        if not SavedItems.query.filter_by(user_id=session['user_id']).filter_by(product_id=product_id).first():
            db.session.add(SavedItems(session['user_id'],product_id))
            db.session.commit()
        flash('Item saved for later','info')
        return redirect(request.referrer)
    else:
        abort(404)

@app.route("/savedItems")
def savedItems():
    if 'user_id' in session:
        items=[]
        for item in SavedItems.query.filter_by(user_id=session['user_id']).all():
            items.append(Product.query.filter_by(product_id=item.product_id).first())
        return render_template('user/saveditems.html',items=items)
    else:
        abort(404)

@app.route("/removeFromSaved/<product_id>/<int:f>")
def removeFromSaved(product_id,f):
    if 'user_id' in session:
        item=SavedItems.query.filter_by(product_id=product_id).first()
        db.session.delete(item)
        db.session.commit()
        if f==1:
            if 'cart' in session:
                di=session['cart']
                if product_id in di:
                    di[product_id]+=1
                    if 'user_id' in session:
                        item=CartItems.query.filter_by(user_id=session['user_id']).filter_by(product_id=product_id).first()
                        item.quantity=item.quantity+1
                        db.session.commit()
                    session['cartlen']+=1
                else:
                    di[product_id]=1
                    if 'user_id' in session:
                        db.session.add(CartItems(session['user_id'],int(product_id),1))
                        db.session.commit()
                    session['cartlen']+=1
            else:
                di={}
                di[product_id]=1
                if 'user_id' in session:
                    db.session.add(CartItems(session['user_id'],int(product_id),1))
                    db.session.commit()
                session['cart']=di
                session['cartlen']=1
        return redirect(request.referrer)
    else:
        abort(404)

@app.route("/checkOut")
def checkOut():
    if 'user_id' in session:
        cart=None
        total=0
        cats=Store.query.all()[0].categories.split(',')
        if 'cart' in session:
            cart=[]
            for product_id,quantity in session['cart'].items():
                item=Product.query.filter_by(product_id=product_id).first()
                cart.append((item,quantity))
                total+=(item.price*int(quantity))
            adds=Address.query.filter_by(user_id=session['user_id']).all()
            return render_template("user/checkout.html",cart=cart,categories=cats,total=total,adds=adds)
    else:
        flash('Sign in required for checkout','error')
        return redirect(url_for("userSignIn"))

@app.route("/addAddress", methods=['POST'])
def addAddress():
    if 'user_id' in session:
        if request.method=='POST':
            add=Address(session['user_id'],request.form['add_line_1'], request.form['add_line_2'], request.form['city'], request.form['state'], request.form['zip_code'])
            db.session.add(add)
            db.session.commit()
            return redirect(request.referrer)
    else:
        flash('Sign in required','error')
        return redirect(url_for("userSignIn"))

@app.route("/placeOrder", methods=['POST'])
def placeOrder():
    if 'user_id' in session:
        if request.method=='POST':
            ts=str(datetime.datetime.now())[:19]
            ordr=Orders(session['user_id'],int(request.form['address_id']),ts,float(request.form['total']))
            db.session.add(ordr)
            db.session.commit()
            ordr=Orders.query.filter_by(time_placed=ts).first()
            if 'cart' in session:
                cart=[]
                for product_id,quantity in session['cart'].items():
                    OI=OrderItems(ordr.order_id,int(product_id),int(quantity))
                    db.session.add(OI)
                    db.session.commit()
                for item in CartItems.query.filter_by(user_id=session['user_id']).all():
                    db.session.delete(item)
                    db.session.commit()
                session.pop('cart')
                session.pop('cartlen')
            flash('Order Placed Successfully!!!')
            return redirect(url_for('home'))
    else:
        flash('Sign in required','error')
        return redirect(url_for("userSignIn"))

@app.route("/myOrders", methods=['POST','GET'])
def myOrders():
    if 'user_id' in session:
        if request.method=='POST':
            for item in OrderItems.query.filter_by(order_id=request.form['order_id']).all():
                db.session.delete(item)
                db.session.commit()
            db.session.delete(Orders.query.filter_by(order_id=request.form['order_id']).first())
            db.session.commit()
            flash('Order Cancled...!!!','info')
            return redirect(request.referrer)
        else:
            cartlen=None
            cats=Store.query.all()[0].categories.split(',')
            data=[]
            for order in Orders.query.filter_by(user_id=session['user_id']).all():
                product=[]
                for item in OrderItems.query.filter_by(order_id=order.order_id).all():
                    product.append((Product.query.filter_by(product_id=item.product_id).first(),item.quantity))
                data.append((order,product,Address.query.filter_by(addr_id=order.address_id).first()))
            return render_template("user/myorders.html",categories=cats,data=data)
    else:
        flash('Sign in required','error')
        return redirect(url_for("userSignIn"))

@app.route("/addReview", methods=['POST'])
def addReview():
    if request.method=='POST':
        if 'user_id' in session:
            db.session.add(Reviews(session['user_id'],request.form['product_id'],request.form['text'],request.form['rating']))
            db.session.commit()
            return redirect(request.referrer)

@app.route("/editReview", methods=['POST'])
def editReview():
    if request.method=='POST':
        if 'user_id' in session:
            rev=Reviews.query.filter_by(review_id=request.form['review_id']).first()
            rev.text=request.form['text']
            rev.rating=request.form['rating']
            db.session.commit()
            return redirect(request.referrer)

# Admin Routes
@app.route("/myShopAdmin", methods=['GET','POST'])
def myShopAdmin():
    if 'admin_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("adminDashboard"))
    else:
        if bool(int(os.getenv("ADMIN_EXISTS"))):
            if request.method=='GET':
                return render_template('admin/signin.html')
            if request.method=='POST':
                if 'admin_id' in session:
                    flash('Existing login is found','error')
                    return redirect(url_for("home"))
                else:
                    print(Admin.query.all())
                    if Admin.query.filter_by(email=request.form['email'].lower()).first():
                        found_user=Admin.query.filter_by(email=request.form['email'].lower()).first()
                    else:
                        found_user=Admin.query.filter_by(phone_number=request.form['email'].lower()).first()
                    if found_user:
                        f=Fernet(pass_key)
                        Myword=f.decrypt(found_user.password.encode()).decode()
                        if request.form['password']==Myword:
                            session['admin_id']=found_user.adm_id
                            flash('You have logged in Successfully','success')
                            return redirect(url_for("adminDashboard"))
                    flash('Incorrect Email or Password','error')
                    return redirect(url_for("myShopAdmin"))
        elif not bool(int(os.getenv("ADMIN_EXISTS"))):
            if request.method=="GET":
                return render_template('admin/signup/signup.html')
            elif request.method=="POST":
                if Otp.query.filter_by(email=request.form['email'].lower()).first():
                    db.session.delete(Otp.query.filter_by(email=request.form['email'].lower()).first())
                    db.session.commit()
                db.session.add(Otp(email=request.form['email'].lower()))
                db.session.commit()
                msg = Message('Sign up OTP | MyShop Admin', sender=app.config.get("MAIL_USERNAME"), recipients = [request.form['email'].lower()])
                msg.body = f"Your OTP is {hotp.at(Otp.query.filter_by(email=request.form['email'].lower()).first().otp_id)}"
                mail.send(msg)
                print(hotp.at(Otp.query.filter_by(email=request.form['email'].lower()).first().otp_id))
                session['xmail']=request.form['email'].lower()
                return render_template("admin/signup/signupotp.html",email=request.form['email'].lower())
    return redirect(url_for('err'))

@app.route("/adminSignUpOTP", methods=['POST'])
def adminSignUpOTP():
    if not bool(int(os.getenv("ADMIN_EXISTS"))):
        if 'admin_id' in session:
            flash('Existing login is found','error')
            return redirect(url_for("adminDadshboard"))
        else:
            if request.method=="POST":
                if hotp.verify(request.form['otp'], Otp.query.filter_by(email=session['xmail'].lower()).first().otp_id):
                    db.session.delete(Otp.query.filter_by(email=session['xmail'].lower()).first())
                    db.session.commit()
                    return render_template("admin/signup/signupgetphone.html")
                else:
                    db.session.delete(Otp.query.filter_by(email=session['xmail'].lower()).first())
                    db.session.commit()
                    session.pop('xmail')
                    flash('OTP was wrong','info')
                    return redirect(url_for("myShopAdmin"))
    else:
        return redirect('err')

@app.route("/adminPhoneOTP", methods=['POST'])
def adminPhoneOTP():
    if not bool(int(os.getenv("ADMIN_EXISTS"))):
        if 'admin_id' in session:
            flash('Existing login is found','error')
            return redirect(url_for("adminDadshboard"))
        else:
            if request.method=="POST":
                if Otp.query.filter_by(email=request.form['phone_number'].lower()).first():
                    db.session.delete(Otp.query.filter_by(email=request.form['phone_number'].lower()).first())
                    db.session.commit()
                db.session.add(Otp(email=request.form['phone_number'].lower()))
                db.session.commit()
                client = Client(account_sid, auth_token)
                message = client.messages.create(
                                    body=f"Your OTP is {hotp.at(Otp.query.filter_by(email=request.form['phone_number'].lower()).first().otp_id)}",
                                    from_='+13197747814',
                                    to=request.form['phone_number']
                                )
                print(hotp.at(Otp.query.filter_by(email=request.form['phone_number'].lower()).first().otp_id))
                session['xnum']=request.form['phone_number']
                return render_template("admin/signup/signupotpphone.html",email=request.form['phone_number'])
    else:
        return redirect('err')

@app.route("/adminValidatePhoneOTP", methods=['POST'])
def adminValidatePhoneOTP():
    if not bool(int(os.getenv("ADMIN_EXISTS"))):
        if 'admin_id' in session:
            flash('Existing login is found','error')
            return redirect(url_for("adminDadshboard"))
        else:
            if request.method=="POST":
                if hotp.verify(request.form['otp'], Otp.query.filter_by(email=session['xnum'].lower()).first().otp_id):
                    db.session.delete(Otp.query.filter_by(email=session['xnum'].lower()).first())
                    db.session.commit()
                    return render_template("admin/signup/signupsetpass.html")
                else:
                    db.session.delete(Otp.query.filter_by(email=session['xnum'].lower()).first())
                    db.session.commit()
                    session.pop('xmail')
                    session.pop('xnum')
                    flash('OTP was wrong','info')
                    return redirect(url_for("myShopAdmin"))
    else:
        return redirect('err')

@app.route("/registerAdmin", methods=['GET','POST'])
def registerAdmin():
    if not bool(int(os.getenv("ADMIN_EXISTS"))):
        if 'admin_id' in session:
            flash('Existing login is found','error')
            return redirect(url_for("adminDadshboard"))
        else:
            if request.method=="POST":
                Myword=request.form['password'].encode()
                f=Fernet(pass_key)
                Myword=f.encrypt(Myword).decode()
                adm=Admin(request.form['first_name'].lower().capitalize(),request.form['last_name'].lower().capitalize(),session['xmail'].lower(),session['xnum'].lower(),Myword)
                db.session.add(adm)
                db.session.commit()
                xmail=session['xmail'].lower()
                session.clear()
                session['admin_id']=Users.query.filter_by(email=xmail).first().adm
                session['first_name']=Users.query.filter_by(email=xmail).first().first_name
                print(os.environ["ADMIN_EXISTS"])
                os.environ["ADMIN_EXISTS"] = "1"
                print(os.environ['ADMIN_EXISTS'])  
                dotenv.set_key(dotenv_file, "ADMIN_EXISTS", os.environ["ADMIN_EXISTS"])
                flash('Registered successfully','success')
                return redirect(url_for("adminDashboard"))
    else:
        return redirect('err')

@app.route("/adminForgotPassword")
def adminForgotPassword():
    if 'admin_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("signout"))
    else:
        return render_template("admin/resetpassword/takemail.html")

@app.route("/adminFPOTP", methods=['POST'])
def adminFPOTP():
    if 'admin_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("signout"))
    else:
        if request.method=="POST":
            if Admin.query.filter_by(email=request.form['email'].lower()).first():
                if Otp.query.filter_by(email=request.form['email'].lower()).first():
                    db.session.delete(Otp.query.filter_by(email=request.form['email'].lower()).first())
                    db.session.commit()
                db.session.add(Otp(email=request.form['email'].lower()))
                db.session.commit()
                msg = Message('Forget password OTP | MyShop Admin', sender=app.config.get("MAIL_USERNAME"), recipients = [request.form['email'].lower()])
                msg.body = f"Your OTP is {hotp.at(Otp.query.filter_by(email=request.form['email'].lower()).first().otp_id)}"
                # mail.send(msg)
                print(hotp.at(Otp.query.filter_by(email=request.form['email'].lower()).first().otp_id))
                session['xmail']=request.form['email'].lower()
                return render_template("admin/resetpassword/otp.html",email=session['xmail'])
            else:
                flash("This email is not registered.",'error')
                return redirect(url_for('adminForgotPassword'))

@app.route("/adminValidateFPOTP", methods=['POST'])
def adminValidateFPOTP():
    if 'admin_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        if request.method=="POST":
            if hotp.verify(request.form['otp'],Otp.query.filter_by(email=session['xmail'].lower()).first().otp_id):
                db.session.delete(Otp.query.filter_by(email=session['xmail'].lower()).first())
                db.session.commit()
                return render_template("admin/resetpassword/resetpassword.html")
            else:
                db.session.delete(Otp.query.filter_by(email=session['xmail'].lower()).first())
                db.session.commit()
                session.pop('xmail')
                flash('OTP was wrong','info')
                return redirect(url_for("adminSignUp"))

@app.route("/adminResetPassword", methods=['POST'])
def adminResetPassword():
    if 'admin_id' in session:
        flash('Existing login is found','error')
        return redirect(url_for("home"))
    else:
        if request.method=='POST':
            if 'xmail' in session:
                adm=Admin.query.filter_by(email=session['xmail'].lower()).first()
                Myword=request.form['password'].encode()
                f=Fernet(pass_key)
                Myword=f.encrypt(Myword).decode()
                adm.password=Myword
                db.session.commit()
                session.clear()
                flash("Password updated successfully")
                return redirect(url_for("myShopAdmin"))
        else:
            abort(404)
    abort(404)

@app.route("/adminDashboard", methods=['GET','POST'])
def adminDashboard():
    if bool(int(os.getenv("ADMIN_EXISTS"))):
        if 'admin_id' in session:
            return render_template('admin/dashboard.html')
    else:
        return redirect('err')
    abort(404)

@app.route("/admin/tables/<table>", methods=['GET','POST'])
def adminTables(table):
    data=None
    if table=='products':
        data=Product.query.all()
        return render_template('admin/products.html',data=data)
    if table=='orders':
        data=Orders.query.all()
        return render_template('admin/orders.html',data=data)
    if table=='users':
        data=Users.query.all()
        return render_template('admin/users.html',data=data)
    if table=='addresses':
        data=Address.query.all()
        return render_template('admin/addresses.html',data=data)
    if table=='reviews':
        data=Reviews.query.all()
        return render_template('admin/reviews.html',data=data)
# error handlers
@app.errorhandler(404) 
def not_found(e): 
    return render_template('404.html')

@app.route("/err")
def err():
    return render_template("err.html")

#Developer only routes
import csv
@app.route("/load")
def load():
    _str=""
    with open('RESULT.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                pro=Product(row[0],row[1],row[2],row[3],row[4])
                db.session.add(pro)
                db.session.commit()
                line_count += 1
    _store=Store("Women Clothing,Men Clothing,Women Shoes,Men Shoes")
    Myword='123'.encode()
    f=Fernet(pass_key)
    Myword=f.encrypt(Myword).decode()
    user=Users('Kishan','Dasondhi','kishandasondhi123@gmail.com','+919981392771',Myword)
    db.session.add(_store)
    db.session.add(user)
    db.session.add(Users('John','Doe','jd@gmail.com','+919981392772',Myword))
    db.session.add(Users('Jane','Doe','dj@gmail.com','+919981392773',Myword))
    db.session.add(Users('Princy','Pi','ppi@gmail.com','+919981392774',Myword))
    db.session.add(Users('Arman','Malik','amalik@gmail.com','+919981392775',Myword))
    db.session.commit()
    db.session.add(Reviews(2,37,'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla a sodales metus. Nullam dapibus ligula vehicula libero tincidunt, laoreet imperdiet tortor viverra.',4))
    db.session.add(Reviews(4,37,'Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.',4))
    db.session.add(Reviews(3,37,'Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.',5))
    db.session.add(Reviews(1,37,'Phasellus vel ipsum ligula. Ut sagittis ligula ut lectus condimentum, et lacinia risus sollicitudin. Phasellus quis lacus a nulla condimentum hendrerit non eget ex.',2))
    db.session.commit()
    db.session.add(Address(1,"123, bakers Street",'My colony','Indore','MP',450022))
    db.session.add(Address(1,"321, Londen dairy",None,'Indore','MP',874676))
    db.session.add(Address(1,'75, Dazzel Town','Rose square','Tokyo','MSstate',414455))
    db.session.add(CartItems(1,27,3))
    db.session.add(CartItems(1,26,1))
    db.session.commit()
    return "DONE <a href='/'>Home</a>"

if __name__ == "__main__":
    app.run(debug=True)