from llama_index import ServiceContext, SQLDatabase
from llama_index.indices.struct_store.sql_query import NLSQLTableQueryEngine
from llama_index.prompts.base import PromptTemplate
from llama_index.prompts.prompt_type import PromptType
from sqlalchemy import (Column, Float, Integer, MetaData, String, Table,
                        create_engine, insert, inspect, select)

DEFAULT_RESPONSE_SYNTHESIS_PROMPT_TMPL = (
    "Given an input question, synthesize a response from the query results.\n"
    "Query: {query_str}\n"
    "SQL: {sql_query}\n"
    "SQL Response: {sql_response_str}\n"
    "Response: "
)

DEFAULT_TEXT_TO_SQL_TMPL = (
    "Given an input question, first create a syntactically correct {dialect} "
    "query to run, then look at the results of the query and return the answer. "
    "You can order the results by a relevant column to return the most "
    "interesting examples in the database.\n\n"
    "Never query for all the columns from a specific table, only ask for a "
    "few relevant columns given the question.\n\n"
    "Pay attention to use only the column names that you can see in the schema "
    "description. "
    "Be careful to not query for columns that do not exist. "
    "Pay attention to which column is in which table. "
    "Use wildcards to query for all posssible appearances of the specific device types names ."
    "Also, qualify column names with the table name when needed. "
    "You are required to use the following format, each taking one line:\n\n"
    "Question: Question here\n"
    "SQLQuery: SQL Query to run\n"
    "SQLResult: Result of the SQLQuery\n"
    "Answer: Final answer here\n\n"
    "Only use tables listed below.\n"
    "{schema}\n\n"
    "Question: {query_str}\n"
    "SQLQuery: "
)

DEFAULT_TEXT_TO_SQL_PROMPT = PromptTemplate(
    DEFAULT_TEXT_TO_SQL_TMPL, prompt_type=PromptType.TEXT_TO_SQL
)


class RobotArmDatabase:
    def __init__(self, llm, logger=None):
        # self.engine = create_engine("sqlite:///:memory:")
        self.engine = create_engine("sqlite:///sqlitedbs/devices.db", echo=True)
        self.metadata_obj = MetaData()
        self.table_name = "robot_arm"
        self.llm = llm
        self.logger = logger

    def create_robot_arm_table(self):
        # create robot arm SQL table
        insp = inspect(self.engine)
        has_table = insp.has_table(self.table_name)
        if not has_table:
            self.logger.debug("Creating table")
            self.robot_table = Table(
                self.table_name,
                self.metadata_obj,
                Column("company_name", String(100)),
                Column("product_name", String(100), primary_key=True),
                Column("product_description", String()),
                Column("payload", Integer),
                Column("reach", Integer),
                Column("degrees_of_freedom", Integer),
                Column("weight", Float),
                Column("operating_temperature_min", Float),
                Column("operating_temperature_max", Float),
                Column("operating_voltage_min", Float),
                Column("operating_voltage_max", Float),
                Column("power_consumption", Float),
                Column("ip_classification", String(20)),
                Column("tcp_speed", Float),
                Column("pose_repeatability", Float),
                Column("axis_working_range", String(200)),
                Column("axis_maximum_speed", String(200)),
                Column("datasheet_source", String()),
            )
            self.metadata_obj.create_all(self.engine)
            self.sql_database = SQLDatabase(
                self.engine, include_tables=[self.table_name]
            )
        else:
            self.logger.debug("Table already exists")

    def insert_robot_arm_data(self, rows):
        user_table = Table(self.table_name, self.metadata_obj)
        for row in rows:
            print(row)
            stmt = insert(user_table).values(**row)
            with self.engine.begin() as connection:
                cursor = connection.execute(stmt)

    def make_query(self, query_str):
        sql_database = SQLDatabase(self.engine, include_tables=[self.table_name])
        query_engine = NLSQLTableQueryEngine(
            sql_database=sql_database,
            tables=[self.table_name],
            text_to_sql_prompt=DEFAULT_TEXT_TO_SQL_PROMPT,
        )
        response = query_engine.query(query_str)
        print(response)


#
#
RobotDB = RobotArmDatabase(llm, logger)
RobotDB.create_robot_arm_table()
#
# rows = [
#    {
#        "company_name": "Universal Robots A/S",
#        "product_name": "UR5e",
#        "product_description": "The UR5e is a lightweight and versatile cobot designed for industrial applications. It has a payload capacity of 5 kg and a reach of 850 mm. The robot features 6 rotating joints and is programmed using a 12-inch touchscreen with a graphical user interface called PolyScope. It consumes less electricity compared to traditional industrial robots and offers increased uptime and productivity. The UR5e is agile and can be quickly deployed in existing manufacturing setups with limited space. It comes with built-in safety features and supports safe human-robot interaction. The robot is part of the e-Series cobots and offers flexibility and ease of use for medium-duty applications.",
#        "payload": 5,
#        "reach": 850,
#        "degrees_of_freedom": 6,
#        "weight": 20.6,
#        "operating_temperature_min": 0,
#        "operating_temperature_max": 50,
#        "operating_voltage_min": 100,
#        "operating_voltage_max": 240,
#        "power_consumption": 570,
#        "ip_classification": "IP54",
#        "tcp_speed": 1.0,
#        "pose_repeatability": 0.03,
#        "axis_working_range": "[360, 360, 360, 360, 360, 360]",
#        "axis_maximum_speed": "[180, 180, 180, 180, 180, 180",
#        "datasheet_source": "['ur5e_user_manual_en_us_url1', 'ur5e_user_manual_en_us_pdf_00', 'ur5e_user_manual_en_us_pdf_sherpa_0', 'ur5e_user_manual_en_us_pdf_sherpa_table_00', 'ur5e_user_manual_en_us_pdf_sherpa_table_01', 'ur5e_user_manual_en_us_pdf_sherpa_table_02', 'ur5e_user_manual_en_us_pdf_sherpa_table_03', 'ur5e_user_manual_en_us_pdf_sherpa_table_04', 'ur5e_user_manual_en_us_pdf_sherpa_table_05', 'ur5e_user_manual_en_us_pdf_sherpa_table_06']",
#    }
# ]
#

rows = [
    {
        "company_name": "Universal Robots A/S",
        "product_name": "UR5e",
        "product_description": "The UR5e is a lightweight and versatile cobot designed for industrial applications. It has a payload capacity of 5 kg and a reach of 850 mm. The robot features 6 rotating joints and is programmed using a 12-inch touchscreen with a graphical user interface called PolyScope. It consumes less electricity compared to traditional industrial robots and offers increased uptime and productivity. The UR5e is agile and can be quickly deployed in existing manufacturing setups with limited space. It comes with built-in safety features and supports safe human-robot interaction. The robot is part of the e-Series cobots and offers flexibility and ease of use for medium-duty applications.",
        "payload": 5,
        "reach": 850,
        "degrees_of_freedom": 6,
        "weight": 20.6,
        "operating_temperature_min": 0,
        "operating_temperature_max": 50,
        "operating_voltage_min": 100,
        "operating_voltage_max": 240,
        "power_consumption": 570,
        "ip_classification": "IP54",
        "tcp_speed": 1.0,
        "pose_repeatability": 0.03,
        "axis_working_range": "[360, 360, 360, 360, 360, 360]",
        "axis_maximum_speed": "[180, 180, 180, 180, 180, 180]",
        "datasheet_source": "['ur5e_user_manual_en_us_url1', 'ur5e_user_manual_en_us_pdf_00', 'ur5e_user_manual_en_us_pdf_sherpa_0', 'ur5e_user_manual_en_us_pdf_sherpa_table_00', 'ur5e_user_manual_en_us_pdf_sherpa_table_01', 'ur5e_user_manual_en_us_pdf_sherpa_table_02', 'ur5e_user_manual_en_us_pdf_sherpa_table_03', 'ur5e_user_manual_en_us_pdf_sherpa_table_04', 'ur5e_user_manual_en_us_pdf_sherpa_table_05', 'ur5e_user_manual_en_us_pdf_sherpa_table_06']",
    },
    {
        "company_name": "Agile Robots AG",
        "product_name": "Diana 7",
        "product_description": "he Diana 7 industrial lightweight seven-axis robot is designed for complex and highly sensitive assembly processes. It has a payload capacity of seven kilograms and a functional reach of 923 mm. The robot is suitable for installing electronic components in smartphones, tablets, PCs, and more. It is being used in the Chinese market and is also being used in the automotive, pharmaceutical, and 3C production sectors. Agile Robots is currently producing Diana 7 in series production in China and plans to set up a production site in Bavaria. The robot offers safety through high precision torque-control and design, maximum dexterity in industrial environments, and intuitive teaching through a user-friendly interface.",
        "payload": 7,
        "reach": 923,
        "degrees_of_freedom": 7,
        "weight": 26,
        "operating_temperature_min": 0,
        "operating_temperature_max": 50,
        "operating_voltage_min": 0,
        "operating_voltage_max": 0,
        "power_consumption": 0,
        "ip_classification": "IP54",
        "tcp_speed": 1.0,
        "pose_repeatability": 0.05,
        "axis_working_range": "[179, 90, 179, 175, 179, 179, 179]",
        "axis_maximum_speed": "[170, 170, 170, 170, 210, 210, 210]",
        "datasheet_source": "['diana7_pdf_00', 'diana7_pdf_01', 'diana7_pdf_02', 'diana7_pdf_03', 'diana7_pdf_sherpa_0', 'diana7_pdf_sherpa_table_00', 'diana7_pdf_00', 'diana7_pdf_01','diana7_pdf_02',]",
    },
]

RobotDB.insert_robot_arm_data(rows)
#
# query_str = "What is the payload of the UR5e?"
#
# RobotDB.make_query(query_str)
#
# # view current table
# stmt = select(
#     robot_table.c.company_name,
#     robot_table.c.product_name,
#     robot_table.c.product_description,
# ).select_from(robot_table)
#
# with engine.connect() as connection:
#     results = connection.execute(stmt).fetchall()
#     print(results)
#
# from sqlalchemy import text
#
# with engine.connect() as con:
#     rows = con.execute(text("SELECT company_name from robot_arm"))
#     for row in rows:
#         print(row)
#
# from llama_index.indices.struct_store.sql_query import NLSQLTableQueryEngine


rows = [
    {
        "company_name": "Universal Robots A/S",
        "product_name": "UR5e",
        "product_description": "The UR5e is a lightweight and versatile cobot designed for industrial applications. It has a payload capacity of 5 kg and a reach of 850 mm. The robot features 6 rotating joints and is programmed using a 12-inch touchscreen with a graphical user interface called PolyScope. It consumes less electricity compared to traditional industrial robots and offers increased uptime and productivity. The UR5e is agile and can be quickly deployed in existing manufacturing setups with limited space. It comes with built-in safety features and supports safe human-robot interaction. The robot is part of the e-Series cobots and offers flexibility and ease of use for medium-duty applications.",
        "payload": 5,
        "reach": 850,
        "degrees_of_freedom": 6,
        "weight": 20.6,
        "operating_temperature_min": 0,
        "operating_temperature_max": 50,
        "operating_voltage_min": 100,
        "operating_voltage_max": 240,
        "power_consumption": 570,
        "ip_classification": "IP54",
        "tcp_speed": 1.0,
        "pose_repeatability": 0.03,
        "axis_working_range": "[360, 360, 360, 360, 360, 360]",
        "axis_maximum_speed": "[180, 180, 180, 180, 180, 180]",
        "datasheet_source": "['ur5e_user_manual_en_us_url1', 'ur5e_user_manual_en_us_pdf_00', 'ur5e_user_manual_en_us_pdf_sherpa_0', 'ur5e_user_manual_en_us_pdf_sherpa_table_00', 'ur5e_user_manual_en_us_pdf_sherpa_table_01', 'ur5e_user_manual_en_us_pdf_sherpa_table_02', 'ur5e_user_manual_en_us_pdf_sherpa_table_03', 'ur5e_user_manual_en_us_pdf_sherpa_table_04', 'ur5e_user_manual_en_us_pdf_sherpa_table_05', 'ur5e_user_manual_en_us_pdf_sherpa_table_06']",
    },
    {
        "company_name": "Agile Robots AG",
        "product_name": "Diana 7",
        "product_description": "he Diana 7 industrial lightweight seven-axis robot is designed for complex and highly sensitive assembly processes. It has a payload capacity of seven kilograms and a functional reach of 923 mm. The robot is suitable for installing electronic components in smartphones, tablets, PCs, and more. It is being used in the Chinese market and is also being used in the automotive, pharmaceutical, and 3C production sectors. Agile Robots is currently producing Diana 7 in series production in China and plans to set up a production site in Bavaria. The robot offers safety through high precision torque-control and design, maximum dexterity in industrial environments, and intuitive teaching through a user-friendly interface.",
        "payload": 7,
        "reach": 923,
        "degrees_of_freedom": 7,
        "weight": 26,
        "operating_temperature_min": 0,
        "operating_temperature_max": 50,
        "operating_voltage_min": 0,
        "operating_voltage_max": 0,
        "power_consumption": 0,
        "ip_classification": "IP54",
        "tcp_speed": 1.0,
        "pose_repeatability": 0.05,
        "axis_working_range": "[179, 90, 179, 175, 179, 179, 179]",
        "axis_maximum_speed": "[170, 170, 170, 170, 210, 210, 210]",
        "datasheet_source": "['diana7_pdf_00', 'diana7_pdf_01', 'diana7_pdf_02', 'diana7_pdf_03', 'diana7_pdf_sherpa_0', 'diana7_pdf_sherpa_table_00', 'diana7_pdf_00', 'diana7_pdf_01','diana7_pdf_02',]",
    },
]


query_str = "Compare the technical characteristics two robots UR5e and Diana7. Answer with the table comparing data of this two robots."
RobotDB.make_query(query_str)
