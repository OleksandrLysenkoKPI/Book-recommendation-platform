from bson import ObjectId
from flask import current_app

# Пайплайн для обрахунку середнього рейтингу за оцінками з відгуків
def update_book_rating(book_id):
    pipeline = [
        {"$match": {"book_id": ObjectId(book_id)}},
        {"$group": {
            "_id": "$book_id",
            "avg_rating": {"$avg": "$rating"}
        }}
    ]
    result = list(current_app.db["Reviews"].aggregate(pipeline))
    avg_rating = round(result[0]["avg_rating"], 2) if result else 0

    current_app.db["Books"].update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"rating": avg_rating}}
    )
    

def get_books_by_genre(user_fav_genres):
    # Жанри до нижнього регістру та без пробілів
    fav_genres_clean = [genre.strip().lower() for genre in user_fav_genres]

    books = list(current_app.db["Books"].find({"title": {"$ne": ""}}))

    # Підрахунок кількості збігів жанрів з улюбленими (ігноруючи регістр та пробіли)
    def match_score(book):
        book_genres = [g.strip().lower() for g in book.get("genre", [])]
        return sum(1 for genre in book_genres if genre in fav_genres_clean)

    # Сортування: більше збігів — вище
    books.sort(key=match_score, reverse=True)

    return books
