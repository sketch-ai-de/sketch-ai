from typing import Any, List, Optional

from llama_index import QueryBundle
from llama_index.retrievers import BaseRetriever
from llama_index.schema import NodeWithScore
from llama_index.vector_stores import ChromaVectorStore, VectorStoreQuery

from llama_index.postprocessor import SentenceTransformerRerank

reranker = SentenceTransformerRerank(top_n=10, model="BAAI/bge-reranker-base")

from llama_index.postprocessor import LLMRerank


class VectorDBRetriever(BaseRetriever):

    """
    It is a subclass of BaseRetriever and is used to retrieve data

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
        similarity_top_k_rerank: int = 15,
        logger: Any = None,
        service_context=None,
        rerank: bool = False,
    ) -> None:
        self._vector_store = vector_store
        self._vector_stores = vector_stores
        self._embed_model = embed_model
        self._query_mode = query_mode
        self._similarity_top_k = similarity_top_k
        self._similarity_top_k_rerank = similarity_top_k_rerank
        self.logger = logger
        self.service_context = service_context
        self._rerank = rerank

    """
    Initialize the VectorDBRetriever.

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
            self.logger.info(
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
            if self._rerank:
                nodes_with_scores_.extend(store_v)  # [0:3]
            else:
                nodes_with_scores_.extend(
                    store_v[0:3]
                )  # take 4 results fom each store and add to nodes_with_scores_
        nodes_with_scores = nodes_with_scores_

        # reranked_nodes = reranker.postprocess_nodes(
        #    nodes_with_scores, query_bundle=query_bundle
        # )

        # reranker = LLMRerank(
        #    choice_batch_size=3,
        #    top_n=self._similarity_top_k_rerank,
        #    service_context=self.service_context,
        # )

        if self._rerank:
            from llama_index.postprocessor import FlagEmbeddingReranker

            self.logger.info(
                "start reranking {} nodes to {} nodes. ".format(
                    len(nodes_with_scores), self._similarity_top_k_rerank
                )
            )
            rerank = FlagEmbeddingReranker(
                model="BAAI/bge-reranker-base", top_n=self._similarity_top_k_rerank
            )

            reranked_nodes = rerank.postprocess_nodes(
                nodes_with_scores, query_bundle=query_bundle
            )

            # reranked_nodes = reranker.postprocess_nodes(
            #    nodes_with_scores, query_str=query_bundle.query_str
            # )

            self.logger.debug("nodes_with_scores MERGED: {}".format(nodes_with_scores))

            # self.logger.debug("reranked_nodes MERGED: {}".format(reranked_nodes))

            self.logger.debug(
                "nodes_with_scores MERGED: {}".format(nodes_with_scores[0:10])
            )
            return reranked_nodes
        else:
            return nodes_with_scores[0 : self._similarity_top_k]

        # self.logger.debug("reranked_nodes MERGED: {}".format(reranked_nodes))
        # self.logger.info("reranked_nodes MERGED: {}".format(reranked_nodes))
        return reranked_nodes  # 4 results with one store, 8 with 2 stores
        # return nodes_with_scores[0:15]  # 4 results with one store, 8 with 2 stores
