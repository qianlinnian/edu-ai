"""
M4 API 测试脚本
用于通过 API 调用创建测试数据和验证接口
"""
import json
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"


def test_auth():
    """测试认证接口"""
    print("\n=== 1. 测试登录接口 ===")

    # 尝试登录
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "test_teacher", "password": "password123"}
    )
    print(f"登录响应状态: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"登录成功: {data.get('username', 'N/A')}")
        return data.get("access_token")
    else:
        print(f"登录失败: {response.text}")
        return None


def test_register():
    """测试注册接口"""
    print("\n=== 1.1 测试注册接口 ===")

    # 尝试注册
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": "test_teacher",
            "email": "teacher@test.com",
            "password": "password123",
            "full_name": "测试教师",
            "role": "teacher"
        }
    )
    print(f"注册响应状态: {response.status_code}")
    print(f"注册响应: {response.text[:200]}")
    return response


def test_health():
    """测试健康检查"""
    print("\n=== 0. 测试健康检查 ===")
    response = requests.get("http://localhost:8000/health")
    print(f"健康检查: {response.json()}")
    return response.json()


def test_chat_send(token):
    """测试普通问答接口"""
    print("\n=== 2. 测试普通问答接口 ===")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/chat/send",
        headers=headers,
        json={
            "agent_id": 3,
            "course_id": 3,
            "message": "什么是 Python 装饰器？"
        }
    )
    print(f"普通问答响应状态: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Session ID: {data.get('session_id')}")
        print(f"响应内容: {data.get('message', {}).get('content', 'N/A')[:100]}...")
        return data
    else:
        print(f"失败: {response.text[:200]}")
        return None


def test_chat_stream(token):
    """测试流式问答接口"""
    print("\n=== 3. 测试流式问答接口 ===")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print("发送流式请求...")
    response = requests.post(
        f"{BASE_URL}/chat/send-stream",
        headers=headers,
        json={
            "agent_id": 3,
            "course_id": 3,
            "session_id": None,
            "message": "请解释什么是闭包？"
        },
        stream=True
    )

    print(f"流式响应状态: {response.status_code}")
    print("流式事件:")

    chunks = []
    done_received = False
    session_id = None
    message_id = None

    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data_str = line_str[6:]
                try:
                    data = json.loads(data_str)
                    event_type = data.get('type')
                    print(f"  事件: {event_type}")

                    if event_type == 'chunk':
                        content = data.get('content', '')
                        chunks.append(content)
                        if len(chunks) <= 3 or len(content) > 80:
                            print(f"    内容: {content[:50]}...")

                    elif event_type == 'done':
                        done_received = True
                        session_id = data.get('session_id')
                        message_id = data.get('message_id')
                        print(f"    Session ID: {session_id}")
                        print(f"    Message ID: {message_id}")

                    elif event_type == 'error':
                        print(f"    错误: {data.get('error')}")

                except json.JSONDecodeError:
                    print(f"  解析错误: {data_str[:50]}")

    print(f"\n流式响应汇总:")
    print(f"  总 chunk 数: {len(chunks)}")
    print(f"  完整内容: {''.join(chunks)[:100]}...")
    print(f"  Done 事件: {'收到' if done_received else '未收到'}")

    return {
        "status": response.status_code,
        "chunks_count": len(chunks),
        "done_received": done_received,
        "session_id": session_id,
        "message_id": message_id,
        "full_content": ''.join(chunks)
    }


def test_chaoxing_lti():
    """测试超星 LTI 启动接口"""
    print("\n=== 4. 测试超星 LTI 启动接口 ===")

    # 正常场景
    response = requests.post(
        f"{BASE_URL}/platform/chaoxing/lti-launch",
        json={
            "resource_link_id": "res-001",
            "user_id": "user-123",
            "roles": "student"
        }
    )
    print(f"超星 LTI 响应状态: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

    # 错误场景
    print("\n测试缺少参数场景:")
    response = requests.post(
        f"{BASE_URL}/platform/chaoxing/lti-launch",
        json={}
    )
    print(f"错误场景响应: {response.json()}")

    return data


def test_dingtalk_auth():
    """测试钉钉认证接口"""
    print("\n=== 5. 测试钉钉认证接口 ===")

    # 正常场景
    response = requests.get(
        f"{BASE_URL}/platform/dingtalk/auth",
        params={"code": "demo-code", "course_id": 1}
    )
    print(f"钉钉认证响应状态: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

    # 错误场景
    print("\n测试缺少 code 参数场景:")
    response = requests.get(f"{BASE_URL}/platform/dingtalk/auth")
    print(f"错误场景响应: {response.json()}")

    return data


def test_agent_builder(token):
    """测试 Agent Builder 保存流程"""
    print("\n=== 6. 测试 Agent Builder 保存接口 ===")

    headers = {"Authorization": f"Bearer {token}"}

    # 先创建 Agent 实例
    print("6.1 创建 Agent 实例...")
    instance_data = {
        "template_id": None,
        "course_id": 3,  # Python程序设计
        "name": "Python课程答疑Agent",
        "description": "由 M4 测试创建",
        "system_prompt": "你是一个智能教学助手。",
        "config": {},
        "tools": [],
        "llm_provider": "dashscope",
        "llm_model": "qwen-max"
    }
    response = requests.post(
        f"{BASE_URL}/agents/instances",
        headers=headers,
        json=instance_data
    )
    print(f"Agent 实例响应状态: {response.status_code}")
    if response.status_code == 200:
        instance = response.json()
        print(f"创建成功: ID={instance.get('id')}, Name={instance.get('name')}")
        agent_id = instance.get('id')
    else:
        print(f"创建失败: {response.text}")
        return None

    # 创建工作流
    print("\n6.2 创建工作流...")
    workflow_data = {
        "agent_id": agent_id,
        "name": "Python课程答疑Agent 工作流",
        "description": "由 M4 测试创建",
        "workflow_dag": {
            "nodes": [
                {
                    "id": "n1",
                    "type": "custom",
                    "position": {"x": 250, "y": 40},
                    "data": {
                        "label": "用户输入",
                        "color": "#6366f1",
                        "icon": "💬",
                        "nodeType": "input_node"
                    }
                },
                {
                    "id": "n2",
                    "type": "custom",
                    "position": {"x": 250, "y": 160},
                    "data": {
                        "label": "知识检索",
                        "color": "#00a8ff",
                        "icon": "🔍",
                        "nodeType": "rag_node",
                        "course": 3,
                        "topK": 5,
                        "similarity": 0.7
                    }
                },
                {
                    "id": "n3",
                    "type": "custom",
                    "position": {"x": 250, "y": 280},
                    "data": {
                        "label": "LLM对话",
                        "color": "#8b5cf6",
                        "icon": "🤖",
                        "nodeType": "llm_node"
                    }
                }
            ],
            "edges": [
                {"id": "e1-2", "source": "n1", "target": "n2"},
                {"id": "e2-3", "source": "n2", "target": "n3"}
            ]
        }
    }
    response = requests.post(
        f"{BASE_URL}/agents/workflows",
        headers=headers,
        json=workflow_data
    )
    print(f"工作流响应状态: {response.status_code}")
    if response.status_code == 200:
        workflow = response.json()
        print(f"创建成功: ID={workflow.get('id')}, Name={workflow.get('name')}")
        return {"instance_id": agent_id, "workflow_id": workflow.get('id')}
    else:
        print(f"创建失败: {response.text}")
        return None


def main():
    print("=" * 60)
    print("M4 端到端测试")
    print("=" * 60)

    # 0. 健康检查
    test_health()

    # 1. 注册（可能已存在，忽略错误）
    test_register()

    # 2. 登录获取 token
    token = test_auth()
    if not token:
        print("\n无法获取 token，测试终止")
        return

    # 3. 测试普通问答
    test_chat_send(token)

    # 4. 测试流式问答
    stream_result = test_chat_stream(token)

    # 5. 测试超星 LTI
    test_chaoxing_lti()

    # 6. 测试钉钉认证
    test_dingtalk_auth()

    # 7. 测试 Agent Builder
    test_agent_builder(token)

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

    return stream_result


if __name__ == "__main__":
    main()
