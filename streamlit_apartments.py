import pandas as pd
import streamlit as st

df = pd.read_csv(r"C:\Users\Omer\Desktop\Coding\yad2 scraper\database_apartments.csv")

st.title("Find the best neighborhood for your budget")
st.sidebar.header("Input your preferences")

budget = st.sidebar.number_input("Enter your budget (in shekels):", min_value=0, value=6000, step=1000)
num_rooms = st.sidebar.number_input("Enter the number of rooms:", min_value=1, value=2, step=1)

filtered_df = df[(df['rooms'] == num_rooms) & (df['price_mean'] <= budget)]

filtered_df = filtered_df.sort_values('price_per_sq_m')

if not filtered_df.empty:
    st.subheader("Best neighborhoods for your budget")
    st.dataframe(filtered_df[['city', 'neighborhood', 'rooms', 'price_mean', 'sq_m_mean', 'price_per_sq_m']])
else:
    st.write("No neighborhoods match your criteria. Try adjusting your budget or number of rooms.")
