import os

import openai
from dotenv import load_dotenv
from llama_index.embeddings import AzureOpenAIEmbedding, OpenAIEmbedding
from llama_index.llms import AzureOpenAI, OpenAI, OpenAILike
from llama_index.llms.llama_utils import messages_to_prompt


def load_models(args, logger):
    llm_service = args.llm_service
    llm_model = args.llm_model
    load_dotenv()
    llm_temperature = 0.1
    timeout = 120.0

    if llm_model == "gpt3":
        # _llm_model = "gpt-35-turbo"
        _llm_model = "gpt-3.5-turbo-1106"
        _azure_openai_key = os.getenv("AZURE_OPENAI_GPT4_KEY")
        _azure_ada_deployment_name = "sketch-ai-gpt4-ada002"
        _azure_endpoint = "https://open-ai-uk-south.openai.azure.com/"
        _azure_deployment_name = "sketch-ai-gpt35turbo"
    elif llm_model == "gpt4":
        _azure_deployment_name = "sketch-ai-gpt4"
        _llm_model = "gpt-4-1106-preview"
        # _llm_model_oai = "gpt-4-1106-preview"
        _azure_openai_key = os.getenv("AZURE_OPENAI_GPT4_KEY")
        _azure_ada_deployment_name = "sketch-ai-gpt4-ada002"
        _azure_endpoint = "https://open-ai-uk-south.openai.azure.com/"
    elif llm_model == "local":
        # TODO: Replace these once I figure out how to get local embedding server working
        _azure_deployment_name = "sketch-ai-gpt4"
        _azure_openai_key = os.getenv("AZURE_OPENAI_GPT4_KEY")
        _azure_ada_deployment_name = "sketch-ai-gpt4-ada002"
        _azure_endpoint = "https://open-ai-uk-south.openai.azure.com/"
        api_version = "2023-07-01-preview"
    else:
        raise ValueError(f"Model {llm_model} not supported")

    _llm = None
    _embed_model = None

    if llm_service == "openai":
        logger.info("Using OPENAI services")
        _embed_model = OpenAIEmbedding()

        openai.api_key = os.getenv("OPENAI_API_KEY")
        _llm = OpenAI(temperature=llm_temperature, model=_llm_model, timeout=timeout)
    elif llm_service == "azure":
        logger.info("Using AZURE services")

        api_version = "2023-07-01-preview"

        _llm = AzureOpenAI(
            model=_llm_model,
            deployment_name=_azure_deployment_name,
            api_key=_azure_openai_key,
            azure_endpoint=_azure_endpoint,
            api_version=api_version,
            temperature=llm_temperature,
            timeout=timeout,
        )

        # You need to deploy your own embedding model as well as your own chat completion model
        _embed_model = AzureOpenAIEmbedding(
            model="text-embedding-ada-002",
            deployment_name=_azure_ada_deployment_name,
            api_key=_azure_openai_key,
            azure_endpoint=_azure_endpoint,
            api_version=api_version,
        )
    elif llm_service == "local":
        MAC_M1_LUNADEMO_CONSERVATIVE_TIMEOUT = 10 * 60  # sec
        _llm = OpenAILike(
            max_tokens=4096,
            temperature=0.9,
            api_key="localai_fake",
            api_version="localai_fake",
            api_base=f"http://{args.local_llm_address}:{args.local_llm_port}/v1",
            model="local llm",
            is_chat_model=True,
            timeout=MAC_M1_LUNADEMO_CONSERVATIVE_TIMEOUT,
            messages_to_prompt=messages_to_prompt,
        )
        # TODO(qu): _embed_model = HuggingFaceEmbedding(model_name="WhereIsAI/UAE-Large-V1")
        _embed_model = OpenAIEmbedding()
    else:
        raise ValueError(f"Service {llm_service} not supported")

    logger.info(f"Loading embedded model {_embed_model.model_name} \n")
    logger.info(f"Loading llm model {_llm.model} \n")

    return _llm, _embed_model
