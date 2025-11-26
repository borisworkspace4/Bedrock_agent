# deploy/deploy_agent.py
import time
from datetime import datetime

from bedrock_agentcore_starter_toolkit import Runtime

from config.settings import ENTRYPOINT, REQUIREMENTS_FILE, REGION, AGENT_NAME
from config.agent_metadata import save_launch_metadata

# 1. 生成带时间戳的 agent_name
def gen_agent_name() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")  # 例如 20251125-153045
    return f"{AGENT_NAME}_{ts}"


# 2. 初始化 Runtime
agentcore_runtime = Runtime()

# 3. 配置：每次运行都会是一个全新的名字
agent_name = gen_agent_name()
print("本次部署使用的 agent_name:", agent_name)

response = agentcore_runtime.configure(
    entrypoint=ENTRYPOINT,
    auto_create_execution_role=True,
    auto_create_ecr=True,
    requirements_file=REQUIREMENTS_FILE,
    region=REGION,
    agent_name=agent_name,
)
print("configure 响应：", response)

# 4. 部署
launch_result = agentcore_runtime.launch()
print("launch 结果：", launch_result)

# 5. 缓存中间结果
save_launch_metadata(launch_result.agent_arn, launch_result.agent_id, launch_result.ecr_uri)

# 6. 等待 READY
end_status = ['READY', 'CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']
status_response = agentcore_runtime.status()
status = status_response.endpoint['status']
print("初始状态:", status)

while status not in end_status:
    time.sleep(10)
    status_response = agentcore_runtime.status()
    status = status_response.endpoint['status']
    print("当前状态:", status)

print("最终状态:", status)

# 7. 调用
if status == "READY":
    invoke_response = agentcore_runtime.invoke({"prompt": "How is the weather now?"})
    print("invoke 响应：", invoke_response)
else:
    print("状态不是 READY，跳过调用")
