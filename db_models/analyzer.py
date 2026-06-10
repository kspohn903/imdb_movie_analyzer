import pandas as pd

class RelationalAnalyzer:
    def __init__(self, principals_df, names_df, titles_df):
        self.principals = principals_df
        self.names = names_df
        self.titles = titles_df

    def analyze_person_impact(self, person_name):
        """Analyzes the impact of a specific person (actor/director/etc.) across their titles."""
        # Find person ID
        person = self.names[self.names['primaryName'].str.contains(person_name, case=False, na=False)]
        if person.empty:
            return None
        
        nconst = person.iloc[0]['nconst']
        
        # Get titles for this person
        person_titles = self.principals[self.principals['nconst'] == nconst]
        merged = person_titles.merge(self.titles, on='tconst')
        
        impact_stats = {
            'name': person.iloc[0]['primaryName'],
            'total_titles': len(merged),
            'avg_rating': merged['averageRating'].mean(),
            'genres': merged['genres'].str.split(',').explode().value_counts().to_dict(),
            'roles': merged['category'].value_counts().to_dict()
        }
        return impact_stats

    def get_top_collaborators(self, person_name):
        """Finds who this person works with most often."""
        person = self.names[self.names['primaryName'].str.contains(person_name, case=False, na=False)]
        if person.empty:
            return None
        
        nconst = person.iloc[0]['nconst']
        tconsts = self.principals[self.principals['nconst'] == nconst]['tconst'].unique()
        
        collaborators = self.principals[self.principals['tconst'].isin(tconsts) & (self.principals['nconst'] != nconst)]
        top_collabs = collaborators['nconst'].value_counts().head(10).reset_index()
        top_collabs.columns = ['nconst', 'count']
        
        result = top_collabs.merge(self.names[['nconst', 'primaryName']], on='nconst')
        return result
