from src.data_loader import AnimeDataLoader
from src.vector_store import VectorStoreBuilder
from dotenv import load_dotenv
from src.utils.logger import logging 
from src.utils.custom_exceptions import AnimeRecommendationException
import os
import sys
load_dotenv()

def main():
    try:
        logging.info("Starting to build pipeline...")

        loader = AnimeDataLoader("data/anime_with_synopsis.csv" , "data/anime_updated.csv")
        processed_csv = loader.load_and_process()

        logging.info("Data loaded and processed...")

        vector_builder = VectorStoreBuilder(processed_csv)
        vector_builder.build_and_save_vector_store()

        logging.info("Vector store Built sucessfully....")

        logging.info("Pipeline built sucessfully....") 
    except Exception as e:
        raise AnimeRecommendationException(e, sys)
    
    
if __name__=="__main__":
     main()
