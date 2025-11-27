# Import LangGraph and LangChain components
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent

# Import the AgentCoreMemorySaver that we will use as a checkpointer
import os
import logging

from langgraph_checkpoint_aws import AgentCoreMemorySaver
from bedrock_agentcore.memory import MemoryClient

region = os.getenv('AWS_REGION', 'us-west-2')
logging.getLogger("math-agent").setLevel(logging.DEBUG)

# Create or get the memory resource
memory_name = "MathLanggraphAgent"
client = MemoryClient(region_name=region)
memory = client.create_or_get_memory(name=memory_name)
memory_id = memory['id']  # Keep this memory ID for later use

MODEL_ID = "global.anthropic.claude-haiku-4-5-20251001-v1:0"

# Initialize checkpointer for state persistence
checkpointer = AgentCoreMemorySaver(memory_id, region_name=region)

# Initialize LLM
llm = init_chat_model(MODEL_ID, model_provider="bedrock_converse", region_name=region)


@tool
def add(a: int, b: int):
    """Add two integers and return the result"""
    return a + b


@tool
def multiply(a: int, b: int):
    """Multiply two integers and return the result"""
    return a * b


tools = [add, multiply]

graph = create_react_agent(
    model=llm,
    tools=tools,
    prompt="You are a helpful assistant",
    checkpointer=checkpointer,
)

graph

config = {
    "configurable": {
        "thread_id": "session-1",  # REQUIRED: This maps to Bedrock AgentCore session_id under the hood
        "actor_id": "react-agent-1",  # REQUIRED: This maps to Bedrock AgentCore actor_id under the hood
    }
}

inputs = {
    "messages": [{"role": "user", "content": "What is 1337 times 515321? Then add 412 and return the value to me."}]}

for chunk in graph.stream(inputs, stream_mode="updates", config=config):
    print(chunk)

for message in graph.get_state(config).values.get("messages"):
    print(f"{message.type}: {message.text()}")
    print("=========================================")

for checkpoint in graph.get_state_history(config):
    print(
        f"(Checkpoint ID: {checkpoint.config['configurable']['checkpoint_id']}) # of messages in state: {len(checkpoint.values.get('messages'))}"
    )

inputs = {"messages": [{"role": "user", "content": "What were the first calculations I asked you to do?"}]}

for chunk in graph.stream(inputs, stream_mode="updates", config=config):
    print(chunk)

config = {
    "configurable": {
        "thread_id": "session-2",  # New session ID
        "actor_id": "react-agent-1",  # Same Actor ID
    }
}

inputs = {"messages": [{"role": "user", "content": "What values did I ask you to multiply and add?"}]}
for chunk in graph.stream(inputs, stream_mode="updates", config=config):
    print(chunk)

client.delete_memory_and_wait(memory_id=memory_id, max_wait=300, poll_interval=10)
