# app/utils/pagination.py

def apply_pagination(query, page: int = 1, per_page: int = 10):
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return total, items
