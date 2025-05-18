from flask import Blueprint, render_template, current_app, request, session, redirect, url_for, abort, jsonify
from bson import ObjectId
from datetime import datetime
from website.db_helpers.books import update_book_rating, get_books_by_genre

views = Blueprint('views', __name__)

# Логіка головної сторінки 
@views.route('/', methods=['GET'])
def index():
    sort_by = request.args.get('sort')
    q = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 12

    user = None
    user_fav_books = []
    user_read_books = []

    if 'user_id' in session:
        user_id = session['user_id']
        user = current_app.db["Users"].find_one({"_id": ObjectId(user_id)})
        favourite_genre = user.get("favourite_genre", [])
        user_fav_books = user.get("favourite_books", [])
        user_read_books = user.get("read_books", [])
        books = get_books_by_genre(favourite_genre)
    else:
        books = list(current_app.db["Books"].find({"title": {"$ne": ""}}))

    # Пошук
    if q:
        books = list(current_app.db["Books"].find({
            "$or": [
                {"title": {"$regex": q, "$options": "i"}},
                {"author": {"$regex": q, "$options": "i"}},
                {"genre": {"$in": [q]}}
            ]
        }))

    # Сортування
    def sort_key(book):
        if sort_by == 'title':
            return book.get('title', '').lower()
        elif sort_by == 'author':
            return book.get('author', '').lower()
        elif sort_by == 'rating':
            try:
                return -float(book.get('rating', 0))
            except:
                return 0
        return 0

    if sort_by:
        books.sort(key=sort_key)

    # Пагінація
    total_books = len(books)
    total_pages = (total_books + per_page - 1) // per_page
    books = books[(page - 1) * per_page : page * per_page]

    
    return render_template(
        "index.html",
        books=books,
        user_fav_books=user_fav_books,
        user_read_books=user_read_books,
        sort_by=sort_by,
        q=q,
        page=page,
        total_pages=total_pages
    )

# Маршрут для запиту на оновлення користувача (додавання у список улюблених)
@views.route('/book/<string:book_id>/toggle_favourite', methods=['POST'])
def toggle_favourite(book_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = ObjectId(session['user_id'])
    user = current_app.db["Users"].find_one({"_id": user_id})

    if not user:
        return jsonify({'error': 'User not found'}), 404

    fav_books = user.get("favourite_books", [])
    book_oid = ObjectId(book_id)

    if book_oid in fav_books:
        fav_books.remove(book_oid)
    else:
        fav_books.append(book_oid)

    current_app.db["Users"].update_one(
        {"_id": user_id},
        {"$set": {"favourite_books": fav_books}}
    )

    return jsonify({'status': 'success', 'favourite': str(book_oid) in map(str, fav_books)})

# Маршрут для запиту на оновлення користувача (додавання у список прочитаних)
@views.route('/book/<string:book_id>/toggle_read', methods=['POST'])
def toggle_read(book_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = ObjectId(session['user_id'])
    user = current_app.db["Users"].find_one({"_id": user_id})

    if not user:
        return jsonify({'error': 'User not found'}), 404

    read_books = user.get("read_books", [])
    book_oid = ObjectId(book_id)

    if book_oid in read_books:
        read_books.remove(book_oid)
    else:
        read_books.append(book_oid)

    current_app.db["Users"].update_one(
        {"_id": user_id},
        {"$set": {"read_books": read_books}}
    )

    return jsonify({'status': 'success', 'read': str(book_oid) in map(str, read_books)})

# Рендеринг і логіка сторінки акаунта
@views.route('/account', methods=['GET', 'POST'])
def account():
    if 'user_id' not in session:
        return render_template('account.html', user=None)

    user_id = session['user_id']
    user = current_app.db["Users"].find_one({"_id": ObjectId(user_id)})

    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        genres_raw = request.form.get('genres', '')
        # Розділення по комах та обрізання пробілів
        favourite_genre = [genre.strip() for genre in genres_raw.split(',') if genre.strip()]

        update_fields = {
            "email": email,
            "username": username,
            "favourite_genre": favourite_genre
        }

        current_app.db["Users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields}
        )

        # Оновлення user, для відображення змін
        user = current_app.db["Users"].find_one({"_id": ObjectId(user_id)})
        print(user)

    return render_template('account.html', user=user)

# Логіка видалення акаунта
@views.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return "Unauthorized", 401

    user_id = session['user_id']
    # Видалення користувача з колекції Users
    result = current_app.db["Users"].delete_one({"_id": ObjectId(user_id)})

    # Видаляєння сесії
    session.pop('user_id', None)

    print(f"Deleted {result.deleted_count} user(s).")

    return redirect(url_for('views.index'))

# Рендеринг сторінки книги
@views.route('/book/<string:book_id>', methods=['GET'])
def book_detail(book_id):
    update_book_rating(book_id)
    
    try:
        book = current_app.db["Books"].find_one({"_id": ObjectId(book_id)})
    except:
        return abort(400, "Invalid book ID format")

    if not book:
        return abort(404, "Book not found")

    reviews = list(current_app.db["Reviews"].find({"book_id": ObjectId(book_id)}))

    # Відображення username у відгуках
    for review in reviews:
        user = current_app.db["Users"].find_one({"_id": review["user_id"]})
        review["username"] = user.get("username", "Unknown") if user else "Unknown"
    
    return render_template("book.html", book=book, reviews=reviews)

# Додавання відгука
@views.route('/book/<string:book_id>/review', methods=['POST'])
def add_review(book_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    review_text = request.form.get('review_text')
    rating = int(request.form.get('rating'))

    review = {
        "book_id": ObjectId(book_id),
        "user_id": ObjectId(session['user_id']),
        "text": review_text,
        "rating": rating,
        "timestamp": datetime.utcnow()
    }

    current_app.db["Reviews"].insert_one(review)
    
    update_book_rating(book_id)

    return redirect(url_for('views.book_detail', book_id=book_id))

# Відображення сторінки з книжками зі списків користувача
@views.route('/my-books')
def my_books():
    if 'user_id' not in session:
        return redirect(url_for('views.index'))

    user = current_app.db["Users"].find_one({"_id": ObjectId(session['user_id'])})
    favourite_ids = set(user.get("favourite_books", []))
    read_ids = set(user.get("read_books", []))

    # Отримати улюблені книжки
    favourite_books = list(current_app.db["Books"].find({
        "_id": {"$in": [ObjectId(book_id) for book_id in favourite_ids]}
    }))

    # Отримати прочитані, які не є улюбленими
    only_read_ids = list(read_ids - favourite_ids)
    read_books = list(current_app.db["Books"].find({
        "_id": {"$in": [ObjectId(book_id) for book_id in only_read_ids]}
    }))

    return render_template("my_books.html",
        favourite_books=favourite_books,
        read_books=read_books
    )