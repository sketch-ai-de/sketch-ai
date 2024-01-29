import json
import re

from langchain.output_parsers import ResponseSchema


class GetSQLDataToInsert:
    def __init__(
        self,
        DBLoader,
        logger,
        retriever,
        product_name=None,
        fields_dict={},
        fields_dict_embed={},
        fields_dict_company={},
    ):
        self.logger = logger
        self.retriever = retriever
        self.db_loader = DBLoader
        self.product_name = product_name
        self.fields_dict = fields_dict
        self.fields_dict_embed = fields_dict_embed
        self.fields_dict_company = fields_dict_company

    def make_llm_request(self, query_engine, query_str):
        response_dict = {}
        response = query_engine.query(query_str)
        self.logger.info(f"response: {response}")
        # logger.info("response:::::::::::::::::::::\n", response.response)
        res = re.sub(r"json", "", re.sub(r"```", "", response.response))
        if " // " in res:
            res = res.split("//")[:-1]
            res = res[0] + "}"
        try:
            response_dict = json.loads(res)
        except ValueError:
            response_dict = {}
            self.logger.error("Decoding JSON has failed")
        for idx, node in enumerate(response.source_nodes):
            self.logger.debug(f"Node {idx} with text \n: {node.text}")
        return response_dict

    def get_data(self):
        """
        Retrieves data related to a robot arm from a database using the provided query engine, retriever, and DBLoader
        and asks llm to extract specific technical data.

        Returns:
        dict: A dictionary containing the retrieved data related to the robot arm, including the product name and other fields.
        """
        response_device_dict = {"product_name": self.product_name}

        for key in self.fields_dict.keys():
            field = ResponseSchema(
                name=key,
                description=self.fields_dict[key]["datatype"],
                type=self.fields_dict[key]["datatype"],
            )
            response_schemas = [field]
            query_engine = self.db_loader.get_query_engine(
                response_schemas, self.retriever
            )
            query_str = f"For the field {key} get all the relevant and detailed information for the product {self.product_name} based on fields description: {self.fields_dict[key]['description']}"
            response_device_details_dict = self.make_llm_request(
                query_engine, query_str
            )
            response_device_dict[key] = response_device_details_dict[key]

        return response_device_dict

    def get_company_data(self, data):
        response_device_dict = self.fields_dict_company
        response_device_dict["company_name"] = data["company_name"]
        response_device_dict["company_name_variations"] = data["company_name"]

        return response_device_dict

    def get_embed_data(self, product_name_id, nodes):
        response_device_list = []

        for node in nodes:
            response_device_dict = self.fields_dict_embed
            response_device_dict = {
                "parent_id": product_name_id,
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
                "pdf_url": node.metadata["pdf_url"]
                if "pdf_url" in node.metadata
                else None,
                "web_url": node.metadata["web_url"]
                if "web_url" in node.metadata
                else None,
            }
            response_device_list.append(response_device_dict)

        return response_device_list
