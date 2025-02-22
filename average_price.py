import pandas as pd

apartments = pd.read_pickle('apartments_database.pkl')
average_price = apartments.groupby(['city', 'neighborhood', 'rooms'])[['price', 'sq_m']].agg(['mean', 'count'])
average_price.columns = ['_'.join(col).strip() for col in average_price.columns]
average_price = average_price.reset_index()
average_price = average_price.drop(['level_0_', 'index_', 'sq_m_count'], axis=1, errors='ignore')
average_price = average_price.rename(columns={'price_count':'count', 'rooms_':'rooms', 'neighborhood_':'neighborhood', 'city_':'city'})
average_price = average_price[['city', 'neighborhood', 'rooms', 'price_mean', 'sq_m_mean', 'count']]
average_price = average_price.fillna(0)
average_price['price_per_sq_m'] = average_price['price_mean'] / average_price['sq_m_mean']
# average_price[['price_mean', 'sq_m_mean', 'price_per_sq_m']] = average_price[['price_mean', 'sq_m_mean', 'price_per_sq_m']].astype(int)

# average_price.to_pickle('average_price_database.pkl')