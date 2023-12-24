from llama_index.llms import ChatMessage, OpenAILike

MAC_M1_LUNADEMO_CONSERVATIVE_TIMEOUT = 10 * 60  # sec
model = OpenAILike(
    max_tokens=4096,
    temperature=0.9,
    api_key="localai_fake",
    api_version="localai_fake",
    api_base="http://host.docker.internal:8080/v1",  # host.docker.internal is necessary for macOS
    model="mistral",
    is_chat_model=True,
    timeout=MAC_M1_LUNADEMO_CONSERVATIVE_TIMEOUT,
)
response = model.chat(messages=[ChatMessage(content="How are you?")])
print(response)
