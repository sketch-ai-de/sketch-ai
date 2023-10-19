# examples:
#   python3 rag_llama_index.py -fs "docs/arduino/uno-rev3/arduino-uno-rev3.pdf" -u="https://store.arduino.cc/products/arduino-uno-rev3" -c="arduino-uno-rev3"
#   python3 rag_llama_index.py -fs "docs/technosoft/technosoft_ipos_233_canopen/technosoft_ipos_233_canopen.pdf" "docs/technosoft/technosoft_ipos_233_canopen/imot23xs.pdf" -u="https://technosoftmotion.com/en/intelligent-motors/\?SingleProduct\=174" -c="technosoft_ipos_233_canopen"
#   python3 rag_llama_index.py -fs "docs/raspberry/pi4/raspberry-pi-4-product-brief.pdf" "docs/raspberry/pi4/raspberry-pi-4-datasheet.pdf" -u="https://www.raspberrypi.com/products/raspberry-pi-4-model-b/" -c="raspberry-pi-4-product-brief"
#   python3 rag_llama_index.py -fs "docs/ur/ur5e/ur5e_user_manual_en_us.pdf" "docs/ur/ur5e/ur5e-fact-sheet.pdf" -u="https://www.universal-robots.com/products/ur5-robot/" -c="ur5e_user_manual_en_us"

# tbd:
#   add additional sources
#   improve sources parser
#   integrate postgresql or another database
#   create simple devices representation in database, e.g. device_type table, and populate it
#   use sql requests to get data from the tables
#   use sql requests to put data to he tables
#   improve openai requsts / consider chains

import argparse
parser = argparse.ArgumentParser(
                    prog='RagLlamaindex',
                    description='Retrieve information from different soures - PDFs and Web-Links'
                    )
parser.add_argument('-f', '--filename')           # positional argument
parser.add_argument('-u', '--url')      # option that takes a value
parser.add_argument('-c', '--collection')      # option that takes a value

args = parser.parse_args()

from llama_index import QueryBundle
from llama_index.retrievers import BaseRetriever
from typing import Any, List

from llama_index import ServiceContext

import os
import openai

from llama_index import VectorStoreIndex

from llama_index.vector_stores import ChromaVectorStore

from llama_index.output_parsers import LangchainOutputParser
from llama_index.prompts.prompts import QuestionAnswerPrompt, RefinePrompt
from llama_index.prompts.default_prompts import DEFAULT_TEXT_QA_PROMPT_TMPL, DEFAULT_REFINE_PROMPT_TMPL
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

from llama_index.llms import OpenAI

from llama_index.embeddings import HuggingFaceEmbedding

from llama_index.vector_stores import VectorStoreQuery

from llama_index.schema import NodeWithScore
from typing import Optional

# load open ai key
os.environ["OPENAI_API_KEY"] = "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"
openai.api_key = os.environ["OPENAI_API_KEY"]

# load embedding model
model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
print("loading embedded model {}", model_name)
embed_model = HuggingFaceEmbedding(model_name=model_name)

# define llm and its params
llm_temperature = 0.3
llm_model = "gpt-3.5-turbo"
llm = OpenAI(temperature=llm_temperature, model=llm_model)

from llama_index.text_splitter import SentenceSplitter

from llama_hub.file.pymu_pdf.base import PyMuPDFReader

# chroma_client = chromadb.EphemeralClient()
# chroma_collection = chroma_client.create_collection("quickstart")

# load data from different sources to vector database collection
def load_data_to_db(filename, url, vector_store):

    from llama_index import download_loader

    ReadabilityWebPageReader = download_loader("ReadabilityWebPageReader")

    # or set proxy server for playwright: loader = ReadabilityWebPageReader(proxy="http://your-proxy-server:port")
    # For some specific web pages, you may need to set "wait_until" to "networkidle". loader = ReadabilityWebPageReader(wait_until="networkidle")
    loader = ReadabilityWebPageReader()

    #documents = loader.load_data(url=args.link)
    documents = loader.load_data(url=url)

    for doc in documents:
        for key in doc.metadata:
            if doc.metadata[key] is None:
                doc.metadata[key] = 0

    loader = PyMuPDFReader()
    file = filename
    documents2 = loader.load(file_path=file)
    documents = documents + documents2

    text_splitter = SentenceSplitter(
        chunk_size=1024,
        separator=" ",
        )
    text_chunks = []

    sentences = []
    window_size = 128
    step_size = 100

    # maintain relationship with source doc index, to help inject doc metadata in (3)
    doc_idxs = []
    for doc_idx, doc in enumerate(documents):
        #cur_text_chunks = text_splitter.split_text(" ".join(doc.text.split()))#text_splitter.split_text(doc.text)
        text_tokens = doc.text.split()
        for i in range(0, len(text_tokens), step_size):
            window = text_tokens[i : i + window_size]
            if len(window) < window_size:
                break
            sentences.append(window)
        paragraphs = [" ".join(s) for s in sentences]
        #text_chunks.extend(paragraphs)
        text_chunks = paragraphs
        doc_idxs.extend([doc_idx] * len(paragraphs))


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

    vector_store.add(nodes)

# prepare query engine for the llm request
def get_query_engine(response_schemas):
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
    
    return query_engine
class VectorDBRetriever(BaseRetriever):
    """Retriever over a ChromaVectorStore vector store."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embed_model: Any,
        query_mode: str = "default",
        similarity_top_k: int = 10,
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

# create vector store and get collection
import chromadb
from llama_index.storage.storage_context import StorageContext
db = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = db.get_or_create_collection(args.collection)
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store) 

if len(chroma_collection.get()['ids']) == 0:
    print("load data to collection")
    load_data_to_db(args.filename, args.url, vector_store)
else:
    print("data already exist in collection")

retriever = VectorDBRetriever(
    vector_store, embed_model, query_mode="default", similarity_top_k=10
)

service_context = ServiceContext.from_defaults(
    chunk_size=1024,
    llm=llm,
    embed_model=embed_model
)

index = VectorStoreIndex.from_vector_store(
    vector_store,
    service_context=service_context,
    storage_context=storage_context,
)

from llama_index.query_engine import RetrieverQueryEngine
query_engine = index.as_query_engine(
    chroma_collection=chroma_collection,
    retriever = retriever
)

device_types = [
    'Motor',
    'Motor Drive',
    'PLC CPU',
    'PLC IO Module System',
    'PLC IO Module',
    'Robot Arm'
]

interface_types = [
    'Ethernet',
    'Ethercat',
    'RS-232',
    'CAN'
]

protocol_types = [
    'Canopen',
    'Profinet',
    'Modbus'
]

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

query_engine = get_query_engine(response_schemas)

query_str = "What is this technical document/manual/specification about? What is company name? What is the product name?"
response_device = query_engine.query(query_str)
print(response_device)

# define output schema
device_type = ResponseSchema(name="device_type",
                             description="What is the device type from the list {} on the following device description {}?".format(device_types,response_device.response))

response_schemas = [device_type]

query_engine = get_query_engine(response_schemas)

query_str = "What is the device type from the list {} based on the following device description {}?".format(device_types, response_device.response)

response = query_engine.query(query_str)
print(response)
####        
####        # print(str(response))
####        # Output:
####        #   ```json
####        #   {
####        #   	"document_description": "This is a technical document/manual/specification about iPOS CANopen Programming.",
####        #   	"company_name": "Technosoft",
####        #   	"product_name": "iMOT233S XM-CAN 12-48V 1.6 Nm Stepper motor CANopen/TMLCAN",
####        #   	"product_description": "The iMOT233S XM-CAN is an intelligent stepper motor with an embedded motion controller, position feedback, RS232 and CAN/CANopen interface. It offers high dynamics and efficiency through field-oriented control (FOC) and operates at a voltage range of 12-48 V with a nominal torque of 1.6 Nm. The motor is designed for simple integration in various drive systems and reduces the amount of wiring required for power supply and communication."
####        #   }
####        #   ```

# define output schema
interfaces = ResponseSchema(name="interfaces",
                             description="What interfaces is this product {} supporting from the list{}?".format(response_device.response,interface_types))
specific_information_interfaces = ResponseSchema(name="specific_information_interfaces",
                                    description="What specific about interfaces that this product supports {}?".format(response_device.response))

response_schemas = [interfaces,
                    specific_information_interfaces]

query_engine = get_query_engine(response_schemas)

query_str = "What interfaces is this product {} supporting from the list{}?".format(response_device.response,interface_types)

response_interfaces = query_engine.query(query_str)
print(response_interfaces)
#   ```json
#   {
#   	"interfaces": "CANopen, RS-232",
#   	"protocols": "TechnoCAN, CiA 301 v4.2 application layer and communication profile, CiA WD 305 v.2.2.130F1 Layer Setting Services, CiA (DSP) 402 v4.0 device profile for drives and motion control, IEC 61800-7-1 Annex A, IEC 61800-7-201, IEC 61800-7-301",
#   	"specific_information": "Technosoft iPOS drives are intelligent drives that can be programmed using the CANopen protocol. They support the TechnoCAN protocol and conform to various communication profiles and device profiles. The drives can be set up and configured using EasySetup or EasyMotion Studio software. They also have the capability to store setup data in EEPROM and retrieve it at power-on. The drives can be used in distributed control systems and can be programmed using Technosoft Motion Language (TML)."
#   }
#   ```

protocols = ResponseSchema(name="protocols",
                                      description="What communication protocols is this product {} supporting from the list{}?".format(response_device.response, protocol_types))
specific_information_protocols = ResponseSchema(name="specific_information_protocols",
                                    description="What specific about communication protocols that this product supports {}?".format(response_device.response))

response_schemas = [protocols,
                    specific_information_protocols]

query_engine = get_query_engine(response_schemas)

query_str = "What protocols is this product {} supporting from the list{}?".format(response_device.response,protocol_types)

response_protocol = query_engine.query(query_str)
print(response_protocol)


#   # define output schema
#   missing_interfaces = ResponseSchema(name="missing_interfaces",
#                                description="Are there missing interfaces that devive {} is supporting and that are missing on this list?".format(response_device.response,response_interfaces.response))
#   response_schemas = [missing_interfaces]
#   
#   query_engine = get_query_engine(response_schemas)
#   
#   query_str = "Are there missing interfaces that devive {} is supporting and that are missing on this list?".format(response_device.response,response_interfaces.response)
#   
#   response_missing_interfaces = query_engine.query(query_str)
#   print(response_missing_interfaces)


#   # define output schema
#   operating_voltage = ResponseSchema(name="operating_voltage",
#                                description="What is the operating supply voltage?")
#   digital_inputs = ResponseSchema(name="digital_inputs",
#                                         description="How many digital inputs is this device {} supporting?".format(response_device))
#   digital_outputs = ResponseSchema(name="digital_outputs",
#                                       description="How many digital outputs is this device {} supporting?".format(response_device))
#   
#   
#   response_schemas = [operating_voltage, 
#                       digital_inputs,
#                       digital_outputs]
#   
#   query_engine = get_query_engine(response_schemas)
#   
#   query_str = "What are the operating voltage for this device? How many digital inputs and digital outputs does this device {} has?".format(response_device)
#   
#   response_ios = query_engine.query(query_str)
#   print(response_ios)
#   #   ```json
#   #   {
#   #   	"operating_voltage": "12 - 48 VDC",
#   #   	"digital_inputs": "5",
#   #   	"digital_outputs": "2"
#   #   }
#   #   ```
