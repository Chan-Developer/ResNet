from fastapi import HTTPException


def bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=401, detail=detail)


def forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=403, detail=detail)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=404, detail=detail)
