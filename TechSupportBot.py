import time
import os
from typing import List, Tuple, Set
from dotenv import load_dotenv, find_dotenv
from pprint import pprint, pformat

from langchain import hub
from langchain_openai  import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import AIMessage, HumanMessage, SystemMessage, Document
from langchain.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader

import asyncio

import tiktoken
load_dotenv(find_dotenv())

persist_directory = 'data/vectorDB/TechSupportBotDB'


def sim_msg():
    time.sleep(2)  # Sleep for 2 seconds to simulate a delay
    return "Result from bot"


def create_documents_from_txt_guides(directory_path):
    '''
    Itterates over all the txt files in the directory and makes a Document out of each with the entire contents of the short guide.

    :param directory_path of the txt files
    :return: List of Document objects
    '''
    # Specify your directory path here
    documents = []
    # Iterate through each file in the specified directory
    for filename in os.listdir(directory_path):
        # Check if the file is a .txt file
        if filename.endswith('.txt'):
            # Construct the full file path
            file_path = os.path.join(directory_path, filename)
            # Open and read the file
            with open(file_path, 'r', encoding='utf-8') as file:
                contents = file.read()
                # Now you have the file name (filename) and its contents (contents)
                # You can perform your operations here
                doc = Document(page_content=contents,
                               metadata={
                                   "source": filename,
                                   # "Title": row['Title'] # TODO: Maybe add description of guide here, perhaps first line of the txt file
                               })
                documents.append(doc)

    return documents

def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    num_tokens = len(encoding.encode(string))
    return num_tokens

def load_pdfs(data_directory):
    """
    Load all documents from the specified directory or directories.

    Returns:
        List: A list of loaded documents.
    """
    doc_counter = 0
    if isinstance(data_directory, list):
        print("Loading the uploaded documents...")
        docs = []
        for doc_dir in data_directory:
            docs.extend(PyPDFLoader(doc_dir).load())
            doc_counter += 1
        print("Number of loaded documents:", doc_counter)
        print("Number of pages:", len(docs), "\n\n")
    else:
        print("Loading documents manually...")
        document_list = os.listdir(data_directory)
        docs = []
        for doc_name in document_list:
            docs.extend(PyPDFLoader(os.path.join(
                data_directory, doc_name)).load())
            doc_counter += 1
        print("Number of loaded documents:", doc_counter)
        print("Number of pages:", len(docs), "\n\n")
    print(docs)
    return docs

def process_pdfs(data_directory):
    """
    Chunk the loaded documents using the specified text splitter.

    Parameters:
        docs (List): The list of loaded documents.

    Returns:
        List: A list of chunked documents.

    """
    docs = load_pdfs(data_directory)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    print("Chunking documents...")
    chunked_documents = text_splitter.split_documents(docs)
    print("Number of chunks:", len(chunked_documents), "\n\n")
    return chunked_documents

def get_embedded_data():
    if not os.path.exists(persist_directory):
        return "Not initialized"
    else:
        vectordb = Chroma(persist_directory=persist_directory, embedding_function=OpenAIEmbeddings())
        doc_set = set()
        for doc in vectordb.get()["metadatas"]:
            doc_set.add(os.path.basename(str(doc['source'])))
        ret_list = ''
        for i, doc in enumerate(doc_set):
            ret_list += str(i+1) + '. ' + str(doc) + '\n'

        ret_list = "These are the guides I know: \n\n" + ret_list
        return ret_list

async def invoke_prompt(question):
    # gpt-4, gpt-4-turbo-preview, gpt-3.5-turbo
    chat_3 = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0)
    chat_4 = ChatOpenAI(model_name='gpt-4', temperature=0)
    chat_4t = ChatOpenAI(model_name='gpt-4-turbo-preview', temperature=0)

    if not os.path.exists(persist_directory):
        # Creating Documents and embedding them
        txt_documents = create_documents_from_txt_guides('data/docs/texts')
        pdf_documents = process_pdfs("data/docs/PDFs")
        documents = txt_documents + pdf_documents

        vectordb = Chroma.from_documents(
            documents=documents,
            embedding=OpenAIEmbeddings(),
            persist_directory=persist_directory
        )
        print("db created")
    else:
        vectordb = Chroma(persist_directory=persist_directory, embedding_function=OpenAIEmbeddings())
        print("db loaded")

    retriever = vectordb.as_retriever(search_kwargs={"k": 4})  # default 4
    # retriever = vectordb.as_retriever()
    # question = "How do I update my NVR?"
    docs = retriever.get_relevant_documents(question)
    for i, doc in enumerate(docs):
        print(f"Doc #{i}: {doc.metadata}\n")
    retrieved_docs_page_content = [str(x.page_content) + "\n\n" for x in docs]
    retrieved_docs_str = "# Retrieved content:\n\n" + str(retrieved_docs_page_content)
    prompt = retrieved_docs_str + "\n\n" + question

    llm_system_role = '''
    You are a helpful and serviceable customer support bot a company called Provision-ISR which responds to clients in a helpful manner. 
    You'll receive a prompt that includes retrieved content from the vectorDB based on the user's question, and the source.
    Your task is to respond to the user's new question using the information from the vectorDB without relying on your own knowledge.
    You will receive a prompt with the the following format:

    # Retrieved content number:\n
    Content\n\n
    Source\n\n

    # User question:\n
    New question

    '''
    response = await chat_4t.ainvoke(llm_system_role + prompt)

    return response.content
# async def main():
#     response = await invoke_prompt("How do I add a camera to the NVR?")
#     print(response)
#
# if __name__ == "__main__":
#     asyncio.run(main())