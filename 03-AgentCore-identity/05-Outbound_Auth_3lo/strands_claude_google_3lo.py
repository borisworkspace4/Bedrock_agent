import os
import datetime
import json
import asyncio
import traceback
from typing import Dict, Any, Optional, AsyncGenerator

from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.identity.auth import requires_access_token

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Environment configuration
os.environ["STRANDS_OTEL_ENABLE_CONSOLE_EXPORT"] = "true"
os.environ["OTEL_PYTHON_EXCLUDED_URLS"] = "/ping,/invocations"

# Required OAuth2 scope for Google Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Global variable to store the access token
google_access_token: Optional[str] = None


@tool(
    name="Get_calendar_events_today",
    description="Retrieves the calendar events for the day from your Google Calendar"
)
def get_calendar_events_today() -> str:
    """
    Retrieve calendar events for today from Google Calendar.

    Returns:
        str: JSON string containing events or error information
    """
    global google_access_token

    # Check if we already have a token
    if not google_access_token:
        return json.dumps({
            "auth_required": True,
            "message": "Google Calendar authentication is required. Please wait while we set up the authorization.",
            "events": []
        })

    # Create credentials from the provided access token
    creds = Credentials(token=google_access_token, scopes=SCOPES)
    try:
        service = build("calendar", "v3", credentials=creds)

        # Calculate today's time range
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)

        # Format with CDT timezone (-05:00)
        time_min = today_start.strftime('%Y-%m-%dT00:00:00-05:00')
        time_max = today_end.strftime('%Y-%m-%dT23:59:59-05:00')

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            return json.dumps({"events": []})

        return json.dumps({"events": events})

    except HttpError as error:
        error_message = str(error)
        return json.dumps({"error": error_message, "events": []})
    except Exception as e:
        error_message = str(e)
        return json.dumps({"error": error_message, "events": []})


# Initialize the agent with tools and your preferred model choice
agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    tools=[get_calendar_events_today]
)

# Initialize app and streaming queue
app = BedrockAgentCoreApp()


class StreamingQueue:
    """A queue for streaming responses asynchronously."""

    def __init__(self):
        self.finished = False
        self.queue = asyncio.Queue()

    async def put(self, item: str) -> None:
        """Add an item to the queue."""
        await self.queue.put(item)

    async def finish(self) -> None:
        """Mark the queue as finished."""
        self.finished = True
        await self.queue.put(None)

    async def stream(self) -> AsyncGenerator[str, None]:
        """Stream items from the queue."""
        while True:
            item = await self.queue.get()
            if item is None and self.finished:
                break
            yield item


queue = StreamingQueue()


async def on_auth_url(url: str) -> None:
    """Handle authorization URL callback."""
    print(f"Authorization url: {url}")
    await queue.put(f"Authorization url: {url}")


async def agent_task(user_message: str) -> None:
    """
    Execute the agent task with authentication handling.

    Args:
        user_message: The user's input message
    """
    try:
        await queue.put("Begin agent execution")

        # Call the agent first to see if it needs authentication
        response = agent(user_message)

        # Extract text content from the response structure
        response_text = ""
        if isinstance(response.message, dict):
            content = response.message.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        response_text += item['text']
        else:
            response_text = str(response.message)

        # Check if the response indicates authentication is required
        auth_keywords = [
            "authentication", "authorize", "authorization", "auth",
            "sign in", "login", "access", "permission", "credential",
            "need authentication", "requires authentication"
        ]
        needs_auth = any(keyword.lower() in response_text.lower() for keyword in auth_keywords)

        if needs_auth:
            await queue.put("Authentication required for Google Calendar access. Starting authorization flow...")

            # Trigger the 3LO authentication flow
            try:
                global google_access_token
                google_access_token = await need_token_3lo_async(access_token='')
                await queue.put("Authentication successful! Retrying calendar request...")

                # Retry the agent call now that we have authentication
                response = agent(user_message)
            except Exception as auth_error:
                print(f"auth_error: {auth_error}")
                await queue.put(f"Authentication failed: {str(auth_error)}")

        await queue.put(response.message)
        await queue.put("End agent execution")
    except Exception as e:
        await queue.put(f"Error: {str(e)}")
    finally:
        await queue.finish()


@requires_access_token(
    provider_name=google-cal-provider,
    scopes=SCOPES,
    auth_flow='USER_FEDERATION',
    on_auth_url=on_auth_url,
    force_authentication=True,
    callback_url="http://localhost:9090/oauth2/callback"  # ¡û Callback URL determined from notebook environment
)
async def need_token_3lo_async(*, access_token: str) -> str:
    """
    Handle 3-legged OAuth token retrieval.

    Args:
        access_token: The OAuth access token

    Returns:
        str: The access token
    """
    global google_access_token
    google_access_token = access_token
    return access_token


@app.entrypoint
async def agent_invocation(payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """
    Main entrypoint for agent invocations.

    Args:
        payload: The request payload containing the prompt

    Yields:
        str: Streaming response items
    """
    user_message = payload.get(
        "prompt",
        "No prompt found in input, please guide customer to create a json payload with prompt key"
    )

    # Create and start the agent task
    task = asyncio.create_task(agent_task(user_message))

    # Return the stream, but ensure the task runs concurrently
    async def stream_with_task() -> AsyncGenerator[str, None]:
        # Stream results as they come
        async for item in queue.stream():
            yield item

        # Ensure the task completes
        await task

    return stream_with_task()


if __name__ == "__main__":
    app.run()
