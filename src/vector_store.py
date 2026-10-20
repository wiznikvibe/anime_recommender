from src.utils.logger import logging
from src.utils.custom_exceptions import AnimeRecommendationException
import sys
import os
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from config.config import EMBEDDING_MODEL_NAME

load_dotenv()

class VectorStoreBuilder:
    def __init__(self, csv_path: str, persist_dir: str="chroma_db"):
        self.csv_path = csv_path
        self.persist_dir = persist_dir
        self.embedding_generator = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    def build_and_save_vector_store(self):
        try:
            logging.info("Building a new vector store")
            loader = CSVLoader(
                file_path=self.csv_path,
                encoding='utf-8',
                metadata_columns=[]
            )
            logging.info("Loading the documents for splitting...")
            data = loader.load()
            splitter = CharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
            documents = splitter.split_documents(data)
            logging.info("document splits generated successfully! generating embeddings and laoding to the vector store")
            db = Chroma.from_documents(documents, self.embedding_generator, persist_directory=self.persist_dir)
            
        except Exception as e:
            logging.info(f"{AnimeRecommendationException(e, sys)}")
            raise AnimeRecommendationException(e, sys)
        
    def load_vector_store(self):
        try:
            logging.info("Loading the Existing Index...")
            return Chroma(persist_directory=self.persist_dir,embedding_function=self.embedding_generator)
        except Exception as e:
            logging.info(f"{AnimeRecommendationException(e, sys)}")
            raise AnimeRecommendationException(e, sys)