import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def fetch_neighborhoods():
    def fetch_neighborhoods_data(i):
        url = f"https://gw.yad2.co.il/realestate-feed/rent/map?property=1&topArea=2&area=1&city=5000&neighborhood={i}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df = df[df.index == 'markers']
            df = pd.json_normalize(df['data'].item())
            if not df.empty:
                df['neighborhood_id'] = i
                return df[['address.neighborhood.text', 'neighborhood_id']].head(1)
        return None
    
    df_list = pd.DataFrame()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(tqdm(executor.map(fetch_neighborhoods_data, range(990000, 992000)), total=2000))
        
    for result in results:
        if result is not None:
            df_list = pd.concat((df_list, result))
            
    return df_list      
    
neighborhoods = fetch_neighborhoods()
neighborhoods.to_excel(r"C:\Users\Omer\Desktop\Coding\yad2 scraper\new_neighborhood_id.xlsx", index=False)

neighborhoods = pd.read_excel(r"C:\Users\Omer\Desktop\Coding\yad2 scraper\neighborhood_id.xlsx")

def fetch_apartments(row):
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
    
    df_list = pd.DataFrame()
    
    for future in as_completed(futures):
        result = future.result()
        if result is not None:
            df_list = pd.concat((df_list, result))
            
    return df_list
            
apartments = fetch_apartments()
    
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

# # Analyzing data
average_price = apartments.groupby(['city', 'neighborhood', 'rooms'])[['price', 'sq_m']].agg(['mean', 'count'])
average_price.columns = ['_'.join(col).strip() for col in average_price.columns]
average_price = average_price.reset_index()
average_price = average_price.drop(['level_0_', 'index_', 'sq_m_count'], axis=1, errors='ignore')
average_price = average_price.rename(columns={'price_count':'count', 'rooms_':'rooms', 'neighborhood_':'neighborhood', 'city_':'city'})
average_price = average_price[['city', 'neighborhood', 'rooms', 'price_mean', 'sq_m_mean', 'count']]
average_price['price_per_sq_m'] = average_price['price_mean'] / average_price['sq_m_mean']
average_price_2_rooms = average_price.query('rooms == 2 & count > 1').sort_values('ratio')

average_price.to_excel(r"C:\Users\Omer\Desktop\Coding\yad2 scraper\database_apartments.xlsx")
