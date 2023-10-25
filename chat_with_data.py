# examples:
#   python3 chat_with_data.py -fs "docs/franka/research3/franka-research3.pdf" -u="https://store.clearpathrobotics.com/products/franka-research-3" -c="franka-research3"
#   python3 chat_with_data.py -fs "docs/ur/ur5e/ur5e-fact-sheet.pdf" -u="https://www.universal-robots.com/products/ur5-robot/" -c="ur5e_user_manual_en_us"
#   python3 chat_with_data.py -fs "docs/agile/diana7/diana7.pdf" -u="" -c="diana7"

import argparse
import os
import re
import json
import logging
import sys

from dotenv import load_dotenv
from langchain.output_parsers import ResponseSchema
from llama_index import ServiceContext, VectorStoreIndex
from llama_index.embeddings import HuggingFaceEmbedding
from llama_index.llms import OpenAI
from vector_db_loader import VectorDBLoader
from vector_db_retriever import VectorDBRetriever
from document_preprocessor import DocumentPreprocessor

import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

parser = argparse.ArgumentParser(
    prog="RagLlamaindex",
    description="Retrieve information from different soures - PDFs and Web-Links",
)

parser.add_argument("-fs", "--filenames", nargs="+", default=[], type=str)
parser.add_argument("-u", "--url", type=str)
parser.add_argument("-c", "--collection", type=str)
parser.add_argument("-k", "--similarity_top_k", default=10, type=int)
parser.add_argument("-d", "--debug", action="store_true")

args = parser.parse_args()

device_types = [
    "Motor",
    "Motor Drive",
    "PLC CPU",
    "PLC IO Module System",
    "PLC IO Module",
    "Robot Arm",
    "Microcontroller Board",
    "Inductive Sensor",
    "Computer",
]

interface_types = [
    "Ethernet",
    "EtherCAT",
    "Recommended Standard RS-232",
    "Recommended Standard RS-485",
    "CAN Bus",
    "Bluetooth",
    "LTE",
    "USB",
    "Wireless LAN / WLAN",
]

protocol_types = ["CANopen", "Profinet", "Modbus", "EtherNet/IP", "Profibus", "IO-Link"]

motor_types = ["Stepper motor", "DC motor", "Brushless DC motor / BLDC", "Servomotor"]

serial_connection_types = ["I2C / IIC", "1-Wire", "SPI", "UART", "RS-232"]

logger = logging.getLogger("DefaultLogger")
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
streamHandler.setFormatter(formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(streamHandler)

logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

embed_model_name = "sentence-transformers/all-MiniLM-L12-v2"

from llama_index.embeddings import OpenAIEmbedding

logger.info(
    "--------------------- Loading embedded model {} \n".format(embed_model_name)
)


embed_model = HuggingFaceEmbedding(model_name=embed_model_name)

# define llm and its params
llm_temperature = 0.1
llm_model = "gpt-3.5-turbo"
# llm_model = "gpt-3.5-turbo-instruct" # not good - responces are too unprecise
# llm_model = "gpt-4" # good responces but way too expencive
logger.info("--------------------- Loading llm model {} \n".format(llm_model))
llm = OpenAI(temperature=llm_temperature, model=llm_model)

service_context = ServiceContext.from_defaults(
    chunk_size=1024, llm=llm, embed_model=embed_model
)

Docs = DocumentPreprocessor(
    logger=logger,
    url=args.url,
    pdf_filenames=args.filenames,
    collection_name=args.collection,
)

DBLoader = VectorDBLoader(
    llm=llm,
    logger=logger,
    service_context=service_context,
    collection_dict=Docs.create_collection_dict(),
    Docs=Docs,
    embed_model=embed_model,
)

vector_stores, storage_context, chroma_collection = DBLoader.get_vector_stores()
vector_store = vector_stores[0]

retriever = VectorDBRetriever(
    vector_store,  # default vector store
    vector_stores,
    embed_model,
    query_mode="default",
    similarity_top_k=int(args.similarity_top_k),
    logger=logger,
)

index = VectorStoreIndex.from_vector_store(
    vector_store,
    service_context=service_context,
    storage_context=storage_context,
)


query_engine = index.as_query_engine(
    chroma_collection=chroma_collection, retriever=retriever
)


def make_llm_request(query_engine, query_str):
    response_dict = []
    response = query_engine.query(query_str)
    print("response:::::::::::::::::::::\n", response)
    # response_dict = json.loads(
    #    re.sub(r"json", "", re.sub(r"```", "", response.response))
    # )

    if logger.getEffectiveLevel() == logging.DEBUG:
        for idx, node in enumerate(response.source_nodes):
            print(
                "######################################### \
                  Node {} with text \n: {}".format(
                    idx, node.text
                )
            )
            print("######################################### \n")

    return response, response_dict


################################################# ask product details ################################################


# define output schema
document_description = ResponseSchema(
    name="document_description", description="What is this technical document about?"
)
company_name = ResponseSchema(name="company_name", description="What is company name?")
product_name = ResponseSchema(
    name="product_name", description="What is the detailed product name?"
)
product_description = ResponseSchema(
    name="product_description",
    description="Summarize a detailed description of the product.",
)

response_schemas = [
    document_description,
    company_name,
    product_name,
    product_description,
]

query_engine = DBLoader.get_query_engine(response_schemas, retriever)
query_str = "What is this technical document/manual/specification about? What is company name? What is the product name?"
response_device, response_device_dict = make_llm_request(query_engine, query_str)
response_device_dict = json.loads(
    re.sub(r"json", "", re.sub(r"```", "", response_device.response))
)


while True:
    query_str = input("Enter a question about document:\n")
    answer = ResponseSchema(
        name="answer",
        description="Give the answer to question: \n Question: "
        + query_str
        + "\n Answer:",
    )
    response_schemas = [answer]
    query_engine = DBLoader.get_query_engine(response_schemas, retriever)
    response_query, response_query_dict = make_llm_request(query_engine, query_str)

#   ################################################# ask device type ################################################
#
#   # define output schema
#   device_type = ResponseSchema(
#       name="device_type",
#       description="""What is the device type from the list below on the following device description?\n
#             List:{device_types} \n
#             Description: {product_description}.""".format(
#           device_types=device_types,
#           product_description=response_device_dict["product_description"],
#       ),
#   )
#
#   response_schemas = [device_type]
#   query_engine = DBLoader.get_query_engine(response_schemas, retriever)
#   query_str = """What is the device type from the list below on the following device description?\n
#             List:{device_types} \n
#             Description: {product_description}.""".format(
#       device_types=device_types,
#       product_description=response_device_dict["product_description"],
#   )
#   response_device_type, response_device_type_dict = make_llm_request(
#       query_engine, query_str
#   )
#   response_device_type_dict = json.loads(
#       re.sub(r"json", "", re.sub(r"```", "", response_device_type.response))
#   )
#
#   ################################################# ask interfaces ################################################
#
#   # define output schema
#   interfaces = ResponseSchema(
#       name="interfaces",
#       description="""What communication interfaces is this {device} supporting from the given list of available interfaces.\n
#           List of interfaces: {interfaces_types}""".format(
#           device=response_device_type_dict["device_type"],
#           interfaces_types=interface_types,
#       ),
#       type="list",
#   )
#   specific_information_interfaces = ResponseSchema(
#       name="specific_information_interfaces",
#       description="What specific about communication interfaces that this {device} supports?".format(
#           device=response_device_type_dict["device_type"]
#       ),
#       type="string",
#   )
#
#   response_schemas = [interfaces, specific_information_interfaces]
#
#   query_engine = DBLoader.get_query_engine(response_schemas, retriever)
#   query_str = """What communication interfaces is this {device} supporting from the given list.\n
#           List: {interfaces_types}""".format(
#       device=response_device_type_dict["device_type"], interfaces_types=interface_types
#   )
#   response_interfaces, response_interfaces_dict = make_llm_request(
#       query_engine, query_str
#   )
#
#   ################################################# ask protocols ################################################
#
#   protocols = ResponseSchema(
#       name="protocols",
#       description="""What communication protocols is this product {device} supporting from the given list of available protocols \n
#           List of protocols: {protocol_types}""".format(
#           device=response_device_type_dict["device_type"], protocol_types=protocol_types
#       ),
#       type="list",
#   )
#   specific_information_protocols = ResponseSchema(
#       name="specific_information_protocols",
#       description="What specific about communication protocols that this device supports ?",
#   )
#
#   response_schemas = [protocols, specific_information_protocols]
#
#   query_engine = DBLoader.get_query_engine(response_schemas, retriever)
#   query_str = """What communication protocols is this product {device} supporting from the given list of available protocols \n
#           List of protocols: {protocol_types}""".format(
#       device=response_device_type_dict["device_type"], protocol_types=protocol_types
#   )
#   response_protocol, response_protocol_dict = make_llm_request(query_engine, query_str)
#
#   ################################################# ask serial protocols ################################################
#
#   serial_communication = ResponseSchema(
#       name="serial_connection",
#       description="""What serial communication protocols is this product {device} supporting from the given list of available protocols \n
#           List of protocols: {serial_connection_types}""".format(
#           device=response_device_type_dict["device_type"],
#           serial_connection_types=serial_connection_types,
#       ),
#       type="list",
#   )
#   specific_information_serial_communication = ResponseSchema(
#       name="specific_information_protocols",
#       description="What specific about serial communication protocols that this product supports?",
#   )
#   response_schemas = [
#       serial_communication,
#       specific_information_serial_communication,
#   ]
#
#   query_engine = DBLoader.get_query_engine(response_schemas, retriever)
#
#   query_str = """What serial communication protocols is this product {device} supporting from the given list of available protocols \n
#           List of protocols: {serial_connection_types}""".format(
#       device=response_device_type_dict["device_type"],
#       serial_connection_types=serial_connection_types,
#   )
#   response_serial_communication, response_serial_communication_dict = make_llm_request(
#       query_engine, query_str
#   )
#
#   ################################################# ask operating voltage ################################################
#
#   # define output schema
#   operating_voltage_min = ResponseSchema(
#       name="operating_voltage_min",
#       description="What is the minimum operating rated supply voltage in volts [V] for the device {}?".format(
#           response_device_dict["product_name"]
#       ),
#       type="int",
#   )
#
#   operating_voltage_max = ResponseSchema(
#       name="operating_voltage_max",
#       description="What is the maximum operating rated supply voltage in volts [V] for the device {}?".format(
#           response_device_dict["product_name"]
#       ),
#       type="int",
#   )
#
#   response_schemas = [operating_voltage_min, operating_voltage_max]
#
#   query_engine = DBLoader.get_query_engine(response_schemas, retriever)
#
#   query_str = "What are the minimum and maximum operating rated supply voltage?"
#
#   response_voltage, response_voltage_dict = (
#       response_protocol,
#       response_protocol_dict,
#   ) = make_llm_request(query_engine, query_str)
#
#   ################################################# ask robot specs ################################################
#
#
#   def ask_robot_specs(retriever):
#       payload = ResponseSchema(
#           name="payload",
#           description="What is the {} maximum payload in kilograms [kg]?".format(
#               response_device_type_dict["device_type"]
#           ),
#           type="int",
#       )
#       response_schemas = [payload]
#
#       query_engine = DBLoader.get_query_engine(response_schemas, retriever)
#
#       query_str = "What is the {} maximum payload in kilograms [kg]?".format(
#           response_device_type_dict["device_type"]
#       )
#
#       response_voltage, response_voltage_dict = make_llm_request(query_engine, query_str)
#
#
#   def ask_robot_specs2(retriever):
#       reach = ResponseSchema(
#           name="reach",
#           description="What is the {} maximum reach in millimeters [mm]?".format(
#               response_device_type_dict["device_type"]
#           ),
#           type="int",
#       )
#
#       response_schemas = [reach]
#
#       query_engine = DBLoader.get_query_engine(response_schemas, retriever)
#
#       query_str = "What is the {} maximum reach in millimeters [mm]?".format(
#           response_device_type_dict["device_type"]
#       )
#
#       response_voltage, response_voltage_dict = make_llm_request(query_engine, query_str)
#
#
#   def ask_robot_specs3(retriever):
#       workspace_coverage = ResponseSchema(
#           name="workspace_coverage",
#           description="What is the {} maximum reach in percentage [%]?".format(
#               response_device_type_dict["device_type"]
#           ),
#           type="int",
#       )
#
#       response_schemas = [workspace_coverage]
#
#       query_engine = DBLoader.get_query_engine(response_schemas, retriever)
#
#       query_str = "What is the {} maximum reach in percentage [%]?".format(
#           response_device_type_dict["device_type"]
#       )
#
#       response_voltage, response_voltage_dict = make_llm_request(query_engine, query_str)
#
#
#   def ask_robot_specs4(retriever):
#       weight = ResponseSchema(
#           name="weight",
#           description="What is the device {} weight in kilograms [kg]? How much it weighs in [kg]?".format(
#               response_device_type_dict["device_type"]
#           ),
#           type="int",
#       )
#
#       response_schemas = [weight]
#
#       query_engine = DBLoader.get_query_engine(response_schemas, retriever)
#
#       query_str = "What are the device weight in [kg]? How much it weighs in [kg]?"
#
#       response_voltage, response_voltage_dict = make_llm_request(query_engine, query_str)
#
#
#   def ask_robot_specs5(retriever):
#       number_of_axes = ResponseSchema(
#           name="number_of_axes",
#           description="What number of axes does this device {} has?".format(
#               response_device_type_dict["device_type"]
#           ),
#           type="int",
#       )
#
#       response_schemas = [number_of_axes]
#
#       query_engine = DBLoader.get_query_engine(response_schemas, retriever)
#
#       query_str = "What number of axes does this device has?"
#
#       response_voltage, response_voltage_dict = make_llm_request(query_engine, query_str)
#
#
#   if response_device_type_dict["device_type"] == "Robot Arm":
#       ask_robot_specs(retriever)
#       ask_robot_specs2(retriever)
#       ask_robot_specs3(retriever)
#       ask_robot_specs4(retriever)
#       ask_robot_specs5(retriever)
#
