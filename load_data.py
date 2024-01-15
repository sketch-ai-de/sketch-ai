#!/usr/bin/env python3
import argparse
import json
import logging
import sys

from llama_index import ServiceContext, VectorStoreIndex
from document_preprocessor import DocumentPreprocessor
from vector_db_loader import VectorDBLoader
from vector_db_retriever import VectorDBRetriever
import json

from load_models import load_models

parser = argparse.ArgumentParser(
    prog="RagLlamaindex",
    description="Retrieve information from different soures - PDFs and Web-Links",
)

parser.add_argument("-j", "--json_file", default="", type=str)
parser.add_argument("-k", "--similarity_top_k", default=15, type=int)
parser.add_argument("-kr", "--similarity_top_k_rerank", default=15, type=int)
parser.add_argument("-r", "--rerank", action="store_true")
parser.add_argument("-d", "--debug", action="store_true")
parser.add_argument("-i", "--insert_in_sql", action="store_false")
parser.add_argument("-m", "--llm-model", default="gpt3", type=str, help="gpt3 or gpt4")
parser.add_argument(
    "-l", "--llm-service", default="azure", type=str, help="azure or openai"
)
parser.add_argument(
    "--local-llm-address",
    default="localhost",  # host.docker.internal for using docker under macOS
    type=str,
    help="address for local llm",
)
parser.add_argument(
    "--local-llm-port", default="8080", type=str, help="port for local llm"
)

args = parser.parse_args()

logger = logging.getLogger(__name__)
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

llm, embed_model = load_models(args, logger=logger)

service_context = ServiceContext.from_defaults(
    chunk_size=512, llm=llm, embed_model=embed_model, context_window=16385
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

from get_sql_data_to_insert import GetSQLDataToInsert

# from get_sql_data_to_insert import (
#    get_robot_arm_data,
#    get_robot_arm_embed_data,
#    get_company_data,
#    get_software_data,
#    get_software_embed_data,
#    get_plc_data,
#    get_plc_embed_data,
# )
from sql_handler_robot_arm import SQLHandlerRobotArm
from sql_handler_company import SQLHandlerCompany
from sql_handler_robot_arm_embed import SQLHandlerRobotArmEmbed
from sql_handler_software import SQLHandlerSoftware
from sql_handler_software_embed import SQLHandlerSoftwareEmbed
from sql_handler_plc import SQLHandlerPLC
from sql_handler_plc_embed import SQLHandlerPLCEmbed
from sketch_ai_sql_types import (
    sql_fields_company,
    sql_fields_robot_arm,
    sql_fields_robot_arm_embed,
    sql_fields_software,
    sql_fields_software_embed,
    sql_fields_plc,
    sql_fields_plc_embed,
)

sql_handler_company = SQLHandlerCompany(
    table_name="company", sql_fields=sql_fields_company, logger=logger
)
sql_handler_company.create_base()
sql_handler_company.create_table()

sql_handler_robot_arm = SQLHandlerRobotArm(
    table_name="robot_arm", sql_fields=sql_fields_robot_arm, logger=logger
)
sql_handler_robot_arm.create_base()
sql_handler_robot_arm.create_table()

sql_handler_robot_arm_embed = SQLHandlerRobotArmEmbed(
    table_name="robot_arm_embed", sql_fields=sql_fields_robot_arm_embed, logger=logger
)
sql_handler_robot_arm_embed.create_base()
sql_handler_robot_arm_embed.create_table()

sql_handler_software = SQLHandlerSoftware(
    table_name="software", sql_fields=sql_fields_software, logger=logger
)
sql_handler_software.create_base()
sql_handler_software.create_table()

sql_handler_software_embed = SQLHandlerSoftwareEmbed(
    table_name="software_embed", sql_fields=sql_fields_software_embed, logger=logger
)
sql_handler_software_embed.create_base()
sql_handler_software_embed.create_table()

sql_handler_plc = SQLHandlerPLC(
    table_name="plc", sql_fields=sql_fields_plc, logger=logger
)
sql_handler_plc.create_base()
sql_handler_plc.create_table()

sql_handler_plc_embed = SQLHandlerPLCEmbed(
    table_name="plc_embed", sql_fields=sql_fields_plc_embed, logger=logger
)
sql_handler_plc_embed.create_base()
sql_handler_plc_embed.create_table()

# async def get_data():
sql_data_to_insert_dict = {}
sql_data_embed_to_insert_list = []
nodes = None
id = None
sql_handler = None

if data["document_type"] == "ROBOT_ARM":
    logger.info("Getting robot_arm id")
    sql_handler = sql_handler_robot_arm
    sql_handler_embed = sql_handler_robot_arm_embed
    fields_dict = sql_fields_robot_arm
    fields_dict_embed = sql_fields_robot_arm_embed
    id = sql_handler.get_id(data["product_name"])
if data["document_type"] == "SOFTWARE":
    logger.info("Getting software id")
    sql_handler = sql_handler_software
    sql_handler_embed = sql_handler_software_embed
    fields_dict = sql_fields_software
    fields_dict_embed = sql_fields_software_embed
if data["document_type"] == "PLC":
    logger.info("Getting plc id")
    sql_handler = sql_handler_plc
    sql_handler_embed = sql_handler_plc_embed
    fields_dict = sql_fields_plc
    fields_dict_embed = sql_fields_plc_embed

id = sql_handler.get_id(data["product_name"])
if id:
    logger.info("Product name already exists in SQL table")
    exit(1)

logger.info("Getting company id")
company_id = sql_handler_company.get_id(data["company_name"])


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
    rerank=args.rerank,
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

sql_data_getter = GetSQLDataToInsert(
    DBLoader=DBLoader,
    logger=logger,
    retriever=retriever,
    product_name=data["product_name"],
    fields_dict=fields_dict,
    fields_dict_embed=fields_dict_embed,
    fields_dict_company=sql_fields_company,
)

if id is None or id == []:
    logger.info("Getting data")
    sql_data_to_insert_dict = sql_data_getter.get_data()
nodes = DBLoader.get_all_nodes()
sql_data_embed_to_insert_list = sql_data_getter.get_embed_data(id, nodes)

if company_id is None or company_id == []:
    response_company_dict = sql_data_getter.get_company_data(data)

# Inserting into SQL
if args.insert_in_sql:
    logger.info("Inserting into SQL")
    if company_id is None or company_id == []:
        logger.info(
            "Inserting into tables {}".format(
                sql_handler_company._table_name,
            )
        )
        sql_handler_company.insert_into_sql(response_company_dict)
    logger.info("Getting company id")
    company_id = sql_handler_company.get_id(data["company_name"])
    sql_data_to_insert_dict["company_id"] = company_id
    if id is None or id == []:
        logger.info(
            "Inserting into tables {} and {}".format(
                sql_handler._table_name,
                sql_handler_embed._table_name,
            )
        )
        sql_handler.insert_into_sql(sql_data_to_insert_dict)
        id = sql_handler.get_id(data["product_name"])
        sql_data_embed_to_insert_list = sql_data_getter.get_embed_data(id, nodes)
        sql_handler_embed.insert_into_sql(sql_data_embed_to_insert_list)
    else:
        logger.info(
            "Inserting into table {}".format(
                sql_handler._table_name,
            )
        )
        sql_handler_embed.insert_into_sql(sql_data_embed_to_insert_list)
