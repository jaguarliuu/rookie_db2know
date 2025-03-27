from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.database_utils import get_db_schema
from tools.dify_knowledge_api_utils import DifyKnowledgeRequest

class RookieDb2knowTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:

        schema = get_db_schema(
            tool_parameters["db_type"],
            tool_parameters["host"],
            tool_parameters["port"],
            tool_parameters["database"],
            tool_parameters["username"],
            tool_parameters["password"],
            tool_parameters["table_names"]
        )

        dify_knowledge_api_url = self.runtime.credentials.get("dify_knowledge_api_url")
        dify_knowledge_api_key = self.runtime.credentials.get("dify_knowledge_api_key")

        embedding_model = tool_parameters.get("embedding_model")
        rerank_model = tool_parameters.get("rerank_model")

        # api = DifyKnowledgeRequest(dify_knowledge_api_url, dify_knowledge_api_key, embedding_model, rerank_model)

        for table_name, table_info in schema.items():
            print(table_name, table_info)

        #dataset_id = api.write_database_schema(schema, tool_parameters["database"])

        yield self.create_text_message("dataset_id")
