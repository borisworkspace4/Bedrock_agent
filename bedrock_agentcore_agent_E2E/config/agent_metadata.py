import json
import os
from typing import Any


DEFAULT_OUTPUT_FILE = "agent_launch_info.json"


def save_launch_metadata(
    agent_arn: str,
    agent_id: str,
    ecr_uri: str,
    output_path: str = DEFAULT_OUTPUT_FILE,
) -> str:
    """
    保存 AgentCore 部署后的信息到本地 JSON 文件。

    Args:
        agent_arn (str): 部署生成的 Agent ARN
        agent_id (str): 部署生成的 Agent ID
        ecr_uri (str): 部署生成的 ECR URI
        output_path (str): 保存文件路径，默认放在项目根目录

    Returns:
        str: 实际写入文件的绝对路径
    """

    repository_name = ecr_uri.split("/")[1] if "/" in ecr_uri else ""

    data = {
        "agent_arn": agent_arn,
        "agent_id": agent_id,
        "ecr_uri": ecr_uri,
        "repositoryName": repository_name,
    }

    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    abs_path = os.path.abspath(output_path)
    print(f"✅ Agent metadata saved to: {abs_path}")

    return abs_path


def load_launch_metadata(path: str = DEFAULT_OUTPUT_FILE) -> dict[str, Any]:
    """
    读取保存的 AgentCore 部署信息。

    Args:
        path (str): JSON 文件路径

    Returns:
        dict[str, Any]: 配置数据
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
