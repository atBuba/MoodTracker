from fastapi import Query

class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.per_page = per_page
        self.skip = (page - 1) * per_page
        self.limit = per_page

def paginate_response(data: list, total: int, page: int, per_page: int) -> dict:
    return {
        "data": data,
        "meta": {
            "total": total,
            "page": page,
            "per_page": per_page
        }
    }

def success_response(data: any, meta: dict = None):
    return {
        "data": data,
        "meta": meta or {}
    }