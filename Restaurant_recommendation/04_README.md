
# Restaurant Recommendation System

A Streamlit-based restaurant recommendation application developed
as part of the SAM AI Technologies Machine Learning Internship.

## Features

- Filter restaurants by city/location.
- Choose cuisine preferences.
- Filter by minimum restaurant rating.
- Set a maximum cost per person.
- Filter by restaurant type.
- Sort matching restaurants by rating.
- Download recommendations as CSV.
- Explore restaurant rating distribution.

## Dataset

The application uses `display.csv`, which contains restaurant
names, cities, ratings, cost per person, restaurant categories,
types, and cuisine indicator columns.



## Installation

1. Install Python.
2. Open this project folder in VS Code.
3. Create and activate a virtual environment.
4. Install the dependencies:

   `python -m pip install -r requirements.txt`

5. Start the application:

   `streamlit run app.py`

## Recommendation Logic

The application filters restaurants according to the selected
preferences and displays matching restaurants in descending
order of rating.

## Technology Stack

- Python
- Pandas
- Streamlit

## Disclaimer

Recommendations are based on the supplied dataset. Ratings,
prices, and restaurant details may not reflect current information.
