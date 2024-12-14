import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import folium
from io import BytesIO
import requests

apartments_url = "https://github.com/OmerS16/neighborhoods/blob/main/apartments_database.pkl?raw=true"
average_price_url = "https://github.com/OmerS16/neighborhoods/blob/main/average_price_database.pkl?raw=true"
apartments_file = BytesIO(requests.get(apartments_url).content)
average_price_file = BytesIO(requests.get(average_price_url).content)
apartments = pd.read_pickle(apartments_file)
average_price = pd.read_pickle(average_price_file)

st.title("מצא את השכונה המתאימה ביותר עבורך")
st.sidebar.header("אפשרויות סינון")

min_price, max_price = st.sidebar.select_slider("מחיר", options=[i for i in range(0, 10001, 500)], value=(5000, 6000))
num_rooms = st.sidebar.pills("מספר חדרים", [i for i in range(1, 6)], selection_mode='multi', default=2)
min_size, max_size = st.sidebar.select_slider("גודל הדירה במ\\"ר, options=[i for i in range(0, 301, 5)], value=(30, 70))
walking_time = st.sidebar.number_input("מרחק הליכה מרכבת קלה בדקות", min_value=0, value=5, step=1)
broker = st.sidebar.toggle("ללא תיווך")

filtered_average_price = average_price[(average_price['rooms'].isin(num_rooms)) & (average_price['price_mean'] >= min_price) & (average_price['price_mean'] <= max_price)]
filtered_average_price = filtered_average_price.sort_values('price_per_sq_m')
filtered_apartments = apartments[(apartments['rooms'].isin(num_rooms)) & (apartments['price'] >= min_price) & (apartments['price'] <= max_price) & (apartments['walking_time'] <= walking_time)]

if not filtered_average_price.empty:
    st.subheader("Best neighborhoods in Tel Aviv area for your budget")
    st.dataframe(filtered_average_price[['city', 'neighborhood', 'rooms', 'price_mean', 'sq_m_mean', 'price_per_sq_m']])
else:
    st.write("No neighborhoods match your criteria. Try adjusting your budget or number of rooms.")

st.title("Find the best apartments for you!")
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
        popup=f"<a href='{row['url']}' target='_blank'>Click here for details</a>",
        tooltip=row.get('price')
        ).add_to(m)
    
st_folium(m, width=700, height=500)