from llama_index.retrievers import BaseRetriever
from llama_index import QueryBundle
from llama_index.schema import NodeWithScore
from llama_index.vector_stores import VectorStoreQuery
from typing import List, Sequence, Any
from llama_index.tools import BaseTool, adapt_to_async_tool
from llama_index import Document, VectorStoreIndex


class ToolRetriever(BaseRetriever):
    def __init__(
        self,
        tools: Sequence[BaseTool],
        sql_tools: Sequence[BaseTool],
        embed_model: Any,
        index: VectorStoreIndex = None,
        message: str = "",
        append_sql: bool = True,
        similarity_top_k: int = 8,
        logger=None,
    ) -> None:
        self._message = message
        self._tools = tools
        self._index = index
        self._sql_tools = sql_tools
        self._append_sql = append_sql
        self._similarity_top_k = similarity_top_k
        self._embed_model = embed_model
        self._logger = logger

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve."""
        from llama_index.retrievers import VectorIndexRetriever

        retriever = VectorIndexRetriever(
            index=self._index,
            similarity_top_k=self._similarity_top_k,
        )

        response = retriever.retrieve(query_bundle)

        tools_ = []

        for n in response:
            tools_.append(self._tools[n.metadata["idx"]])

        if self._append_sql:
            tools_.append(self._sql_tools)
            # tools_.append(self._tools[-1])  # add SQL tool

        self._logger.debug("Tools before: ", self._tools)
        _tmp = set(adapt_to_async_tool(t) for t in tools_)
        self._logger.debug("Tools after: ", list(_tmp))
        return list(_tmp)

        # return [adapt_to_async_tool(t) for t in tools_]

    def create_vector_index_from_tools(self):
        from llama_index.tools import adapt_to_async_tool

        get_tools = lambda _: self._tools
        tools = [adapt_to_async_tool(t) for t in get_tools("")]
        docs = [
            str(
                "idx: "
                + str(idx)
                + ", name: "
                + str(t.metadata.name)
                + ", description: "
                + str(t.metadata.description)
            )
            for idx, t in enumerate(tools)
        ]

        documents = [
            Document(text=t, metadata={"idx": idx}) for idx, t in enumerate(docs)
        ]

        self._index = VectorStoreIndex.from_documents(
            documents, embed_model=self._embed_model
        )
