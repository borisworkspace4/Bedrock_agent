# deploy/cleanup_agent.py
import boto3
from config.settings import settings
from config.agent_metadata import load_launch_metadata

agentcore_control_client = boto3.client(
    service_name=settings.agentcore_service_name,
    region_name=settings.region
)
ecr_client = boto3.client(
    service_name=settings.ecr_service_name,
    region_name=settings.region

)

info = load_launch_metadata()

agent_id = info["agent_id"]
repositoryName = info["repositoryName"]

runtime_delete_response = agentcore_control_client.delete_agent_runtime(
    agentRuntimeId=agent_id,

)

response = ecr_client.delete_repository(
    repositoryName=repositoryName,
    force=True
)
