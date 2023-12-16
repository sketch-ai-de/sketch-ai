from langchain.output_parsers import ResponseSchema

import logging, json, re
import time


def make_llm_request(query_engine, query_str, logger):
    response_dict = {}
    response = query_engine.query(query_str)
    print(response)
    # logger.info("response:::::::::::::::::::::\n", response.response)
    res = re.sub(r"json", "", re.sub(r"```", "", response.response))
    if "//" in res:
        res = res.split("//")[:-1]
        res = res[0] + "}"
    response_dict = json.loads(res)
    for idx, node in enumerate(response.source_nodes):
        logger.debug(" Node {} with text \n: {}".format(idx, node.text))
    return response_dict


def get_robot_arm_data(
    query_engine, retriever, DBLoader, logger, product_name=None, fields_dict=[]
):
    """
    Retrieves data related to a robot arm from a database using the provided query engine, retriever, and DBLoader
    and asks llm to extract specific technical data.

    Args:
        query_engine (QueryEngine): The query engine used to execute the database queries.
        retriever (Retriever): The retriever used to retrieve data from the database.
        DBLoader (DBLoader): The DBLoader used to load the database.
        logger (Logger): The logger used for logging.
        product_name (str, optional): The name of the robot arm product. Defaults to None.

    Returns:
        dict: A dictionary containing the retrieved data related to the robot arm, including the product name and other fields.
    """
    # Function implementation goes here
    response_device_dict = {"product_name": product_name}

    for key in fields_dict.keys():
        field = ResponseSchema(
            name=key,
            description=fields_dict[key]["datatype"],
            type=fields_dict[key]["datatype"],
        )
        response_schemas = [field]
        # query_engine = DBLoader.get_query_engine(response_schemas, retriever)
        query_engine = DBLoader.get_query_engine(response_schemas, retriever)
        query_str = "Extract relevant information about the field based on fields description for the product. \n \
                Product name: {} \n \
                Field: {} \n \
                Field description: {}. \n \
                    Always answer in JSON format. \n.".format(
            key,
            response_device_dict["product_name"],
            fields_dict[key]["description"],
        )
        response_device_details_dict = make_llm_request(query_engine, query_str, logger)
        response_device_dict[key] = response_device_details_dict[key]

    return response_device_dict


def get_robot_arm_embed_data(robot_arm_id, nodes, fields_dict=[]):
    response_device_list = []

    for node in nodes:
        response_device_dict = fields_dict
        response_device_dict = {
            "robot_arm_id": robot_arm_id,
            "document_type": node.metadata["document_type"],
            "page_label": (int(node.metadata["page_idx"]))
            if "page_idx" in node.metadata
            else None,
            "file_name": node.metadata["file_path"]
            if "file_path" in node.metadata
            else None,
            "text": node.get_content(),
            "embedding_openai": node.embedding,
            "collection_name": node.metadata["collection_name"]
            if "collection_name" in node.metadata
            else None,
            "pdf_url": node.metadata["pdf_url"] if "pdf_url" in node.metadata else None,
            "web_url": node.metadata["web_url"] if "web_url" in node.metadata else None,
        }
        response_device_list.append(response_device_dict)

    return response_device_list


def get_company_data(data, fields_dict=[]):
    response_device_dict = fields_dict
    response_device_dict["company_name"] = data["company_name"]
    response_device_dict["company_name_variations"] = data["company_name"]

    return response_device_dict


async def get_software_data(
    query_engine, retriever, DBLoader, logger, product_name=None, fields_dict=[]
):
    """
    Retrieves data related to a robot arm from a database using the provided query engine, retriever, and DBLoader
    and asks llm to extract specific technical data.

    Args:
        query_engine (QueryEngine): The query engine used to execute the database queries.
        retriever (Retriever): The retriever used to retrieve data from the database.
        DBLoader (DBLoader): The DBLoader used to load the database.
        logger (Logger): The logger used for logging.
        product_name (str, optional): The name of the robot arm product. Defaults to None.

    Returns:
        dict: A dictionary containing the retrieved data related to the robot arm, including the product name and other fields.
    """
    # Function implementation goes here
    response_device_dict = {"product_name": product_name}

    # fields_dict = get_sql_fields_for_robot_arm()

    for key in fields_dict.keys():
        field = ResponseSchema(
            name=key,
            description=fields_dict[key]["description"],
            type=fields_dict[key]["datatype"],
        )
        response_schemas = [field]
        query_engine = DBLoader.get_query_engine(response_schemas, retriever)
        query_str = (
            "Given a description of the field, extract the relevant information.\n"
            "Always answer information related to product {} with the provided data type: {}".format(
                response_device_dict["product_name"],
                fields_dict[key]["datatype"]
                + ". \n"
                + "If no information is provided for the field, leave it empty or 0."
                + "Answer always in json format. Don't put any additional information or comments. \
                Use only provided fields.",
            )
        )
        response_device_details_dict = await make_llm_request(
            query_engine, query_str, logger
        )
        response_device_dict[key] = response_device_details_dict[key]

    return response_device_dict


def get_software_embed_data(software_id, nodes, fields_dict=[]):
    response_device_list = []

    for node in nodes:
        response_device_dict = fields_dict
        response_device_dict = {
            "software_id": software_id,
            "document_type": node.metadata["document_type"],
            "page_label": node.metadata["page_idx"]
            if "source" in node.metadata
            else None,
            "file_name": node.metadata["file_path"]
            if "file_path" in node.metadata
            else None,
            "text": node.get_content(),
            "embedding_openai": node.embedding,
            "collection_name": node.metadata["collection_name"]
            if "collection_name" in node.metadata
            else None,
            "pdf_url": node.metadata["pdf_url"] if "pdf_url" in node.metadata else None,
            "web_url": node.metadata["web_url"] if "web_url" in node.metadata else None,
        }
        response_device_list.append(response_device_dict)

    return response_device_list
