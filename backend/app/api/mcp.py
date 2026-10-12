
from app.common.response import Response
from app.models import User
from app.dependencies.auth import get_current_user
from fastapi import Depends
from fastapi import Query
from typing import Annotated
from app.services import mcp_client_service
from fastapi import Request
from fastapi import APIRouter

router = APIRouter(prefix='/mcp', tags=['MCP服务调试'])


@router.get('/my-schedules')
async def get_my_schedules_by_mcp(_user:Annotated[User,Depends(get_current_user)],request: Request, date: Annotated[str | None, Query(description="YYYY-MM-DD，不传返回全部")] = None,):
    Authorization = request.headers.get('Authorization') or ""
    result = await mcp_client_service.call_get_my_schedule(Authorization, date)
    return Response.success(data=result)
