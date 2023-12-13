import logging
import sys
import argparse
from llama_index.service_context import ServiceContext
from create_tools import CreateTools
from tool_retriever import ToolRetriever
from load_models import load_models

parser = argparse.ArgumentParser(
    prog="RagLlamaindex",
    description="Retrieve information from different soures - PDFs and Web-Links",
)
parser.add_argument("-d", "--debug", action="store_true")
parser.add_argument("-s", "--seq_react", action="store_true")
parser.add_argument("-r", "--rerank", action="store_true")
parser.add_argument("-kr", "--similarity_top_k_rerank", default=15, type=int)
parser.add_argument("-m", "--llm-model", default="gpt3", type=str, help="gpt3 or gpt4")
parser.add_argument(
    "-s", "--llm-service", default="azure", type=str, help="azure or openai"
)
args = parser.parse_args()

logger = logging.getLogger(__name__)
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

llm, embed_model = load_models(
    llm_service=args.llm_service, llm_model=args.llm_model, logger=logger
)

service_context = ServiceContext.from_defaults(
    chunk_size=1024, llm=llm, embed_model=embed_model
)

create_tools = CreateTools(
    service_context=service_context,
    logger=logger,
    embed_model=embed_model,
    chroma_db_path="./chroma_db",
)
query_engine_tools, sql_query_engine_tool = create_tools.get_tools()


tool_retriever = ToolRetriever(
    tools=query_engine_tools,
    sql_tools=sql_query_engine_tool,
    embed_model=embed_model,
    append_sql=False,
)
tool_retriever.create_vector_index_from_tools()


if args.seq_react:
    from llama_index.agent import ReActAgent
else:
    from libs.react.base import ReActAgent


agent_sys_promt = f"""\
                            You are a specialized agent designed to provide specific technical information about robot arms or compare robot arms. \
                            Try to use different requests to find out which one gives you the best results. \
                            Rewrite Action Input to get the best results.
                                """
agent = ReActAgent.from_tools(
    llm=llm,
    verbose=True,
    system_prompt=agent_sys_promt,
    service_context=service_context,
    max_iterations=6,
    tool_retriever=tool_retriever,
)


async def predict(query_str, history, agent=agent):
    history_openai_format = []

    from llama_index.llms.base import ChatMessage

    # history_message = ChatMessage(content=str(history), role="user")
    print("history: ", history)

    response = await agent.achat(message=query_str)
    print(response)  # print the response
    info_sources = set()
    for node in response.source_nodes:
        if "pdf_url" in node.metadata.keys():
            info_sources.add(node.metadata["pdf_url"])
        if "web_url" in node.metadata.keys():
            info_sources.add(node.metadata["web_url"])
    final_responce = str(response.response + "\n\n" + "Info sources: ")
    if info_sources:
        for info_source in info_sources:
            final_responce += info_source + "\n"
    else:
        final_responce += "Local Database."
    return final_responce


import gradio as gr

chatbot = gr.Chatbot(height=600, label="Sketch-AI Hardware Selection Advisor")
gr.ChatInterface(
    chatbot=chatbot,
    fn=predict,
    textbox=gr.Textbox(
        placeholder=(
            "Ask me aquestion about robot arms, drives, sensors and other components."
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
