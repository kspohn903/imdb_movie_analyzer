import pandas as pd
import os
import urllib.request
import gzip
import numpy as np
import io

class BasicStatisticsVisualizer():
    def __init__(self, root_dir="/home/kspohn/datasets/imdb_movie_analyzer"):
        self.file_directory = os.path.join(root_dir, "processed_data")
        if not os.path.exists(self.file_directory):
            os.makedirs(self.file_directory)
        
        self.dataset_filenames = {
            "title_basics": {
                "url": "https://datasets.imdbws.com/title.basics.tsv.gz",
                "file": os.path.join(self.file_directory, "title.basics.tsv.gz"),
                "df_name": "title_basics",
            },
            "title_ratings": {
                "url": "https://datasets.imdbws.com/title.ratings.tsv.gz",
                "file": os.path.join(self.file_directory, "title.ratings.tsv.gz"),
                "df_name": "title_ratings",
            },
            "title_episodes": {
                "url": "https://datasets.imdbws.com/title.episode.tsv.gz",
                "file": os.path.join(self.file_directory, "title.episode.tsv.gz"),
                "df_name": "title_episodes",
            },
            "title_crews": {
                "url": "https://datasets.imdbws.com/title.crew.tsv.gz",
                "file": os.path.join(self.file_directory, "title.crew.tsv.gz"),
                "df_name": "title_crews"
            },
            "title_principals": {
                "url": "https://datasets.imdbws.com/title.principals.tsv.gz",
                "file": os.path.join(self.file_directory, "title.principals.tsv.gz"),
                "df_name": "title_principals",
            },
            "title_akas": {
                "url": "https://datasets.imdbws.com/title.akas.tsv.gz",
                "file": os.path.join(self.file_directory, "title.akas.tsv.gz"),
                "df_name": "title_akas",
            },
            "name_basics": {
                "url": "https://datasets.imdbws.com/name.basics.tsv.gz",
                "file": os.path.join(self.file_directory, "name.basics.tsv.gz"),
                "df_name": "name_basics",
            }
        }

    def download_file(self, file_alias, delimiter='\t', encoding_fmt='utf-8'):
        url = self.dataset_filenames[file_alias]["url"]
        print(f"Downloading {file_alias} from {url}...")
        response = urllib.request.urlopen(url)
        compressed_file = response.read()
        uncompressed_file = gzip.decompress(compressed_file)
        
        file_contents = uncompressed_file.decode(encoding_fmt)
        df = pd.read_csv(io.StringIO(file_contents), delimiter=delimiter, low_memory=False)
        return df

    def get_df_info(self, df):
        buffer = io.StringIO()
        df.info(buf=buffer)
        return buffer.getvalue()

    def get_merged_title_dfs(self, name_df1="title_basics", 
                             name_df2="title_ratings",
                             name_df3="title_episodes",
                             merged_on="tconst", delimiter='\t'):
        df1 = self.download_file(name_df1, delimiter)
        df2 = self.download_file(name_df2, delimiter)
        df3 = self.download_file(name_df3, delimiter)
        
        df_merged = pd.merge(df1, df2, on=merged_on)
        df_merged = pd.merge(df_merged, df3, on=merged_on)

        print(f"Dataframe Shape: {df_merged.shape}\n{df_merged.head()}\n")
        return df_merged

    def get_duplicated_ratings(self, df):
        duplicate_rows = df[df.duplicated()]
        n_rows = len(duplicate_rows)
        dup_string = "%d" % (n_rows) if (n_rows > 0) else "no"
        print(f'There are {dup_string} duplicate rows in the dataframe.')
        return duplicate_rows

    def get_nullity_count(self, df):
        return df.isnull().sum()
