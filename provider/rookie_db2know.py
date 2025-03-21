from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from tools.dify_knowledge_api_utils import auth


class RookieDb2knowProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        auth(credentials)
