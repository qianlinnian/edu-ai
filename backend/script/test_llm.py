import asyncio
from agent_core.llm_provider import get_llm_provider
# 测试 LLM 能否正常工作
# 通过修改 .env 中的 DEFAULT_LLM_PROVIDER 来切换不同的 LLM 提供者进行测试
async def main():
    llm = get_llm_provider()
    resp = await llm.chat([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Reply with only API OK"}
    ])
    print(resp)

asyncio.run(main())
