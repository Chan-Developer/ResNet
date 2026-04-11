from fastapi import APIRouter, Depends

from ..dependencies import require_permissions
from ..schemas.common import ApiResponse
from ..schemas.consult import ConsultRequest, ConsultResponse
from ..services import consult_service

router = APIRouter(prefix="/api/consult", tags=["consult"])


@router.post("", response_model=ApiResponse[ConsultResponse])
async def disease_consult(
    payload: ConsultRequest,
    user=Depends(require_permissions("predict:single")),
):
    answer = await consult_service.generate_consult_answer(payload.question, payload.history)
    return ApiResponse(data=ConsultResponse(answer=answer))
