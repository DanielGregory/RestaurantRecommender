🍽 Restaurant Recommender
A full-stack, data-driven web application that leverages Natural Language Processing (NLP) to deliver tailored restaurant recommendations using Yelp review data.

Users can search for a specific dish or cuisine, and a custom scoring algorithm analyzes millions of reviews to rank restaurants based on sentiment and frequency of mentions.

📺 Demo
🎥 Video Walkthrough: Watch Here
(Replace with your YouTube video URL and thumbnail)

✨ Key Features
🔍 Custom Recommender Algorithm – Weighted scoring model based on dish mentions, sentiment, and star ratings in Yelp reviews.

💡 Intuitive Search Interface – Simple keyword search for dishes or cuisines.

🗺 Interactive Map View – Folium-based map showing restaurant locations alongside a sortable list view.

📊 Dynamic Data Visualization – Data displayed in both list format and geographic context for easy exploration.

⚡ Scalable Architecture – Deployed with Flask, Gunicorn, and Nginx on AWS for production reliability.

🛠 Technical Stack
Category	Tools & Libraries
Language	Python
Framework	Flask
Data Processing	Pandas, NLTK (or other NLP libraries)
Visualization	Matplotlib, Seaborn, Folium
Deployment	AWS EC2, Gunicorn, Nginx
Dataset	Yelp Academic Dataset (Business + Review JSON)

🚀 Installation & Setup
1️⃣ Clone the repository

bash
Copy
Edit
git clone https://github.com/DanielGregory/RestaurantRecommender.git
cd RestaurantRecommender
2️⃣ Create a virtual environment & install dependencies

bash
Copy
Edit
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
3️⃣ Download Yelp Dataset

Get yelp_academic_dataset_business.json and yelp_academic_dataset_review.json from the Yelp Dataset.

Place them inside a /data folder in the project root.

4️⃣ Run the application

bash
Copy
Edit
python app.py
Visit: http://127.0.0.1:5000/

🔮 Future Enhancements
📍 Location-Based Filtering – Show only restaurants within a user’s selected area.

👤 User Profiles & Saved Recommendations – Personalized experiences for repeat users.

🤖 Semantic Search – Transition from keyword matching to embeddings (e.g., Word2Vec, spaCy) for deeper context understanding.

