import json
import boto3
from config.settings import settings
from config.agent_metadata import load_launch_metadata

# 读取 metadata
info = load_launch_metadata()
agent_arn = info["agent_arn"]
agent_id = info["agent_id"]
repositoryName = info["repositoryName"]

# 创建 AgentCore 客户端
agentcore_client = boto3.client(
    'bedrock-agentcore',
    region_name=settings.region
)


def invoke_agent(prompt: str):
    """调用 AgentCore，并处理输出"""
    boto3_response = agentcore_client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        qualifier="DEFAULT",
        payload=json.dumps({"prompt": prompt})
    )

    # SSE 文本流处理
    if "text/event-stream" in boto3_response.get("contentType", ""):
        content = []
        for line in boto3_response["response"].iter_lines(chunk_size=1):
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                    print(line)
                    content.append(line)

    # JSON 事件流处理
    else:
        try:
            events = []
            for event in boto3_response.get("response", []):
                events.append(event)
        except Exception as e:
            events = [f"Error reading EventStream: {e}"]

        print(json.loads(events[0].decode("utf-8")))


# ---------------------------
# ✅ 循环输入部分
# ---------------------------
print("🚀 AgentCore 调用已准备就绪。输入 exit 退出。")

while True:
    user_input = input("请输入 prompt > ").strip()

    if user_input.lower() == "exit":
        print("👋 已退出。")
        break

    if not user_input:
        continue  # 跳过空输入

    print(f"\n➡️ 正在调用 Agent...（prompt: {user_input}）\n")
    invoke_agent(user_input)
    print("\n---------------------------------\n")
