import os
import random
import re
import string
import subprocess
from pathlib import Path

from llama_hub.file.pymu_pdf.base import PyMuPDFReader
from llama_hub.file.unstructured import UnstructuredReader
from llama_index import Document, download_loader
from llama_index.node_parser import SentenceSplitter
from llama_index.prompts import PromptTemplate
from llama_index.readers.schema.base import Document
from llama_index.schema import TextNode
from llmsherpa.readers import LayoutPDFReader

from metadata import Metadata

# TODO(qu): Consider using this for splitting code
# from llama_index.text_splitter import CodeSplitter


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
        self._nodes = []
        self._embedding = None
        self._collections = {}
        self._url_docs = {}
        self._pdf_docs = {}
        self._pdf_docs_sherpa = {}
        self._pdf_docs_sherpa_tables = {}

        self._pdf_name = "temp.pdf"
        self._load_sherpa = load_sherpa

    def generate_random_string(self, length=30):
        return str(
            "".join(
                random.choice(string.ascii_uppercase + string.digits)
                for _ in range(length)
            )
        )

    def path_generator(self, target_directory):
        url_list = []
        for root, _, files in os.walk(target_directory):
            for file in files:
                if any(ext in file for ext in [".html", ".htm"]):
                    url_list.append(f"{root}/{file}")
        return url_list  # returns a list of path for each file in the director

    def get_text_from_html(self, file_path):
        loader = UnstructuredReader()
        documents = loader.load_data(file=Path(file_path))
        return documents  # returns text and source url (metadata) from an HTML fil

    def load_from_html(self, html):
        web_page_reader = download_loader("SimpleWebPageReader")
        url_loader = web_page_reader()
        docs = url_loader.load_data(url=html)
        return docs  # returns text and source url (metadata) from an HTML file

    def load_urls_from_path(self, urls):
        """
        Loads documents from URLs.
        """
        path = "tmp" + self.generate_random_string(3)
        subprocess.run(["mkdir", path], shell=False, check=True)
        for url in urls:
            _docs = []
            collection_name = "web_url_" + self.generate_random_string()
            self._url_docs[collection_name] = {}
            self._url_docs[collection_name]["docs"] = []
            f = open(path + "/" + "test.html", "w")
            self._logger.info(f"Load url {url} in folder {path}\n")
            # google-chrome --headless --dump-dom --virtual-time-budget=10000 --timeout=10000 --run-all-compositor-stages-before-draw --disable-gpu --user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36" "https://franka.de/production" > file2.html
            command = [
                "google-chrome",
                "--headless",
                "--dump-dom",
                "--virtual-time-budget=10000",
                "--timeout=10000",
                "--run-all-compositor-stages-before-draw",
                "--disable-gpu",
                '--user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36"',
                url,
            ]
            out = subprocess.check_output(command)
            f.write(out.decode())
            f.close()
            # subprocess.run(["wget", "-q", "-r", "-l1", "-nd", "-P", path, url])
            for file_path in self.path_generator(path):
                _docs.append(self.get_text_from_html(file_path))
            for idx, docs in enumerate(_docs):
                self._url_docs[collection_name]["text"] = re.sub(
                    "\n\n", " ", docs[0].text
                )
                self._url_docs[collection_name]["text"] = re.sub(
                    "{{", " ", self._url_docs[collection_name]["text"]
                )
                self._url_docs[collection_name]["text"] = re.sub(
                    "}}", " ", self._url_docs[collection_name]["text"]
                )
                self._url_docs[collection_name]["text"] = re.sub(
                    "}", " ", self._url_docs[collection_name]["text"]
                )
                self._url_docs[collection_name]["text"] = re.sub(
                    "{", " ", self._url_docs[collection_name]["text"]
                )
                docs[0].text = self._url_docs[collection_name]["text"]
                self._url_docs[collection_name]["docs"].append(docs)
                self._url_docs[collection_name]["metadata"] = self._metadata.get_dict()
                self._url_docs[collection_name]["metadata"]["web_url"] = url
                for doc in docs:
                    doc.metadata.update(self._url_docs[collection_name]["metadata"])
            self.remove_none_fields(self._url_docs)
            subprocess.run(["rm", path + "/test.html"], check=True)
        subprocess.run(["rm", "-r", path])

    def load_pdfs(self):
        """
        This function is responsible for loading PDF documents
        """
        loader_pdf = PyMuPDFReader()
        for idx, pdf_url in enumerate(self._pdf_urls):
            if pdf_url:
                self._logger.info(f"Load PDF document {pdf_url} \n")
                subprocess.run(["wget", "-O", self._pdf_name, pdf_url])
                collection_name = "pdf_url_" + str(idx) + self.generate_random_string()
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
                subprocess.run(["rm", "", self._pdf_name], check=True)

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
            self._pdf_docs_sherpa_tables[collection_name_sherpa_table_pdf]["metadata"][
                "page_idx"
            ] = (
                int(table.page_idx) + 1
            )  # pylint: disable=superfluous-parens

    def remove_none_fields(self, docs_dict):
        """
        Removes fields with None values from a list of documents.
        Args:
        - docs (list): a list of Document objects.
        """
        for collection_name in docs_dict.keys():
            for doc in docs_dict[collection_name]["docs"]:
                for meta_key in doc[0].metadata:
                    if doc[0].metadata[meta_key] is None:
                        doc[0].metadata[meta_key] = 0

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
            # parser = SentenceSplitter()
            node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=20)
            for doc in self._url_docs[colection_name]["docs"]:
                nodes = node_parser.get_nodes_from_documents(doc)
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
                doc.metadata["page_idx"] = int(chunk.page_idx) + 1
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
            for _, doc in enumerate(self._pdf_docs[colection_name]["pdf"]):
                # self._pdf_docs[colection_name]["metadata"] = self._metadata.get_dict()
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
                        node.metadata["page_idx"] = int(doc.metadata["source"]) + 1
                        self._pdf_docs[colection_name]["nodes"].append(node)
                        self._collections[colection_name].append(node)
                        self._nodes.append(node)
                        self._logger.debug(f"paragraph: {line}")
                else:
                    node = TextNode(
                        text=doc.text,
                    )
                    node.metadata = self._pdf_docs[colection_name]["metadata"]
                    node.metadata["collection_name"] = colection_name
                    node.metadata["page_idx"] = int(doc.metadata["source"]) + 1
                    self._nodes.append(node)
                    self._pdf_docs[colection_name]["nodes"].append(node)
                    self._logger.debug(f"paragraph: {doc.text}")

    def process_sherpa_table(self):
        """
        Processes sherpa table PDF documents.

        """
        qa_prompt = PromptTemplate(
            """\
            Extract relevant technical information from the provided PDF table. \
            If necessary, provide a translation into English. \

            Identify and summarize the specific data that can be compound. \
            Put compounded data with all the context information into paragraphs. \
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
        _collection_name = "sherpa_table_pdf_url_" + self.generate_random_string()
        self._logger.info("Number of tables: " + str(len(self._pdf_docs_sherpa_tables)))
        for colection_name in self._pdf_docs_sherpa_tables.keys():
            self._pdf_docs_sherpa_tables[colection_name]["nodes"] = []
            # self._collections[colection_name] = []
            self._collections[_collection_name] = []
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
                    # doc.metadata["collection_name"] = colection_name
                    doc.metadata["collection_name"] = _collection_name
                    self._nodes.append(doc)
                    # self._collections[colection_name].append(doc)
                    self._collections[_collection_name].append(doc)
                    self._pdf_docs_sherpa_tables[colection_name]["nodes"].append(doc)
                    self._logger.debug(f"text: {text}")

    def get_collections(self):
        """
        Returns a list of collections.
        """
        return self._collections
