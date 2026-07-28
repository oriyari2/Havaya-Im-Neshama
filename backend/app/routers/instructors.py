from typing import Annotated,NoReturn
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Query,Response
from backend.app.application.services import instructor_service as service
from backend.app.core.auth import get_current_user,require_roles
from backend.app.schemas.instructor import InstructorCreate,InstructorListResponse,InstructorResponse,InstructorUpdate

router=APIRouter(tags=["instructors"]); Manager=Depends(require_roles("manager"))
def errors(exc:Exception)->NoReturn:
    if isinstance(exc,service.InstructorNotFoundError):raise HTTPException(404,"Instructor not found") from exc
    if isinstance(exc,service.InstructorAccessDeniedError):raise HTTPException(403,"Not authorized") from exc
    if isinstance(exc,service.InstructorConflictError):raise HTTPException(409,str(exc)) from exc
    if isinstance(exc,service.InstructorDeleteConflictError):raise HTTPException(409,str(exc)) from exc
    raise exc
@router.get("/instructors",response_model=InstructorListResponse)
def list_items(search:str|None=None,city:str|None=None,is_active:bool|None=None,order_by:Annotated[str,Query(pattern="^(full_name|created_at)$")]="full_name",limit:Annotated[int,Query(ge=1,le=200)]=50,offset:Annotated[int,Query(ge=0)]=0,current_user:dict=Depends(get_current_user)):
    try:items=service.list_instructors(search=search,city=city,is_active=is_active,order_by=order_by,limit=limit,offset=offset,current_user=current_user)
    except Exception as exc:
        try:errors(exc)
        except (service.InstructorNotFoundError,service.InstructorAccessDeniedError,service.InstructorConflictError):raise
        raise HTTPException(500,"Could not list instructors") from exc
    return InstructorListResponse(items=items,count=len(items))
@router.get("/instructors/me",response_model=InstructorResponse)
def me(current_user:dict=Depends(get_current_user)):
    try:return service.get_my_profile(current_user)
    except Exception as exc:errors(exc)
@router.get("/instructors/{instructor_id}",response_model=InstructorResponse)
def detail(instructor_id:UUID,_user:dict=Manager):
    try:return service.get_instructor(instructor_id,_user)
    except Exception as exc:errors(exc)
@router.post("/instructors",response_model=InstructorResponse,status_code=201)
def create(payload:InstructorCreate,_user:dict=Manager):
    try:return service.create_instructor(payload)
    except Exception as exc:errors(exc)
@router.put("/instructors/{instructor_id}",response_model=InstructorResponse)
def update(instructor_id:UUID,payload:InstructorUpdate,_user:dict=Manager):
    try:return service.update_instructor(instructor_id,payload)
    except Exception as exc:errors(exc)
@router.delete("/instructors/{instructor_id}",status_code=204,responses={404:{"description":"Instructor not found"},409:{"description":"Protected dependencies prevent deletion"}})
def delete(instructor_id:UUID,_user:dict=Manager):
    try:service.delete_instructor(instructor_id);return Response(status_code=204)
    except (service.InstructorNotFoundError,service.InstructorAccessDeniedError,service.InstructorConflictError,service.InstructorDeleteConflictError) as exc:errors(exc)
    except Exception as exc:raise HTTPException(500,"Could not delete instructor") from exc
