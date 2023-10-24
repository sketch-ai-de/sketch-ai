from typing import List, Tuple
from llama_index.schema import TextNode
from llama_index.storage.storage_context import StorageContext
from document_preprocessor import DocumentPreprocessor

from llama_index.query_engine import RetrieverQueryEngine

from langchain.output_parsers import StructuredOutputParser

from llama_index.prompts.prompts import QuestionAnswerPrompt, RefinePrompt

import chromadb

from llama_index.vector_stores import ChromaVectorStore

from llama_index.output_parsers import LangchainOutputParser

from llama_index.prompts.default_prompts import (
    DEFAULT_TEXT_QA_PROMPT_TMPL,
    DEFAULT_REFINE_PROMPT_TMPL,
)


class VectorDBLoader:
    def __init__(
        self,
        llm,
        logger,
        service_context,
        collection_dict: List[str],
    ):
        self.llm = llm
        self.logger = logger
        self.service_context = service_context
        self.collection_dict = collection_dict

    def load_documents_to_db(
        self, vector_store, sherpa_pdf=False, sherpa_table=False
    ) -> List[TextNode]:
        """Load data to vector database collection."""
        nodes = []

        if not sherpa_pdf and not sherpa_table:
            self.logger.info("--------------------- Process normal PDF \n")
            self.Docs.process_normal_pdf(self.llm, self.documents, nodes)

        if sherpa_table and not sherpa_pdf:
            self.Docs.process_sherpa_table(self.llm, self.documents, nodes)

        nodes = self.Docs.get_nodes()

        for node in nodes:
            node_embedding = self.embed_model.get_text_embedding(
                node.get_content(metadata_mode="all")
            )
            node.embedding = node_embedding

        vector_store.add(nodes)
        return nodes

    def get_query_engine(self, response_schemas, retriever) -> RetrieverQueryEngine:
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
        chroma_db_path = "./chroma_db"
        db = chromadb.PersistentClient(path=chroma_db_path)
        chroma_collection = db.get_or_create_collection(collection)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        return vector_store, storage_context, chroma_collection

    def get_vector_stores(
        self,
    ) -> Tuple[List[ChromaVectorStore], StorageContext, chromadb.Collection]:
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

            if sherpa_table and not chroma_collection.get()["ids"]:
                self.logger.info("--------------------- Load data to collection  \n")
                self.logger.debug(
                    "coll_name, sherpa_table, sherpa_pdf: %s, %s, %s",
                    coll_name,
                    sherpa_table,
                    sherpa_pdf,
                )
                self.load_documents_to_db(
                    vector_store,
                    sherpa_pdf=sherpa_pdf,
                    sherpa_table=sherpa_table,
                )
            elif sherpa_table:
                self.logger.info(
                    "--------------------- Data already exist in collection  \n"
                )

            vector_stores.append(vector_store)

        for v in vector_stores:
            self.logger.debug(
                "vector_stores client --------------------------------------------------\n%s",
                v.client,
            )

        return vector_stores, storage_context, chroma_collection

    def get(
        self,
    ) -> Tuple[List[ChromaVectorStore], StorageContext, chromadb.Collection]:
        return self.get_vector_stores()
