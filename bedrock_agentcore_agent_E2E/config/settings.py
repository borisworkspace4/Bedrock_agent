# config/settings.py
from boto3.session import Session

# 获取 region（你也可以写死成 "us-west-2" 等）
_boto_session = Session()
REGION = _boto_session.region_name

# 统一使用的 entrypoint & requirements
ENTRYPOINT = "strands_claude.py"
REQUIREMENTS_FILE = "requirements.txt"

# 统一使用的 Agent 名称
AGENT_NAME = "strands_claude_getting_started"
