from llama_index import QueryBundle
from llama_index.retrievers import BaseRetriever
from llama_index.vector_stores import ChromaVectorStore, VectorStoreQuery
from llama_index.schema import NodeWithScore
from typing import Any, List, Optional


class VectorDBRetriever(BaseRetriever):
    """It is a subclass of BaseRetriever and is used to retrieve data from a ChromaVectorStore vector store.
    The class takes in several arguments including the vector store, a list of vector stores, an embedding model, query mode, similarity top k, and a logger.
    The class has a method named _retrieve which retrieves data from the vector store and returns a list of NodeWithScore objects.

    Args:
        vector_store (ChromaVectorStore): The vector store to retrieve from.
        vector_stores (list): A list of vector stores to retrieve from.
        embed_model (Any): The embedding model to use for queries.
        query_mode (str, optional): The query mode to use. Defaults to "default".
        similarity_top_k (int, optional): The number of results to return. Defaults to 10.
        logger (Any, optional): The logger to use. Defaults to None.
    """

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        vector_stores: [],
        embed_model: Any,
        query_mode: str = "default",
        similarity_top_k: int = 10,
        logger: Any = None,
    ) -> None:
        self._vector_store = vector_store
        self._vector_stores = vector_stores
        self._embed_model = embed_model
        self._query_mode = query_mode
        self._similarity_top_k = similarity_top_k
        self.logger = logger

    """Initialize the VectorDBRetriever.

        Args:
            vector_store (ChromaVectorStore): The vector store to retrieve from.
            vector_stores (list): A list of vector stores to retrieve from.
            embed_model (Any): The embedding model to use for queries.
            query_mode (str, optional): The query mode to use. Defaults to "default".
            similarity_top_k (int, optional): The number of results to return. Defaults to 10.
            logger (Any, optional): The logger to use. Defaults to None.
        """

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve."""
        nodes_with_scores_matrix = [[] for _ in range(len(self._vector_stores))]
        for store_index, store in enumerate(self._vector_stores):
            nodes_with_scores = []
            self._vector_store = store
            self.logger.debug(
                "vector_store client: {}".format(self._vector_store.client)
            )
            query_embedding = self._embed_model.get_query_embedding(
                query_bundle.query_str
            )
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
