import numpy as np

# Optimized dtypes to save RAM
TITLE_BASICS_SCHEMA = {
    'tconst': 'string',
    'titleType': 'category',
    'primaryTitle': 'string',
    'originalTitle': 'string',
    'isAdult': 'int8',
    'startYear': 'string', # Handled as string then coerced to int due to \N
    'endYear': 'string',
    'runtimeMinutes': 'string',
    'genres': 'string'
}

TITLE_RATINGS_SCHEMA = {
    'tconst': 'string',
    'averageRating': 'float32',
    'numVotes': 'int32'
}

# Mapping region/language codes for requirement #6
TITLE_AKAS_SCHEMA = {
    'titleId': 'string',
    'ordering': 'int16',
    'title': 'string',
    'region': 'category',
    'language': 'category',
    'types': 'string',
    'attributes': 'string',
    'isOriginalTitle': 'float32' # Use float to handle NaNs/Ints
}
