import os
from flask import Flask, render_template, request, url_for
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # Use 'Agg' backend for non-interactive plots (for web servers)
import matplotlib.pyplot as plt
import seaborn as sns
import json
import re
from collections import defaultdict
# from nltk.corpus import stopwords # Removed if not used for simplicity

# --- NEW: Import Folium for mapping ---
import folium

# --- Configuration ---
app = Flask(__name__)
app.config['STATIC_IMG_FOLDER'] = 'static/img/' # Folder to save generated plots (for list view)
app.config['STATIC_MAP_FOLDER'] = 'static/map/' # Folder to save generated maps (for map view)

# Ensure necessary folders exist
os.makedirs(app.config['STATIC_IMG_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_MAP_FOLDER'], exist_ok=True)

# --- GLOBAL DATA LOADING (Load once when app starts) ---
# IMPORTANT: Adjust these paths to your actual Yelp data files
# Create a 'data' folder in your project root and place the JSON files there
BUSINESS_JSON_PATH = 'data/yelp_academic_dataset_business.json'
REVIEW_JSON_PATH = 'data/yelp_academic_dataset_review.json'

biz_info = {} # Stores business ID -> {name, address, latitude, longitude, categories}
all_reviews = [] # Store all relevant reviews in memory

print("Loading Yelp data (this may take a while)...")

# Load Business Data
try:
    with open(BUSINESS_JSON_PATH, 'r', encoding='utf-8') as f:
        print("Starting to parse business data...")
        processed_biz_count = 0
        restaurants_category_count = 0 # This counter will become irrelevant for the primary filter
        open_restaurants_count = 0
        geo_restaurants_count = 0

        for i, line in enumerate(f):
            try:
                biz = json.loads(line)
                
                # We'll no longer strictly filter by 'Restaurants' or specific food categories here.
                # Just get the categories for info, but don't filter on them yet.
                categories_str = biz.get('categories', '')
                if isinstance(categories_str, str):
                    categories_list = [c.strip() for c in categories_str.split(',')]
                else:
                    categories_list = []
                
                # NO CATEGORY FILTER HERE ANYMORE FOR INITIAL INCLUSION
                # The 'restaurants_category_count' is now technically just 'any_category_count'
                restaurants_category_count += 1 # Count all businesses parsed

                # Filter for open businesses
                if biz.get('open') is True:
                    open_restaurants_count += 1
                    
                    # Filter for businesses with coordinates
                    latitude = biz.get('latitude')
                    longitude = biz.get('longitude')
                    
                    if latitude is not None and longitude is not None:
                        geo_restaurants_count += 1
                        biz_id = biz['business_id']
                        name = biz['name']
                        address = f"{biz.get('address', '')}, {biz.get('city', '')}, {biz.get('state', '')} {biz.get('postal_code', '')}"
                        
                        biz_info[biz_id] = {
                            'name': name,
                            'address': address,
                            'latitude': latitude,
                            'longitude': longitude,
                            'categories': categories_list # Store the processed list here
                        }
                        processed_biz_count += 1

            except json.JSONDecodeError:
                print(f"WARNING: Could not parse JSON on line {i+1} in business file: {line.strip()}")
                continue
            except KeyError as e:
                print(f"WARNING: Missing key {e} on line {i+1} in business file for business: {biz.get('business_id', 'N/A')}")
                continue
            
    print(f"Finished parsing business data.")
    print(f"Total lines processed in business file: {i+1 if 'i' in locals() else 0}")
    # Update print statements to reflect the new filtering logic
    print(f"Businesses with any category (all parsed): {restaurants_category_count}") 
    print(f"Open businesses: {open_restaurants_count}")
    print(f"Open businesses with geo-coordinates: {geo_restaurants_count}")
    print(f"Loaded {len(biz_info)} businesses (open and geo-tagged).")

except FileNotFoundError:
    print(f"Error: Business JSON not found at {BUSINESS_JSON_PATH}. Please check the path.")
    biz_info = {}
except Exception as e:
    print(f"An unexpected error occurred during business data loading: {e}")
    biz_info = {}

# Load ALL Review Data (filter reviews that belong to loaded businesses)
try:
    with open(REVIEW_JSON_PATH, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            review = json.loads(line)
            # Only store reviews for known (open, restaurant, geo-tagged) businesses
            if review['business_id'] in biz_info: 
                all_reviews.append({
                    'business_id': review['business_id'],
                    'stars': review['stars'],
                    'text': review['text'].lower() # Pre-lowercase review text for efficiency
                })
            #if (i + 1) % 500 == 0: # Optional: print progress for large files
                 #print(f"Processed {i + 1} reviews...")
    print(f"Finished loading {len(all_reviews)} relevant reviews.")
except FileNotFoundError:
    print(f"Error: Review JSON not found at {REVIEW_JSON_PATH}. Please check the path and ensure it's in a 'data/' subdirectory relative to app.py.")
    all_reviews = [] # Ensure it's empty if file not found

# --- Recommendation Logic Function (Adapted from your script) ---
def get_restaurant_recommendations(target_dish_lower, min_mentions, min_reviews_mentioning_dish, num_display):
    restaurant_scores = defaultdict(lambda: [0, 0, 0]) # [weighted_score, raw_mentions, num_reviews_with_dish]

    for review in all_reviews:
        biz_id = review['business_id']
        text = review['text']
        stars = review['stars']
        
        # Ensure business still exists in biz_info (might have been filtered out earlier)
        if biz_id not in biz_info:
            continue

        mentions = text.count(target_dish_lower)
        if mentions > 0:
            restaurant_scores[biz_id][0] += mentions * stars
            restaurant_scores[biz_id][1] += mentions
            restaurant_scores[biz_id][2] += 1
    
    # Filter restaurants based on minimum mentions and reviews
    filtered_restaurants = {
        biz_id: scores for biz_id, scores in restaurant_scores.items()
        if scores[1] >= min_mentions and scores[2] >= min_reviews_mentioning_dish
    }

    # Sort results by weighted score
    sorted_restaurants = sorted(filtered_restaurants.items(), key=lambda x: x[1][0], reverse=True)

    recommendations_list = []
    for i, (biz_id, (score, mentions, count)) in enumerate(sorted_restaurants):
        if i >= num_display: # Limit to num_display results
            break
        info = biz_info.get(biz_id)
        if info: # Ensure business info exists (should always if filtered correctly)
            recommendations_list.append({
                'name': info['name'],
                'score': score,
                'mentions': mentions,
                'reviews': count,
                'address': info['address'],
                'latitude': info['latitude'], 
                'longitude': info['longitude'] 
            })
    return recommendations_list

# --- Define the maximum number of restaurants to display ---
MAX_DISPLAY_RESTAURANTS = 500
# --- Flask Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    recommendations = []
    plot_url = None # For the bar chart image
    map_html = None # For the Folium map HTML content
    error_message = None
    
    # Default values for form fields, will be updated from POST request
    default_target_dish = "" # Default dish to search for 
    default_min_mentions = 5
    default_min_reviews = 2
    default_num_display = 10
    default_view_type = "list" # Default to list view

    if request.method == 'POST':
        
        # Determine the target dish directly from the text input
        target_dish_input = request.form.get('target_dish', '').strip()

        # Update default_target_dish for rendering the form
        default_target_dish = target_dish_input

        min_mentions = int(request.form.get('min_mentions', default_min_mentions))
        min_reviews = int(request.form.get('min_reviews', default_min_reviews))
        
        num_display_requested = int(request.form.get('num_display', default_num_display))
        if num_display_requested > MAX_DISPLAY_RESTAURANTS:
            num_display = MAX_DISPLAY_RESTAURANTS
            if error_message is None:
                 error_message = f"Requested number of restaurants ({num_display_requested}) exceeds the limit. Displaying a maximum of {MAX_DISPLAY_RESTAURANTS}."
        else:
            num_display = num_display_requested
            
        view_type = request.form.get('view_type', default_view_type)

        default_min_mentions = min_mentions
        default_min_reviews = min_reviews
        default_num_display = num_display_requested
        default_view_type = view_type

        if error_message is None or ("exceeds the limit" in error_message and target_dish_input): 
            if not target_dish_input:
                error_message = "Please enter a dish name to search for." # Simplified message
            elif biz_info is None or all_reviews is None:
                error_message = "Data not loaded. Please ensure Yelp JSON files are correct and accessible."
            else:
                recommendations = get_restaurant_recommendations(
                    target_dish_input.lower(),
                    min_mentions,
                    min_reviews,
                    num_display
                )

                if recommendations:
                    plot_df = pd.DataFrame(recommendations)
                    plot_df_sorted = plot_df.sort_values(by='score', ascending=True)

                    plt.figure(figsize=(10, max(6, len(plot_df_sorted)*0.7)))
                    sns.barplot(x='score', y='name', data=plot_df_sorted, palette='viridis')

                    plt.xlabel(f"Weighted Score for '{target_dish_input.title()}'")
                    plt.ylabel("Restaurant Name")
                    plt.title(f"Top Matches for '{target_dish_input.title()}'")

                    for index, row in enumerate(plot_df_sorted.itertuples()):
                        plt.text(row.score + (plot_df_sorted['score'].max()*0.01),
                                     index,
                                     f' Mentions: {row.mentions}, Reviews: {row.reviews}',
                                     va='center',
                                     fontsize=9,
                                     color='black')

                    plt.grid(axis='x', linestyle='--', alpha=0.7)
                    plt.tight_layout()

                    plot_filename = f"{target_dish_input.replace(' ', '_')}_recommendations_bar.png"
                    plot_path = os.path.join(app.config['STATIC_IMG_FOLDER'], plot_filename)
                    plt.savefig(plot_path)
                    plt.close()
                    plot_url = url_for('static', filename=f'img/{plot_filename}')

                    if view_type == 'map' and all(r.get('latitude') is not None for r in recommendations):
                        lats = [r['latitude'] for r in recommendations]
                        lons = [r['longitude'] for r in recommendations]
                        
                        if lats and lons:
                            bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
                            avg_lat = np.mean(lats)
                            avg_lon = np.mean(lons)
                            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
                            m.fit_bounds(bounds)
                        else:
                            m = folium.Map(location=[40.7128, -74.0060], zoom_start=10)

                        for i, r in enumerate(recommendations):
                            popup_html = f"""
                            <b>{i+1}. {r['name']}</b><br>
                            Score: {r['score']:.2f}<br>
                            Mentions: {r['mentions']}<br>
                            Reviews: {r['reviews']}<br>
                            Address: {r['address']}
                            """
                            if r.get('latitude') is not None and r.get('longitude') is not None:
                                folium.Marker(
                                    location=[r['latitude'], r['longitude']],
                                    popup=folium.Popup(popup_html, max_width=300),
                                    tooltip=f"{i+1}. {r['name']}"
                                ).add_to(m)

                        map_filename = f"{target_dish_input.replace(' ', '_')}_map.html"
                        map_path = os.path.join(app.config['STATIC_MAP_FOLDER'], map_filename)
                        m.save(map_path)
                        map_html = open(map_path, 'r', encoding='utf-8').read()
                    elif view_type == 'map':
                        error_message = "Map view not available: Some restaurants are missing location data or no recommendations were found for map display."
                elif not recommendations and not error_message:
                    error_message = f"No results found for '{target_dish_input.title()}' with the given filters."

    return render_template('index.html',
                            recommendations=recommendations,
                            plot_url=plot_url,
                            map_html=map_html,
                            default_target_dish=default_target_dish,
                            default_min_mentions=default_min_mentions,
                            default_min_reviews=default_min_reviews,
                            default_num_display=default_num_display,
                            default_view_type=default_view_type,
                            error_message=error_message)

if __name__ == '__main__':
    # Ensure 'data' directory exists for JSON files
    os.makedirs('data', exist_ok=True)
    # Important: Ensure your yelp JSON files are in the 'data' directory
    # before running the app.
    if not os.path.exists(BUSINESS_JSON_PATH) or not os.path.exists(REVIEW_JSON_PATH):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("WARNING: Yelp dataset JSON files not found in 'data/' directory.")
        print(f"Please place '{os.path.basename(BUSINESS_JSON_PATH)}' and")
        print(f"'{os.path.basename(REVIEW_JSON_PATH)}' into the '{os.path.join(os.getcwd(), 'data')}' folder.")
        print("The application will attempt to run but will not load data.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    app.run(debug=False) # debug=True is good for development, set to False for production