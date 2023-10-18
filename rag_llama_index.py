

from llama_index.embeddings import HuggingFaceEmbedding

# embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en")

embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

from pathlib import Path
from llama_hub.file.pymu_pdf.base import PyMuPDFReader

loader = PyMuPDFReader()
documents = loader.load(file_path="./docs/233.pdf")
documents = documents[10:-1]

from llama_index.text_splitter import SentenceSplitter

text_splitter = SentenceSplitter(
    chunk_size=1024,
    separator=" ",
    )

text_chunks = []
# maintain relationship with source doc index, to help inject doc metadata in (3)
doc_idxs = []
for doc_idx, doc in enumerate(documents):
    cur_text_chunks = text_splitter.split_text(" ".join(doc.text.split()))#text_splitter.split_text(doc.text)
    text_chunks.extend(cur_text_chunks)
    doc_idxs.extend([doc_idx] * len(cur_text_chunks))

from llama_index.schema import TextNode

nodes = []
for idx, text_chunk in enumerate(text_chunks):
    node = TextNode(
        text=text_chunk,
    )
    src_doc = documents[doc_idxs[idx]]
    node.metadata = src_doc.metadata
    nodes.append(node)

for node in nodes:
    node_embedding = embed_model.get_text_embedding(
        node.get_content(metadata_mode="all")
    )
    node.embedding = node_embedding

import chromadb
from llama_index.vector_stores import ChromaVectorStore
# create client and a new collection
chroma_client = chromadb.EphemeralClient()
chroma_collection = chroma_client.create_collection("quickstart")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)


vector_store.add(nodes)

query_str = "What is this technical document/manual/specification about? What is company name? What is the product name?"
query_str2 = "What is specific about iPOS drives? What is it for and what interfaces and protocols it is supporting?"

query_embedding = embed_model.get_query_embedding(query_str2)


# construct vector store query
from llama_index.vector_stores import VectorStoreQuery

query_mode = "default"
# query_mode = "sparse"
# query_mode = "hybrid"

vector_store_query = VectorStoreQuery(
    query_embedding=query_embedding, similarity_top_k=32, mode=query_mode
)

# returns a VectorStoreQueryResult
query_result = vector_store.query(vector_store_query)
print(query_result.nodes[0].get_content())


from llama_index.schema import NodeWithScore
from typing import Optional

nodes_with_scores = []
for index, node in enumerate(query_result.nodes):
    score: Optional[float] = None
    if query_result.similarities is not None:
        score = query_result.similarities[index]
    nodes_with_scores.append(NodeWithScore(node=node, score=score))


from llama_index import QueryBundle
from llama_index.retrievers import BaseRetriever
from typing import Any, List


class VectorDBRetriever(BaseRetriever):
    """Retriever over a ChromaVectorStore vector store."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embed_model: Any,
        query_mode: str = "default",
        similarity_top_k: int = 5,
    ) -> None:
        """Init params."""
        self._vector_store = vector_store
        self._embed_model = embed_model
        self._query_mode = query_mode
        self._similarity_top_k = similarity_top_k

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve."""
        query_embedding = embed_model.get_query_embedding(query_str)
        vector_store_query = VectorStoreQuery(
            query_embedding=query_embedding,
            similarity_top_k=self._similarity_top_k,
            mode=self._query_mode,
        )
        query_result = vector_store.query(vector_store_query)

        nodes_with_scores = []
        for index, node in enumerate(query_result.nodes):
            score: Optional[float] = None
            if query_result.similarities is not None:
                score = query_result.similarities[index]
            nodes_with_scores.append(NodeWithScore(node=node, score=score))

        return nodes_with_scores

retriever = VectorDBRetriever(
    vector_store, embed_model, query_mode="default", similarity_top_k=5
)


from llama_index import ServiceContext

import os
import openai

os.environ["OPENAI_API_KEY"] = "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"
openai.api_key = os.environ["OPENAI_API_KEY"]

from llama_index.llms import OpenAI

llm = OpenAI(temperature=0.1, model="gpt-3.5-turbo")


service_context = ServiceContext.from_defaults(
    chunk_size=1024,
    llm=llm,
)

service_context = ServiceContext.from_defaults(llm=llm, embed_model=embed_model)

from llama_index.query_engine import RetrieverQueryEngine
query_engine = RetrieverQueryEngine.from_args(
    retriever, service_context=service_context
)

from llama_index import VectorStoreIndex, SimpleDirectoryReader
from llama_index.output_parsers import LangchainOutputParser
from llama_index.llm_predictor import StructuredLLMPredictor
from llama_index.prompts.prompts import QuestionAnswerPrompt, RefinePrompt
from llama_index.prompts.default_prompts import DEFAULT_TEXT_QA_PROMPT_TMPL, DEFAULT_REFINE_PROMPT_TMPL
from langchain.output_parsers import StructuredOutputParser, ResponseSchema


# define output schema
document_description = ResponseSchema(name="document_description",
                             description="What is this technical document about?")
company_name = ResponseSchema(name="company_name",
                                      description="What is company name?")
product_name = ResponseSchema(name="product_name",
                                    description="What is the product name?")
product_description = ResponseSchema(name="product_description",
                                    description="What is this product about?")

response_schemas = [document_description, 
                    company_name,
                    product_name,
                    product_description]

# define output parser
lc_output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
output_parser = LangchainOutputParser(lc_output_parser)

# format each prompt with output parser instructions
fmt_qa_tmpl = output_parser.format(DEFAULT_TEXT_QA_PROMPT_TMPL)
fmt_refine_tmpl = output_parser.format(DEFAULT_REFINE_PROMPT_TMPL)
qa_prompt = QuestionAnswerPrompt(fmt_qa_tmpl, output_parser=output_parser)
refine_prompt = RefinePrompt(fmt_refine_tmpl, output_parser=output_parser)

query_engine = RetrieverQueryEngine.from_args(
    retriever, 
    service_context=service_context,
    text_qa_template=qa_prompt,
    refine_template=refine_prompt,
)

query_str = "What is this technical document/manual/specification about? What is company name? What is the product name?"
query_str = "What is specific about iPOS drives? What is it for and what interfaces and protocols it is supporting?"

response = query_engine.query(query_str)


from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser


document_description = ResponseSchema(name="document_description",
                             description="What is this technical document about?")
company_name = ResponseSchema(name="company_name",
                                      description="What is company name?")
product_name = ResponseSchema(name="product_name",
                                    description="What is the product name?")
product_description = ResponseSchema(name="product_description",
                                    description="What is this product about?")

response_schemas = [document_description, 
                    company_name,
                    product_name,
                    product_description]

output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()
print(format_instructions)

review_template_2 = """\
give a short answer of what this technical document/manual/specification about in form of:

document_description: What is this technical document about?

company_name: What is company name?

product_name: What is the product name?

product_description: What is this product about?

text: {text}

{format_instructions}
"""

from langchain.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template(template=review_template_2)

messages = prompt.format_messages(text=query_result.nodes[0].text + query_result.nodes[1].text + query_result.nodes[2].text + query_result.nodes[3].text + query_result.nodes[4].text, 
                                format_instructions=format_instructions)

text = """'may be reproduced or transmitted in any form or by any means, electrical or mechanical including photocopying, recording or by any information-retrieval system without permission in writing from Technosoft S.A. The information in this document is subject to change without notice. About This Manual This manual describes how to program Technosoft iPOS family of intelligent drives using CANopen protocol. 1 The iPOS drives are conforming to CiA 301 v4.2 application layer and communication profile, CiA WD 305 v.2.2.130F Layer Setting Services and to CiA (DSP) 402 v4.0 device profile for drives and motion control, now included in IEC 61800-7-1 Annex A, IEC 61800-7-201 and IEC 61800-7-301 standards. The manual presents the object dictionary associated with these three profiles. It also explains how to combine the Technosoft Motion Language',
 '2023 10 iPOS CANopen Programming 22.6 Customizing the Drive Reaction to Fault Conditions ......................................... 231 Read This First Whilst Technosoft believes that the information and guidance given in this manual is correct, all parties must rely upon their own skill and judgment when making use of it. Technosoft does not assume any liability to anyone for any loss or damage caused by any error or omission in the work, whether such error or omission is the result of negligence or any other cause. Any and all such liability is disclaimed. All rights reserved. No part or parts of this document may be reproduced or transmitted in any form or by any means, electrical or mechanical including photocopying, recording or by any information-retrieval system without permission in writing from',
 'Name Object code Data type Access PDO mapping Value range Default value 100Ah Manufacturer software version VAR Visible String Const No No Product dependent 5.8.5 Object 2060h: Software version of a TML application By inspecting this object, the user can find out the software version of the TML application (drive setup plus motion setup and eventually cam tables) that is stored in the EEPROM memory of the drive. The object shows a string of the first 4 elements written in the TML application field, grouped in a 32-bit variable. If more character are written, only the first 4 will be displayed. Each byte represents an ASCII character. Object description: Entry description: Example: Index Name Object code Data type Access PDO mapping Units Value range Default value 2060h Software',
 '1018h: Identity Object This object provides general information about the device. Sub-index 01h shows the unique Vendor ID allocated to Technosoft (1A3h). Sub-index 02h contains the Technosoft drive product ID. It can be found physically on the drive label or in Drive Setup/ Drive info button under the field product ID. If the Technosoft product ID is P027.214.E121, sub-index 02h will be read as the number 27214121 in decimal. Sub-index 03h shows the Revision number. Sub-index 04h shows the drives Serial number. For example the number 0x4C451158 will be 0x4C (ASCII L); 0x45 (ASCII E); 0x1158 --> the serial number will be LE1158. Object description: Entry description: Index Name Object code Data type Sub-index Description Access PDO mapping Value range Default value Sub-index Description Access PDO mapping Value',
"""
messages = prompt.format_messages(text=text, 
                                format_instructions=format_instructions)

from langchain.chat_models import ChatOpenAI
chat = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo")
response = chat(messages)
print(response.content)