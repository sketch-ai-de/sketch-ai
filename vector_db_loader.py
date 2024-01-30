from typing import List, Tuple

import chromadb
from langchain.output_parsers import StructuredOutputParser
from llama_index.output_parsers import LangchainOutputParser
from llama_index.prompts.default_prompts import (
    DEFAULT_REFINE_PROMPT_TMPL,
    DEFAULT_TEXT_QA_PROMPT_TMPL,
)
from llama_index.prompts.prompts import QuestionAnswerPrompt, RefinePrompt
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.schema import TextNode
from llama_index.storage.storage_context import StorageContext
from llama_index.vector_stores import ChromaVectorStore


class VectorDBLoader:
    """
    A class for loading data into a vector database collection and
    retrieving data from it.

    Args:
    - llm: An instance of the Langchain LLM class.
    - logger: An instance of the Python logging class.
    - service_context: A dictionary containing the service context.
    - collection_dict: A dictionary containing the names of the collections and the documents to be loaded into them.
    - Docs: An instance of the Langchain Docs class.
    - embed_model: An instance of the Langchain EmbedModel class.
    """

    def __init__(
        self,
        llm,
        logger,
        service_context,
        collection_dict: List[str],
        embed_model,
        verbose=False,
    ):
        self.llm = llm
        self.logger = logger
        self.service_context = service_context
        self.collection_dict = collection_dict
        self.embed_model = embed_model
        self.all_nodes = []
        self.verbose = verbose

    def get_all_nodes(self):
        return self.all_nodes

    def load_documents_to_db(self, vector_store, nodes) -> List[TextNode]:
        """
        Load data to vector database collection.

        Args:
        - vector_store: An instance of the ChromaVectorStore class.
        - documents: A list of documents to be loaded into the collection.
        - sherpa_pdf: A boolean indicating whether the documents are sherpa PDFs.
        - sherpa_table: A boolean indicating whether the documents are sherpa tables.

        Returns:
        - A list of TextNode objects.
        """
        for node in nodes:
            node_embedding = self.embed_model.get_text_embedding(
                node.get_content(metadata_mode="all")
            )
            node.embedding = node_embedding
            self.all_nodes.append(node)

        self.logger.debug(
            "adding node to vector_store client: {}".format(vector_store.client)
        )
        vector_store.add(nodes)
        # return nodes

    def get_query_engine(self, response_schemas, retriever) -> RetrieverQueryEngine:
        """
        Get a RetrieverQueryEngine object.

        Args:
        - response_schemas: A list of response schemas.
        - retriever: An instance of the Retriever class.

        Returns:
        - An instance of the RetrieverQueryEngine class.
        """
        # define output parser
        lc_output_parser = StructuredOutputParser.from_response_schemas(
            response_schemas
        )
        output_parser = LangchainOutputParser(lc_output_parser)

        # format each prompt with output parser instructions
        fmt_qa_tmpl = output_parser.format(DEFAULT_TEXT_QA_PROMPT_TMPL)
        fmt_refine_tmpl = output_parser.format(DEFAULT_REFINE_PROMPT_TMPL)
        qa_prompt = QuestionAnswerPrompt(fmt_qa_tmpl, output_parser=output_parser)
        refine_prompt = RefinePrompt(fmt_refine_tmpl, output_parser=output_parser)

        query_engine = RetrieverQueryEngine.from_args(
            retriever,
            service_context=self.service_context,
            text_qa_template=qa_prompt,
            verbose=self.verbose
            # refine_template=refine_prompt,
        )

        return query_engine

    def get_collection_from_db(self, collection) -> Tuple:
        """
        This function takes in a collection parameter which is the name of the
        collection to retrieve.

        Args:
        - collection: The name of the collection.

        Returns:
        - A tuple containing a ChromaVectorStore object, a StorageContext object, and a chromadb Collection object.
        """
        chroma_db_path = "./db/chroma_db"
        db = chromadb.PersistentClient(path=chroma_db_path)
        chroma_collection = db.get_or_create_collection(collection)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        return vector_store, storage_context, chroma_collection

    def get_vector_stores(
        self,
    ) -> Tuple[List[ChromaVectorStore], StorageContext, chromadb.Collection]:
        """
        The purpose of this function is to retrieve a list of `ChromaVectorStore`
        objects, a `StorageContext` object, and a `chromadb.Collection` object.

        Returns:
        - A tuple containing a list of ChromaVectorStore objects, a StorageContext object, and a chromadb Collection object.
        """
        vector_stores = []
        chroma_collection = None

        for coll_name in self.collection_dict.keys():
            (
                vector_store,
                storage_context,
                chroma_collection,
            ) = self.get_collection_from_db(coll_name)

            if len(chroma_collection.get()["ids"]) == 0:
                self.logger.info(f"Load data to collection {coll_name} \n")

                self.load_documents_to_db(
                    vector_store,
                    nodes=self.collection_dict[coll_name],
                )
            else:
                self.logger.info(f"Data already exist in collection {coll_name} \n")

            vector_stores.append(vector_store)

        for v in vector_stores:
            self.logger.debug(f"vector_stores client {v.client} \n")

        return vector_stores, storage_context


#   def get(
#       self,
#   ) -> Tuple[List[ChromaVectorStore], StorageContext, chromadb.Collection]:
#       """
#       Get a list of ChromaVectorStore objects, a StorageContext object,
#       and a chromadb Collection object.
#       """
#       return self.get_vector_stores()
