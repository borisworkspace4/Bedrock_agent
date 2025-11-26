# scripts/invoke_agent.py
from config.runtime_utils import get_runtime

def main():
    agentcore_runtime = get_runtime()

    payload = {"prompt": "How is the weather now?"}
    invoke_response = agentcore_runtime.invoke(payload)

    print("💬 Invoke response:")
    print(invoke_response)

if __name__ == "__main__":
    main()
