import pandas as pd
import json
import re
from database import *

# Define all functions needed

def clean_string_value(value):
    if isinstance(value, str):
        if (len(value) != 0):
            return re.sub(r'[^\w\s\t]+', '', value.strip())
        else:
            return 'NA'
    return value

def extract_array_of_values_single_key(json_string, key):
    try:
        # Load JSON Data
        data = json.loads(json_string)
        
        # Check if the loaded JSON data is a non-empty list
        if isinstance(data, list) and len(data) > 0:

            # An empty set to maintain values (no duplicates allowed)
            cleaned_values = set()

            # Iterate over each dictionary in the JSON data
            for dict in data:
                value = dict.get(key)

                if isinstance(value, str):
                    # Append the cleaned value to the appropriate list
                    cleaned_values.add(clean_string_value(value))
                else:
                    cleaned_values.add(value)

            if not cleaned_values:
                return None
            else:
                # Surround each cleaned values with double inverted commas
                final_values = ', '.join(['"{}"'.format(cleaned_value) for cleaned_value in cleaned_values])
                return "[" + final_values + "]"
            
    except (json.JSONDecodeError, KeyError):
        return None

def extract_array_of_values_multiple_keys(json_string, keys):
    try:
        # Load JSON Data
        data = json.loads(json_string)

        # Check if the loaded JSON data is a non-empty list
        if isinstance(data, list) and len(data) > 0:

            # An empty dictionary to maintain various list for each key
            cleaned_values_dict = {key: [] for key in keys}

            # Iterate over each dictionary in the JSON data
            for dict in data:
                for key in keys:
                    if key in dict:
                        # Append the cleaned value associated with the key to the appropriate list
                        cleaned_values_dict[key].append(clean_string_value(dict[key]))
                    
            return pd.DataFrame(cleaned_values_dict)
    except (json.JSONDecodeError, KeyError):
        pass
    return None

def extract_array_of_values_multiple_keys_with_title(json_string, keys, title):
    try:
        # Load JSON Data
        data = json.loads(json_string)

        # Check if the loaded JSON data is a non-empty list
        if isinstance(data, list) and len(data) > 0:

            # An empty dictionary to maintain various list for each key
            cleaned_values_dict = {key: [] for key in keys}
            cleaned_values_dict['title'] = []

            # Iterate over each dictionary in the JSON data
            for dict in data:
                for key in keys:
                    if key in dict:
                        # Append the cleaned value associated with the key to the appropriate list
                        cleaned_values_dict[key].append(clean_string_value(dict[key]))
                
                cleaned_values_dict['title'].append(title)
                    
            return pd.DataFrame(cleaned_values_dict)
    except (json.JSONDecodeError, KeyError):
        pass
    return None

def extract_array_of_values_with_keyword(json_string, inputKey, extractKey, keyword):
    try:
        # Load JSON Data
        data = json.loads(json_string)

        # Check if the loaded JSON data is a non-empty list
        if isinstance(data, list) and len(data) > 0:

            # An empty set to maintain values (no duplicates allowed)
            cleaned_values = set()
            
            # Iterate over each dictionary in the JSON data
            for dict in data:
                if inputKey in dict and extractKey in dict:
                    # The value of the key matches with the keyword
                    if dict[inputKey] == keyword:
                        # Append the cleaned value to the appropriate list
                        cleaned_values.add(clean_string_value(dict[extractKey]))
            
            if not cleaned_values:
                return None
            else:
                # Convert the list of names to a comma-separated string
                final_values = ', '.join(['"{}"'.format(cleaned_value) for cleaned_value in cleaned_values])
                return "[" + final_values + "]"
    except (json.JSONDecodeError, KeyError):
        pass
    return None

def extract_array_of_values_with_keyword_reversed(json_string, inputKey, extractKey, keyword):
    try:
        # Load JSON Data
        data = json.loads(json_string)

        # Check if the loaded JSON data is a non-empty list
        if isinstance(data, list) and len(data) > 0:

            # An empty set to maintain values (no duplicates allowed)
            cleaned_values = set()
            
            # Iterate over each dictionary in the JSON data
            for dict in data:
                if inputKey in dict and extractKey in dict:
                    # The value of the key does not match with the keyword
                    if dict[inputKey] != keyword:
                        # Append the cleaned value to the appropriate list
                        cleaned_values.add(clean_string_value(dict[extractKey]))
            
            if not cleaned_values:
                return None
            else:
                # Convert the list of names to a comma-separated string
                final_values = ', '.join(['"{}"'.format(cleaned_value) for cleaned_value in cleaned_values])
                return "[" + final_values + "]"
    except (json.JSONDecodeError, KeyError):
        pass
    return None

def insert_mongodb_records(collection, records):
    if collection.name not in mongodb.list_collection_names():
        rows = None
        try:
            rows = collection.insert_many(records)
            print(f"{len(rows.inserted_ids)} records added into '{collection.name}' successfully")
        except Exception as e:
            print(e)
        return rows
    else:
        print(f"The collection '{collection.name}' already exists in the '{mongodb.name}' database.")
        return 0

mongodb = get_mongodb_database()
list_of_collection_names = ["country", "company",  "genre", "crew", "cast"]

# Create all collections in the db
collection_production_country = mongodb[list_of_collection_names[0]]
collection_production_company = mongodb[list_of_collection_names[1]]
collection_genre = mongodb[list_of_collection_names[2]]
collection_crew = mongodb[list_of_collection_names[3]]
collection_cast = mongodb[list_of_collection_names[4]]

# Load CSV files
movies_df = pd.read_csv('csv/tmdb_5000_movies.csv', encoding='utf-8')
credits_df = pd.read_csv('csv/tmdb_5000_credits.csv', encoding='utf-8')
print("[0] CSVs are loaded.")

# Drop columns
movies_df.drop(columns=['homepage', 'overview', 'original_title', 'status', 'spoken_languages', 'tagline', 'vote_count'], inplace=True)

# Convert date column to datetime
movies_df['release_date'] = pd.to_datetime(movies_df['release_date'])

# Extract all the production countries in the dataset
fields_to_extract_df1 = ["iso_3166_1", "name"]
extracted_df1 = movies_df['production_countries'].apply(extract_array_of_values_multiple_keys, keys=fields_to_extract_df1)
result_df1 = pd.concat(extracted_df1.to_list(), ignore_index=True)
result_df1 = result_df1.drop_duplicates(subset=fields_to_extract_df1)
result_df1 = result_df1.reset_index(drop=True)
result_df1 = result_df1.sort_values(by="iso_3166_1", ascending=True)
result_df1.rename(columns={'iso_3166_1': 'country_code'}, inplace=True)
print("[1] Extracted all the production countries in the dataset.")

# Extract all the production companies in the dataset
fields_to_extract_df2 = ["id", "name"]
extracted_df2 = movies_df['production_companies'].apply(extract_array_of_values_multiple_keys, keys=fields_to_extract_df2)
result_df2 = pd.concat(extracted_df2.to_list(), ignore_index=True)
result_df2 = result_df2.drop_duplicates(subset=fields_to_extract_df2)
result_df2 = result_df2.reset_index(drop=True)
result_df2 = result_df2.sort_values(by="id", ascending=True)
result_df2.rename(columns={'id': 'company_id'}, inplace=True)
print("[2] Extracted all the production companies in the dataset.")

# Extract all the genres in the dataset
fields_to_extract_df3 = ["id", "name"]
extracted_df3 = movies_df['genres'].apply(extract_array_of_values_multiple_keys, keys=fields_to_extract_df3)
result_df3 = pd.concat(extracted_df3.to_list(), ignore_index=True)
result_df3 = result_df3.drop_duplicates(subset=fields_to_extract_df3)
result_df3 = result_df3.reset_index(drop=True)
result_df3 = result_df3.sort_values(by="id", ascending=True)
result_df3.rename(columns={'id': 'genre_id'}, inplace=True)
print("[3] Extracted all the genres in the dataset.")

# Insert result_df1 into the 'country' collection
records_production_country = json.loads(result_df1.T.to_json()).values()
insert_mongodb_records(collection_production_country, records_production_country)

# Insert result_df2 into the 'company' collection
records_production_company = json.loads(result_df2.T.to_json()).values()
insert_mongodb_records(collection_production_company, records_production_company)

# Insert result_df3 into the 'genre' collection
records_genre = json.loads(result_df3.T.to_json()).values()
insert_mongodb_records(collection_genre, records_genre)

# Extract all the production countries involved for each movie in the dataset
movies_df['production_countries'] = movies_df['production_countries'].apply(extract_array_of_values_single_key, key="name")

# Extract all the production companies involved for each movie in the dataset
movies_df['production_companies'] = movies_df['production_companies'].apply(extract_array_of_values_single_key, key="name")

# Extract all the keywords relevant for each movie in the dataset
movies_df['keywords'] = movies_df['keywords'].apply(extract_array_of_values_single_key, key="name")

# Extract all of the genres each movie has in the dataset
movies_df['genres'] = movies_df['genres'].apply(extract_array_of_values_single_key, key="name")



##### CREDITS DATAFRAME #####

# Extract all the casts in the dataset
fields_to_extract_df4 = ["id", "name", "gender", "character"]
extracted_df4 = credits_df.apply(lambda x: extract_array_of_values_multiple_keys_with_title(x['cast'], fields_to_extract_df4, x['title']), axis=1)
result_df4 = pd.concat(extracted_df4.to_list(), ignore_index=True)
result_df4 = result_df4.drop_duplicates(subset=fields_to_extract_df4)
result_df4 = result_df4.reset_index(drop=True)
result_df4 = result_df4.sort_values(by="id", ascending=True)
result_df4.rename(columns={'id': 'cast_id'}, inplace=True)
print("[4] Extracted all the casts in the dataset.")

# Extract all the crews in the dataset
fields_to_extract_df5 = ["id", "name", "gender", "job", "department"]
extracted_df5 = credits_df.apply(lambda x: extract_array_of_values_multiple_keys_with_title(x['crew'], fields_to_extract_df5, x['title']), axis=1)
result_df5 = pd.concat(extracted_df5.to_list(), ignore_index=True)
result_df5 = result_df5.drop_duplicates(subset=fields_to_extract_df5)
result_df5 = result_df5.reset_index(drop=True)
result_df5 = result_df5.sort_values(by=["id", "department"], ascending=True)
result_df5.rename(columns={'id': 'crew_id'}, inplace=True)
print("[5] Extracted all the crews in the dataset.")

# Insert result_df4 into the 'cast' collection
records_cast = json.loads(result_df4.T.to_json()).values()
insert_mongodb_records(collection_cast, records_cast)

# Insert result_df5 into the 'crew' collection
records_crew = json.loads(result_df5.T.to_json()).values()
insert_mongodb_records(collection_crew, records_crew)

# Extract all the production companies involved for each movie in the dataset
credits_df['cast'] = credits_df['cast'].apply(extract_array_of_values_single_key, key="name")

# Extract all the directors who are part of the crew team for each movie in the dataset
credits_df['director'] = credits_df['crew'].apply(extract_array_of_values_with_keyword,
                                                inputKey="job", extractKey="name", keyword="Director")

# Extract all remaining crew who are not directors for each movie in the dataset
credits_df['crew'] = credits_df['crew'].apply(extract_array_of_values_with_keyword_reversed,
                                                inputKey="job", extractKey="name", keyword="Director")


##### FINAL DATAFRAME #####

# Merge the credits_df with the movies_df
credits_df.drop('title', axis=1, inplace=True)
final_df = pd.merge(movies_df, credits_df, left_on='id', right_on='movie_id', how='inner')

# Drop both movie_id and id as they are no longer needed
final_df.drop('movie_id', axis=1, inplace=True)
final_df.drop('id', axis=1, inplace=True)

# Reorder the remaining columns
final_df = final_df[['title', 'director','crew', 'cast', 'keywords', 'runtime','release_date','production_companies',
                    'production_countries', 'original_language', 'genres', 'budget', 'revenue', 'popularity', 'vote_average']]

# Sort the column
final_df.sort_values(by=['title'], ascending=True, inplace=True)

final_df.to_csv('csv/tmdb_5000_movies_clean.csv', index=False, encoding='utf-8')
print("[6] Exported final into CSV files.")