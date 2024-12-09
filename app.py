from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'library.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

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

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    print("entered login")
    if request.method == 'POST':
        # Check if it's JSON or form data
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')

        # Validate input
        if not username or not password:
            print("Username or password is missing.")
            return jsonify({
                'success': False, 
                'message': 'Username and password are required'
            }), 400

        print(f"Attempting login with username: {username}")

        user = User.query.filter_by(username=username).first()

        if user:
            print(f"User found: {user.username}")
            try:
                if bcrypt.check_password_hash(user.password, password):
                    print("Password is correct.")

                    return redirect(url_for('dashboard'))
                    
                else:
                    print("Incorrect password.")
                    return jsonify({
                        'success': False, 
                        'message': 'Invalid username or password'
                    }), 401
            except Exception as e:
                print(f"Password verification error: {str(e)}")
                return jsonify({
                    'success': False, 
                    'message': 'Authentication error'
                }), 500
        else:
            print("User not found.")
            return jsonify({
                'success': False, 
                'message': 'Invalid username or password'
            }), 404

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    print("Entered dashboard route")
    try:
        print("hiii")
        return render_template('dashboard.html')
    except Exception as e:
        print(f"Error in dashboard route: {str(e)}")
        flash('An error occurred while accessing the dashboard', 'error')
        return redirect(url_for('login'))
    


@app.route('/logout')
def logout():
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))


@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':

        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']

        existing_book = Book.query.filter_by(isbn=isbn).first()
        if existing_book:
            flash('A book with this ISBN already exists!', 'danger')
            return render_template('add_book.html')
        
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

@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        
        existing_member = Member.query.filter_by(email=email).first()
        if existing_member:
            flash('A member with this email already exists!', 'danger')
            return render_template('add_member.html')
        
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

def init_db():
    with app.app_context():
        db.create_all() 

if __name__ == '__main__':
    init_db()
    app.run(debug=True)