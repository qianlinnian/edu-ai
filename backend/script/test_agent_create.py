"""测试 Agent 创建的简单脚本"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 登录获取 token
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "test_teacher", "password": "password123"}
)
print(f"登录状态: {response.status_code}")
token = response.json().get("access_token")
print(f"Token: {token[:50]}...")

# 测试创建 Agent
headers = {"Authorization": f"Bearer {token}"}
data = {
    "template_id": None,
    "course_id": 3,
    "name": "Test Agent Builder",
    "description": "测试",
    "system_prompt": "你是一个智能教学助手。",
    "config": {},
    "tools": [],
    "llm_provider": "dashscope",
    "llm_model": "qwen-max"
}

response = requests.post(
    f"{BASE_URL}/agents/instances",
    headers=headers,
    json=data
)
print(f"\n创建 Agent 状态: {response.status_code}")
print(f"响应: {response.text}")
