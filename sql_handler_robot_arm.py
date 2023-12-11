from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
    Boolean,
    create_engine,
    text,
)
from sqlalchemy.orm import declarative_base, mapped_column

from sqlalchemy import create_engine

from sqlalchemy import String, Float, Boolean

from sketch_ai_types import device_type_dict
from sqlalchemy import MetaData, Table, insert, select


def get_sql_fields_for_robot_arm():
    sql_fields = {
        "device_type_name": {
            "datatype": "str",
            "description": (
                "Device type name. List of device types:{device_types}:".format(
                    device_types=device_type_dict,
                )
            ),
        },
        "device_type_id": {
            "datatype": "int",
            "description": (
                "Device type id. List of device types:{device_types}:".format(
                    device_types=device_type_dict,
                )
            ),
        },
        "company_name": {"datatype": "str", "description": "Company name"},
        "product_name": {"datatype": "str", "description": "Product name"},
        "product_description": {
            "datatype": "str",
            "description": "Product description",
        },
        "payload": {"datatype": "float", "description": "Payload in [kg]"},
        "reach": {"datatype": "float", "description": "Reach in [mm]"},
        "weight": {"datatype": "float", "description": "Weight in [kg]"},
        "number_of_joints": {
            "datatype": "str",
            "description": "Number of joints and Dimension of freedom",
        },
        "operating_temperature": {
            "datatype": "str",
            "description": "Operating temperature min-max in [°C]",
        },
        "operating_voltage": {
            "datatype": "str",
            "description": "Operating/rated voltage min-max in [V]",
        },
        "power_consumption": {
            "datatype": "float",
            "description": "Power consumption in [W]",
        },
        "ip_classification": {
            "datatype": "str",
            "description": "IP / protection classification",
        },
        "tcp_speed": {
            "datatype": "float",
            "description": "TCP / Cartesian speed in [m/s]",
        },
        "pose_repeatability": {
            "datatype": "str",
            "description": "Pose repeatability / ISO 9283 in ±[mm]",
        },
        "joints_position_range": {
            "datatype": "str",
            "description": "Joints / Axis position working range in [°]",
        },
        "joints_speed_range": {
            "datatype": "str",
            "description": "Joints / Axis speed in [°/s]",
        },
        "iso_safety_standard": {
            "datatype": "str",
            "description": (
                "ISO safety / EN ISO 13849-1 / PLd Category 3 / EN ISO 10218-1 standard"
            ),
        },
        "iso_non_safety_standard": {
            "datatype": "str",
            "description": "ISO non-safety standard",
        },
        "safety_functions": {"datatype": "str", "description": "Safety functions"},
        "control_box": {"datatype": "bool", "description": "Control box"},
        "control_box_description": {
            "datatype": "str",
            "description": "Control box description",
        },
        "tool_flange": {
            "datatype": "str",
            "description": "Tool flange, e.g. EN ISO-9409-1-50-4-M6",
        },
        "gripper": {
            "datatype": "str",
            "description": (
                "Description of the default gripper shipped with the robot arm. None if"
                " no gripper is shipped."
            ),
        },
        "footprint": {"datatype": "str", "description": "Footprint in [mm]"},
        "force_sensing": {
            "datatype": "str",
            "description": "Force sensing on tool or robot / Guiding force [Nm]",
        },
    }

    for field in sql_fields:
        datatype = sql_fields[field]["datatype"]
        if datatype == "str":
            sql_fields[field]["sql_datatype"] = String
        elif datatype == "float":
            sql_fields[field]["sql_datatype"] = Float
        elif datatype == "int":
            sql_fields[field]["sql_datatype"] = Integer
        elif datatype == "bool":
            sql_fields[field]["sql_datatype"] = Boolean

    return sql_fields


class SQLHandlerRobotArm:
    def __init__(
        self,
        engine_config="postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
        engine=None,
    ):
        self._engine = engine or create_engine(engine_config)
        self._sql_fields_for_robot_arm = get_sql_fields_for_robot_arm()
        self._base = None
        self._robot_sql_table = None
        self._robot_embed_sql_table = None

    def create_base(self):
        self._base = declarative_base()

        class RobotSQLTable(self._base):
            sql_fields = self._sql_fields_for_robot_arm
            __tablename__ = "robot_arm"
            id = mapped_column(
                Integer,
                primary_key=True,
                autoincrement=True,
                comment="Unique identifier for the robot arm",
            )
            for field in sql_fields.keys():
                locals()[field] = mapped_column(
                    sql_fields[field]["sql_datatype"],
                    comment=sql_fields[field]["description"],
                )

        class RobotEmbedSQLTable(self._base):
            __tablename__ = "robot_arm_embed"
            id = mapped_column(Integer, primary_key=True)
            robot_id = mapped_column(
                Integer, ForeignKey("robot_arm.id"), nullable=False
            )
            document_type = mapped_column(Integer)
            page_label = mapped_column(Integer)
            file_name = mapped_column(String)
            text = mapped_column(String)
            # embedding = mapped_column(Vector(768))
            embedding_openai = mapped_column(Vector(1536))
            embedding_all_mpnet_base_v2 = mapped_column(Vector(768))
            collection_name = mapped_column(String)
            pdf_url = mapped_column(String)
            web_url = mapped_column(String)

            # Base.metadata.drop_all(engine)

        self._robot_sql_table = RobotSQLTable
        self._robot_embed_sql_table = RobotEmbedSQLTable

    def create_robot_table(self):
        with self._engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

        self.create_base()
        self._base.metadata.create_all(self._engine)

    def get_robot_arm_id(self, product_name):
        robot_arm_id = None
        with self._engine.connect() as connection:
            # cursor = connection.execute(stmt)
            connection.commit()
            metadata = MetaData()
            robot_arm_table = Table("robot_arm", metadata, autoload_with=self._engine)
            stmt = select(robot_arm_table.c.id).where(
                robot_arm_table.c.product_name == product_name
            )
            with self._engine.connect() as conn:
                robot_arm_id = conn.execute(stmt).fetchall()

        return robot_arm_id

    def insert_device_into_sql(self, device_info):
        for dev_key in device_info.keys():
            device_info["product_description"] = (
                device_info["product_description"]
                + "\n"
                + str(dev_key)
                + ": "
                + str(device_info[dev_key])
            )

        stmt = insert(self._robot_sql_table).values(**device_info)
        with self._engine.connect() as connection:
            cursor = connection.execute(stmt)
            connection.commit()

    def insert_nodes_into_sql(self, nodes, product_name):
        robot_arm_id = self.get_robot_arm_id(product_name)
        # insert into database
        for node in nodes:
            print("node: ", node)
            row_dict_robot_arm_embed = {
                "robot_id": robot_arm_id[0][0],
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
                "pdf_url": node.metadata["pdf_url"]
                if "pdf_url" in node.metadata
                else None,
                "web_url": node.metadata["web_url"]
                if "web_url" in node.metadata
                else None,
            }

            stmt = insert(self._robot_embed_sql_table).values(
                **row_dict_robot_arm_embed
            )
            with self._engine.connect() as connection:
                cursor = connection.execute(stmt)
                connection.commit()
