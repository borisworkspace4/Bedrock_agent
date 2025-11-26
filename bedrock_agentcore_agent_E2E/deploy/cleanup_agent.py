# deploy/cleanup_agent.py
import boto3
from config.settings import REGION
from config.agent_metadata import load_launch_metadata

agentcore_control_client = boto3.client(
    'bedrock-agentcore-control',
    region_name=REGION
)
ecr_client = boto3.client(
    'ecr',
    region_name=REGION

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
