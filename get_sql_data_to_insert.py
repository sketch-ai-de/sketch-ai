from langchain.output_parsers import ResponseSchema

import logging, json, re


def make_llm_request(query_engine, query_str, logger):
    response_dict = []
    response = query_engine.query(query_str)
    print("response:::::::::::::::::::::\n", response)
    response_dict = json.loads(
        re.sub(r"json", "", re.sub(r"```", "", response.response))
    )
    if logger.getEffectiveLevel() == logging.DEBUG:
        for idx, node in enumerate(response.source_nodes):
            print(
                "#########################################                      "
                " Node {} with text \n: {}".format(idx, node.text)
            )
            print("######################################### \n")
    return response, response_dict


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

    # fields_dict = get_sql_fields_for_robot_arm()

    for key in fields_dict.keys():
        field = ResponseSchema(
            name=key,
            description=fields_dict[key]["description"]
            + ". "
            + "Always answer informationen related to robot arm {} with the specified datatype {}".format(
                response_device_dict["product_name"], fields_dict[key]["datatype"]
            ),
            type=fields_dict[key]["datatype"],
        )
        response_schemas = [field]
        query_engine = DBLoader.get_query_engine(response_schemas, retriever)
        query_str = (
            fields_dict[key]["description"]
            + ". "
            + "Answer always in json format. Add no comments."
        )
        response_device_details, response_device_details_dict = make_llm_request(
            query_engine, query_str, logger
        )
        response_device_dict[key] = response_device_details_dict[key]

    return response_device_dict


def get_robot_arm_embed_data(robot_arm_id, nodes, fields_dict=[]):
    response_device_list = []

    for node in nodes:
        response_device_dict = fields_dict
        response_device_dict = {
            "robot_arm_id": robot_arm_id,
            "document_type": node.metadata["document_type"],
            "page_label": node.metadata["source"]
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


def get_company_data(data, fields_dict=[]):
    response_device_dict = fields_dict
    response_device_dict["company_name"] = data["company_name"]
    response_device_dict["company_name_variations"] = data["company_name"]

    return response_device_dict


def get_software_data(
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
            description=fields_dict[key]["description"]
            + ". "
            + "Always answer informationen related to robot arm {} with the specified datatype {}".format(
                response_device_dict["product_name"], fields_dict[key]["datatype"]
            ),
            type=fields_dict[key]["datatype"],
        )
        response_schemas = [field]
        query_engine = DBLoader.get_query_engine(response_schemas, retriever)
        query_str = (
            fields_dict[key]["description"]
            + ". "
            + "Answer always in json format. Don't put any additional information or comments. Don't add any additional fields, only requested fields."
        )
        response_device_details, response_device_details_dict = make_llm_request(
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
            "page_label": node.metadata["source"]
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
