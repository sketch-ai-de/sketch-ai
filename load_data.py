#!/usr/bin/env python3

# ToDo (Dimi): extend metadata with filename, and doc_id with filename

import argparse
import json
import logging
import os
import re
import sys

import openai
from dotenv import load_dotenv
from langchain.output_parsers import ResponseSchema
from llama_index import ServiceContext, VectorStoreIndex
from llama_index.embeddings import OpenAIEmbedding
from llama_index.llms import OpenAI

from document_preprocessor import DocumentPreprocessor
from vector_db_loader import VectorDBLoader
from vector_db_retriever import VectorDBRetriever

import json

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

parser = argparse.ArgumentParser(
    prog="RagLlamaindex",
    description="Retrieve information from different soures - PDFs and Web-Links",
)

parser.add_argument("-j", "--json_file", default="", type=str)
parser.add_argument("-k", "--similarity_top_k", default=10, type=int)
parser.add_argument("-kr", "--similarity_top_k_rerank", default=15, type=int)
parser.add_argument("-d", "--debug", action="store_true")
parser.add_argument("-i", "--insert_in_sql", action="store_true")

args = parser.parse_args()

logger = logging.getLogger(__name__)
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

# embed_model_name = "sentence-transformers/all-MiniLM-L12-v2"

# embed_model_name = "thenlper/gte-base"

# logger.info(#    "--------------------- Loading embedded model {} \n".format(embed_model_name)#)

embed_model = OpenAIEmbedding()
service_context = ServiceContext.from_defaults(embed_model=embed_model)

# embed_model = HuggingFaceEmbedding(model_name=embed_model_name)

# define llm and its params
llm_temperature = 0.3
# llm_model = "gpt-4-1106-preview"
llm_model = "gpt-3.5-turbo"
# llm_model = "gpt-3.5-turbo-instruct" # not good - responces are too unprecise
# llm_model = "gpt-4"  # good responces but way too expencive
logger.info("--------------------- Loading llm model {} \n".format(llm_model))
llm = OpenAI(temperature=llm_temperature, model=llm_model)

service_context = ServiceContext.from_defaults(
    chunk_size=1024, llm=llm, embed_model=embed_model
)

from metadata import Metadata
from sketch_ai_types import document_type_robot_arm_dict

f = open(args.json_file)
data = json.load(f)

document_metadata = Metadata(
    company_name=data["company_name"],
    product_name=data["product_name"],
    document_type=document_type_robot_arm_dict[data["document_type"]],
)

Docs = DocumentPreprocessor(
    web_urls=data["web_urls"],
    pdf_urls=data["pdf_urls"],
    metadata=document_metadata,
    logger=logger,
    llm=llm,
)


if data["load_urls"]:
    Docs.load_urls_from_path(data["web_urls"])
    Docs.process_urls()

if data["load_pdfs"]:
    Docs.load_pdfs()
    Docs.process_sherpa_pdf()
    Docs.process_normal_pdf()
    Docs.process_sherpa_table()


# Creating a VectorDBLoader object to load the vectors into the database
DBLoader = VectorDBLoader(
    llm=llm,
    logger=logger,
    service_context=service_context,
    collection_dict=Docs.get_collections(),
    embed_model=embed_model,
    verbose=True,
)
# Getting the vector stores, storage context and chroma collection from the VectorDBLoader object
vector_stores, storage_context = DBLoader.get_vector_stores()
if len(vector_stores) == 0:
    logger.error("No vector store exists.")
    exit(1)
# Getting the first vector store from the vector stores
vector_store = vector_stores[0]
# Creating a VectorDBRetriever object to retrieve the vectors from the database
retriever = VectorDBRetriever(
    vector_store,  # default vector store
    vector_stores,
    embed_model,
    query_mode="default",
    similarity_top_k=int(args.similarity_top_k),
    similarity_top_k_rerank=int(args.similarity_top_k_rerank),
    logger=logger,
    service_context=service_context,
)
# Creating a VectorStoreIndex object from the vector store
index = VectorStoreIndex.from_vector_store(
    vector_store, service_context=service_context, storage_context=storage_context
)
# Creating a query engine from the VectorStoreIndex object
# query_engine = index.as_query_engine(
#    chroma_collection=chroma_collection, retriever=retriever
# )
query_engine = index.as_query_engine(retriever=retriever)

from get_robot_arm_data import get_robot_arm_data
from sql_handler_robot_arm import SQLHandlerRobotArm


sql_handler_robot_arm = SQLHandlerRobotArm()
sql_handler_robot_arm.create_base()
sql_handler_robot_arm.create_robot_table()

logger.info("Getting arm id")
robot_arm_id = sql_handler_robot_arm.get_robot_arm_id(data["product_name"])

if robot_arm_id is None or robot_arm_id == []:
    logger.info("Getting robot arm data")
    response_device_dict = get_robot_arm_data(
        query_engine, retriever, DBLoader, logger, data["product_name"]
    )

nodes = DBLoader.get_all_nodes()

from sketch_ai_types import DeviceType

if args.insert_in_sql:
    logger.info("Inserting into SQL")
    if robot_arm_id is None or robot_arm_id == []:
        if response_device_dict["device_type_name"] == DeviceType.ROBOT_ARM.name:
            sql_handler_robot_arm.insert_device_into_sql(response_device_dict)
            sql_handler_robot_arm.insert_nodes_into_sql(nodes, data["product_name"])
    else:
        sql_handler_robot_arm.insert_nodes_into_sql(nodes, data["product_name"])
