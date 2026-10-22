from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage
from langchain_core.messages import BaseMessage
from app.schemas.chat import ChatMessage
from app.common.exceptions import BusinessException
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.config import settings
import logging
from datetime import date
from langchain.agents import create_agent
from langgraph.errors import GraphRecursionError
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是校园课程智能助手，使用中文回答。
今天是 {today}。将“明天”“这周三”等相对日期换算成 YYYY-MM-DD。
本周按周一至周日计算；日期含义不明确时，先询问用户。
get_my_schedules 查询当前登录用户自己的课表。
参数 date 为可选的 YYYY-MM-DD；不传则查询全部课表。
回答规则：
1. 查询课表时必须调用工具，只根据本轮工具返回的数据回答。
2. 查询某一天时传 date；查询一周时可获取全部课表，再按日期筛选。
3. 工具结果含 error 时说明查询失败，不能将失败解释成没有课程。
4. 正常返回且没有符合条件的课程时，说明对应日期没有课程安排。
5. 列出日期、节次、课程和地点，并按日期、节次排序。
6. 闲聊直接回答；没有实时查询工具的事情，应说明无法实时查询。
"""


def _build_model() -> ChatOpenAI:
    """根据配置创建模型的客户端请求，此时尚未发送实际的对话请求"""
    # 缺少密钥时立即提示配置问题，避免到远端调用时才失败
    if not settings.LLM_API_KEY.strip():
        raise BusinessException(message="未配置 LLM_API_KEY，请先填写模型密钥")
    return ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        # 较低随机性，适合按查询结果组织回答
        temperature=0.3,
        # 显式关闭 DeepSeek 思考模式，保持纯文本历史格式适用
        extra_body={"thinking": {
            "type": "disabled"
        }},
    )


async def _load_mcp_tools(authorization: str):
    """加载绑定本次JWT请求凭证的MCP工具"""
    client = MultiServerMCPClient(
        {
            "campus": {  # 本地连接别名，必须与 get_tools 的 server_name 一致
                "transport": "streamable_http",
                "url": f"http://{settings.MCP_HOST}:{settings.MCP_PORT}{settings.MCP_PATH}",
                "headers": {"Authorization": authorization},
            }
        }
    )
    try:
        # 这里只加载工具定义；具体选哪个工具、传什么参数，交给 Agent 决定
        return await client.get_tools(server_name="campus")
    except Exception as exc:
        logger.exception("加载 campus MCP 工具失败")
        raise BusinessException(message="加载课表工具失败，请检查 MCP 服务和后端日志") from exc

def _build_messages(history: list[ChatMessage], question: str) -> list[BaseMessage]:
    """根据历史对话构建模型请求"""
    # 接口角色已由 Literal 校验；按角色选择消息类，保留用户与助手的发言身份
    message_types = {"user": HumanMessage, "assistant": AIMessage}
    messages = [message_types[item.role](content=item.content) for item in history]
    # 当前问题必须排在历史之后，避免模型把旧问题当作本次需要处理的问题
    return [*messages, HumanMessage(content=question)]
def _read_result(messages: list[BaseMessage]) -> dict:
    """读取模型的最终的回复，收集请求的工具名+最终的回复消息，回复格式：
    {"answer": "你好，我是 campus-course-agent，我可以帮助你查询课表",
     "tools_used": ["get_my_schedules"]}
    """
    last_message = messages[-1] if messages else None
    # 只接受本轮最后一条无工具调用的助手消息，避免误取中间消息
    if not isinstance(last_message, AIMessage) or last_message.tool_calls:
        raise BusinessException(message="助手未生成最终回答，请重新提问")
    # text 兼容字符串正文与文本块；去掉首尾空白后再检查
    answer = last_message.text.strip()
    if not answer:
        raise BusinessException(message="助手未生成最终回答，请重新提问")
    # 同一工具可能被重复调用；按首次出现顺序去重，只返回名称清单
    tools_used = list(
        dict.fromkeys(
            call["name"]
            for message in messages
            if isinstance(message, AIMessage)
            for call in message.tool_calls
        )
    )
    # dict.fromkeys({"get_my_shedules": None}) -> ["get_my_shedules"]
    return {"answer": answer, "tools_used": tools_used}

async def ask(question: str, history: list[ChatMessage], authorization: str) -> dict:
    """根据历史对话构建模型请求，加载MCP工具，创建本次请求的Agent，发送请求，返回模型回复"""
    model = _build_model()
    tools = await _load_mcp_tools(authorization)
    if not tools:
        raise BusinessException(
            message="MCP未返回任何可用的 tool，请检查 MCP 服务和后端日志"
        )
    agent = create_agent(
        model, tools, system_prompt=SYSTEM_PROMPT.format(today=date.today().isoformat())
    )
    input_messages = _build_messages(history, question)
    try:
        result = await agent.ainvoke(
            {
                "messages": input_messages,
            },
            config={"recursion_limit": settings.AGENT_RECURSION_LIMIT},
        )
        logger.info("大模型输出的结果：%s", result)
    except GraphRecursionError as exc:
        logger.exception("Agent 达到了图步骤达到上限")
        raise BusinessException(
            message="本次处理的步骤过多，请缩小问题范围重试"
        ) from exc
    except Exception as exc:
        logger.exception("模型调用失败")
        raise BusinessException(
            message="模型调用失败，请检查模型服务和后端日志"
        ) from exc
    new_messages = result["messages"][len(input_messages) :]
    return _read_result(new_messages)