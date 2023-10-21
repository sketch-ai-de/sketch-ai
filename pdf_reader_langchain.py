import os
import sys

import openai
from dotenv import find_dotenv, load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
# Split
from langchain.text_splitter import (CharacterTextSplitter,
                                     RecursiveCharacterTextSplitter)
from langchain.vectorstores import Chroma

sys.path.append("../..")


_ = load_dotenv(find_dotenv())  # read local .env file


openai.api_key = os.environ["OPENAI_API_KEY"]

loader_et200 = PyPDFLoader("docs/et200sp_cm_can.pdf")
pages_1 = loader_et200.load()

loader_233 = PyPDFLoader("docs/233.pdf")
pages_2 = loader_233.load()

r_splitter = RecursiveCharacterTextSplitter(
    chunk_size=450, chunk_overlap=0, separators=["\n\n", "\n"]
)

r_splitter2 = RecursiveCharacterTextSplitter(
    chunk_size=150, chunk_overlap=0, separators=["\n\n", "\n", "\. ", " ", ""]
)
# r_splitter.split_text(some_text)

# Load PDF
loaders = [
    # Duplicate documents on purpose - messy data
    PyPDFLoader("docs/et200sp_cm_can.pdf"),
    PyPDFLoader("docs/233.pdf"),
]
docs = []
for loader in loaders:
    docs.extend(loader.load())


text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)

splits = text_splitter.split_documents(docs)
len(splits)


embedding = OpenAIEmbeddings()


persist_directory = "docs/chroma/"

vectordb = Chroma.from_documents(
    documents=splits, embedding=embedding, persist_directory=persist_directory
)

print(vectordb._collection.count())

question = "is there an email i can ask for help"
docs = vectordb.similarity_search(question, k=3)
len(docs)
docs[0].page_content
vectordb.persist()

for doc in docs:
    print(doc.metadata)
