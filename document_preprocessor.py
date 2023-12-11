import re

from llama_hub.file.pymu_pdf.base import PyMuPDFReader
from llama_index import Document, download_loader
from llama_index.prompts import PromptTemplate
from llama_index.schema import TextNode

from llmsherpa.readers import LayoutPDFReader

from metadata import Metadata
import subprocess
from llama_index.node_parser import SentenceSplitter


import requests
import PyPDF2
import io

from pathlib import Path
from llama_hub.file.unstructured import UnstructuredReader
import os
import random, string


class DocumentPreprocessor:
    def __init__(
        self,
        web_urls: list = None,
        pdf_urls: list = None,
        metadata: Metadata = None,
        logger=None,
        llm=None,
        load_sherpa=True,
    ):
        self._web_urls = web_urls
        self._pdf_urls = pdf_urls
        self._metadata = metadata
        self._logger = logger
        self._llm = llm
        self._nodes = list()
        self._embedding = None
        self._collections = dict()
        self._url_docs = dict()
        self._pdf_docs = dict()
        self._pdf_docs_sherpa = dict()
        self._pdf_docs_sherpa_tables = dict()

        self._pdf_name = "temp.pdf"
        self._load_sherpa = load_sherpa

    def generate_random_string(self, length=30):
        return str(
            "".join(
                random.choice(string.ascii_uppercase + string.digits)
                for _ in range(length)
            )
        )

    def load_urls(self):
        """
        Loads documents from URLs.
        """
        self._logger.info("Load urls \n")
        ReadabilityWebPageReader = download_loader("ReadabilityWebPageReader")
        loader_url = ReadabilityWebPageReader()
        collection_name = "web_url_" + self.generate_random_string()
        self._url_docs[collection_name] = {}
        self._url_docs[collection_name]["docs"] = []
        for idx, url in enumerate(self._web_urls):
            docs = loader_url.load_data(url=url)
            self._url_docs[collection_name]["metadata"] = self._metadata.get_dict()
            self._url_docs[collection_name]["metadata"]["web_url"] = url
            for doc in docs:
                doc.metadata.update(self._url_docs[collection_name]["metadata"])
            self._url_docs[collection_name]["docs"].append(docs)
            self._url_docs[collection_name]["text"] = re.sub("\n\n", " ", docs[0].text)
        self.remove_none_fields(self._url_docs)

    def path_generator(self, target_directory):
        url_list = []
        for root, dirs, files in os.walk(target_directory):
            for file in files:
                if any(ext in file for ext in [".html", ".htm"]):
                    url_list.append(f"{root}/{file}")
        return url_list  # returns a list of path for each file in the directory

    def get_text_from_html(self, file_path):
        loader = UnstructuredReader()
        documents = loader.load_data(file=Path(file_path))
        return documents  # returns text and source url (metadata) from an HTML file

    def load_urls_from_path(self, urls):
        """
        Loads documents from URLs.
        """
        path = "tmp" + self.generate_random_string(3)
        collection_name = "web_url_" + self.generate_random_string()
        self._url_docs[collection_name] = {}
        self._url_docs[collection_name]["docs"] = []
        docs = []
        for url in urls:
            subprocess.run(["wget", "-r", "-l1", "-nd", "-P", path, url])
            for file_path in self.path_generator(path):
                docs.append(self.get_text_from_html(file_path))
            for idx, docs in enumerate(docs):
                self._url_docs[collection_name]["docs"].append(docs)
                self._url_docs[collection_name]["metadata"] = self._metadata.get_dict()
                self._url_docs[collection_name]["metadata"]["web_url"] = url
                for doc in docs:
                    doc.metadata.update(self._url_docs[collection_name]["metadata"])
                self._url_docs[collection_name]["text"] = re.sub(
                    "\n\n", " ", docs[0].text
                )
            self.remove_none_fields(self._url_docs)
            subprocess.run(["rm", "-r", path])

    def load_pdfs(self):
        """
        This function is responsible for loading PDF documents
        """
        loader_pdf = PyMuPDFReader()
        for idx, pdf_url in enumerate(self._pdf_urls):
            if pdf_url:
                self._logger.info("Load PDF document {} \n".format(pdf_url))
                subprocess.run(["wget", "-O", self._pdf_name, pdf_url])
                collection_name = "pdf_url_" + str(idx)
                self._pdf_docs[collection_name] = {}
                self._pdf_docs[collection_name]["metadata"] = self._metadata.get_dict()
                self._pdf_docs[collection_name]["metadata"]["pdf_url"] = pdf_url
                self._pdf_docs[collection_name]["pdf"] = loader_pdf.load(
                    file_path=self._pdf_name
                )
                for page in self._pdf_docs[collection_name]["pdf"]:
                    page.metadata.update(self._metadata.get_dict())
                    page.metadata["pdf_url"] = pdf_url

                if self._load_sherpa:
                    self.load_sherpa_pdfs(idx, pdf_url)
                subprocess.run(["rm", "", self._pdf_name])

    def load_sherpa_pdfs(self, idx, pdf_url):
        """
        This function is responsible for loading PDF documents with sherpa`.

        """
        llmsherpa_api_url = "https://readers.llmsherpa.com/api/document/developer/parseDocument?renderFormat=all"
        pdf_reader = LayoutPDFReader(llmsherpa_api_url)
        # for idx, pdf_url in enumerate(self._pdf_urls):
        collection_name_sherpa_pdf = (
            "sherpa_pdf_url_" + str(idx) + self.generate_random_string()
        )
        self._pdf_docs_sherpa[collection_name_sherpa_pdf] = {}
        self._pdf_docs_sherpa[collection_name_sherpa_pdf]["pdf"] = pdf_reader.read_pdf(
            self._pdf_name
        )
        self._pdf_docs_sherpa[collection_name_sherpa_pdf][
            "metadata"
        ] = self._metadata.get_dict()
        self._pdf_docs_sherpa[collection_name_sherpa_pdf]["metadata"][
            "pdf_url"
        ] = pdf_url

        # self._pdf_docs_sherpa_tables["sherpa_table_pdf_url_" + str(idx)] = {}
        for table_id, table in enumerate(
            self._pdf_docs_sherpa[collection_name_sherpa_pdf]["pdf"].tables()
        ):
            collection_name_sherpa_table_pdf = (
                "sherpa_table_pdf_url_"
                + str(idx)
                + "_"
                + str(table_id)
                + self.generate_random_string()
            )
            self._pdf_docs_sherpa_tables[collection_name_sherpa_table_pdf] = {}
            self._pdf_docs_sherpa_tables[collection_name_sherpa_table_pdf][
                "text"
            ] = table.to_context_text()
            self._pdf_docs_sherpa_tables[collection_name_sherpa_table_pdf][
                "metadata"
            ] = self._metadata.get_dict()
            self._pdf_docs_sherpa_tables[collection_name_sherpa_table_pdf]["metadata"][
                "pdf_url"
            ] = pdf_url

    def remove_none_fields(self, docs_dict):
        """
        Removes fields with None values from a list of documents.
        Args:
        - docs (list): a list of Document objects.
        """
        print("docs_dict: ", docs_dict)
        for collection_name in docs_dict.keys():
            for doc in docs_dict[collection_name]["docs"]:
                for meta_key in doc[0].metadata:
                    if doc[0].metadata[meta_key] is None:
                        doc[0].metadata[meta_key] = 0

    # def extract_tables_from_pdf(self):
    #    for pdf_url in self._pdf_urls:
    #        pdf_reader = PyMuPDFReader(pdf_url)
    #        pdf_reader.extract_tables()

    def process_urls(self):
        """
        Processes sherpa PDF documents.
        Args:
        - documents (Document): a Document object.
        """
        # self.load_pdfs()
        self._logger.info("Process urls \n")
        for colection_name in self._url_docs.keys():
            self._url_docs[colection_name]["nodes"] = []
            self._collections[colection_name] = []
            parser = SentenceSplitter()
            for doc in self._url_docs[colection_name]["docs"]:
                nodes = parser.get_nodes_from_documents(doc)
                for node in nodes:
                    node.metadata["collection_name"] = colection_name
                    # node.metadata.update(self._url_docs[colection_name]["metadata"])
                    self._nodes.append(node)
                    self._collections[colection_name].append(node)
                    self._url_docs[colection_name]["nodes"].append(node)

    def process_sherpa_pdf(self):
        """
        Processes sherpa PDF documents.
        Args:
        - documents (Document): a Document object.
        """
        # self.load_pdfs()
        self._logger.info("Process sherpa pdf \n")
        for colection_name in self._pdf_docs_sherpa.keys():
            self._pdf_docs_sherpa[colection_name]["nodes"] = []
            self._collections[colection_name] = []
            for chunk in self._pdf_docs_sherpa[colection_name]["pdf"].chunks():
                doc = Document(text=chunk.to_context_text(), extra_info={})
                doc.metadata["collection_name"] = colection_name
                doc.metadata.update(self._pdf_docs_sherpa[colection_name]["metadata"])
                self._nodes.append(doc)
                self._collections[colection_name].append(doc)
                self._pdf_docs_sherpa[colection_name]["nodes"].append(doc)

    def process_normal_pdf(self):
        """
        The function uses the OpenAI object to generate a detailed summary of
        each PDF page and adds the summary to the `nodes` list as a `TextNode`
        object.

        """

        qa_prompt = PromptTemplate(
            """\
            Extract relevant technical information from the provided PDF page. \
            If necessary, provide a translation into English. \

            Identify and summarize the specific data that can be condensed. \
            Put condensed data with all the context information into paragraphs. \
            Put an empty line after each paragraph. \
            IMPORTANT NOTE: avoid using bullet points of any form, instead put all the related data in the paragraphs in sentences. \

            IMPORTANT NOTE: Preserve all technical information data, including any accompanying units of measurement and context. \

            PDF page: '{pdf_page}'
            Answer: \
            """
        )
        self._logger.info("Process normal PDF \n")
        for colection_name in self._pdf_docs.keys():
            self._pdf_docs[colection_name]["nodes"] = []
            self._collections[colection_name] = []
            for doc_idx, doc in enumerate(self._pdf_docs[colection_name]["pdf"]):
                print(doc)
                self._pdf_docs[colection_name]["metadata"] = self._metadata.get_dict()
                if len(doc.text) > 200:
                    self._logger.info(
                        "Ask LLM to summarize page {page} from PDF {pdf} \n".format(
                            page=doc.metadata["source"], pdf=doc.metadata["pdf_url"]
                        )
                    )
                    fmt_qa_prompt = qa_prompt.format(pdf_page=doc.text)
                    response = self._llm.complete(fmt_qa_prompt)
                    for line in response.text.split("\n\n"):
                        node = TextNode(text=line)
                        node.metadata = self._pdf_docs[colection_name]["metadata"]
                        node.metadata["collection_name"] = colection_name
                        self._pdf_docs[colection_name]["nodes"].append(node)
                        self._collections[colection_name].append(node)
                        self._nodes.append(node)
                        self._logger.debug("paragraph: {}".format(line))
                else:
                    node = TextNode(
                        text=doc.text,
                    )
                    node.metadata = self._pdf_docs[colection_name]["metadata"]
                    node.metadata["collection_name"] = colection_name
                    self._nodes.append(node)
                    self._pdf_docs[colection_name]["nodes"].append(node)
                    self._logger.debug("paragraph: {}".format(doc.text))

    def process_sherpa_table(self):
        """
        Processes sherpa table PDF documents.

        """
        from llama_index.prompts import PromptTemplate
        from llama_index.readers.schema.base import Document

        qa_prompt = PromptTemplate(
            """\
            Extract relevant technical information from the provided PDF table. \
            If necessary, provide a translation into English. \

            Identify and summarize the specific data that can be condensed. \
            Put condensed data with all the context information into paragraphs. \
            Put an empty line after each paragraph. \
            IMPORTANT NOTE: avoid using bullet points of any form, instead put all the related data in the paragraphs in sentences. \
                            
            IMPORTANT NOTE: Preserve all technical information data, including any accompanying units of measurement and context. \

            PDF page: '{table}'
            Answer: \
            """
        )

        """            As the last paragraph write a detailed summary for the PDF table with all the technical information and values in a one paragraph, \
            including any accompanying units of measurement and context. \
        """
        self._logger.info("Process sherpa table \n")
        for colection_name in self._pdf_docs_sherpa_tables.keys():
            self._pdf_docs_sherpa_tables[colection_name]["nodes"] = []
            self._collections[colection_name] = []
            self._logger.info("Process sherpa table PDF \n")
            table_text = self._pdf_docs_sherpa_tables[colection_name]["text"]
            fmt_qa_prompt = qa_prompt.format(table=table_text)
            self._logger.info("Ask LLM to summarize table\n")
            response = self._llm.complete(fmt_qa_prompt)
            lines = str(response.text).split("\n\n")
            # for i in lines:
            #    if not i:
            #        lines.remove(i)
            for i in range(len(lines)):
                if lines[i]:
                    text = lines[i]
                    doc = Document(
                        text=text,
                        extra_info={},
                    )
                    doc.metadata = self._pdf_docs_sherpa_tables[colection_name][
                        "metadata"
                    ]
                    doc.metadata["collection_name"] = colection_name
                    self._nodes.append(doc)
                    self._collections[colection_name].append(doc)
                    self._pdf_docs_sherpa_tables[colection_name]["nodes"].append(doc)
                    self._logger.debug("text: {}".format(text))

    def get_collections(self):
        """
        Returns a list of collections.
        """
        return self._collections
