from llama_index import QueryBundle
from llama_index.retrievers import BaseRetriever
from typing import Any, List
from llama_index.vector_stores import ChromaVectorStore
from llama_index.vector_stores import VectorStoreQuery

from llama_index.schema import NodeWithScore
from typing import Optional


class VectorDBRetriever(BaseRetriever):
    """Retriever over a ChromaVectorStore vector store."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        vector_stores: [],
        embed_model: Any,
        query_mode: str = "default",
        similarity_top_k: int = 10,
        logger: Any = None,
        query_str: str = "",
    ) -> None:
        """Init params."""
        self._vector_store = vector_store
        self._vector_stores = vector_stores
        self._embed_model = embed_model
        self._query_mode = query_mode
        self._similarity_top_k = similarity_top_k
        self.logger = logger
        self.query_str = query_str

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve."""
        nodes_with_scores_matrix = [[] for _ in range(len(self._vector_stores))]
        for store_index, store in enumerate(self._vector_stores):
            nodes_with_scores = []
            self._vector_store = store
            self.logger.debug(
                "vector_store client: {}".format(self._vector_store.client)
            )
            query_embedding = self.embed_model.get_query_embedding(query_str)
            vector_store_query = VectorStoreQuery(
                query_embedding=query_embedding,
                similarity_top_k=self._similarity_top_k,
                mode=self._query_mode,
            )
            query_result = self._vector_store.query(vector_store_query)

            for index, node in enumerate(query_result.nodes):
                score: Optional[float] = None
                if query_result.similarities is not None:
                    score = query_result.similarities[index]
                nodes_with_scores.append(NodeWithScore(node=node, score=score))
            self.logger.debug("nodes_with_scores: {}".format(nodes_with_scores))
            nodes_with_scores_matrix[store_index] = nodes_with_scores

        nodes_with_scores_ = []
        for store_v in nodes_with_scores_matrix:
            nodes_with_scores_.extend(store_v[0:3])
        nodes_with_scores = nodes_with_scores_

        self.logger.debug("nodes_with_scores MERGED: {}".format(nodes_with_scores))
        return nodes_with_scores[0:30]
