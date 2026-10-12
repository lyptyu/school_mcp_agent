from app.config import settings
from app.database import SessionLocal
from pydantic import Field
from typing import Annotated
from app.dependencies.mcp_auth import user_id_from_authorization
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from app.services.schedule_service import list_schedules_as_dict

mcp = FastMCP('school_mcp_agent')


def _current_user_id() -> int:
    headers = get_http_headers() or {}
    authorization = headers.get("authorization", "")
    return user_id_from_authorization(authorization)


@mcp.tool()
def get_my_schedules(
    date: Annotated[str | None,
                    Field(
                        description="可选参数，上课日期，格式YYYY-MM-DD 不传返回全部列表")] = None
) -> dict:
    """查询当前登录用户个人的课程列表"""
    try:
        user_id = _current_user_id()
        db = SessionLocal()
        try:
            items = list_schedules_as_dict(db, user_id, date)
            return {"items": items, "count": len(items)}
        finally:
            db.close()
    except Exception as exc:
        return {"error": f"查询课表失败 {exc}", "items": []}

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=settings.MCP_HOST,
        port=settings.MCP_PORT,
        path=settings.MCP_PATH,
        uvicorn_config={"ws":"websockets"}
    )