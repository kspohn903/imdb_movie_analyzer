import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import os

class BasicEDA():
    def __init__(self, df1=None, df2=None, df1_filepath=None, df2_filepath=None):
        if df1_filepath:
            self.df1 = pd.read_csv(df1_filepath, low_memory=False)
        else:
            self.df1 = df1
            
        if df2_filepath:
            self.df2 = pd.read_csv(df2_filepath, low_memory=False)
        else:
            self.df2 = df2

    def drop_nulls(self, df, header=['startYear', 'genres','runtimeMinutes']):
        df = df.dropna(subset=header)
        return df
    
    def convert_numbers_to_int(self, df, header=['seasonNumber', 'episodeNumber']):
        for h in header:
            if h in df.columns:
                df[h] = pd.to_numeric(df[h], errors='coerce').fillna(0).astype(int)
             
    def convert_years_to_int(self, df, header=['startYear','endYear']):
        years = []
        for h in header:
            if h in df.columns:
                df[h] = pd.to_datetime(df[h], format="%Y", errors='coerce')
                df[h] = df[h].dt.year.fillna(0).astype(int)
                years.append(list(df[h]))
        return years

    def get_spread(self, df):
        n_years = df['startYear'].nunique()
        min_start_year = df['startYear'].min()
        max_start_year = df['startYear'].max()
        
        n_title_types = df['titleType'].nunique() if 'titleType' in df.columns else 0
        n_genres = df['genres'].nunique() if 'genres' in df.columns else 0
        
        start_year_range = f"{min_start_year}-{max_start_year}"
        
        print(f"[n_yrs, start_yr_range, n_title_types, n_genres] = [{n_years}, {start_year_range}, {n_title_types}, {n_genres}]")
        return [n_years, start_year_range, n_title_types, n_genres]

    def get_top_elements(self, df, prop="genres", k=10):
        return df[prop].value_counts().head(k)

    def get_top_genres_grouped_by_decade(self, df, year="startYear", runtime="runtimeMinutes", k_sorted=5):
        df = df.copy()
        df["decade"] = (df[year] // 10) * 10
        df["runtimeMinutes"] = df["runtimeMinutes"].replace('\\N', np.nan).astype(float)
        
        # Ensure averageRating and numVotes are numeric
        df['averageRating'] = pd.to_numeric(df['averageRating'], errors='coerce')
        df['numVotes'] = pd.to_numeric(df['numVotes'], errors='coerce')
        
        grouped = df.groupby(['decade','genres'])
        grouped_mean = round(grouped[['averageRating','numVotes']].mean(), 2)
        sorted_mean = grouped_mean.sort_values(['decade', 'averageRating', 'numVotes'], ascending=[True, False, False])
        
        top_genres = {}
        min_decade = int(df['decade'].min())
        max_decade = int(df['decade'].max())
        
        for decade in range(min_decade, max_decade + 10, 10):
            try:
                decade_data = sorted_mean.loc[decade].nlargest(k_sorted, ['averageRating', 'numVotes'])
                top_genres[f"{decade}s"] = decade_data
                top_genres[f"{decade}s"]['genres'] = top_genres[f"{decade}s"].index
                top_genres[f"{decade}s"].reset_index(drop=True, inplace=True)
            except KeyError:
                continue

        for decade in top_genres.keys():
            print(f"{decade}\n{top_genres[decade]}\n\n")
        return top_genres
