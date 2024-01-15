from sketch_ai_types import device_type_dict

sql_fields_company = {
    "company_name": {"datatype": "str", "description": "Company name", "sql_extra": {}},
    "company_name_variations": {
        "datatype": "str",
        "description": "Company name variations",
        "sql_extra": {},
    },
}

sql_fields_robot_arm = {
    "company_id": {
        "datatype": "int",
        "description": "ID of the company. Default 1.",
        "sql_extra": {"ForeignKey": "company.id", "nullable": "False"},
    },
    "company_name": {"datatype": "str", "description": "Company name", "sql_extra": {}},
    "device_type_name": {
        "datatype": "str",
        "description": (
            "Device type name. List of device types:{device_types}:".format(
                device_types=device_type_dict,
            )
        ),
        "sql_extra": {},
    },
    "device_type_id": {
        "datatype": "int",
        "description": (
            "Device type id. List of device types:{device_types}:".format(
                device_types=device_type_dict,
            )
        ),
        "sql_extra": {},
    },
    "product_name": {"datatype": "str", "description": "Product name", "sql_extra": {}},
    "product_description": {
        "datatype": "str",
        "description": "About Product - Detailed product description with key technical data and features. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "payload": {
        "datatype": "float",
        "description": "Payload in [kg]. 0 if not provided.",
        "sql_extra": {},
    },
    "reach": {
        "datatype": "float",
        "description": "Reach in [mm]. 0 if not provided.",
        "sql_extra": {},
    },
    "weight": {
        "datatype": "float",
        "description": "Weight in [kg]. 0 if not provided.",
        "sql_extra": {},
    },
    "number_of_joints": {
        "datatype": "str",
        "description": "Number of joints and Dimension of freedom",
        "sql_extra": {},
    },
    "operating_temperature": {
        "datatype": "str",
        "description": "Operating temperature min-max in [°C]",
        "sql_extra": {},
    },
    "operating_voltage": {
        "datatype": "str",
        "description": "Operating, rated voltage min-max in [V]",
        "sql_extra": {},
    },
    "power_consumption": {
        "datatype": "float",
        "description": "Power consumption in [W]. 0 if not provided.",
        "sql_extra": {},
    },
    "ip_classification": {
        "datatype": "str",
        "description": "IP protection classification",
        "sql_extra": {},
    },
    "tcp_speed": {
        "datatype": "float",
        "description": "TCP, Cartesian speed in [m/s]. 0 if not provided.",
        "sql_extra": {},
    },
    "pose_repeatability": {
        "datatype": "str",
        "description": "Pose repeatability,  ISO 9283 in ±[mm]",
        "sql_extra": {},
    },
    "joints_position_range": {
        "datatype": "str",
        "description": "Joints or Axis position working range in [°]. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "joints_speed_range": {
        "datatype": "str",
        "description": "Joints or Axis speed in [°/s]. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "iso_safety_standard": {
        "datatype": "str",
        "description": (
            "ISO safety, EN ISO 13849-1, PLd Category 3, EN ISO 10218-1 standards. Without any website links. Do not create multiline lists."
        ),
        "sql_extra": {},
    },
    "iso_non_safety_standard": {
        "datatype": "str",
        "description": "ISO non-safety standard. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "safety_functions": {
        "datatype": "str",
        "description": "Safety functions. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "control_box": {
        "datatype": "bool",
        "description": "Control box or Cabinet included or not. Bool value. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "control_box_description": {
        "datatype": "str",
        "description": "Detailed Description of Control box or Control Cabinet. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "tool_flange": {
        "datatype": "str",
        "description": "Tool flange, e.g. EN ISO-9409-1-50-4-M6.",
        "sql_extra": {},
    },
    "gripper": {
        "datatype": "str",
        "description": (
            "Description of the default gripper shipped with the robot arm., if any. Without any website links. Do not create multiline lists."
        ),
        "sql_extra": {},
    },
    "footprint": {
        "datatype": "str",
        "description": "Footprint in [mm]",
        "sql_extra": {},
    },
    "force_sensing": {
        "datatype": "str",
        "description": "Force or torque sensing, tool or robot or guiding force [Nm]",
        "sql_extra": {},
    },
}
sql_fields_robot_arm_embed = {
    "parent_id": {
        "datatype": "int",
        "description": "The ID of the robot arm",
        "sql_extra": {"ForeignKey": "robot_arm.id", "nullable": "False"},
    },
    "document_type": {
        "datatype": "int",
        "description": "The type of the document",
        "sql_extra": {},
    },
    "page_label": {
        "datatype": "int",
        "description": "The label of the page",
        "sql_extra": {},
    },
    "file_name": {
        "datatype": "str",
        "description": "The name of the file",
        "sql_extra": {},
    },
    "text": {
        "datatype": "str",
        "description": "The text content",
        "sql_extra": {},
    },
    "embedding_openai": {
        "datatype": "vector",
        "datatype_extra": {"dim": 1536},
        "description": "The OpenAI embedding",
        "sql_extra": {},
    },
    "embedding_all_mpnet_base_v2": {
        "datatype": "vector",
        "datatype_extra": {"dim": 768},
        "description": "The embedding from the MPNet base model",
        "sql_extra": {},
    },
    "collection_name": {
        "datatype": "str",
        "description": "The name of the collection",
        "sql_extra": {},
    },
    "pdf_url": {
        "datatype": "str",
        "description": "The URL of the PDF",
        "sql_extra": {},
    },
    "web_url": {
        "datatype": "str",
        "description": "The URL of the web page",
        "sql_extra": {},
    },
}

sql_fields_software = {
    "company_id": {
        "datatype": "int",
        "description": "The ID of the company. Default 1.",
        "sql_extra": {"ForeignKey": "company.id", "nullable": "False"},
    },
    "company_name": {"datatype": "str", "description": "Company name", "sql_extra": {}},
    "device_type_name": {
        "datatype": "str",
        "description": (
            "Software device type name. List of types:{device_types}:".format(
                device_types=device_type_dict,
            )
        ),
        "sql_extra": {},
    },
    "device_type_id": {
        "datatype": "int",
        "description": (
            "Software type id. List of types:{device_types}:".format(
                device_types=device_type_dict,
            )
        ),
        "sql_extra": {},
    },
    "product_name": {
        "datatype": "str",
        "description": "Software product name",
        "sql_extra": {},
    },
    "product_description": {
        "datatype": "str",
        "description": "Detialed software product, package description. With all the relevant information regarding libraries and usage.",
        "sql_extra": {},
    },
}

sql_fields_software_embed = {
    "parent_id": {
        "datatype": "int",
        "description": "The ID of the software product",
        "sql_extra": {"ForeignKey": "software.id", "nullable": "False"},
    },
    "document_type": {
        "datatype": "int",
        "description": "The type of the document",
        "sql_extra": {},
    },
    "page_label": {
        "datatype": "int",
        "description": "The label of the page",
        "sql_extra": {},
    },
    "file_name": {
        "datatype": "str",
        "description": "The name of the file",
        "sql_extra": {},
    },
    "text": {
        "datatype": "str",
        "description": "The text content",
        "sql_extra": {},
    },
    "embedding_openai": {
        "datatype": "vector",
        "datatype_extra": {"dim": 1536},
        "description": "The OpenAI embedding",
        "sql_extra": {},
    },
    "embedding_all_mpnet_base_v2": {
        "datatype": "vector",
        "datatype_extra": {"dim": 768},
        "description": "The embedding from the MPNet base model",
        "sql_extra": {},
    },
    "collection_name": {
        "datatype": "str",
        "description": "The name of the collection",
        "sql_extra": {},
    },
    "pdf_url": {
        "datatype": "str",
        "description": "The URL of the PDF",
        "sql_extra": {},
    },
    "web_url": {
        "datatype": "str",
        "description": "The URL of the web page",
        "sql_extra": {},
    },
}


sql_fields_plc = {
    "company_id": {
        "datatype": "int",
        "description": "The ID of the company. Default 1.",
        "sql_extra": {"ForeignKey": "company.id", "nullable": "False"},
    },
    "company_name": {"datatype": "str", "description": "Company name", "sql_extra": {}},
    "device_type_name": {
        "datatype": "str",
        "description": (
            "Software device type name. List of types:{device_types}:".format(
                device_types=device_type_dict,
            )
        ),
        "sql_extra": {},
    },
    "device_type_id": {
        "datatype": "int",
        "description": (
            "Software type id. List of types:{device_types}:".format(
                device_types=device_type_dict,
            )
        ),
        "sql_extra": {},
    },
    "product_name": {
        "datatype": "str",
        "description": "Product name. ",
        "sql_extra": {},
    },
    "article_number": {
        "datatype": "str",
        "description": "Article number of the product. Use only one article number per product. If more available, seperate with ','.",
        "sql_extra": {},
    },
    "product_description": {
        "datatype": "str",
        "description": "Detailed product or package overview, its design and description of technical data and specifications. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "product_description_long": {
        "datatype": "str",
        "description": "Detailed product or package overview, its design and description of technical data and specifications. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "technical_data": {
        "datatype": "str",
        "description": "Detailed overview of all the technical data and specifications. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "related_components": {
        "datatype": "str",
        "description": "System (hardware and software) components related to this product or can be used together with this product. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "compatible_components": {
        "datatype": "str",
        "description": "Compatible system (hardware and software) components related this product or can be used together with this product. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "must_have_components": {
        "datatype": "str",
        "description": "Mandatory/must have system (hardware and software) components and requierements needed to use this product. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
    "references": {
        "datatype": "str",
        "description": "References to this and other products, manuals, components, packages, libraries, etc. Without any website links. Do not create multiline lists.",
        "sql_extra": {},
    },
}

sql_fields_plc_embed = {
    "parent_id": {
        "datatype": "int",
        "description": "The ID of the plc product",
        "sql_extra": {"ForeignKey": "plc.id", "nullable": "False"},
    },
    "document_type": {
        "datatype": "int",
        "description": "The type of the document",
        "sql_extra": {},
    },
    "page_label": {
        "datatype": "int",
        "description": "The label of the page",
        "sql_extra": {},
    },
    "file_name": {
        "datatype": "str",
        "description": "The name of the file",
        "sql_extra": {},
    },
    "text": {
        "datatype": "str",
        "description": "The text content",
        "sql_extra": {},
    },
    "embedding_openai": {
        "datatype": "vector",
        "datatype_extra": {"dim": 1536},
        "description": "The OpenAI embedding",
        "sql_extra": {},
    },
    "embedding_all_mpnet_base_v2": {
        "datatype": "vector",
        "datatype_extra": {"dim": 768},
        "description": "The embedding from the MPNet base model",
        "sql_extra": {},
    },
    "collection_name": {
        "datatype": "str",
        "description": "The name of the collection",
        "sql_extra": {},
    },
    "pdf_url": {
        "datatype": "str",
        "description": "The URL of the PDF",
        "sql_extra": {},
    },
    "web_url": {
        "datatype": "str",
        "description": "The URL of the web page",
        "sql_extra": {},
    },
}
