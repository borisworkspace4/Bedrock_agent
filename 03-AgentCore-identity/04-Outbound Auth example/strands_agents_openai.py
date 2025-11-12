import json
from strands import Agent, tool
from strands_tools import calculator
from strands.models.litellm import LiteLLMModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from botocore.exceptions import ClientError
from boto3.session import Session

boto_session = Session()

secret_name = "bedrock-agentcore-identity!default/apikey/openai-apikey-provider"

def get_secret(session="", secret_name=""):

    session = session
    secret_name = secret_name
    region_name = session.region_name

    # Create a Secrets Manager client

    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']

    return secret
    # Your code goes here.

api_key_value = get_secret(boto_session, secret_name)

data = json.loads(api_key_value)
api_key = data["api_key_value"]

app = BedrockAgentCoreApp()

@tool
def weather():
    """ Get weather """ # Dummy implementation
    return "sunny"

@app.entrypoint
async def strands_agent_open_ai(payload):
    """
    Invoke the agent with a payload
    """

    # Initialize agent after API key is set
    print("Initializing agent with OPENAI API KEY...")
    model = "gpt-4o-mini"
    litellm_model = LiteLLMModel(
        model_id=model,
        params={
            "max_tokens": 8192,
            "temperature": 0.7
        },
        client_args={
            "api_key": api_key
        }
    )

    agent = Agent(
        model=litellm_model,
        tools=[calculator, weather],
        system_prompt="You're a helpful assistant. You can do simple math calculation, and tell the weather."
    )
    print("Agent initialized successfully")

    user_input = payload.get("prompt")
    print(f"User input: {user_input}")

    try:
        response = agent(user_input)
        print(f"Agent response: {response}")
        return response.message['content'][0]['text']
    except Exception as e:
        print(f"Error in agent processing: {e}")
        raise

if __name__ == "__main__":
    app.run()
