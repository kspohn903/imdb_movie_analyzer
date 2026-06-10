import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class TimeSeriesAnalyzer:
    def __init__(self, df):
        self.df = df.copy()
        self.df['startYear'] = pd.to_numeric(self.df['startYear'], errors='coerce')
        self.df = self.df.dropna(subset=['startYear'])

    def analyze_title_progression(self, output_path=None):
        """Analyzes the number of titles released over the years."""
        yearly_counts = self.df.groupby('startYear').size()
        
        plt.figure(figsize=(12, 6))
        yearly_counts.plot(kind='line', marker='o')
        plt.title('Progression of Titles Over Time')
        plt.xlabel('Year')
        plt.ylabel('Number of Titles')
        plt.grid(True)
        
        if output_path:
            plt.savefig(output_path)
        plt.show()
        return yearly_counts

    def analyze_genre_evolution(self, top_n_genres=5):
        """Analyzes how specific genres have evolved over time."""
        df_exploded = self.df.assign(genre=self.df['genres'].str.split(',')).explode('genre')
        top_genres = df_exploded['genre'].value_counts().nlargest(top_n_genres).index
        
        genre_progression = df_exploded[df_exploded['genre'].isin(top_genres)].groupby(['startYear', 'genre']).size().unstack()
        
        plt.figure(figsize=(12, 6))
        genre_progression.plot(kind='line', ax=plt.gca())
        plt.title(f'Evolution of Top {top_n_genres} Genres')
        plt.xlabel('Year')
        plt.ylabel('Number of Titles')
        plt.legend(title='Genre')
        plt.grid(True)
        plt.show()
        return genre_progression
