# config/memory.py
from dataclasses import dataclass
from typing import Optional

from bedrock_agentcore.memory import MemoryClient
from langgraph_checkpoint_aws import AgentCoreMemorySaver

from config.settings import settings


@dataclass
class MemoryContext:
    """封装 Memory 相关对象，方便 runtime / deploy 复用"""
    memory_id: str
    saver: AgentCoreMemorySaver
    client: MemoryClient


def init_memory(
        region_name: Optional[str] = None,
        memory_name: Optional[str] = None,
) -> MemoryContext:
    """
    初始化 AgentCore Memory，并返回 MemoryContext。
    - 如果 memory_name 不填，就用默认的 settings.memory_name
    - 如果 region_name 不填，就用默认的 settings.aws_region
    """

    region = region_name or settings.aws_region
    name = memory_name or settings.memory_name

    client = MemoryClient(region_name=region)
    memory = client.create_or_get_memory(
        name=name, # This name is unique across all memories in this account
        description="Fitness Coach Agent",  # Human-readable description
        strategies=[],  # No memory strategies for short-term memory
        event_expiry_days=7,  # Memories expire after 7 days
    )

    memory_id = memory["id"]

    saver = AgentCoreMemorySaver(memory_id, region_name=region)

    return MemoryContext(memory_id=memory_id, saver=saver, client=client)


def delete_memory(
        ctx: MemoryContext,
        max_wait: int = 300,
        poll_interval: int = 10,
) -> None:
    """
    删除一块 Memory（开发 / 测试用）。
    """
    ctx.client.delete_memory_and_wait(
        memory_id=ctx.memory_id,
        max_wait=max_wait,
        poll_interval=poll_interval,
    )
