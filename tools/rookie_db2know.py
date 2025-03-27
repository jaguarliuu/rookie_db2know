from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.database_utils import get_db_schema
from tools.dify_knowledge_api_utils import DifyKnowledgeRequest
from utils.prompt_loader import PromptLoader
from dify_plugin.entities.model.llm import LLMModelConfig
from dify_plugin.entities.model.message import SystemPromptMessage

class RookieDb2knowTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        model_info= tool_parameters.get('chat_model')
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

        api = DifyKnowledgeRequest(dify_knowledge_api_url, dify_knowledge_api_key, embedding_model, rerank_model)
        # 创建知识库
        dataset_id = api._create_dataset(dataset_name=tool_parameters['database'])
        # 初始化模板加载器
        prompt_loader = PromptLoader()
        for table_name, table_info in schema.items():
            # 在这里调用大模型去创建知识库
            context = {
                'table_name': table_name,
                'meta_data': table_info
            }
            system_prompt = prompt_loader.get_prompt(context)
            print(system_prompt)
            response = self.session.model.llm.invoke(
                model_config=LLMModelConfig(
                    provider=model_info.get('provider'),
                    model=model_info.get('model'),
                    mode=model_info.get('mode'),
                    completion_params=model_info.get('completion_params')
                ),
                prompt_messages=[
                    SystemPromptMessage(content=system_prompt),
                ],
                stream=False
            )
            document_dict = api._create_document_by_text(dataset_id, table_name, response.message.content)
            if document_dict is None:
                raise ValueError("Failed to create document")
            
        #dataset_id = api.write_database_schema(schema, tool_parameters["database"])
        yield self.create_text_message(dataset_id)
