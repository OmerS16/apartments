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
    
    url = f"https://gw.yad2.co.il/realestate-feed/rent/map?property=1&topArea=2&area={area_id}&city={city_id}&neighborhood={neighborhood_id}"
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

# # Analyzing data
average_price = apartments.groupby(['city', 'neighborhood', 'rooms'])[['price', 'sq_m']].agg(['mean', 'count'])
average_price.columns = ['_'.join(col).strip() for col in average_price.columns]
average_price = average_price.reset_index()
average_price = average_price.drop(['level_0_', 'index_', 'sq_m_count'], axis=1, errors='ignore')
average_price = average_price.rename(columns={'price_count':'count', 'rooms_':'rooms', 'neighborhood_':'neighborhood', 'city_':'city'})
average_price = average_price[['city', 'neighborhood', 'rooms', 'price_mean', 'sq_m_mean', 'count']]
average_price['price_per_sq_m'] = average_price['price_mean'] / average_price['sq_m_mean']
average_price[['price_mean', 'sq_m_mean', 'price_per_sq_m']] = average_price[['price_mean', 'sq_m_mean', 'price_per_sq_m']].astype(int)

left = min(apartments['lon'].min(), stations['lon'].min())
bottom = min(apartments['lat'].min(), stations['lat'].min())
right = max(apartments['lon'].max(), stations['lon'].max())
top = max(apartments['lat'].max(), stations['lat'].max())

bbox = (left, bottom, right, top)

G = ox.graph_from_bbox(bbox, network_type='walk')

station_nodes = stations.apply(lambda row: ox.distance.nearest_nodes(G, X=row['lon'], Y=row['lat']), axis=1)
apartments['nearest_node'] = apartments.apply(lambda row: ox.distance.nearest_nodes(G, X=row['lon'], Y=row['lat']), axis=1)

def calculate_distance(apartment_node):
    try:
        distances = [nx.shortest_path_length(G, apartment_node, station_node, weight='length') for station_node in station_nodes]
        return min(distances)
    except Exception:
        return None

results = Parallel(n_jobs=-1, prefer='processes', batch_size=50)(
    delayed(calculate_distance)(node)
    for node in tqdm(apartments['nearest_node']))
       
apartments['walking_distance'] = results
walking_speed = 83.33
apartments['walking_time'] = apartments['walking_distance'] / walking_speed
apartments['walking_time'] = apartments['walking_time'].fillna(-1)

apartments.to_pickle('apartments_database.pkl')
average_price.to_pickle('average_price_database.pkl')
