import re
from llmsherpa.readers import LayoutPDFReader
from llama_index import download_loader, Document
from llama_hub.file.pymu_pdf.base import PyMuPDFReader
from llama_index.prompts import PromptTemplate
from llama_index.schema import TextNode


class DocumentPreprocessor:

    """
    The DocumentPreprocessor class is responsible for processing different types of documents, including normal PDFs and Sherpa table PDFs.
    It uses an OpenAI object to summarize the documents and create a dictionary of collections.
    The class contains methods for clearing the nodes list, processing normal PDFs, processing Sherpa table PDFs, and creating a collection dictionary.
    The methods take in arguments such as an OpenAI object and a list of Document objects.
    The class also contains docstrings for each method that describe their functionality and input parameters.
    """

    def __init__(self, logger, url, pdf_filenames, collection_name):
        """
        Initializes a DocumentPreprocessor object.
        Args:
        - logger (Logger): a logger object.
        - url (str): a URL string.
        - pdf_filenames (list): a list of PDF file names.
        - collection_name (str): the name of the collection.
        Attributes:
        - logger (Logger): a logger object.
        - nodes (list): a list of TextNode objects.
        - url (str): a URL string.
        - pdf_filenames (list): a list of PDF file names.
        - collection_name (str): the name of the collection.
        """
        self.logger = logger
        self.nodes = []
        self.url = url
        self.pdf_filenames = pdf_filenames
        self.collection_name = collection_name

    def get_nodes(self):
        return self.nodes

    def load_url_documents(self):
        """
        Loads documents from URLs.
        Returns:
        - url_docs (list): a list of Document objects.
        """
        self.logger.info("--------------------- Load urls \n")
        ReadabilityWebPageReader = download_loader("ReadabilityWebPageReader")
        loader_url = ReadabilityWebPageReader()
        if self.url:
            docs = loader_url.load_data(url=self.url)
            doc = docs[0]
            doc.metadata["file_path"] = self.url
            t = re.sub("\n\n", " ", doc.text)
            doc.text = t
            return [doc]
        return []

    def load_pdf_documents(self):
        """
        This function is responsible for loading PDF documents and returning two lists of `Document` objects: `pdf_docs` and `pdf_docs_sherpa`.
        The function first initializes two objects: `loader_pdf` and `pdf_reader`.
        `loader_pdf` is an instance of the `PyMuPDFReader` class, which is used to load PDF files from the local file system.
        `pdf_reader` is an instance of the `LayoutPDFReader` class, which is used to read PDF files and extract their layout information using the LLMSherpa API.

        The function then initializes two empty lists: `pdf_docs` and `pdf_docs_sherpa`.
        These lists will be used to store the `Document` objects that are created from the PDF files.

        The function then iterates over the list of PDF file names that was passed to the `DocumentPreprocessor` object during initialization.
        For each file name, the function first loads the PDF file using `loader_pdf.load(file_path=file)`.
        This returns a `Document` object that represents the PDF file.
        The function then uses `pdf_reader.read_pdf(file)` to extract the layout information from the PDF file using the LLMSherpa API.
        This returns a `Document` object that represents the PDF file with layout information.

        The function then appends the two `Document` objects to the `pdf_docs` and `pdf_docs_sherpa` lists, respectively.

        Finally, the function returns the two lists of `Document` objects: `pdf_docs` and `pdf_docs_sherpa`.

        Returns:
        - pdf_docs (list): a list of Document objects.
        - pdf_docs_sherpa (list): a list of Document objects.
        """
        loader_pdf = PyMuPDFReader()
        llmsherpa_api_url = "https://readers.llmsherpa.com/api/document/developer/parseDocument?renderFormat=all"
        pdf_reader = LayoutPDFReader(llmsherpa_api_url)
        pdf_docs = []
        pdf_docs_sherpa = []
        for file in self.pdf_filenames:
            self.logger.info(
                "--------------------- Load local PDF document {} \n".format(file)
            )
            pdf_docs.append(loader_pdf.load(file_path=file))
            self.logger.info(
                "--------------------- Ask Sherpa to analyze PDF document\n"
            )
            pdf_docs_sherpa.append(pdf_reader.read_pdf(file))
        return pdf_docs, pdf_docs_sherpa

    def remove_none_fields(self, docs):
        """
        Removes fields with None values from a list of documents.
        Args:
        - docs (list): a list of Document objects.
        """
        for doc in docs:
            for key in doc.metadata:
                if doc.metadata[key] is None:
                    doc.metadata[key] = 0

    def load_documents(self):
        """
        Loads documents from different sources.
        Returns:
        - url_docs (list): a list of Document objects.
        - pdf_docs (list): a list of Document objects.
        - pdf_docs_sherpa (list): a list of Document objects.
        """
        url_docs = self.load_url_documents()
        pdf_docs, pdf_docs_sherpa = self.load_pdf_documents()
        self.remove_none_fields(url_docs)
        return url_docs, pdf_docs, pdf_docs_sherpa

    def process_sherpa_pdf(self, documents):
        """
        Processes sherpa PDF documents.
        Args:
        - documents (Document): a Document object.
        """
        for chunk in documents.chunks():
            self.nodes.append(Document(text=chunk.to_context_text(), extra_info={}))

    def clear_nodes(self):
        """
        Clears the nodes list.
        """
        self.nodes = []

    def process_normal_pdf(self, llm, documents):
        """
        The function uses the OpenAI object to generate a detailed summary of each PDF page and adds the summary to the `nodes` list as a `TextNode` object.


        The function prompts the user to read each PDF page and prepare a detailed summary of it using a `PromptTemplate` object.
        The prompt instructs the user to start each sentence with a new line, retain all the technical specification data, and translate to English before if required.

        The function then uses the OpenAI object to generate a response to the prompt.
        The response is split into lines and each line is added to the `nodes` list as a `TextNode` object.
        The `TextNode` object contains the text of the line and the metadata of the source document.
        The `nodes` list is an attribute of the `DocumentPreprocessor` class that stores a list of `TextNode` objects.

        Args:
        - llm (OpenAI): an OpenAI object.
        - documents (list): a list of Document objects.
        """
        qa_prompt2 = PromptTemplate(
            """\
            Read this PDF page and summarize semantically in form of sentences. \
            Start each sentence with a new line. \
            Retain all the technical specification data. \
            Translate to english before if required. \
            PDF page: '{pdf_page}'
            Answer: \
            """
        )
        qa_prompt = PromptTemplate(
            """\
            Read this PDF page and prepare a detailed summary of it. Start each sentence with new line. \
            Retain all the technical specification data. \
            Translate to english before if required. \
            PDF page: '{pdf_page}'
            Answer: \
            """
        )

        for doc_idx, doc in enumerate(documents):
            if len(doc.text) > 200:
                self.logger.info(
                    "--------------------- Ask LLM to summarize page {page} from PDF {pdf} \n".format(
                        page=doc_idx, pdf=doc.metadata["file_path"]
                    )
                )
                fmt_qa_prompt = qa_prompt.format(pdf_page=doc.text)
                response = llm.complete(fmt_qa_prompt)
                for line in response.text.splitlines():
                    src_doc = documents[doc_idx]
                    node = TextNode(
                        text=line,
                    )
                    node.metadata = src_doc.metadata
                    self.nodes.append(node)
                    self.logger.debug("text: {}".format(line))

    def process_sherpa_table(self, llm, documents):
        """
        Processes sherpa table PDF documents.
        This function processes a Sherpa table PDF document by using the llm object to generate a detailed summary of the table.
        The summary is generated by prompting the user to read the table and prepare a detailed summary of it.
        The table is then added to the nodes list as a Document object with the generated summary as its text.
        The nodes list is an attribute of the DocumentPreprocessor class that stores a list of Document objects.

        Args:
        - llm (OpenAI): an OpenAI object.
        - documents (Document): a Document object.
        """
        from llama_index.prompts import PromptTemplate
        from llama_index.readers.schema.base import Document

        qa_prompt = PromptTemplate(
            """\
            read this table and prepare a detailed summary of it:
            Table: '{table}'
            Answer: \
            """
        )

        self.logger.info("--------------------- Process sherpa table PDF \n")
        table_text = documents.to_context_text()
        fmt_qa_prompt = qa_prompt.format(table=table_text)
        self.logger.info("--------------------- Ask LLM to summarize table\n")
        response = llm.complete(fmt_qa_prompt)
        lines = str(response.text).splitlines()
        for i in lines:
            if not i:
                lines.remove(i)
        for i in range(len(lines)):
            if lines[i]:
                text = lines[i]
                self.nodes.append(
                    Document(
                        text=text,
                        extra_info={},
                    )
                )
                self.logger.debug("text: {}".format(text))

    def create_collection_dict(self) -> dict:
        """
        This function creates a dictionary of collections from the loaded documents.
        The function takes no arguments, but it relies on the load_documents method to load the documents from the specified URLs and PDF files.
        The loaded documents are then used to create the collection dictionary.
        The function first creates an empty dictionary called collection_dict.
        It then checks if there are any URL documents loaded, and if so, it adds the first URL document to the dictionary under the key self.collection_name + "_url1".
        Next, the function iterates over the PDF filenames and the corresponding loaded PDF documents.
        For each PDF file, it adds each document to the dictionary under a unique key that includes the collection name, the PDF index, and the document index.
        The function then adds the Sherpa table PDF documents to the dictionary under the key self.collection_name + "_pdf_sherpa_" + str(idx).
        It also iterates over each table in each Sherpa table PDF document and adds each table to the dictionary under a unique key that includes the collection name, the PDF index, and the table index.

        Finally, the function returns the collection_dict dictionary.
        The function returns a dictionary of collections, where each collection is a list of documents.
        The keys of the dictionary are unique identifiers for each document, which include the collection name, the PDF index (if applicable), and the document or table index. ▌

        Returns:
        - collection_dict (dict): a dictionary of collections.
        """

        url_docs, pdf_docs, pdf_docs_sherpa = self.load_documents()
        collection_dict = {}
        if url_docs:
            collection_dict[self.collection_name + "_url1"] = [url_docs[0]]
        # collection_dict[self.collection_name + "_url2"] = [url_docs[1]]
        for idx, name in enumerate(self.pdf_filenames):
            for i in range(len(pdf_docs[0])):
                collection_dict[self.collection_name + "_pdf_" + str(idx) + str(i)] = [
                    pdf_docs[idx][i]
                ]

            collection_dict[
                self.collection_name + "_pdf_sherpa_" + str(idx)
            ] = pdf_docs_sherpa[idx]

            for table_id, table in enumerate(pdf_docs_sherpa[idx].tables()):
                collection_dict[
                    self.collection_name
                    + "_pdf_sherpa_table_"
                    + str(idx)
                    + str(table_id)
                ] = pdf_docs_sherpa[idx].tables()[table_id]

        return collection_dict
