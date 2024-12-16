import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import folium
from io import BytesIO
import requests

apartments_url = "https://github.com/OmerS16/apartments/blob/main/apartments_database.pkl?raw=true"
average_price_url = "https://github.com/OmerS16/apartments/blob/main/average_price_database.pkl?raw=true"
apartments_file = BytesIO(requests.get(apartments_url).content)
average_price_file = BytesIO(requests.get(average_price_url).content)
apartments = pd.read_pickle(apartments_file)
average_price = pd.read_pickle(average_price_file)

st.sidebar.header("אפשרויות סינון")

min_price, max_price = st.sidebar.select_slider("מחיר", options=[i for i in range(0, 20000, 500)] + ['20,000+'], value=(5000, 6000))
num_rooms = st.sidebar.pills("מספר חדרים", [i for i in range(1, 6)], selection_mode='multi', default=2)
min_size, max_size = st.sidebar.select_slider('(מ"ר) גודל הדירה', options=[i for i in range(0, 301, 5)] + ['300+'], value=(30, 70))
min_floor, max_floor = st.sidebar.select_slider("מס' קומה", options=['קרקע'] + [i for i in range(1, 10, 1)] + ['10+'], value=(1, 5))
walking_time = st.sidebar.number_input("מרחק הליכה מרכבת קלה בדקות", min_value=0, value=10, step=1)
broker = st.sidebar.toggle("ללא תיווך", value=True)

min_price, max_price = map(lambda price: float(apartments['price'].max()) if price == '20,000+' else price, (min_price, max_price))
min_size, max_size = map(lambda size: float(apartments['sq_m'].max()) if size == '300+' else size, (min_size, max_size))
min_floor, max_floor = map(lambda floor: 0 if floor == 'קרקע' else float(apartments['floor'].max()) if floor == '10+' else floor, (min_floor, max_floor))                       

conditions = (
    (apartments['rooms'].isin(num_rooms)) &
    (apartments['price'] >= min_price) &
    (apartments['price'] <= max_price) &
    (apartments['sq_m'] >= min_size) &
    (apartments['sq_m'] <= max_size) &
    (apartments['floor'] >= min_floor) &
    (apartments['floor'] <= max_floor) &
    (apartments['walking_time'] <= walking_time)
)

if broker:
    conditions &= (apartments['adType'] == 'private')

filtered_apartments = apartments[conditions]

st.title("מצא דירות המתאימות עבורך")
map_center = [apartments['lat'].mean(), apartments['lon'].mean()]
m = folium.Map(location=map_center, zoom_start=12)

for _, row in filtered_apartments.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=5,
        color='orange',
        fill=True,
        fill_color='white',
        fill_opacity=0.8,
        popup=f'''
            <div style="display: flex; align-items: center; direction: rtl;">
                <a href="{row['url']}" target="_blank">
                    <img src="{row['image']}" 
                         style="width: 200px; height: 150px; object-fit: cover; border-radius: 5px; margin-left: 10px;">
                </a>
                <div style="white-space: nowrap; text-align: right;">
                    <a href="{row['url']}" target="_blank" style="color: black; text-decoration: none;">
                        <h5><b>{row['street']} {int(row['house_num'])}</b></h5>
                        <h5>₪{row['price']}</h5>
                        <h6>{int(row['rooms'])} חדרים</h6>
                        <h6>{int(row['sq_m'])} מ"ר</h6>
                    </a>
                </div>
            </div>
        ''',
        ).add_to(m)
    
st_folium(m, width=700, height=500)