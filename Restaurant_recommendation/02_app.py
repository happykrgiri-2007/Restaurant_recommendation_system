
import re
from pathlib import Path

import pandas as pd
import streamlit as st


# --------------------------------------------------
# RESTAURANT RECOMMENDATION SYSTEM
# SAM AI TECHNOLOGIES - INTERNSHIP PROJECT
# --------------------------------------------------

st.set_page_config(
    page_title="Restaurant Recommendation System",
    page_icon="🍽️",
    layout="wide"
)

DATA_PATH = Path(__file__).parent / "display.csv"

# Dataset columns that describe restaurants
BASE_COLUMNS = [
    "Name",
    "City",
    "Type",
    "Category",
    "Price_Category",
    "Cost_Per_Person",
    "Rating",
    "Menu",
    "Delivery",
    "Booking",
    "No_of_Best_Sellers",
    "No_of_Varieties",
]


# --------------------------------------------------
# 1. LOAD AND CLEAN DATA
# --------------------------------------------------

@st.cache_data(show_spinner="Loading restaurant dataset...")
def load_data(path, modified_time, file_size):
    data = pd.read_csv(path, encoding="latin-1", low_memory=False)

    # Remove accidental spaces from column names
    data.columns = data.columns.str.strip()

    required = [
        "Name",
        "City",
        "Cost_Per_Person",
        "Rating",
        "Type",
    ]

    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing)
        )

    # Convert numeric columns safely
    for col in [
        "Cost_Per_Person",
        "Rating",
        "No_of_Best_Sellers",
        "No_of_Varieties",
    ]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    # Clean text fields
    for col in data.select_dtypes(include="object").columns:
        data[col] = data[col].fillna("").astype(str).str.strip()

    data["Name"] = data["Name"].replace("", pd.NA)
    data["City"] = data["City"].replace("", pd.NA)
    data = data.dropna(subset=["Name", "City"]).copy()

    # Remove invalid ratings and negative prices
    data.loc[
        ~data["Rating"].between(0, 5), "Rating"
    ] = float("nan")

    data.loc[
        data["Cost_Per_Person"] < 0, "Cost_Per_Person"
    ] = float("nan")

    # Cuisine columns are the columns after Price_Category
    # in this dataset. They contain 1/0 indicators.
    if "Price_Category" in data.columns:
        start = data.columns.get_loc("Price_Category") + 1
        possible_cuisines = list(data.columns[start:])
    else:
        possible_cuisines = []

    # Keep only columns that actually contain binary cuisine values
    cuisine_columns = []
    for col in possible_cuisines:
        values = set(
            pd.to_numeric(data[col], errors="coerce")
            .dropna()
            .unique()
        )
        if values and values.issubset({0, 1}):
            cuisine_columns.append(col)

    # Remove duplicate restaurant records when all key fields match
    data = data.drop_duplicates(
        subset=["Name", "City", "Type", "Cost_Per_Person"]
    ).copy()

    return data, cuisine_columns


# --------------------------------------------------
# 2. CHECK DATASET
# --------------------------------------------------

st.title("🍽️ Restaurant Recommendation System")

st.write(
    "Discover restaurants based on your preferred city, "
    "cuisine, rating, and budget."
)

st.caption(
    "Machine Learning Internship Project | SAM AI Technologies"
)

if not DATA_PATH.exists():
    st.error(
        "Dataset not found. Put display.csv in the same folder "
        "as app.py."
    )
    st.stop()

try:
    df, cuisine_columns = load_data(
        str(DATA_PATH),
        DATA_PATH.stat().st_mtime,
        DATA_PATH.stat().st_size,
    )
except Exception as error:
    st.error(f"Unable to load the dataset: {error}")
    st.stop()

if df.empty:
    st.warning("No usable restaurant records found.")
    st.stop()


# --------------------------------------------------
# 3. DATASET SUMMARY
# --------------------------------------------------

m1, m2, m3 = st.columns(3)

m1.metric("Restaurants", f"{len(df):,}")
m2.metric("Cities / Locations", f"{df['City'].nunique():,}")
m3.metric("Cuisine Options", f"{len(cuisine_columns):,}")

st.divider()


# --------------------------------------------------
# 4. USER PREFERENCES
# --------------------------------------------------

st.subheader("🎯 Choose Your Preferences")

left, right = st.columns(2)

cities = sorted(df["City"].dropna().unique().tolist())
city_options = ["All Locations"] + cities

with left:
    selected_city = st.selectbox(
        "📍 Select Location",
        city_options,
    )

    selected_cuisine = st.selectbox(
        "🍛 Select Cuisine",
        ["All Cuisines"] + sorted(cuisine_columns),
    )

    if "Type" in df.columns:
        types = sorted(
            x for x in df["Type"].dropna().unique().tolist() if x
        )
        selected_type = st.selectbox(
            "🍴 Restaurant Type",
            ["All Types"] + types,
        )
    else:
        selected_type = "All Types"

with right:
    rating_values = df["Rating"].dropna()

    if rating_values.empty:
        st.warning("No valid ratings are available.")
        min_rating = 0.0
    else:
        min_rating = st.slider(
            "⭐ Minimum Rating",
            min_value=0.0,
            max_value=5.0,
            value=3.5,
            step=0.1,
        )

    costs = df["Cost_Per_Person"].dropna()

    if costs.empty:
        budget = None
        st.info("Cost information is unavailable.")
    else:
        max_cost = max(100, int(costs.max()))
        max_cost = min(max_cost, 10000)

        budget = st.slider(
            "💰 Maximum Cost Per Person (₹)",
            min_value=0,
            max_value=max_cost,
            value=max_cost,
            step=50 if max_cost <= 2000 else 100,
        )

st.caption(
    "Budget uses Cost_Per_Person from your dataset, not cost for two."
)


# --------------------------------------------------
# 5. FILTER AND RANK RESTAURANTS
# --------------------------------------------------

filtered = df.copy()

if selected_city != "All Locations":
    filtered = filtered[filtered["City"] == selected_city]

if selected_cuisine != "All Cuisines":
    cuisine_values = pd.to_numeric(
        filtered[selected_cuisine], errors="coerce"
    ).fillna(0)
    filtered = filtered[cuisine_values == 1]

if selected_type != "All Types":
    filtered = filtered[filtered["Type"] == selected_type]

filtered = filtered[
    filtered["Rating"].notna()
    & (filtered["Rating"] >= min_rating)
]

if budget is not None:
    filtered = filtered[
        filtered["Cost_Per_Person"].notna()
        & (filtered["Cost_Per_Person"] <= budget)
    ]

# Highest-rated restaurants appear first
filtered = filtered.sort_values(
    by=["Rating", "Name"],
    ascending=[False, True],
)


# --------------------------------------------------
# 6. DISPLAY RECOMMENDATIONS
# --------------------------------------------------

st.divider()
st.subheader("🏆 Recommended Restaurants")
st.write(f"Found **{len(filtered):,}** matching restaurants.")

if filtered.empty:
    st.warning(
        "No restaurants match your filters. Try lowering the rating "
        "or increasing the budget."
    )
else:
    display_columns = [
        col for col in [
            "Name",
            "City",
            "Type",
            "Category",
            "Rating",
            "Cost_Per_Person",
            "Price_Category",
            "Delivery",
            "Booking",
        ]
        if col in filtered.columns
    ]

    results = filtered[display_columns].copy()

    if "Rating" in results.columns:
        results["Rating"] = results["Rating"].round(1)

    if "Cost_Per_Person" in results.columns:
        results["Cost_Per_Person"] = results[
            "Cost_Per_Person"
        ].apply(
            lambda x: f"₹{x:,.0f}" if pd.notna(x) else "Not available"
        )

    st.dataframe(
        results.head(100),
        use_container_width=True,
        hide_index=True,
    )

    st.caption("Showing up to 100 matching restaurants.")

    csv_bytes = filtered[display_columns].to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="⬇️ Download Recommendations as CSV",
        data=csv_bytes,
        file_name="restaurant_recommendations.csv",
        mime="text/csv",
    )


# --------------------------------------------------
# 7. RATING ANALYSIS
# --------------------------------------------------

st.divider()
st.subheader("📊 Restaurant Rating Analysis")

valid_ratings = df["Rating"].dropna()

if not valid_ratings.empty:
    chart_data = (
        valid_ratings.round(1)
        .value_counts()
        .sort_index()
    )

    st.bar_chart(chart_data)

    avg_rating = valid_ratings.mean()
    st.write(
        f"**Average rating in the dataset:** {avg_rating:.2f}/5"
    )

    st.write(
        f"**Restaurants with valid ratings:** "
        f"{len(valid_ratings):,}"
    )
else:
    st.info("No valid restaurant ratings are available.")


# --------------------------------------------------
# 8. DATA PREVIEW
# --------------------------------------------------

with st.expander("🔎 Preview cleaned dataset"):
    st.dataframe(
        df[[
            c for c in [
                "Name", "City", "Type", "Rating",
                "Cost_Per_Person", "Category"
            ] if c in df.columns
        ]].head(20),
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "Recommendations use dataset ratings and the filters selected "
    "by the user. Results are not live restaurant availability."
)
