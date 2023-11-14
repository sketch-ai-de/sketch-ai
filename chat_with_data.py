#!/usr/bin/env python3

# ToDo(dimi)
# 1. improve prompting templates for document preprocessing

# ToDo(dimi)
# 1. improve prompting templates for document preprocessing

import argparse
import json
import logging
import os
import re
import sys
from enum import Enum

import openai
from dotenv import load_dotenv
from langchain.output_parsers import ResponseSchema
from llama_index import ServiceContext, VectorStoreIndex
from llama_index.embeddings import HuggingFaceEmbedding, OpenAIEmbedding
from llama_index.llms import OpenAI

from document_preprocessor import DocumentPreprocessor
from vector_db_loader import VectorDBLoader
from vector_db_retriever import VectorDBRetriever

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
parser.add_argument("-i", "--insert_in_sql", action="store_true")
parser.add_argument("-g", "--gradio_on", action="store_true")
parser.add_argument("-p", "--product_name", type=str)

args = parser.parse_args()


class DeviceType(Enum):
    MOTOR = 1
    MOTOR_DRIVE = 2
    PLC_CPU = 3
    PLC_IO_MODULE_SYSTEM = 4
    PLC_IO_MODULE = 5
    ROBOT_ARM = 6
    MICROCONTROLLER_BOARD = 7
    INDUCTIVE_SENSOR = 8
    COMPUTER = 9
    ROBOT_SERVO_DRIVE_JOINT = 10


device_type_dict = [el.name for el in DeviceType]

logger = logging.getLogger(__name__)
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

# embed_model_name = "sentence-transformers/all-MiniLM-L12-v2"

embed_model_name = "thenlper/gte-base"


logger.info(
    "--------------------- Loading embedded model {} \n".format(embed_model_name)
)

embed_model = OpenAIEmbedding()
service_context = ServiceContext.from_defaults(embed_model=embed_model)

# embed_model = HuggingFaceEmbedding(model_name=embed_model_name)

# define llm and its params
llm_temperature = 0.3
llm_model = "gpt-4-1106-preview"
# llm_model = "gpt-3.5-turbo"
# llm_model = "gpt-3.5-turbo-instruct" # not good - responces are too unprecise
llm_model = "gpt-4"  # good responces but way too expencive
logger.info("--------------------- Loading llm model {} \n".format(llm_model))
llm = OpenAI(temperature=llm_temperature, model=llm_model)

service_context = ServiceContext.from_defaults(
    chunk_size=1024, llm=llm, embed_model=embed_model
)

if not args.gradio_on:
    # Creating a DocumentPreprocessor object to preprocess the documents
    Docs = DocumentPreprocessor(
        logger=logger,
        url=args.url,
        pdf_filenames=args.filenames,
        collection_name=args.collection,
    )

    # Creating a VectorDBLoader object to load the vectors into the database
    DBLoader = VectorDBLoader(
        llm=llm,
        logger=logger,
        service_context=service_context,
        collection_dict=Docs.create_collection_dict(),
        Docs=Docs,
        embed_model=embed_model,
        verbose=True,
    )

    # Getting the vector stores, storage context and chroma collection from the VectorDBLoader object
    vector_stores, storage_context, chroma_collection = DBLoader.get_vector_stores(
        load_always=args.insert_in_sql
    )

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
        logger=logger,
    )

    # Creating a VectorStoreIndex object from the vector store
    index = VectorStoreIndex.from_vector_store(
        vector_store, service_context=service_context, storage_context=storage_context
    )

    # Creating a query engine from the VectorStoreIndex object
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
                    "#########################################                      "
                    " Node {} with text \n: {}".format(idx, node.text)
                )
                print("######################################### \n")

        return response, response_dict

    ################################################# ask product details ################################################

    # define output schema
    document_description = ResponseSchema(
        name="document_description",
        description="What is this technical document about?",
    )
    company_name = ResponseSchema(
        name="company_name", description="What is company name?"
    )
    product_name = ResponseSchema(
        name="product_name", description="What is the detailed product name?"
    )
    product_description = ResponseSchema(
        name="product_description",
        description=(
            "Summarize a description of the product without too much technical"
            " characteristics. Put detailed company name and product name"
            " in the description"
        ),
    )

    response_schemas = [
        document_description,
        company_name,
        product_name,
        product_description,
    ]

    query_engine = DBLoader.get_query_engine(response_schemas, retriever)
    query_str = (
        "What is this technical document/manual/specification about? What is company"
        " name? What is the product name? Answer always in json format."
    )
    response_device, response_device_dict = make_llm_request(query_engine, query_str)
    response_device_dict = json.loads(
        re.sub(r"json", "", re.sub(r"```", "", response_device.response))
    )

    if args.product_name:
        response_device_dict["product_name"] = args.product_name

    ################################################# ask device type ################################################
    # define output schema
    device_type = ResponseSchema(
        name="device_type",
        description="""What is the device type from the list below on the following device description?\n
              List:{device_types} \n
              Description: {product_description}.""".format(
            device_types=device_type_dict,
            product_description=response_device_dict["product_description"],
        ),
    )
    response_schemas = [device_type]
    query_engine = DBLoader.get_query_engine(response_schemas, retriever)
    query_str = """What is the device type from the list below on the following device description? Answer always in json format.\n
              List:{device_types} \n
              Description: {product_description}.""".format(
        device_types=device_type_dict,
        product_description=response_device_dict["product_description"],
    )
    response_device_type, response_device_type_dict = make_llm_request(
        query_engine, query_str
    )
    response_device_type_dict = json.loads(
        re.sub(r"json", "", re.sub(r"```", "", response_device_type.response))
    )

    response_device_dict["device_type_name"] = response_device_type_dict["device_type"]
    response_device_dict["device_type_id"] = DeviceType[
        response_device_type_dict["device_type"]
    ].value

    ################################################# ask technical details ################################################

    # define output schema
    if response_device_type_dict["device_type"] == DeviceType.ROBOT_ARM.name:
        payload = ResponseSchema(
            name="payload",
            description="What is payload in [kg] of the robot arm {}?".format(
                response_device_dict["product_name"]
            ),
            type="float",
        )
        reach = ResponseSchema(
            name="reach",
            description="What is reach of the robot arm {} in [mm]?".format(
                response_device_dict["product_name"]
            ),
            type="float",
        )
        weight = ResponseSchema(
            name="weight",
            description=(
                "What is weight of the robot arm {} in [kg]? Consider only arm weight"
                " and not the weight of the other components.".format(
                    response_device_dict["product_name"]
                )
            ),
            type="float",
        )

        response_schemas = [payload, reach, weight]

        query_engine = DBLoader.get_query_engine(response_schemas, retriever)
        query_str = (
            "What is payload in [kg], reachability in [mm] and weight of the robot arm"
            " {} in [kg]? Answer always in json format.".format(
                response_device_dict["product_name"]
            )
        )

        response_device_details, response_device_details_dict = make_llm_request(
            query_engine, query_str
        )
        response_device_details_dict = json.loads(
            re.sub(r"json", "", re.sub(r"```", "", response_device_details.response))
        )

        response_device_dict["payload"] = response_device_details_dict["payload"]
        response_device_dict["reach"] = response_device_details_dict["reach"]
        response_device_dict["weight"] = response_device_details_dict["weight"]

    if (
        response_device_type_dict["device_type"]
        == DeviceType.ROBOT_SERVO_DRIVE_JOINT.name
    ):
        power = ResponseSchema(
            name="power",
            description=(
                "What is power in [W] of the {} {}? Answer 0.0 if not provided.".format(
                    response_device_dict["device_type_name"],
                    response_device_dict["product_name"],
                )
            ),
            type="float",
        )
        weight = ResponseSchema(
            name="weight",
            description=(
                "What is weight of the {} {} in [kg]? Answer 0.0 if not provided."
                .format(
                    response_device_dict["device_type_name"],
                    response_device_dict["product_name"],
                )
            ),
            type="float",
        )
        gear_ratio = ResponseSchema(
            name="gear_ratio",
            description=(
                "What is gear_ratio of the {} {}? Answer 0.0 if not provided.".format(
                    response_device_dict["device_type_name"],
                    response_device_dict["product_name"],
                )
            ),
            type="float",
        )

        response_schemas = [power, weight, gear_ratio]

        query_engine = DBLoader.get_query_engine(response_schemas, retriever)
        query_str = (
            "What are the weight in [kg], power in [W] and gear ratio of the {} {}?"
            " Answer 0.0 if not provided. Answer always in json format.".format(
                response_device_dict["device_type_name"],
                response_device_dict["product_name"],
            )
        )
        response_device_details, response_device_details_dict = make_llm_request(
            query_engine, query_str
        )
        response_device_details_dict = json.loads(
            re.sub(r"json", "", re.sub(r"```", "", response_device_details.response))
        )

        response_device_dict["power"] = response_device_details_dict["power"]
        response_device_dict["weight"] = response_device_details_dict["weight"]
        response_device_dict["gear_ratio"] = response_device_details_dict["gear_ratio"]

    nodes = DBLoader.get_all_nodes()


def insert_into_sql(engine, RobotSQLTable, RobotEmbedSQLTable, device_info, nodes):
    from sqlalchemy import MetaData, Table, insert, select

    row_dict_robot_arm = {
        "device_type_name": device_info["device_type_name"],
        "device_type_id": device_info["device_type_id"],
        "company_name": device_info["company_name"],
        "product_name": device_info["product_name"],
        "product_description": device_info["document_description"],
        "payload": device_info["payload"],
        "reach": device_info["reach"],
        "weight": device_info["weight"],
    }

    stmt = insert(RobotSQLTable).values(**row_dict_robot_arm)
    with engine.connect() as connection:
        cursor = connection.execute(stmt)
        connection.commit()
        metadata = MetaData()
        robot_arm_table = Table("robot_arm", metadata, autoload_with=sql_engine)
        stmt = select(robot_arm_table.c.id).where(
            robot_arm_table.c.product_name == device_info["product_name"]
        )
        with sql_engine.connect() as conn:
            robot_arm_id = conn.execute(stmt).fetchall()
    # insert into database
    for node in nodes:
        # row_dict = {
        #    "text": node.get_content(),
        #    "embedding": node.embedding,
        #    "page_label": node.metadata['source'] if 'source' in node.metadata else None,
        #    "file_name": node.metadata['file_path'] if 'file_path' in node.metadata else None,
        #    "collection_name": node.metadata['collection_name'] if 'collection_name' in node.metadata else None,
        # }
        row_dict_robot_arm_embed = {
            "robot_id": robot_arm_id[0][0],
            "page_label": node.metadata["source"]
            if "source" in node.metadata
            else None,
            "file_name": node.metadata["file_path"]
            if "file_path" in node.metadata
            else None,
            "text": node.get_content(),
            "embedding": node.embedding,
            "collection_name": node.metadata["collection_name"]
            if "collection_name" in node.metadata
            else None,
        }

        stmt = insert(RobotEmbedSQLTable).values(**row_dict_robot_arm_embed)
        with engine.connect() as connection:
            cursor = connection.execute(stmt)
            connection.commit()


def insert_into_sql_robot_servo_drive_joint(
    engine, RobotServoJointSQLTable, RobotServoJointEmbedSQLTable, device_info, nodes
):
    from sqlalchemy import MetaData, Table, insert, select

    row_dict_robot_arm = {
        "device_type_name": device_info["device_type_name"],
        "device_type_id": device_info["device_type_id"],
        "company_name": device_info["company_name"],
        "product_name": device_info["product_name"],
        "product_description": device_info["document_description"],
        "power": device_info["power"],
        "weight": device_info["weight"],
        "gear_ratio": device_info["gear_ratio"],
    }

    stmt = insert(RobotServoJointSQLTable).values(**row_dict_robot_arm)
    with engine.connect() as connection:
        cursor = connection.execute(stmt)
        connection.commit()
        metadata = MetaData()
        robot_arm_table = Table(
            "robot_servo_drive_joint", metadata, autoload_with=sql_engine
        )
        stmt = select(robot_arm_table.c.id).where(
            robot_arm_table.c.product_name == device_info["product_name"]
        )
        with sql_engine.connect() as conn:
            robot_arm_id = conn.execute(stmt).fetchall()
    # insert into database
    for node in nodes:
        # row_dict = {
        #    "text": node.get_content(),
        #    "embedding": node.embedding,
        #    "page_label": node.metadata['source'] if 'source' in node.metadata else None,
        #    "file_name": node.metadata['file_path'] if 'file_path' in node.metadata else None,
        #    "collection_name": node.metadata['collection_name'] if 'collection_name' in node.metadata else None,
        # }
        row_dict_robot_arm_embed = {
            "robot_servo_drive_joint_id": robot_arm_id[0][0],
            "page_label": node.metadata["source"]
            if "source" in node.metadata
            else None,
            "file_name": node.metadata["file_path"]
            if "file_path" in node.metadata
            else None,
            "text": node.get_content(),
            "embedding": node.embedding,
            "collection_name": node.metadata["collection_name"]
            if "collection_name" in node.metadata
            else None,
        }

        stmt = insert(RobotServoJointEmbedSQLTable).values(**row_dict_robot_arm_embed)
        with engine.connect() as connection:
            cursor = connection.execute(stmt)
            connection.commit()


def create_sql_engine():
    from pgvector.sqlalchemy import Vector
    from sqlalchemy import (
        Float,
        ForeignKey,
        Integer,
        String,
        create_engine,
        insert,
        text,
    )
    from sqlalchemy.orm import declarative_base, mapped_column

    engine = create_engine(
        "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
    )
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base = declarative_base()

    class RobotSQLTable(Base):
        __tablename__ = "robot_arm"

        id = mapped_column(Integer, primary_key=True)
        device_type_name = mapped_column(String)
        device_type_id = mapped_column(Integer)
        company_name = mapped_column(String)
        product_name = mapped_column(String)
        product_description = mapped_column(String)
        payload = mapped_column(Float)
        reach = mapped_column(Float)
        weight = mapped_column(Float)

    class RobotEmbedSQLTable(Base):
        __tablename__ = "robot_arm_embed"

        id = mapped_column(Integer, primary_key=True)
        robot_id = mapped_column(Integer, ForeignKey("robot_arm.id"), nullable=False)
        page_label = mapped_column(Integer)
        file_name = mapped_column(String)
        text = mapped_column(String)
        # embedding = mapped_column(Vector(768))
        embedding = mapped_column(Vector(1536))
        collection_name = mapped_column(String)

    class RobotServoJointSQLTable(Base):
        __tablename__ = "robot_servo_drive_joint"

        id = mapped_column(Integer, primary_key=True)
        device_type_name = mapped_column(String)
        device_type_id = mapped_column(Integer)
        company_name = mapped_column(String)
        product_name = mapped_column(String)
        product_description = mapped_column(String)
        power = mapped_column(Float)
        weight = mapped_column(Float)
        gear_ratio = mapped_column(Float)

    class RobotServoJointEmbedSQLTable(Base):
        __tablename__ = "robot_servo_drive_joint_embed"

        id = mapped_column(Integer, primary_key=True)
        robot_servo_drive_joint_id = mapped_column(
            Integer, ForeignKey("robot_servo_drive_joint.id"), nullable=False
        )
        page_label = mapped_column(Integer)
        file_name = mapped_column(String)
        text = mapped_column(String)
        # embedding = mapped_column(Vector(768))
        embedding = mapped_column(Vector(1536))
        collection_name = mapped_column(String)

    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    return (
        engine,
        RobotSQLTable,
        RobotEmbedSQLTable,
        RobotServoJointSQLTable,
        RobotServoJointEmbedSQLTable,
    )


(
    sql_engine,
    RobotSQLTable,
    RobotEmbedSQLTable,
    RobotServoJointSQLTable,
    RobotServoJointEmbedSQLTable,
) = create_sql_engine()
print("args.insert_in_sql", args.insert_in_sql)
if args.insert_in_sql and not args.gradio_on:
    logger.info("Inserting into SQL")
    if response_device_dict["device_type_name"] == DeviceType.ROBOT_ARM.name:
        insert_into_sql(
            sql_engine, RobotSQLTable, RobotEmbedSQLTable, response_device_dict, nodes
        )
    if (
        response_device_dict["device_type_name"]
        == DeviceType.ROBOT_SERVO_DRIVE_JOINT.name
    ):
        insert_into_sql_robot_servo_drive_joint(
            sql_engine,
            RobotServoJointSQLTable,
            RobotServoJointEmbedSQLTable,
            response_device_dict,
            nodes,
        )


if args.gradio_on:

    def get_vector_store_from_collection(collection_name):
        import chromadb
        from llama_index.storage.storage_context import StorageContext
        from llama_index.vector_stores import ChromaVectorStore

        chroma_db_path = "./chroma_db"
        db = chromadb.PersistentClient(path=chroma_db_path)
        chroma_collection = db.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        return vector_store, storage_context

    def create_query_engine_tools(
        sql_engine, table_name, table_embed_name, query_engine_tools
    ):
        from llama_index.query_engine import RetrieverQueryEngine
        from llama_index.tools import QueryEngineTool, ToolMetadata

        # sql_engine, RobotSQLTable = create_sql_engine()
        from sqlalchemy import MetaData, Table, select

        metadata = MetaData()
        robot_arm_table = Table(table_name, metadata, autoload_with=sql_engine)
        robot_arm_embed_table = Table(
            table_embed_name, metadata, autoload_with=sql_engine
        )
        stmt = select(robot_arm_table.c.product_name).group_by(
            robot_arm_table.c.product_name
        )
        with sql_engine.connect() as conn:
            robot_arms_values = conn.execute(stmt).fetchall()

        robot_arms_collections = {}
        robot_arms_descriptions = {}
        # SELECT robot_arm_embed.collection_name  FROM robot_arm_embed, robot_arm WHERE robot_arm_embed.robot_id=robot_arm.id AND robot_arm.product_name LIKE 'Diana 7' GROUP BY robot_arm_embed.collection_name;
        for value in robot_arms_values:
            if table_name == "robot_arm":
                stmt = (
                    select(robot_arm_embed_table.c.collection_name)
                    .where(robot_arm_table.c.product_name == value[0])
                    .where(robot_arm_embed_table.c.robot_id == robot_arm_table.c.id)
                    .group_by(robot_arm_embed_table.c.collection_name)
                )
            if table_name == "robot_servo_drive_joint":
                stmt = (
                    select(robot_arm_embed_table.c.collection_name)
                    .where(robot_arm_table.c.product_name == value[0])
                    .where(
                        robot_arm_embed_table.c.robot_servo_drive_joint_id
                        == robot_arm_table.c.id
                    )
                    .group_by(robot_arm_embed_table.c.collection_name)
                )
            logger.debug(stmt)
            with sql_engine.connect() as conn:
                robot_arms_collections[value[0]] = conn.execute(stmt).fetchall()

            stmt = (
                select(robot_arm_table.c.product_description)
                .where(robot_arm_table.c.product_name == value[0])
                .group_by(robot_arm_table.c.product_description)
            )
            with sql_engine.connect() as conn:
                robot_arms_descriptions[value[0]] = conn.execute(stmt).fetchall()

        for key, value in robot_arms_collections.items():
            vector_stores = []
            for collection in value:
                vector_store, storage_context = get_vector_store_from_collection(
                    collection[0]
                )
                vector_stores.append(vector_store)

            retriever = VectorDBRetriever(
                vector_stores[0],  # default vector store
                vector_stores,
                embed_model,
                query_mode="default",
                similarity_top_k=int(10),
                logger=logger,
            )
            query_engine = RetrieverQueryEngine.from_args(
                retriever, service_context=service_context
            )
            query_engine_tool = QueryEngineTool(
                query_engine=query_engine,
                metadata=ToolMetadata(
                    name=key,
                    description=(
                        str(robot_arms_descriptions[key][0][0])
                        + "\n Use a detailed plain text question as input to the tool."
                    ),
                ),
            )

            query_engine_tools.append(query_engine_tool)

        return query_engine_tools

    def get_database_query_engine_tools(sql_engine):
        from llama_index import SQLDatabase
        from llama_index.prompts import PromptTemplate
        from llama_index.query_engine import PGVectorSQLQueryEngine
        from llama_index.tools import QueryEngineTool, ToolMetadata

        sql_database = SQLDatabase(
            sql_engine, include_tables=["robot_arm", "robot_servo_drive_joint"]
        )

        table_desc = """\
            This table represents text chunks about different robots. Each row contains the following columns: \
            Table: robot_arm

            id: identifier \
            device_type_name: name of the device type \
            device_type_id: identifier of the device type \
            company_name: name of the company \
            product_name: name of the product \
            product_description: description of the product \
            payload: payload in kg \
            reach: reachability in mm \
            weight: weight in kg \
            Table: robot_servo_drive_joint

            "id": "Primary key of the table",
            "device_type_name": "Name of the device type",
            "device_type_id": "ID of the device type",
            "company_name": "Name of the company",
            "product_name": "Name of the product",
            "product_description": "Description of the product",
            "power": "Power of the device",
            "weight": "Weight of the device",
            "gear_ratio": "Gear ratio of the device"

            For most queries you should perform semantic search against the `text` column values. \

            """

        text_to_sql_tmpl = """\
        Given an input question, first create a syntactically correct {dialect} \
        query to run, then look at the results of the query and return the answer. \
        You can order the results by a relevant column to return the most \
        interesting examples in the database.

        Pay attention to use only the column names that you can see in the schema \
        description. Be careful to not query for columns that do not exist. \
        Pay attention to which column is in which table. Also, qualify column names \
        with the table name when needed.

        You are required to use the following format, \
        each taking one line:

        Question: Question here
        SQLQuery: SQL Query to run
        SQLResult: Result of the SQLQuery
        Answer: Final answer here

        Only use tables listed below.
        {schema}


        Question: {query_str}
        SQLQuery: \
        """
        text_to_sql_prompt = PromptTemplate(text_to_sql_tmpl)

        context_query_kwargs = {"robot_arm": table_desc}

        text_to_sql_prompt = PromptTemplate(text_to_sql_tmpl)

        query_engine = PGVectorSQLQueryEngine(
            sql_database=sql_database,
            text_to_sql_prompt=text_to_sql_prompt,
            service_context=service_context,
            context_query_kwargs=context_query_kwargs,
        )

        query_engine_tool = QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name="database",
                description="""This query engine provides access to the database. Use it to query the database directly. 

                    The table "robot_arm" represents different robots. It contains the following columns: \
         
                                id: identifier \
                                device_type_name: name of the device type \
                                device_type_id: identifier of the device type \
                                company_name: name of the company \
                                product_name: name of the product \
                                product_description: description of the product \
                                payload: payload in kg \
                                reach: reachability in mm \
                                weight: weight in kg \
                    The table "robot_servo_drive_joint" represents different joint actuators for robto arms. It contains the following columns: \
                            "id": "Primary key of the table",
                            "device_type_name": "Name of the device type",
                            "device_type_id": "ID of the device type",
                            "company_name": "Name of the company",
                            "product_name": "Name of the product",
                            "product_description": "Description of the product",
                            "power": "Power of the device",
                            "weight": "Weight of the device",
                            "gear_ratio": "Gear ratio of the device"
                                                                
                    IMPORTANT NOTE: For the search in the columns company_name and product_name and product_description, use SQL ILIKE operator instead. \
                    Seach case insensitive by using SQL ILIKE operator. \
                    Always use wildcards % before and after the search string. \
                        """,
            ),
        )
        return query_engine_tool

    query_engine_tools = []
    query_engine_tools = create_query_engine_tools(
        sql_engine, "robot_arm", "robot_arm_embed", query_engine_tools
    )
    query_engine_tools = create_query_engine_tools(
        sql_engine,
        "robot_servo_drive_joint",
        "robot_servo_drive_joint_embed",
        query_engine_tools,
    )

    query_engine_tools.append(get_database_query_engine_tools(sql_engine))

    def predict(query_str, history):
        history_openai_format = []

        # query_engine_tools = create_query_engine_tools()

        agent_sys_promt = f"""\
                                You are a specialized agent designed to provide specific technical information about robot arms or compare robot arms. \
                                Try to use different requests to find out which one gives you the best results. \
                                Rewrite Action Input to get the best results.
                                    """
        from llama_index.agent import ReActAgent

        agent = ReActAgent.from_tools(
            query_engine_tools,
            llm=llm,
            verbose=True,
            system_prompt=agent_sys_promt,
            service_context=service_context,
        )
        from llama_index.llms.base import ChatMessage

        # history_message = ChatMessage(content=str(history), role="user")
        print("history: ", history)
        # print("history_message: ", history_message)
        response = agent.chat(message=query_str)
        print(response)  # print the response
        info_sources = set()
        for node in response.source_nodes:
            if "file_path" in node.metadata.keys():
                info_sources.add(node.metadata["file_path"])

        final_responce = str(response.response + "\n\n" + "Info sources: ")
        if info_sources:
            for info_source in info_sources:
                final_responce += info_source + "\n"
        else:
            final_responce += "Local Database."
        return final_responce
        # from langchain.schema import AIMessage, HumanMessage

    import gradio as gr

    chatbot = gr.Chatbot(height=300, label="Sketch-AI Hardware Selection Advisor")

    gr.ChatInterface(
        chatbot=chatbot,
        fn=predict,
        textbox=gr.Textbox(
            placeholder=(
                "Ask me aquestion about robot arms, drives, sensors and other"
                " components."
            ),
            container=False,
            scale=7,
        ),
        title="Sketch-AI",
        examples=[
            "How many axes does the robot Franka Emika production have?",
            "What is the payload of the Kuka LBR iiwa 7 R800?",
            "How many Kuka robots are present in the system? List all of them.",
            (
                "Compare the technical specifications of two robot arms: KR6-R700-CR"
                " and KR6-R700-HM-SC."
            ),
            (
                "List robot arms with a maximum payload of 3 kg that comply with EN ISO"
                " 13849-1 (PLd Category 3) and EN ISO 10218-1."
            ),
            (
                "Compare the technical specifications, noting similarities and"
                " differences, of two robot arms: UR3e and Franka Emika Production."
            ),
        ],
        retry_btn=None,
        undo_btn=None,
        clear_btn=None,
    ).queue().launch()

    # while True:
    #    query_str = input("Enter a question about document:\n")
    #    answer = ResponseSchema(
    #        name="answer",
    #        description="Give the answer to question: \n Question: "
    #        + query_str
    #        + "\n Answer:",
    #    )
    #    response_schemas = [answer]
    #    query_engine = DBLoader.get_query_engine(response_schemas, retriever)
    #    response_query, response_query_dict = make_llm_request(query_engine, query_str)
