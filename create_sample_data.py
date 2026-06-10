import os
import pandas as pd
import numpy as np

def create_sample_data(data_dir="test_data"):
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Sample title.basics.tsv
    basics_data = [
        ["tt0000001", "short", "Carmencita", "Carmencita", 0, "1894", "\\N", "1", "Documentary,Short"],
        ["tt0000002", "short", "Le clown et ses chiens", "Le clown et ses chiens", 0, "1892", "\\N", "5", "Animation,Short"],
        ["tt0000003", "short", "Pauvre Pierrot", "Pauvre Pierrot", 0, "1892", "\\N", "4", "Animation,Comedy,Romance"],
        ["tt1234567", "movie", "Test Movie", "Test Movie", 0, "2020", "\\N", "120", "Drama,Action"],
        ["tt7654321", "movie", "Action Thriller", "Action Thriller", 0, "2021", "\\N", "110", "Action,Thriller"]
    ]
    basics_df = pd.DataFrame(basics_data, columns=["tconst", "titleType", "primaryTitle", "originalTitle", "isAdult", "startYear", "endYear", "runtimeMinutes", "genres"])
    basics_df.to_csv(os.path.join(data_dir, "title.basics.tsv"), sep='\t', index=False)
    
    # Sample title.ratings.tsv
    ratings_data = [
        ["tt0000001", 5.6, 2000],
        ["tt0000002", 6.1, 200],
        ["tt0000003", 6.5, 300],
        ["tt1234567", 8.5, 10000],
        ["tt7654321", 7.2, 5000]
    ]
    ratings_df = pd.DataFrame(ratings_data, columns=["tconst", "averageRating", "numVotes"])
    ratings_df.to_csv(os.path.join(data_dir, "title.ratings.tsv"), sep='\t', index=False)

    # Sample name.basics.tsv
    names_data = [
        ["nm0000001", "Fred Astaire", "1899", "1987", "soundtrack,actor,miscellaneous", "tt0000001,tt1234567"],
        ["nm1234567", "John Doe", "1970", "\\N", "director,writer", "tt1234567"]
    ]
    names_df = pd.DataFrame(names_data, columns=["nconst", "primaryName", "birthYear", "deathYear", "primaryProfession", "knownForTitles"])
    names_df.to_csv(os.path.join(data_dir, "name.basics.tsv"), sep='\t', index=False)

    # Sample title.principals.tsv
    principals_data = [
        ["tt0000001", 1, "nm0000001", "actor", "\\N", "['Carmencita']"],
        ["tt1234567", 1, "nm1234567", "director", "\\N", "\\N"],
        ["tt1234567", 2, "nm0000001", "actor", "\\N", "\\N"]
    ]
    principals_df = pd.DataFrame(principals_data, columns=["tconst", "ordering", "nconst", "category", "job", "characters"])
    principals_df.to_csv(os.path.join(data_dir, "title.principals.tsv"), sep='\t', index=False)

if __name__ == "__main__":
    create_sample_data()
    print("Sample data created in test_data/")
