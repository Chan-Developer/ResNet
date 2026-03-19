from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..schemas.common import ApiResponse
from ..schemas.diagnosis import CaseConfirmOut, CaseOut, ConfirmDiagnosisIn, SimilarCaseOut
from ..services import case_service

router = APIRouter(prefix="/api/case", tags=["case"])


@router.post("/confirm", response_model=ApiResponse[CaseConfirmOut])
async def confirm_case(
    data: ConfirmDiagnosisIn,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    case, similar_cases = await case_service.create_case_from_draft(
        db,
        user_id=user.id,
        draft_token=data.draft_token,
        confirmed_label=data.confirmed_label,
    )
    return ApiResponse(data=CaseConfirmOut(case=case, similar_cases=similar_cases))


@router.get("/{case_id}", response_model=ApiResponse[CaseOut])
async def get_case_detail(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    case = await case_service.get_case(db, case_id, user.id)
    return ApiResponse(data=case)


@router.get("/{case_id}/similar", response_model=ApiResponse[list[SimilarCaseOut]])
async def get_similar_cases(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    case = await case_service.get_case(db, case_id, user.id)
    similar_cases = await case_service.search_similar_cases(
        db, case.confirmed_label, exclude_case_id=case.id
    )
    return ApiResponse(data=similar_cases)
