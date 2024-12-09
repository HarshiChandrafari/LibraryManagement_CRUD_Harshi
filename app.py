
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
# from werkzeug.security import generate_password_hash, check_password_hash


# Determine the absolute path for the database file
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'library.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Important for flash messages
CORS(app)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
jwt = JWTManager(app)

# User Model
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(100), nullable=False, unique=True)
#     password_hash = db.Column(db.String(255), nullable=False)

#     def set_password(self, password):
#         self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

#     def check_password(self, password):
#         return bcrypt.check_password_hash(self.password_hash, password)

# Database Model for User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)


# Book Model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    available = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'available': self.available
        }

# Member Model
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    membership_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'membership_date': self.membership_date.isoformat()
        }
    
with app.app_context():
    db.create_all()  # Create tables

# Home Route
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Generate access token
        access_token = create_access_token(identity=new_user.id)
        flash('Registration successful', 'success')

        # Store the token in a session or return it in the response
        response = redirect(url_for('dashboard'))
        return response

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Debugging
        print(f"Attempting to login with username: {username}")

        # Check if user exists and password is correct
        user = User.query.filter_by(username=username).first()
        if not user:
            print("User not found.")
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

        if not user.check_password(password):
            print("Incorrect password.")
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

        # Generate access token
        access_token = create_access_token(identity=user.id)
        print(f"Generated access token: {access_token}")

        flash('Login successful', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')




@app.route('/dashboard')
# @jwt_required()
def dashboard():
    # current_user_id = get_jwt_identity()
    # user = User.query.get(current_user_id)
    # Pass the username or user data to the template
    return render_template('dashboard.html')


@app.route('/logout')
def logout():
    # In a real app, you'd invalidate the token here
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))


# Books Routes
@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        # Get form data
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        
        # Check if book already exists
        existing_book = Book.query.filter_by(isbn=isbn).first()
        if existing_book:
            flash('A book with this ISBN already exists!', 'danger')
            return render_template('add_book.html')
        
        # Create new book
        new_book = Book(title=title, author=author, isbn=isbn)
        
        try:
            db.session.add(new_book)
            db.session.commit()
            flash('Book added successfully!', 'success')
            return redirect(url_for('view_books'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding book: {str(e)}', 'danger')
    
    return render_template('add_book.html')

@app.route('/books', methods=['GET'])
def view_books():
    page = request.args.get('page', 1, type=int)
    books = Book.query.paginate(page=page, per_page=10)
    return render_template('view_books.html', books=books)

# Members Routes
@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        
        # Check if member already exists
        existing_member = Member.query.filter_by(email=email).first()
        if existing_member:
            flash('A member with this email already exists!', 'danger')
            return render_template('add_member.html')
        
        # Create new member
        new_member = Member(name=name, email=email)
        
        try:
            db.session.add(new_member)
            db.session.commit()
            flash('Member added successfully!', 'success')
            return redirect(url_for('view_members'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding member: {str(e)}', 'danger')
    
    return render_template('add_member.html')

@app.route('/members')
def view_members():
    members = Member.query.all()
    return render_template('view_members.html', members=members)

# Delete Routes
@app.route('/books/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    try:
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting book: {str(e)}', 'danger')
    return redirect(url_for('view_books'))

@app.route('/members/delete/<int:member_id>', methods=['POST'])
def delete_member(member_id):
    member = Member.query.get_or_404(member_id)
    try:
        db.session.delete(member)
        db.session.commit()
        flash('Member deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting member: {str(e)}', 'danger')
    return redirect(url_for('view_members'))

# Initialize Database
def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)