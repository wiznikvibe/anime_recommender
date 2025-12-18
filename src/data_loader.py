import pandas as pd 
from src.utils.logger import logging
from src.utils.custom_exceptions import AnimeRecommendationException
import sys

class AnimeDataLoader: 
    def __init__(self, original_csv: str, processed_csv: str):
        self.original_csv = original_csv
        self.processed_csv = processed_csv
        
    def load_and_process(self):
        try:
            logging.info("Initiate Data Loading, processing CSV file...")
            df = pd.read_csv(self.original_csv, encoding='utf-8', on_bad_lines='skip').dropna()
            required_columns = {'Name', 'Genres', 'sypnopsis'}
            missing_columns = required_columns - set(df.columns)
            if missing_columns:
                logging.info(f"Missing Columns: {missing_columns}")
                raise ValueError(f"Data Missing Columns: {missing_columns}")

            df["combined_info"] = (
                "Title: "
                + df["Name"].astype(str)
                + " Overview: "
                + df["sypnopsis"].astype(str)
                + " Genres: "
                + df["Genres"].astype(str)
            )

            
            df[['combined_info']].to_csv(self.processed_csv, index=False, encoding='utf-8')
            return self.processed_csv
            
        except Exception as e:
            logging.info(f"{AnimeRecommendationException(e, sys)}")
            raise AnimeRecommendationException(e,sys)