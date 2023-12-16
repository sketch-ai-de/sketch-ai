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
        "description": "Detialed product description",
        "sql_extra": {},
    },
    "payload": {"datatype": "float", "description": "Payload in [kg]", "sql_extra": {}},
    "reach": {"datatype": "float", "description": "Reach in [mm]", "sql_extra": {}},
    "weight": {"datatype": "float", "description": "Weight in [kg]", "sql_extra": {}},
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
        "description": "Power consumption in [W]",
        "sql_extra": {},
    },
    "ip_classification": {
        "datatype": "str",
        "description": "IP protection classification",
        "sql_extra": {},
    },
    "tcp_speed": {
        "datatype": "float",
        "description": "TCP, Cartesian speed in [m/s]",
        "sql_extra": {},
    },
    "pose_repeatability": {
        "datatype": "str",
        "description": "Pose repeatability,  ISO 9283 in ±[mm]",
        "sql_extra": {},
    },
    "joints_position_range": {
        "datatype": "str",
        "description": "Joints or Axis position working range in [°]",
        "sql_extra": {},
    },
    "joints_speed_range": {
        "datatype": "str",
        "description": "Joints or Axis speed in [°/s]",
        "sql_extra": {},
    },
    "iso_safety_standard": {
        "datatype": "str",
        "description": (
            "ISO safety, EN ISO 13849-1, PLd Category 3, EN ISO 10218-1 standards"
        ),
        "sql_extra": {},
    },
    "iso_non_safety_standard": {
        "datatype": "str",
        "description": "ISO non-safety standard",
        "sql_extra": {},
    },
    "safety_functions": {
        "datatype": "str",
        "description": "Safety functions",
        "sql_extra": {},
    },
    "control_box": {"datatype": "bool", "description": "Control box", "sql_extra": {}},
    "control_box_description": {
        "datatype": "str",
        "description": "Control box description",
        "sql_extra": {},
    },
    "tool_flange": {
        "datatype": "str",
        "description": "Tool flange, e.g. EN ISO-9409-1-50-4-M6",
        "sql_extra": {},
    },
    "gripper": {
        "datatype": "str",
        "description": (
            "Description of the default gripper shipped with the robot arm., if any"
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
        "description": "Force sensing, tool or robot or guiding force [Nm]",
        "sql_extra": {},
    },
}
sql_fields_robot_arm_embed = {
    "robot_arm_id": {
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
    "software_id": {
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
