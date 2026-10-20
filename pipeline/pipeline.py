from src.vector_store import VectorStoreBuilder
from src.recommender import AnimeRecommender
from config.config import GROQ_API_KEY,MODEL_NAME
import os
import sys
from src.utils.logger import logging
from src.utils.custom_exceptions import AnimeRecommendationException


class AnimeRecommendationPipeline:
    def __init__(self, persist_dir="chroma_db"):
        try:
            logging.info("Initializing the Recommendation Engine")
            logging.info(f"Using Groq model: {MODEL_NAME}")
            vector_builder = VectorStoreBuilder(csv_path="", persist_dir=persist_dir)
            retriever = vector_builder.load_vector_store().as_retriever()
            self.recommender = AnimeRecommender(retriever=retriever, api_key=GROQ_API_KEY, model_name=MODEL_NAME)
        except Exception as e:
            raise AnimeRecommendationException(e, sys)
        
    def recommend(self, query: str) -> str:
        try: 
            logging.info(f"Recieved User Query: {query}")
            recommendations = self.recommender.get_recommendation(query)
            return recommendations 
        except Exception as e:
            raise AnimeRecommendationException(e, sys)