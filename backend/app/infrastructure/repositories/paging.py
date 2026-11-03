def query_page(query, *, page, page_size):
    """Count/filter before slicing; clamp pages after concurrent removals."""
    total = query.order_by(None).count()
    page = min(page, max(1, (total + page_size - 1) // page_size))
    return {
        "items": query.offset((page - 1) * page_size).limit(page_size).all(),
        "total": total, "page": page, "page_size": page_size,
    }
