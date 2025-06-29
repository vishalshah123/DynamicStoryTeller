import streamlit as st
import google.generativeai as genai
import os
import re # For regular expressions to parse Gemini's response
from dotenv import load_dotenv

# --- Configuration and Setup ---
# Load environment variables from .env file
load_dotenv()

# Get Gemini API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Check if API key is set, if not, stop the app with an error
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found. Please set it in a .env file or as an environment variable.")
    st.stop()

# Configure the google-generativeai library with the API key
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Gemini model (using gemini-1.5-flash as discussed)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error initializing model 'gemini-1.5-flash': {e}. Please check your API key or model availability.")
    st.stop()


# --- Session State Initialization ---
# This is crucial for Streamlit to maintain state across interactions.
# Ensure all session state variables are initialized at the top-level of the script.
if 'story_history' not in st.session_state:
    st.session_state.story_history = [] # Stores all generated story segments
if 'current_choices' not in st.session_state:
    st.session_state.current_choices = [] # Stores choices for the current segment
if 'current_image_path' not in st.session_state: # Changed back to _path for local files
    st.session_state.current_image_path = None # Stores the local file path for the current image to display
if 'story_started' not in st.session_state:
    st.session_state.story_started = False
if 'full_story_text' not in st.session_state:
    st.session_state.full_story_text = "" # To accumulate the entire story for display


st.title("🌟 डायनामिक स्टोरीटेलर 📖")
st.write("अपनी कहानी शुरू करने के लिए कुछ शब्द लिखें और देखें AI कैसे एक अनोखी कहानी बनाता है!")


# --- Helper Function to get local image path from keywords ---
# This function will map keywords from Gemini to your local image files.
def get_local_image_path_from_keywords(keywords_list):
    # This dictionary maps common keywords to your image files in the 'images/' folder.
    # Make sure these image files exist in your 'dynamic_storyteller/images/' directory.
    image_mapping = {
        "forest": "images/forest.jpg",
        "woods": "images/forest.jpg", # Example: map similar keywords to the same image
        "trees": "images/forest.jpg",
        "castle": "images/castle.jpg",
        "city": "images/city.jpg",
        "town": "images/city.jpg",
        "village": "images/city.jpg",
        "mountain": "images/mountain.jpg",
        "cave": "images/cave.jpg",
        "river": "images/river.jpg",
        "hero": "images/hero.jpg",
        "celebration": "images/celebration.jpg",
        "dark": "images/dark.jpg", # Generic dark scene, if you have one
        "mystery": "images/mystery.jpg", # If you have a generic mystery image
        "adventure": "images/adventure.jpg", # If you have a generic adventure image
    }

    # Convert keywords to lowercase for case-insensitive matching
    lower_keywords = [kw.lower() for kw in keywords_list]

    for keyword in lower_keywords:
        for mapped_keyword, path in image_mapping.items():
            if mapped_keyword in keyword: # Check if the mapped_keyword is part of Gemini's keyword
                if os.path.exists(path): # Ensure the file actually exists
                    return path
    
    # Fallback to a default image if no specific match is found or file doesn't exist
    if os.path.exists("images/forest.jpg"): # Using forest.jpg as a primary fallback as requested
        return "images/forest.jpg"
    elif os.path.exists("images/default.jpg"): # If you have a generic default.jpg
        return "images/default.jpg"
    # If no local image found, return a generic online placeholder
    return "https://via.placeholder.com/600x400?text=No+Local+Image"


# --- Function to generate story segment using Gemini ---
def generate_story_segment(current_story_context, choice_made=None, is_initial=False, initial_prompt="", genre="", mood=""):
    prompt = ""
    # Construct the prompt for Gemini based on whether it's the start of the story or a continuation
    if is_initial:
        prompt = (
            f"Write the beginning of a {mood}, {genre} story. "
            f"The story starts with: '{initial_prompt}'. "
            "Keep it concise, around 3-5 sentences. "
            "Then, suggest 2-3 clear and distinct choices for the next step. "
            "At the very end, provide a single, short, comma-separated image keyword phrase "
            "that best describes the scene, like: 'mysterious forest, ancient tree' or 'futuristic city, flying cars'."
            "Example output format:\n\n"
            "Story text goes here...\n\n"
            "1. Choice 1\n2. Choice 2\n3. Choice 3\n\n"
            "IMAGE_KEYWORD: keyword1, keyword2"
        )
    else:
        # Contextual prompt for continuation, including the previous context and user's choice
        prompt = (
            f"The story so far: \"{current_story_context}\"\n\n"
            f"The user chose: \"{choice_made}\"\n\n"
            "Continue the story based on the choice. Keep the new segment concise, around 3-5 sentences. "
            "Then, suggest 2-3 clear and distinct choices for the next step. "
            "If the story feels like it's reaching a natural conclusion, you can suggest fewer choices (1 or 2) or a choice to 'End the story'. "
            "At the very end, provide a single, short, comma-separated image keyword phrase "
            "that best describes the new scene, like: 'dark cave, flickering light' or 'hero's triumph, grand celebration'."
            "Example output format:\n\n"
            "Story text goes here...\n\n"
            "1. Choice 1\n2. Choice 2\n\n"
            "IMAGE_KEYWORD: keyword1, keyword2"
        )

    story_text = ""
    choices = []
    image_keywords = [] # This will be used to select a local image path
    local_image_path_for_display = None

    with st.spinner("कहानी बन रही है..."): # Changed spinner message back
        try:
            # Generate story text and image keywords using Gemini
            response = model.generate_content(prompt)
            full_content = response.text.strip()

            # Use regex to parse the response for image keywords and choices
            image_keyword_match = re.search(r"IMAGE_KEYWORD:\s*(.*)", full_content, re.IGNORECASE | re.DOTALL)
            if image_keyword_match:
                image_keywords_phrase = image_keyword_match.group(1).strip()
                image_keywords = [kw.strip() for kw in image_keywords_phrase.split(',')]
                content_before_keywords = full_content[:image_keyword_match.start()].strip()
            else:
                content_before_keywords = full_content # No image keyword found

            choice_matches = re.findall(r"(\d+)\.\s*(.+)", content_before_keywords)
            if choice_matches:
                choices = [match[1].strip() for match in choice_matches]
                story_text_lines = []
                for line in content_before_keywords.split('\n'):
                    if not re.match(r"^\d+\.\s*", line.strip()):
                        story_text_lines.append(line)
                story_text = "\n".join(story_text_lines).strip()
            else:
                story_text = content_before_keywords # No choices found, entire content is story

            # --- Get Local Image Path based on Keywords ---
            local_image_path_for_display = get_local_image_path_from_keywords(image_keywords)
            
        except Exception as e:
            st.error(f"कहानी बनाने में त्रुटि हुई: {e}")
            return "त्रुटि: कहानी जेनरेट नहीं हो सकी। कृपया पुनः प्रयास करें।", [], None

    return story_text, choices, local_image_path_for_display


# --- Story Setup and Start Section ---
# This section is shown only when a story has not started yet.
if not st.session_state.story_started:
    with st.expander("कहानी की शुरुआत करें!", expanded=True):
        initial_prompt = st.text_input(
            "आपकी कहानी कहाँ से शुरू होती है? (जैसे: 'एक रहस्यमय जंगल में', 'पुराने महल की परछाइयों में')",
            "एक जादुई शहर में एक साहसी बच्चा"
        )
        story_genre = st.selectbox(
            "कहानी की शैली चुनें:",
            ["फंतासी", "रहस्य", "विज्ञान-फाई", "हास्य", "साहसिक"],
            index=0
        )
        story_mood = st.selectbox(
            "कहानी का मूड चुनें:",
            ["रोमांचक", "डरावना", "मज़ेदार", "विचारोत्तेजक", "शांत"],
            index=0
        )

        if st.button("कहानी शुरू करें!"):
            if initial_prompt:
                # Reset all session state variables for a new story
                st.session_state.story_history = []
                st.session_state.current_choices = []
                st.session_state.current_image_path = None # Use _path for local
                st.session_state.full_story_text = ""

                # Generate the first segment of the story
                story_segment, choices, local_image_path = generate_story_segment(
                    None, None, is_initial=True,
                    initial_prompt=initial_prompt, genre=story_genre, mood=story_mood
                )
                
                # If story generation was successful, update session state and re-run
                if story_segment != "त्रुटि: कहानी जेनरेट नहीं हो सकी। कृपया पुनः प्रयास करें।":
                    st.session_state.story_history.append(story_segment)
                    st.session_state.current_choices = choices
                    st.session_state.current_image_path = local_image_path # Store the local path
                    st.session_state.story_started = True
                    st.session_state.full_story_text += story_segment + "\n\n"
                    st.rerun() # Rerun to display the first part of the story
            else:
                st.warning("कृपया कहानी शुरू करने के लिए कुछ लिखें!")

# --- Display Story and Interaction Section ---
# This section is shown only when a story has already started.
if st.session_state.story_started:
    st.markdown("---")
    st.subheader("आपकी कहानी:")

    # Display current image if available (using _path now)
    if st.session_state.current_image_path:
        st.image(st.session_state.current_image_path, use_container_width=True, caption="कहानी का दृश्य") # use_container_width
    
    st.markdown(st.session_state.full_story_text)

    # --- Choice Handling ---
    # Display choices as buttons if there are any
    if st.session_state.current_choices:
        st.subheader("आगे क्या करना चाहेंगे?")
        cols = st.columns(len(st.session_state.current_choices)) # Create columns for choices
        
        for i, choice in enumerate(st.session_state.current_choices):
            with cols[i]: # Place each button in its own column
                if st.button(choice, key=f"choice_{i}"): # Unique key for each button
                    # Get the chosen action and current story context for the next generation
                    chosen_action = choice
                    current_context_for_gemini = st.session_state.story_history[-1] # Use the last segment

                    # Generate the next segment of the story
                    new_story_segment, new_choices, new_local_image_path = generate_story_segment(
                        current_context_for_gemini, chosen_action, is_initial=False
                    )

                    # If new segment generation was successful, update state and re-run
                    if new_story_segment != "त्रुटि: कहानी जेनरेट नहीं हो सकी। कृपया पुनः प्रयास करें।":
                        st.session_state.story_history.append(new_story_segment)
                        st.session_state.current_choices = new_choices
                        st.session_state.current_image_path = new_local_image_path # Update with new local path
                        st.session_state.full_story_text += new_story_segment + "\n\n"
                        st.rerun() # Re-run to display the new segment and choices
    else:
        # If no choices are provided by Gemini, assume the story has ended or is stuck
        st.markdown("---")
        st.success("कहानी यहाँ समाप्त होती है! आशा है आपको यह पसंद आई होगी।")
        if st.button("एक नई कहानी शुरू करें"):
            # Reset everything to start a new story
            st.session_state.story_started = False
            st.session_state.story_history = []
            st.session_state.current_choices = []
            st.session_state.current_image_path = None
            st.session_state.full_story_text = ""
            st.rerun()