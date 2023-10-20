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

parser.add_argument('-fs', '--filenames', nargs='+', default=[])
parser.add_argument('-u', '--url')      # option that takes a value
parser.add_argument('-c', '--collection')      # option that takes a value

args = parser.parse_args()

import logging
import sys
logger = logging.getLogger("DefaultLogger")
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
streamHandler.setFormatter(formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(streamHandler)

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
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# load embedding model
#model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
embed_model_name = "sentence-transformers/all-MiniLM-L12-v2"
#model_name = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"

logger.info("--------------------- Loading embedded model {} \n".format(embed_model_name))
embed_model = HuggingFaceEmbedding(model_name=embed_model_name)

# define llm and its params
llm_temperature = 0.1
llm_model = "gpt-3.5-turbo"
#llm_model = "gpt-4"
logger.info("--------------------- Loading llm model {} \n".format(llm_model))
llm = OpenAI(temperature=llm_temperature, model=llm_model)

from llama_index.text_splitter import SentenceSplitter

from llama_hub.file.pymu_pdf.base import PyMuPDFReader

# chroma_client = chromadb.EphemeralClient()
# chroma_collection = chroma_client.create_collection("quickstart")

def load_documents(filenames, url):    
    ''' load documents from different sources'''

    #load from url
    from llama_index import download_loader
    ReadabilityWebPageReader = download_loader("ReadabilityWebPageReader")
    # or set proxy server for playwright: loader = ReadabilityWebPageReader(proxy="http://your-proxy-server:port")
    # For some specific web pages, you may need to set "wait_until" to "networkidle". loader = ReadabilityWebPageReader(wait_until="networkidle")
    loader_url = ReadabilityWebPageReader()
    documents = []
    if url:
        logger.info("--------------------- Load urls \n")
        documents = loader_url.load_data(url=url)

    # load from PDFs
    loader_pdf = PyMuPDFReader()
    for file in filenames:
        logger.info("--------------------- Load document {} \n".format(file))
        doc = loader_pdf.load(file_path=file)
        documents = documents + doc
    
    # remove fields having value None -> cause error
    for doc in documents:
        for key in doc.metadata:
            if doc.metadata[key] is None:
                doc.metadata[key] = 0

    return documents

def load_documents_to_db(filenames, url, vector_store):
    '''load data to vector database collection'''

    import re
    documents = load_documents(filenames, url)

    text_splitter = SentenceSplitter(
        chunk_size=1024,
        separator=" ",
        )
    text_chunks = []

    # old with k=10 was not good for different devices
    sentences = []
    window_size = 128
    step_size = 20

    # new - gives much better results with k=20
    sentences = []
    window_size = 96
    step_size = 76

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
        for i, p in enumerate(paragraphs):
            paragraphs[i] = re.sub(r'\.+', ".", p) # remove dots
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

# create vector store and get collection
import chromadb
from llama_index.storage.storage_context import StorageContext
db = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = db.get_or_create_collection(args.collection)
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store) 

if len(chroma_collection.get()['ids']) == 0:
    logger.info("--------------------- Load data to collection  \n")
    load_documents_to_db(args.filenames, args.url, vector_store)
else:
    logger.info("--------------------- Data already exist in collection  \n")

retriever = VectorDBRetriever(
    vector_store, embed_model, query_mode="default", similarity_top_k=20
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
    'Robot Arm',
    'Microcontroller Board'
]

interface_types = [
    'Ethernet',
    'Ethercat',
    'RS-232',
    'CAN',
    'Bluetooth',
    'LTE',
    'USB',
    'Wireless LAN / WLAN'
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

#    gpt3.5-turbo:
#   ```json
#   {
#   	"document_description": "This technical document is a manual for the iPOS 233 CANopen drive.",
#   	"company_name": "Technosoft",
#   	"product_name": "iPOS 233 CANopen",
#   	"product_description": "The iPOS 233 CANopen is a drive/motor system that offers various features such as integrated 
#           absolute position sensor, over-current and over-temperature protection, data acquisition capabilities, and multiple h/w addresses."
#   }
#   ```
#   gpt4 output:
#     ```json
#     {
#     	"document_description": "This technical document appears to be a manual or specification for a drive or motor controller, detailing 
#           its various modes of operation, input and output specifications, and various other technical details.",
#     	"company_name": "Technosoft",
#     	"product_name": "iPOS 233 CANopen",
#     	"product_description": "The iPOS 233 CANopen is a drive or motor controller. It features digital and analogue I/Os, 
#           integrated absolute position sensor, protections such as over-current and over-temperature, and has hardware addresses 
#           selectable by hex switch. It also has SRAM for data acquisition and E2ROM for motion programs and data storage."
#     }
#      ```

# define output schema
device_type = ResponseSchema(name="device_type",
                             description="What is the device type from the list {} on the following device description {}?".format(device_types,response_device.response))

response_schemas = [device_type]

query_engine = get_query_engine(response_schemas)

query_str = "What is the device type from the list {} based on the following device description {}?".format(device_types, response_device.response)

response = query_engine.query(query_str)
print(response)

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
#    gpt3.5-turbo:
#   ```json
#   {
#   	"interfaces": ["CAN"],
#   	"specific_information_interfaces": "The iPOS 233 CANopen drive supports the CAN interface. 
#           It also has digital inputs (IN0, IN1, IN2/LSP, IN3/LSN, Enable) and digital outputs (OUT0, OUT1) for general-purpose use."
#   }
#   ```
#   
#   gpt4 output
#   ```json
#   {
#   	"interfaces": "RS-232, CAN",
#   	"specific_information_interfaces": "The iPOS 233 CANopen supports RS-232 and CAN interfaces. 
#           The RS-232 interface has a software selectable bit rate between 9600 and 115200 Baud. 
#           The CAN interface complies with ISO11898 and CiA 402v3.0, with a software selectable bit rate between 125 and 1000 Kbps."
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

#   gpt3.5-turbo: 
#   ```json
#   {
#   	"protocols": "Canopen",
#   	"specific_information_protocols": "The iPOS 233 CANopen drive supports the CANopen protocol for communication."
#   }
#   ```
#   
#   gpt4 output:
#   ```json
#   {
#   	"protocols": "Canopen",
#   	"specific_information_protocols": "The iPOS 233 CANopen supports the TMLCAN and CANopen (CiA 402 v3.0) protocols, which are selectable by a hardware pin. It does not support Profinet or Modbus protocols."
#   }
#   ```


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


# define output schema
operating_voltage_min = ResponseSchema(name="operating_voltage_min",
                             description="What is the recommended operating supply voltage minimum?")

operating_voltage_max = ResponseSchema(name="operating_voltage_max",
                             description="What is the recommended operating supply voltage maximum?")

response_schemas = [operating_voltage_min,
                    operating_voltage_max
                    ]

query_engine = get_query_engine(response_schemas)

query_str = "What are the minimum and maximum operating supply voltage for this device?".format(response_device.response)

response_voltage = query_engine.query(query_str)
print(response_voltage)
#   ```json
#   {
#   	"operating_voltage": "12 - 48 VDC",
#   	"digital_inputs": "5",
#   	"digital_outputs": "2"
#   }
#   ```
