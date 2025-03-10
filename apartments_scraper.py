import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import osmnx as ox
import networkx as nx
from tqdm import tqdm
from joblib import Parallel, delayed

neighborhoods = pd.read_pickle('neighborhoods_database.pkl')
stations = pd.read_excel('dankal.xlsx')

def fetch_apartments_data(row):
    area_id = row['area_id']
    city_id = row['city_id']
    neighborhood_id = row['neighborhood_id']
    
    url = f"https://gw.yad2.co.il/realestate-feed/rent/map?property=1,3,6,7,25,49,51,11,31,43,4&topArea=2&area={area_id}&city={city_id}&neighborhood={neighborhood_id}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data)
    df = df[df.index == 'markers']
    df = pd.json_normalize(df['data'].item())
    return df
    
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(fetch_apartments_data, row) for index, row in neighborhoods.iterrows()]

apartments = pd.DataFrame()

for future in as_completed(futures):
    result = future.result()
    if result is not None:
        apartments = pd.concat((apartments, result))
    
# # Cleaning up the df
apartments = apartments.drop(['orderId', 'tags', 'subcategoryId',
                  'priority', 'additionalDetails.property.text',
                  'priceBeforeTag', 'customer.agencyName','inProperty.isAssetExclusive'],axis=1, errors='ignore')

apartments = apartments.rename(columns={'address.city.text':'city',
                            'address.neighborhood.text':'neighborhood',
                            'address.street.text':'street',
                            'address.house.number':'house_num',
                            'address.house.floor':'floor',
                            'address.coords.lon':'lon',
                            'address.coords.lat':'lat',
                            'additionalDetails.roomsCount':'rooms',
                            'additionalDetails.squareMeter':'sq_m',
                            'metaData.coverImage':'image',})

apartments['url'] = "https://www.yad2.co.il/realestate/item/" + apartments['token']

left = min(apartments['lon'].min(), stations['lon'].min())
bottom = min(apartments['lat'].min(), stations['lat'].min())
right = max(apartments['lon'].max(), stations['lon'].max())
top = max(apartments['lat'].max(), stations['lat'].max())

bbox = (left, bottom, right, top)

G = ox.graph_from_bbox(bbox, network_type='walk')

station_nodes = stations.apply(lambda row: ox.distance.nearest_nodes(G, X=row['lon'], Y=row['lat']), axis=1)
lons = apartments['lon'].values
lats = apartments['lat'].values
apartments['nearest_node'] = ox.distance.nearest_nodes(G, X=lons, Y=lats)

def calculate_distance(apartment_node):
    try:
        distances = [nx.shortest_path_length(G, apartment_node, station_node, weight='length') for station_node in station_nodes]
        return min(distances)
    except Exception:
        return None

results = Parallel(n_jobs=-1, prefer='processes', batch_size=100)(
    delayed(calculate_distance)(node)
    for node in tqdm(apartments['nearest_node']))
       
apartments['walking_distance'] = results
walking_speed = 83.33
apartments['walking_time'] = apartments['walking_distance'] / walking_speed
apartments['walking_time'] = apartments['walking_time'].fillna(-1)

apartments.to_pickle('apartments_database.pkl')

