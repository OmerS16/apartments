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

st.title("Find the best neighborhood for your budget")
st.sidebar.header("Input your preferences")

budget = st.sidebar.number_input("Enter your budget (in shekels):", min_value=0, value=5000, step=1000)
num_rooms = st.sidebar.number_input("Enter the number of rooms:", min_value=1, value=2, step=1)

filtered_average_price = average_price[(average_price['rooms'] == num_rooms) & (average_price['price_mean'] <= budget)]
filtered_average_price = filtered_average_price.sort_values('price_per_sq_m')
filtered_apartments = apartments[(apartments['rooms'] == num_rooms) & (apartments['price'] <= budget)]

if not filtered_average_price.empty:
    st.subheader("Best neighborhoods in Tel Aviv area for your budget")
    st.dataframe(filtered_average_price[['city', 'neighborhood', 'rooms', 'price_mean', 'sq_m_mean', 'price_per_sq_m']])
else:
    st.write("No neighborhoods match your criteria. Try adjusting your budget or number of rooms.")

map_center = [apartments['lat'].mean(), apartments['lon'].mean()]
m = folium.Map(location=map_center, zoom_start=10)

for _, row in filtered_apartments.iterrows():
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=f"<a href='{row['url']}' target='_blank'>Click here for details</a>",
        tooltip=row.get('street')
        ).add_to(m)
    
st_folium(m, width=700, height=500)