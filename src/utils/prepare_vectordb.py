from langchain.vectorstores import Chroma
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from typing import List
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document


class PrepareVectorDB:
    """
    TODO: Rewrite this comment
    """

    def __init__(
            self,
            data_directory_texts: str,
            data_directory_pdfs: str,
            persist_directory: str,
            embedding_model_engine: str,
            chunk_size: int,
            chunk_overlap: int
    ) -> None:

        self.embedding_model_engine = embedding_model_engine
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # separators=["\n\n", "\n", " ", ""]
        )
        """Other options: CharacterTextSplitter, TokenTextSplitter, etc."""
        self.data_directory_texts = data_directory_texts
        self.data_directory_pdfs = data_directory_pdfs
        self.persist_directory = persist_directory
        self.embedding = OpenAIEmbeddings()

    # def __load_all_documents(self) -> List:
    #     """
    #     Load all documents from the specified directory or directories.
    #
    #     Returns:
    #         List: A list of loaded documents.
    #     """
    #     doc_counter = 0
    #     if isinstance(self.data_directory, list):
    #         print("Loading the uploaded documents...")
    #         docs = []
    #         for doc_dir in self.data_directory:
    #             docs.extend(PyPDFLoader(doc_dir).load())
    #             doc_counter += 1
    #         print("Number of loaded documents:", doc_counter)
    #         print("Number of pages:", len(docs), "\n\n")
    #     else:
    #         print("Loading documents manually...")
    #         document_list = os.listdir(self.data_directory)
    #         docs = []
    #         for doc_name in document_list:
    #             docs.extend(PyPDFLoader(os.path.join(
    #                 self.data_directory, doc_name)).load())
    #             doc_counter += 1
    #         print("Number of loaded documents:", doc_counter)
    #         print("Number of pages:", len(docs), "\n\n")
    #
    #     return docs

    def __load_all_texts(self):
        '''
        Loads all the txt files in the directory and makes a Document out of each with the entire contents of the short guide.

        :param directory_path of the txt files
        :return: List of Document objects
        '''

        docs = []
        # Iterate through each file in the specified directory
        for filename in os.listdir(self.data_directory_texts):
            # Check if the file is a .txt file
            if filename.endswith('.txt'):
                # Construct the full file path
                file_path = os.path.join(self.data_directory_texts, filename)
                # Open and read the file
                with open(file_path, 'r', encoding='utf-8') as file:
                    contents = file.read()
                    doc = Document(page_content=contents,
                                   metadata={
                                       "source": filename,
                                       # "description": ... # TODO: Maybe add description of guide here, perhaps first line of the txt file
                                   })
                    docs.append(doc)

        return docs

    def __load_all_pdfs(self):
        """
        Load all pdf documents from the specified directory or directories.

        Returns:
            List: A list of loaded pdf documents.
        """
        doc_counter = 0
        if isinstance(self.data_directory_pdfs, list):
            print("Loading the uploaded pdf documents...")
            docs = []
            for doc_dir in self.data_directory_pdfs:
                docs.extend(PyPDFLoader(doc_dir).load())
                doc_counter += 1
            print("Number of loaded pdf documents:", doc_counter)
            print("Number of pages:", len(docs), "\n\n")
        else:
            print("Loading documents manually...")
            document_list = os.listdir(self.data_directory_pdfs)
            docs = []
            for doc_name in document_list:
                docs.extend(PyPDFLoader(os.path.join(
                    self.data_directory_pdfs, doc_name)).load())
                doc_counter += 1
            print("Number of loaded pdf documents:", doc_counter)
            print("Number of pages:", len(docs), "\n\n")

        return docs

    def __chunk_documents(self, docs: List) -> List:
        """
        Chunk the loaded documents using the specified text splitter.

        Parameters:
            docs (List): The list of loaded documents.

        Returns:
            List: A list of chunked documents.

        """
        print("Chunking documents...")
        chunked_documents = self.text_splitter.split_documents(docs)
        print("Number of chunks:", len(chunked_documents), "\n\n")
        return chunked_documents

    def prepare_and_save_vectordb(self):
        """
        Load, chunk, and create a VectorDB with OpenAI embeddings, and save it.

        Returns:
            Chroma: The created VectorDB.
        """
        # Todo: Fix this part, missing embedding model when loaded DB from persist directory
        # if os.path.exists(self.persist_directory):
        #     print("Vector DB already initialized")
        #     return Chroma(persist_directory=self.persist_directory)
        print("Preparing vectordb...")
        docs_texts = self.__load_all_texts()
        docs_pdfs = self.__load_all_pdfs()
        chunked_pdf_documents = self.__chunk_documents(docs_pdfs)
        documents = chunked_pdf_documents + docs_texts
        vectordb = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding,
            persist_directory=self.persist_directory
        )
        print("VectorDB is created and saved.")
        print("Number of vectors in vectordb:", vectordb._collection.count(), "\n\n")
        return vectordb