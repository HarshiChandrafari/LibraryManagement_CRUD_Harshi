import csv
from app import db, Book, Member
from app import app

def load_books_from_csv(file_path):
    with app.app_context():  # Activate the application context
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                book = Book(
                    title=row['title'],
                    author=row['author'],
                    isbn=row['isbn'],
                    available=True
                )
                db.session.add(book)
        db.session.commit()
        print(f"Loaded {len(list(reader))} books.")

def load_members_from_csv(file_path):
    with app.app_context():  # Activate the application context
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                member = Member(
                    name=row['name'],
                    email=row['email']
                )
                db.session.add(member)
        db.session.commit()
        print(f"Loaded {len(list(reader))} members.")

if __name__ == '__main__':
    load_books_from_csv('books.csv')
    load_members_from_csv('members.csv')