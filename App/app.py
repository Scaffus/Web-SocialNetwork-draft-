from functools import partialmethod
from flask import Flask, redirect, url_for, render_template, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_manager, login_user, login_required, logout_user, current_user, LoginManager, UserMixin
from sqlalchemy.orm import defaultload
from werkzeug.security import check_password_hash, generate_password_hash
import uuid
from datetime import datetime
import logger

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/database.db'
app.config['SECRET_KEY'] = '16a627a9-a69b-4b07-7836-51bh32b1idm0'

db = SQLAlchemy(app)
SQLALCHEMY_TRACK_MODIFICATIONS = False

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

admins = ['']

@login_manager.user_loader
def load_user(mail):

    return User.query.get(mail)

class Post(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(70))
    content = db.Column(db.String(500))
    author_name = db.Column(db.String(24))
    author_uuid = db.Column(db.String(36))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.Boolean, default=False)
    uuid = db.Column(db.String(36))

class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36))
    username = db.Column(db.String(24))
    mail = db.Column(db.String(120))
    password = db.Column(db.String(80))
    joined = db.Column(db.DateTime, default=datetime.utcnow)
    post_number = db.Column(db.Integer, default=0)
    admin = db.Column(db.Boolean, default=False)
    ranks = db.Column(db.String, default='member')
    points = db.Column(db.Integer, default=0)

    def is_active(self):
        return True

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False
    
    # def is_admin(self):
    #     if self.uuid in admins:
    #         return True
    #     else:
    #         return False


@app.route('/')
def index():
    
    posts = Post.query.order_by(Post.date.desc()).all()

    return render_template('index.html', user=current_user, posts=posts)


@login_required
@app.route('/u/<string:username>',  methods=['GET', 'POST'])
def user(username):

    if username:

        user = User.query.filter_by(username=username).first()
        user_posts = Post.query.filter_by(author_uuid=user.uuid).all()

        return render_template('user/user.html', user=user, user_posts=user_posts)

    else:

        return render_template('user/user.html', username=username)

@app.route('/u/create', methods=['GET', 'POST'])
def user_create():
    
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        mail     = request.form['mail'].lower()

        # user = User.query.filter_by(mail=mail).first()

        # if user:
        #     flash('L\'addresse email existe déjà.', category='error')
        #     return redirect(url_for('user_create'))

        # elif len(username) < 3:
        #     flash('Le pseudonyme doit contennir plus de 2 caractères.', category='error')
        #     return redirect(url_for('user_create'))

        # elif len(password) < 8:
        #     flash('Le mot de passe doit faire au moins 8 caractères.', category='error')
        #     return redirect(url_for('user_create'))
            
        # elif len(mail) < 4:
        #     flash('L\'addresse mail doit contennir plus de 3 caractères.', category='error')
        #     return redirect(url_for('user_create'))

        # else:
        new_user = User(username=username.lower(), mail=mail.lower(), password=generate_password_hash(password, method='sha256'), uuid=str(uuid.uuid4()))
        
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user, remember=True)

        # flash('Compte créé avec succès!', category='success')

        return redirect(url_for('user_login'))
    return render_template('user/create.html', user=current_user)


@app.route('/u/login', methods=['GET', 'POST'])
def user_login():

    if request.method == 'POST':

        mail     = request.form['mail']
        password = request.form['password']

        user = User.query.filter_by(mail=mail).first()

        # if user:
        if check_password_hash(user.password, password):
            # flash('Vous avez été connecté avec succès!', category='success')
            login_user(user, remember=True)

            return redirect(url_for('index'))

        #     else:
        #         flash('Le mot de passe est incorrect.', category='error')
        # else:
        #     flash('L\'addresse email n\'existe pas.')

    return render_template('user/login.html', user=current_user)

@login_required
@app.route('/u/logout')
def logout():
    
    logout_user()
    
    return redirect(url_for('user_login'))

@login_required
@app.route('/p/new', methods=['GET', 'POST'])
def new_post():

    if request.method == 'POST':

        author_uuid = current_user.uuid
        content = request.form['content']
        title = request.form['title']

        if len(title) > 1 and len(content) > 10 and len(author_uuid) == 36:
            current_user.post_number += 1

            new_post = Post(author_uuid=author_uuid, author_name=current_user.username, title=title, content=content, uuid=str(uuid.uuid4()))

            db.session.add(new_post)
            db.session.commit()

        
        return redirect(url_for('index'))

    return render_template('post/create.html', user=current_user)


@login_required
@app.route('/p/delete')
def delete_post():
    
    post_uuid = request.args.get('post_uuid')
    
    post = Post.query.filter_by(uuid=post_uuid).first()
    
    if post:
    
        current_user.post_number -= 1
    
        db.session.delete(post)
        db.session.commit()
        
    
    return redirect(url_for('user', username=current_user.username))


@login_required
@app.route('/admin/dashboard')
def admin_dashboard():
    
    if current_user.admin is True:
        
        all_users = User.query.all()
        
        return render_template('admin/dashboard.html', user=current_user, all_users=all_users)

    else:
        
        return redirect(url_for('index'))
    

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
