import argparse
import logging
import sys
import time

from llama_index.service_context import ServiceContext

from create_tools import CreateTools
from load_models import load_models
from tool_retriever import ToolRetriever


async def main():
    parser = argparse.ArgumentParser(
        prog="RagLlamaindex",
        description="Retrieve information from different soures - PDFs and Web-Links",
    )
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-s", "--seq_react", action="store_true")
    parser.add_argument("-r", "--rerank", action="store_true")
    parser.add_argument("-kr", "--similarity_top_k_rerank", default=15, type=int)
    parser.add_argument(
        "-m", "--llm-model", default="gpt4", type=str, help="local, gpt3 or gpt4"
    )
    parser.add_argument(
        "-l", "--llm-service", default="azure", type=str, help="local, azure or openai"
    )
    parser.add_argument("-p", "--prompt", default="", type=str, help="Prompt for input")
    parser.add_argument(
        "--local-llm-address",
        default="localhost",  # host.docker.internal for using docker under macOS
        type=str,
        help="address for local llm",
    )
    parser.add_argument(
        "--local-llm-port", default="8080", type=str, help="port for local llm"
    )
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    streamHandler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    llm, embed_model = load_models(args, logger=logger)

    # service_context = ServiceContext.from_defaults(
    #    chunk_size=1024, llm=llm, embed_model=embed_model
    # )
    service_context = ServiceContext.from_defaults(
        chunk_size=1024, llm=llm, embed_model=embed_model, context_window=128000
    )

    create_tools = CreateTools(
        service_context=service_context,
        logger=logger,
        embed_model=embed_model,
        chroma_db_path="./db/chroma_db",
        rerank=args.rerank,
    )
    query_engine_tools, sql_query_engine_tool = create_tools.get_tools()

    tool_retriever = ToolRetriever(
        tools=query_engine_tools,
        sql_tools=sql_query_engine_tool,
        embed_model=embed_model,
        append_sql=False,
        logger=logger,
    )
    tool_retriever.create_vector_index_from_tools()

    if args.seq_react or args.llm_model == "local":
        logger.info("Using standard ReActAgent")
        from llama_index.agent import ReActAgent
    else:
        logger.info("Using customized ReActAgent from libs.react.base")
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
        # history_message = ChatMessage(content=str(history), role="user")
        if history:
            logger.info(f"history: {history}")

        response = await agent.astream_chat(message=query_str + "\n Use tools.")
        print("Response: ", response)

        final_responce = ""
        async for token in response.async_response_gen():
            final_responce += token
            yield (final_responce)
        logger.info(f"response: {response.response}")  # print the response
        info_sources_pdfs = {}
        info_sources_urls = set()
        for node in response.source_nodes:
            if "pdf_url" in node.metadata.keys():
                if not node.metadata["pdf_url"] in info_sources_pdfs.keys():
                    info_sources_pdfs[node.metadata["pdf_url"]] = set()
                info_sources_pdfs[node.metadata["pdf_url"]].add(
                    node.metadata["page_idx"]
                )
            if "web_url" in node.metadata.keys():
                info_sources_urls.add(node.metadata["web_url"])
        # final_responce = str(response.response)
        if info_sources_pdfs or info_sources_urls:
            final_responce += "\nSources: \n"
        if info_sources_pdfs:
            final_responce += "PDFs: \n"
            for info_source in info_sources_pdfs.keys():
                final_responce += (
                    info_source
                    + " . "
                    + "Pages: "
                    + str(info_sources_pdfs[info_source])
                    + "\n "
                )
        if info_sources_urls:
            final_responce += "URLs: \n"
            for info_source in info_sources_urls:
                final_responce += info_source + "\n "
        # else:
        #    final_responce += "Local Database."
        yield final_responce

    if args.prompt:
        tic = time.perf_counter()
        if args.seq_react or args.llm_model == "local":
            logger.info("Ask local llm with standard sequential ReActAgent")
            response = agent.chat(args.prompt)
        else:
            logger.info("Ask customized parallel ReActAgent")
            response = await agent.achat(args.prompt)
        toc = time.perf_counter()
        print("\n==========================================\n")
        print("\033[92m{}\033[00m".format("Prompt: "), args.prompt)
        print("\033[91m{}\033[00m".format("Response: "), response)
        print(f"Elapsed time: {toc - tic:0.4f} seconds")
    else:
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
                (
                    "Compare the technical specifications, noting similarities and"
                    " differences,  of two robot arms: KR6-R700-CR"
                    " and KR6-R700-HM-SC."
                ),
                (
                    "Compare the technical specifications, noting similarities and"
                    " differences, of two robot arms: UR3e and Franka Emika Production."
                ),
                "Prepare a siemens setup of all components with the followig requierements: CANopen and 8 digital inputs.",
                "What are the input modules for siemens et200sp?",
                "Tell me more about Frankas FCI interface.",
            ],
            retry_btn=None,
            undo_btn=None,
            clear_btn=None,
            css="footer{display:none !important}",
        ).queue().launch(server_name="0.0.0.0", show_api=False, auth=("admin", "admin"), favicon_path="images/favicon.ico",)


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
