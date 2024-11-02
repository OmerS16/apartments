import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

"""
topArea:
    2 - Merkaz
area:
    1 - Tel Aviv Yafo
    3 - Ramat Gan Givatayim
city:
    5000 - Tel Aviv Yafo
    8600 - Ramat Gan
    6300 - Givatayim
"""

input_df = pd.DataFrame({
    'topArea_id': [2, 2, 2],
    'area_id': [1, 3, 3],
    'city_id': [5000, 8600, 6300]
})

# Function to fetch neighborhood data
def fetch_neighborhood_data(topArea_id, area_id, city_id, neighborhood_id):
    url = f"https://gw.yad2.co.il/realestate-feed/rent/map?property=1&topArea={topArea_id}&area={area_id}&city={city_id}&neighborhood={neighborhood_id}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df = df[df.index == 'markers']
        df = pd.json_normalize(df['data'].item())
        if not df.empty:
            neighborhood_name = df['address.neighborhood.text'].iloc[0]
            return {
                'topArea_id': topArea_id,
                'area_id': area_id,
                'city_id': city_id,
                'neighborhood_id': neighborhood_id,
                'neighborhood_name': neighborhood_name
            }
    else:
        return None

results_list = []

with ThreadPoolExecutor(max_workers=10) as executor:
    tasks = [(row['topArea_id'], row['area_id'], row['city_id'], neighborhood_id) 
             for _, row in input_df.iterrows() for neighborhood_id in range(1, 2001)]
    
    for result in tqdm(executor.map(lambda args: fetch_neighborhood_data(*args), tasks), total=len(tasks)):
        if result is not None:
            results_list.append(result)

final_df = pd.DataFrame(results_list)
final_df.to_pickle('neighborhoods_database.pkl')
