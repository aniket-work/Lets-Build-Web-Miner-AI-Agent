import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(page_title="Car Data Explorer", layout="wide")

# Title and description
st.title("🚗 Car Data Explorer")
st.markdown("""
This app provides an interactive exploration of used car data, including perspectives on years, prices, kilometers driven, and brands. Use the filters and visualizations to dive deep into the data!
""")


# Helper function to clean the data
def clean_data(df):
    # Clean kilometers: remove " km" and commas, convert to int
    df['kilometers'] = df['kilometers'].str.replace(' km', '').str.replace(',', '').astype(int)

    # Clean price: remove "$" and commas, convert to int
    df['price'] = df['price'].str.replace('$', '').str.replace(',', '').astype(int)

    # Extract brand from name (first word of the name)
    df['brand'] = df['name'].str.split().str[0]

    return df


# Load and clean the data
@st.cache_data
def load_data():
    df = pd.read_csv("complete_cars.csv")
    df = clean_data(df)
    return df


df = load_data()

# --- Overview Section ---
st.header("📊 Overview")
st.write(f"**Total Cars:** {len(df)}")
st.write(f"**Average Price:** ${df['price'].mean():,.2f}")
st.write(f"**Average Kilometers:** {df['kilometers'].mean():,.0f} km")
st.write(f"**Oldest Car:** {df['year'].min()}")
st.write(f"**Newest Car:** {df['year'].max()}")

# Display raw data
st.subheader("Raw Data")
st.dataframe(df)

# --- Cars by Year ---
st.header("📅 Cars by Year")
year_counts = df['year'].value_counts().sort_index()
fig_year = px.bar(
    x=year_counts.index,
    y=year_counts.values,
    labels={'x': 'Year', 'y': 'Number of Cars'},
    title="Number of Cars by Year",
    color=year_counts.index,
    color_continuous_scale='Viridis'
)
st.plotly_chart(fig_year, use_container_width=True)

# Filter by year
selected_years = st.multiselect("Filter by Year", options=sorted(df['year'].unique()),
                                default=sorted(df['year'].unique()))
filtered_by_year = df[df['year'].isin(selected_years)]
st.write(f"**Cars in Selected Years ({len(filtered_by_year)} cars):**")
st.dataframe(filtered_by_year)

# --- Price Analysis ---
st.header("💰 Price Analysis")

# Histogram of prices
fig_price_hist = px.histogram(
    df,
    x='price',
    nbins=10,
    title="Distribution of Car Prices",
    labels={'price': 'Price ($)'},
    color_discrete_sequence=['#00CC96']
)
st.plotly_chart(fig_price_hist, use_container_width=True)

# Most and least expensive cars
most_expensive = df.loc[df['price'].idxmax()]
least_expensive = df.loc[df['price'].idxmin()]
st.write(
    f"**Most Expensive Car:** {most_expensive['name']} ({most_expensive['year']}) - ${most_expensive['price']:,.0f}")
st.write(
    f"**Least Expensive Car:** {least_expensive['name']} ({least_expensive['year']}) - ${least_expensive['price']:,.0f}")

# Price range analysis
price_bins = [0, 20000, 30000, 40000, 50000, float('inf')]
price_labels = ['< $20,000', '$20,000-$30,000', '$30,000-$40,000', '$40,000-$50,000', '> $50,000']
df['price_range'] = pd.cut(df['price'], bins=price_bins, labels=price_labels, include_lowest=True)
price_range_counts = df['price_range'].value_counts().sort_index()
fig_price_range = px.bar(
    x=price_range_counts.index,
    y=price_range_counts.values,
    labels={'x': 'Price Range', 'y': 'Number of Cars'},
    title="Cars by Price Range",
    color=price_range_counts.index,
    color_discrete_sequence=px.colors.qualitative.Pastel
)
st.plotly_chart(fig_price_range, use_container_width=True)

# Filter by price range
selected_price_range = st.multiselect("Filter by Price Range", options=price_labels, default=price_labels)
filtered_by_price = df[df['price_range'].isin(selected_price_range)]
st.write(f"**Cars in Selected Price Range ({len(filtered_by_price)} cars):**")
st.dataframe(filtered_by_price)

# --- Kilometers Analysis ---
st.header("🛞 Kilometers Analysis")

# Scatter plot of kilometers vs price
fig_km_price = px.scatter(
    df,
    x='kilometers',
    y='price',
    color='year',
    size='price',
    hover_data=['name'],
    title="Kilometers vs Price (Color by Year, Size by Price)",
    labels={'kilometers': 'Kilometers Driven', 'price': 'Price ($)'},
    color_continuous_scale='Plasma'
)
st.plotly_chart(fig_km_price, use_container_width=True)

# Kilometer range analysis
km_bins = [0, 25000, 50000, 75000, 100000, float('inf')]
km_labels = ['0-25,000 km', '25,001-50,000 km', '50,001-75,000 km', '75,001-100,000 km', '> 100,000 km']
df['km_range'] = pd.cut(df['kilometers'], bins=km_bins, labels=km_labels, include_lowest=True)
km_range_counts = df['km_range'].value_counts().sort_index()
fig_km_range = px.bar(
    x=km_range_counts.index,
    y=km_range_counts.values,
    labels={'x': 'Kilometer Range', 'y': 'Number of Cars'},
    title="Cars by Kilometer Range",
    color=km_range_counts.index,
    color_discrete_sequence=px.colors.qualitative.Set2
)
st.plotly_chart(fig_km_range, use_container_width=True)

# Filter by kilometer range
selected_km_range = st.multiselect("Filter by Kilometer Range", options=km_labels, default=km_labels)
filtered_by_km = df[df['km_range'].isin(selected_km_range)]
st.write(f"**Cars in Selected Kilometer Range ({len(filtered_by_km)} cars):**")
st.dataframe(filtered_by_km)

# --- Brand Analysis ---
st.header("🏷️ Brand Analysis")

# Pie chart of brands
brand_counts = df['brand'].value_counts()
fig_brand_pie = px.pie(
    names=brand_counts.index,
    values=brand_counts.values,
    title="Distribution of Cars by Brand",
    color_discrete_sequence=px.colors.qualitative.Bold
)
st.plotly_chart(fig_brand_pie, use_container_width=True)

# Filter by brand
selected_brands = st.multiselect("Filter by Brand", options=sorted(df['brand'].unique()),
                                 default=sorted(df['brand'].unique()))
filtered_by_brand = df[df['brand'].isin(selected_brands)]
st.write(f"**Cars by Selected Brand ({len(filtered_by_brand)} cars):**")
st.dataframe(filtered_by_brand)

# --- Creative Visualizations ---
st.header("🎨 Creative Visualizations")

# Bubble chart: Year vs Price, size by kilometers, color by brand
fig_bubble = px.scatter(
    df,
    x='year',
    y='price',
    size='kilometers',
    color='brand',
    hover_data=['name', 'kilometers'],
    title="Bubble Chart: Year vs Price (Size by Kilometers, Color by Brand)",
    labels={'year': 'Year', 'price': 'Price ($)'},
    color_discrete_sequence=px.colors.qualitative.D3
)
st.plotly_chart(fig_bubble, use_container_width=True)

# Box plot: Price distribution by year
fig_box = px.box(
    df,
    x='year',
    y='price',
    title="Price Distribution by Year",
    labels={'year': 'Year', 'price': 'Price ($)'},
    color='year',
    color_discrete_sequence=px.colors.qualitative.Set1
)
st.plotly_chart(fig_box, use_container_width=True)

# --- Footer ---
st.markdown("""
---
**Built with ❤️ by Aniket AI :) **  
Explore your car data like never before! If you have more data or need additional features, let me know.
""")