# config/settings.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from boto3.session import Session


# 1) 自动加载当前项目根目录下的 .env 文件
# allow override=True 表示 .env 参数可覆盖系统环境变量
load_dotenv(override=True)


@dataclass
class Settings:
    """
    全局项目配置类
    从 .env（或系统环境变量）加载：
      - AWS Region
      - Agent 名称
      - Entrypoint / requirements
      - Memory 配置
      - 模型配置
    """

    region: str
    agent_name: str
    entrypoint: str
    requirements_file: str

    # Memory 相关
    memory_name: str

    # 模型相关
    model_id: str
    agentcore_service_name: str
    ecr_service_name: str

    @classmethod
    def load(cls):
        """
        从 .env 或系统环境变量加载 Settings
        """

        # -------- AWS Region --------
        region = os.getenv("AWS_REGION")
        if not region:
            # 如果没配置，则 fallback 到 boto3 默认 session
            _session = Session()
            region = _session.region_name or "ap-southeast-1"

        # -------- 读取其余关键参数（带默认值）--------
        agent_name = os.getenv("AGENT_NAME", "default_agent_name")
        entrypoint = os.getenv("ENTRYPOINT", "agent.py")
        requirements_file = os.getenv("REQUIREMENTS_FILE", "requirements.txt")

        # Memory
        memory_name = os.getenv("MEMORY_NAME", "DefaultAgentMemory")

        # Model
        model_id = os.getenv(
            "MODEL_ID",
            "anthropic.claude-3-haiku-20240307-v1:0",
        )

        agentcore_service_name = os.getenv(
            "AGENTCORE_SERVICE_NAME",
            "bedrock-agentcore-control"
        )

        ecr_service_name = os.getenv(
            "ECR_SERVICE_NAME",
            "ecr"
        )

        return cls(
            region=region,
            agent_name=agent_name,
            entrypoint=entrypoint,
            requirements_file=requirements_file,
            memory_name=memory_name,
            model_id=model_id,
            agentcore_service_name=agentcore_service_name,
            ecr_service_name=ecr_service_name,
        )


# 单例，用于项目中直接 import settings 即可
settings = Settings.load()
