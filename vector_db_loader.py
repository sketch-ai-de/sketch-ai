from typing import List, Tuple

import chromadb
from langchain.output_parsers import StructuredOutputParser
from llama_index.output_parsers import LangchainOutputParser
from llama_index.prompts.default_prompts import (DEFAULT_REFINE_PROMPT_TMPL,
                                                 DEFAULT_TEXT_QA_PROMPT_TMPL)
from llama_index.prompts.prompts import QuestionAnswerPrompt, RefinePrompt
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.schema import TextNode
from llama_index.storage.storage_context import StorageContext
from llama_index.vector_stores import ChromaVectorStore


class VectorDBLoader:
    """
    A class for loading data into a vector database collection and retrieving data from it.
    There are methods in the class that are used to retrieve data from a ChromaVectorStore object, a StorageContext object, and a chromadb Collection object.
    The data is then processed and added to the vector store.

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
        Docs,
        embed_model,
    ):
        self.llm = llm
        self.logger = logger
        self.service_context = service_context
        self.collection_dict = collection_dict
        self.Docs = Docs
        self.embed_model = embed_model

    def load_documents_to_db(
        self, vector_store, documents, sherpa_pdf=False, sherpa_table=False
    ) -> List[TextNode]:
        """
        Load data to vector database collection.

        It takes in an instance of the `ChromaVectorStore` class, a list of documents to be loaded into the collection, and two boolean values indicating whether the documents are sherpa PDFs or tables.

        The function first initializes an empty list called `nodes` and clears the `TextNode` objects in the `Docs` instance.
        Then, depending on the boolean values of `sherpa_pdf` and `sherpa_table`, the function processes the documents using different methods of the `Docs` instance. If neither boolean is `True`, the function processes normal PDFs using the `process_normal_pdf` method. If `sherpa_pdf` is `True`, the function processes sherpa PDFs using the `process_sherpa_pdf` method.
        If `sherpa_table` is `True`, the function processes sherpa tables using the `process_sherpa_table` method.

        After processing the documents, the function retrieves the `TextNode` objects using the `get_nodes` method of the `Docs` instance.
        For each `TextNode` object, the function retrieves the text content and generates an embedding using the `get_text_embedding` method of the `embed_model` instance.
        The embedding is then assigned to the `embedding` attribute of the `TextNode` object.

        Finally, the function adds the `TextNode` objects to the `ChromaVectorStore` instance using the `add` method and returns the list of `TextNode` objects.

        Args:
        - vector_store: An instance of the ChromaVectorStore class.
        - documents: A list of documents to be loaded into the collection.
        - sherpa_pdf: A boolean indicating whether the documents are sherpa PDFs.
        - sherpa_table: A boolean indicating whether the documents are sherpa tables.

        Returns:
        - A list of TextNode objects.
        """
        nodes = []
        self.Docs.clear_nodes()

        if not sherpa_pdf and not sherpa_table:
            self.logger.info("--------------------- Process normal PDF \n")
            self.Docs.process_normal_pdf(self.llm, documents)

        if sherpa_pdf and not sherpa_table:
            print(documents)
            self.logger.info("--------------------- Process sherpa PDF \n")
            self.Docs.process_sherpa_pdf(documents)

        if sherpa_table and not sherpa_pdf:
            self.Docs.process_sherpa_table(self.llm, documents)

        nodes = self.Docs.get_nodes()

        for node in nodes:
            node_embedding = self.embed_model.get_text_embedding(
                node.get_content(metadata_mode="all")
            )
            node.embedding = node_embedding

        self.logger.debug(
            "adding node to vector_store client: {}".format(vector_store.client)
        )
        vector_store.add(nodes)
        return nodes

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
            # refine_template=refine_prompt,
        )

        return query_engine

    def get_collection_from_db(self, collection) -> Tuple:
        """
        This function takes in a collection parameter which is the name of the collection to retrieve.
        The function returns a tuple containing a ChromaVectorStore object, a StorageContext object, and a chromadb Collection object.

        The function first creates a PersistentClient object from the chromadb module, \
            which is used to connect to a persistent database located at the path specified by chroma_db_path.
        The get_or_create_collection method is then called on the db object to retrieve or \
              create a collection with the name specified by the collection parameter.

        A ChromaVectorStore object is then created using the chroma_collection object retrieved from the previous step.
        A StorageContext object is also created using the vector_store object. The StorageContext object is used to manage the storage of the vector data.

        Finally, the function returns a tuple containing the vector_store, storage_context, and chroma_collection objects. ▌

        Args:
        - collection: The name of the collection.

        Returns:
        - A tuple containing a ChromaVectorStore object, a StorageContext object, and a chromadb Collection object.
        """
        chroma_db_path = "./chroma_db"
        db = chromadb.PersistentClient(path=chroma_db_path)
        chroma_collection = db.get_or_create_collection(collection)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        return vector_store, storage_context, chroma_collection

    def get_vector_stores(
        self,
    ) -> Tuple[List[ChromaVectorStore], StorageContext, chromadb.Collection]:
        """
        The purpose of this function is to retrieve a list of `ChromaVectorStore` objects, a `StorageContext` object, and a `chromadb.Collection` object.

        The function first initializes an empty list called `vector_stores`.
        It then iterates over the keys of the `collection_dict` dictionary attribute of the `VectorDBLoader` instance.
        For each key, the function calls the `get_collection_from_db` method of the `VectorDBLoader` instance to retrieve a \
            `ChromaVectorStore` object, a `StorageContext` object, and a `chromadb.Collection` object.

        The function then checks if the length of the `ids` attribute of the `chroma_collection` object is zero.
        If it is, the function logs a message indicating that data is being loaded into the collection.
        It then calls the `load_documents_to_db` method of the `VectorDBLoader` instance to load the documents associated with \
              the collection into the `vector_store` object.
        If the length of the `ids` attribute of the `chroma_collection` object is not zero, the function logs a message \
              indicating that data already exists in the collection.

        The `vector_store` object is appended to the `vector_stores` list.
        Once all the collections have been processed, the function logs the `client` attribute of each `ChromaVectorStore` object in the `vector_stores` list.
        Finally, the function returns a tuple containing the `vector_stores` list, the `storage_context` object, and the `chroma_collection` object.

        Returns:
        - A tuple containing a list of ChromaVectorStore objects, a StorageContext object, and a chromadb Collection object.
        """
        vector_stores = []

        for coll_name in self.collection_dict.keys():
            (
                vector_store,
                storage_context,
                chroma_collection,
            ) = self.get_collection_from_db(coll_name)

            sherpa_pdf = (
                "_pdf_sherpa_" in coll_name and not "_pdf_sherpa_table_" in coll_name
            )
            sherpa_table = "_pdf_sherpa_table_" in coll_name

            self.logger.debug(
                ":::::::::::::::::::::::::::::::::::::::::\n ",
                coll_name,
                " ",
                sherpa_table,
                " ",
                chroma_collection.get()["ids"],
            )

            if len(chroma_collection.get()["ids"]) == 0:
                self.logger.info("--------------------- Load data to collection  \n")
                self.logger.debug(
                    "coll_name, sherpa_table, sherpa_pdf: {}, {}, {}".format(
                        coll_name, sherpa_table, sherpa_pdf
                    )
                )
                self.load_documents_to_db(
                    vector_store,
                    self.collection_dict[coll_name],
                    sherpa_pdf=sherpa_pdf,
                    sherpa_table=sherpa_table,
                )
            else:
                self.logger.info(
                    "--------------------- Data already exist in collection  \n"
                )

            vector_stores.append(vector_store)

        for v in vector_stores:
            self.logger.debug(
                "vector_stores client --------------------------------------------------\n{}".format(
                    v.client
                )
            )

        return vector_stores, storage_context, chroma_collection

    def get(
        self,
    ) -> Tuple[List[ChromaVectorStore], StorageContext, chromadb.Collection]:
        """
        Get a list of ChromaVectorStore objects, a StorageContext object, and a chromadb Collection object.

        Returns:
        - A tuple containing a list of ChromaVectorStore objects, a StorageContext object, and a chromadb Collection object.
        """
        return self.get_vector_stores()
