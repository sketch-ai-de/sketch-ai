from llama_index.llms import AzureOpenAI
from llama_index.embeddings import AzureOpenAIEmbedding
from llama_index.embeddings import OpenAIEmbedding
from llama_index.llms import OpenAI
import openai
import os
from dotenv import load_dotenv


def load_models(llm_model, llm_service, logger):
    load_dotenv()
    llm_temperature = 0.1

    if llm_model == "gpt3":
        # _llm_model = "gpt-35-turbo"
        _llm_model = "gpt-3.5-turbo-1106"
        _azure_openai_key = os.getenv("AZURE_OPENAI_GPT4_KEY")
        _azure_ada_deployment_name = "sketch-ai-gpt4-ada002"
        _azure_endpoint = "https://open-ai-uk-south.openai.azure.com/"
        _azure_deployment_name = "sketch-ai-gpt35turbo"
    if llm_model == "gpt4":
        _azure_deployment_name = "sketch-ai-gpt4"
        _llm_model = "gpt-4-1106-preview"
        # _llm_model_oai = "gpt-4-1106-preview"
        _azure_openai_key = os.getenv("AZURE_OPENAI_GPT4_KEY")
        _azure_ada_deployment_name = "sketch-ai-gpt4-ada002"
        _azure_endpoint = "https://open-ai-uk-south.openai.azure.com/"

    _llm = None
    _embed_model = None

    if llm_service == "openai":
        logger.info("Using OPENAI services")
        _embed_model = OpenAIEmbedding()

        openai.api_key = os.getenv("OPENAI_API_KEY")
        _llm = OpenAI(temperature=llm_temperature, model=_llm_model)

    if llm_service == "azure":
        logger.info("Using AZURE services")

        api_version = "2023-07-01-preview"

        _llm = AzureOpenAI(
            model=_llm_model,
            deployment_name=_azure_deployment_name,
            api_key=_azure_openai_key,
            azure_endpoint=_azure_endpoint,
            api_version=api_version,
            temperature=llm_temperature,
        )

        # You need to deploy your own embedding model as well as your own chat completion model
        _embed_model = AzureOpenAIEmbedding(
            model="text-embedding-ada-002",
            deployment_name=_azure_ada_deployment_name,
            api_key=_azure_openai_key,
            azure_endpoint=_azure_endpoint,
            api_version=api_version,
        )

    logger.info("Loading embedded model {} \n".format(_embed_model.model_name))
    logger.info("Loading llm model {} \n".format(_llm.model))

    return _llm, _embed_model
