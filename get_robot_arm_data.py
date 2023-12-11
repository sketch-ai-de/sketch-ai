from langchain.output_parsers import ResponseSchema

from sql_handler_robot_arm import get_sql_fields_for_robot_arm

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


def get_robot_arm_data(query_engine, retriever, DBLoader, logger, product_name=None):
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

    fields_dict = get_sql_fields_for_robot_arm()

    for key in fields_dict.keys():
        field = ResponseSchema(
            name=key,
            description=fields_dict[key]["description"]
            + ". "
            + "Always answer informationen related to robot arm {}".format(
                response_device_dict["product_name"]
            ),
            type=fields_dict[key]["datatype"],
        )
        response_schemas = [field]
        query_engine = DBLoader.get_query_engine(response_schemas, retriever)
        query_str = (
            fields_dict[key]["description"] + ". " + "Answer always in json format."
        )
        response_device_details, response_device_details_dict = make_llm_request(
            query_engine, query_str, logger
        )
        response_device_dict[key] = response_device_details_dict[key]

    return response_device_dict
