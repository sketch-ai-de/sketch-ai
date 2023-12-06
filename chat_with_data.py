import logging
import os
import sys
import argparse

import openai
from dotenv import load_dotenv
from langchain.output_parsers import ResponseSchema
from llama_index import ServiceContext, VectorStoreIndex
from llama_index.embeddings import HuggingFaceEmbedding, OpenAIEmbedding
from llama_index.llms import OpenAI

from document_preprocessor import DocumentPreprocessor
from vector_db_loader import VectorDBLoader
from vector_db_retriever import VectorDBRetriever

parser = argparse.ArgumentParser(
    prog="RagLlamaindex",
    description="Retrieve information from different soures - PDFs and Web-Links",
)
parser.add_argument("-d", "--debug", action="store_true")
args = parser.parse_args()

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


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

logger.info("--------------------- Loading llm model {} \n".format(llm_model))
llm = OpenAI(temperature=llm_temperature, model=llm_model)

service_context = ServiceContext.from_defaults(
    chunk_size=1024, llm=llm, embed_model=embed_model
)


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


# ToDo (Dimi) - create a tol retriever and pass it as parameter to ReAct agent
# tool_retriever: Optional[ObjectRetriever[BaseTool]] = None
def create_vector_index_from_tools(tools):
    get_tools = lambda _: tools

    from llama_index.tools import adapt_to_async_tool

    tools = [adapt_to_async_tool(t) for t in get_tools("")]
    # print("tools: ", tools)
    docs = [
        str(
            "idx: "
            + str(idx)
            + ", name: "
            + str(t.metadata.name)
            + ", description: "
            + str(t.metadata.description)
        )
        for idx, t in enumerate(tools)
    ]
    # print("docs: ", docs)
    from llama_index import Document, VectorStoreIndex

    documents = [Document(text=t, metadata={"idx": idx}) for idx, t in enumerate(docs)]

    from llama_index.embeddings import OpenAIEmbedding

    embed_model = OpenAIEmbedding()

    index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)

    from llama_index.retrievers import VectorIndexRetriever

    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=5,
    )

    return retriever


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
            scale=5,
        ),
        examples=[
            "How many axes does the robot Franka Emika production have?",
            "What is the payload of the Kuka LBR iiwa 7 R800?",
            "How many Kuka robots are present in the system? List all of them.",
            (
                "Compare the technical specifications, noting similarities and"
                " differences,  of two robot arms: KR6-R700-CR"
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
        css="footer{display:none !important}",
    ).queue().launch(server_name="0.0.0.0", show_api=False, auth=("admin", "admin"))

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
