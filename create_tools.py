from vector_db_retriever import VectorDBRetriever
from typing import Any


class CreateTools:
    def __init__(
        self, embed_model: Any, service_context, chroma_db_path: str, logger
    ) -> None:
        self.embed_model = embed_model
        self.service_context = service_context
        self.chroma_db_path = chroma_db_path
        self.logger = logger

    def get_vector_store_from_collection(self, collection_name):
        import chromadb
        from llama_index.storage.storage_context import StorageContext
        from llama_index.vector_stores import ChromaVectorStore

        chroma_db_path = self.chroma_db_path  # "./chroma_db"
        db = chromadb.PersistentClient(path=chroma_db_path)
        chroma_collection = db.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        return vector_store, storage_context

    def create_query_engine_tools(
        self, sql_engine, table_name, table_embed_name, query_engine_tools
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
            self.logger.debug(stmt)
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
                vector_store, storage_context = self.get_vector_store_from_collection(
                    collection[0]
                )
                vector_stores.append(vector_store)
            _retriever = VectorDBRetriever(
                vector_stores[0],  # default vector store
                vector_stores,
                self.embed_model,
                query_mode="default",
                similarity_top_k=int(10),
                logger=self.logger,
                service_context=self.service_context,
            )
            _query_engine = RetrieverQueryEngine.from_args(
                _retriever, service_context=self.service_context, use_async=True
            )
            query_engine_tool = QueryEngineTool(
                query_engine=_query_engine,
                metadata=ToolMetadata(
                    name=key.replace(" ", "-").replace(",", "-"),
                    description=(
                        str(robot_arms_descriptions[key][0][0])
                        # +"\n Use a detailed plain text question as input to the tool."
                    ),
                ),
            )
            query_engine_tools.append(query_engine_tool)
        return query_engine_tools

    def get_database_query_engine_tools(self, sql_engine):
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
            For most queries you should perform semantic search against the `text` column values. \
            """
        text_to_sql_tmpl = """\
        Given an input question, first create a syntactically correct {dialect} \
        query to run, then look at the results of the query and return the answer. \
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
            service_context=self.service_context,
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
                    Do not select all the columns, only relevant ones, e.g. company_name and product_name. \
                    Seach case insensitive by using SQL ILIKE operator. \
                    Always use wildcards % before and after the search string. \
                    If you count number of tables in the database, use SQL COUNT function with AS keyword. \
                    Never use column names in the query that do not exist in the table description. \
                    Be sparing when creating SQL queries. Minimize the number of selected columns. \
                        """,
            ),
        )
        return query_engine_tool

    def get_tools(self):
        from create_sql_engine import create_sql_engine

        sql_engine = create_sql_engine()

        query_engine_tools = []
        query_engine_tools = self.create_query_engine_tools(
            sql_engine, "robot_arm", "robot_arm_embed", query_engine_tools
        )
        query_engine_tools = self.create_query_engine_tools(
            sql_engine,
            "robot_servo_drive_joint",
            "robot_servo_drive_joint_embed",
            query_engine_tools,
        )
        sql_query_engine_tool = self.get_database_query_engine_tools(sql_engine)
        return query_engine_tools, sql_query_engine_tool
