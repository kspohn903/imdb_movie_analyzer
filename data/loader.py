import os
import pandas as pd
from .schema import TITLE_BASICS_SCHEMA, TITLE_RATINGS_SCHEMA, TITLE_AKAS_SCHEMA

try:
    import dask.dataframe as dd
    USE_DASK = True
except (ImportError, TypeError):
    USE_DASK = False

class IMDBLoader:
    def __init__(self, data_path):
        self.path = data_path

    def load_basics(self):
        if USE_DASK:
            df = dd.read_csv(
                os.path.join(self.path, "title.basics.tsv"),
                sep='\t',
                dtype=TITLE_BASICS_SCHEMA,
                na_values='\\N',
                blocksize="64MB"
            )
            df['startYear'] = dd.to_numeric(df['startYear'], errors='coerce')
        else:
            df = pd.read_csv(
                os.path.join(self.path, "title.basics.tsv"),
                sep='\t',
                dtype=TITLE_BASICS_SCHEMA,
                na_values='\\N'
            )
            df['startYear'] = pd.to_numeric(df['startYear'], errors='coerce')
        return df

    def load_ratings(self):
        if USE_DASK:
            return dd.read_csv(
                os.path.join(self.path, "title.ratings.tsv"),
                sep='\t',
                dtype=TITLE_RATINGS_SCHEMA
            )
        else:
            return pd.read_csv(
                os.path.join(self.path, "title.ratings.tsv"),
                sep='\t',
                dtype=TITLE_RATINGS_SCHEMA
            )

    def load_merged_lake(self):
        """Unified empirical dataset for ANOVA/Regression."""
        basics = self.load_basics()
        ratings = self.load_ratings()
        return basics.merge(ratings, on='tconst', how='inner')
