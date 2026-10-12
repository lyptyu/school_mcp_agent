import json
from app.common.exceptions import BusinessException
from app.config import settings
from langchain_mcp_adapters.client import MultiServerMCPClient
async def call_get_my_schedule(authorization:str,date:str|None = None)->dict:
    client = MultiServerMCPClient({
        "school":{
            "transport":"streamable_http",
            #http://127.0.0.1:8001/mcp
            "url": f"http://{settings.MCP_HOST}:{settings.MCP_PORT}{settings.MCP_PATH}",
            "headers": {"Authorization": authorization}
        }
    })
    tools = await client.get_tools()
    tool = next((t for t in tools if t.name == 'get_my_schedules'), None)
    if tool is None:
        raise BusinessException(message='未找到工具【get_my_schedules】，请确认mcp服务是否正常')
    payload = {}
    if date:
        payload['date'] = date
    result = await tool.ainvoke(payload)
    print('result:', result)
    return json.loads(result[0]['text'])