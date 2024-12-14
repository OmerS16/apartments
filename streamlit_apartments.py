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

# st.title("מצא את השכונה המתאימה ביותר עבורך")
st.sidebar.header("אפשרויות סינון")

min_price, max_price = st.sidebar.select_slider("מחיר", options=[i for i in range(0, 10000, 500)] + ["10,000+"], value=(5000, 6000))
num_rooms = st.sidebar.pills("מספר חדרים", [i for i in range(1, 6)], selection_mode='multi', default=2)
min_size, max_size = st.sidebar.select_slider('(מ"ר) גודל הדירה', options=[i for i in range(0, 301, 5)], value=(30, 70))
walking_time = st.sidebar.number_input("מרחק הליכה מרכבת קלה בדקות", min_value=0, value=5, step=1)
broker = st.sidebar.toggle("ללא תיווך", value=True)

# filtered_average_price = average_price[(average_price['rooms'].isin(num_rooms)) & (average_price['price_mean'] >= min_price) & (average_price['price_mean'] <= max_price)]
# filtered_average_price = filtered_average_price.sort_values('price_per_sq_m')

min_price, max_price = map(lambda price: float('inf') if price == '10,000+' else price, (min_price, max_price))

conditions = (
    (apartments['rooms'].isin(num_rooms)) &
    (apartments['price'] >= min_price) &
    (apartments['price'] <= max_price) &
    (apartments['walking_time'] <= walking_time)
)

if broker:
    conditions &= (apartments['adType'] == 'private')

filtered_apartments = apartments[conditions]

# if not filtered_average_price.empty:
#     st.subheader("השכונות הכי טובות עבור ההעדפות שלך")
#     st.dataframe(filtered_average_price[['city', 'neighborhood', 'rooms', 'price_mean', 'sq_m_mean', 'price_per_sq_m']])
# else:
#     st.write("לא נמצאו שכונות מתאימות, אנא שנה את העדפותיך")

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
        # popup=f"<a href='{row['url']}' target='_blank'>Click here for details</a>",
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
                    </a>
                </div>
            </div>
        ''',
        ).add_to(m)
    
st_folium(m, width=700, height=500)