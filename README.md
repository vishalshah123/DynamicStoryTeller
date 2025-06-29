# DynamicStoryTeller


1) Create virtual env and actiavate it
python -m venv venv
# For Windows:
.\venv\Scripts\activate
# For macOS/Linux:
source venv/bin/activate


2) install libarary
# pip install google-generativeai streamlit python-dotenv # python-dotenv for managing API key safely


3) create .env file and add your api key
# GEMINI_API_KEY="YOUR_YOUR_API_KEY_HERE"

4) write main logic in app.py

5) add some images in folder:images

6) To run this code:
    1.  Navigate to your `DynamicStoryTeller` folder in your terminal.
    2.  Activate your virtual environment (`.\venv\Scripts\activate` or `source venv/bin/activate`).
    3.  Run the command: `streamlit run app.py`
    4.  This will open your web browser, and you'll be able to see your storyteller app.