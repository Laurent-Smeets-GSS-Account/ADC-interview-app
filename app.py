import os
import time
import streamlit as st
from openai import OpenAI
from datetime import datetime
import json
import re
import pandas as pd
import plotly.express as px
import hashlib

# Hard-coded Assistant ID
ASSISTANT_ID = "asst_TfoEvnYGlEvgVucL6miMvoEU"

# Page configuration
st.set_page_config(
    page_title="UNFPA Document Assistant",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"  # Start with sidebar collapsed for better mobile view
)

# Initialize session state variables
if "client" not in st.session_state:
    st.session_state.client = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "loading_state" not in st.session_state:
    st.session_state.loading_state = False
if "country_data" not in st.session_state:
    # Load only full country names for detection
    st.session_state.country_data = [
        "Afghanistan", "Albania", "Algeria", "Angola", "Argentina", "Armenia", "Australia", 
        "Austria", "Azerbaijan", "Bahamas", "Bangladesh", "Belarus", "Belgium", "Belize", 
        "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", 
        "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", 
        "Central African Republic", "Chad", "Chile", "China", "Colombia", "Congo", 
        "Costa Rica", "Cote d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czech Republic", 
        "Democratic Republic of Congo", "Denmark", "Djibouti", "Dominican Republic", 
        "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", 
        "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", 
        "Germany", "Ghana", "Greece", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", 
        "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", 
        "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", 
        "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", 
        "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Mali", "Malta", 
        "Mauritania", "Mauritius", "Mexico", "Moldova", "Mongolia", "Montenegro", "Morocco", 
        "Mozambique", "Myanmar", "Namibia", "Nepal", "Netherlands", "New Zealand", "Nicaragua", 
        "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", 
        "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", 
        "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saudi Arabia", "Senegal", "Serbia", 
        "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", 
        "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", 
        "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", 
        "Timor-Leste", "Togo", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", 
        "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", 
        "Uruguay", "Uzbekistan", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
    ]

# UNFPA themed styling with modern design
st.markdown("""
<style>
    /* Modern Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
        box-sizing: border-box;
    }
    
    /* Main background and text colors with subtle gradient - dark blue */
    .stApp {
        background: linear-gradient(135deg, #005B7F 0%, #004563 100%);
        color: #FFFFFF;
    }
    
    /* Hide streamlit sidebar expand button */
    button[kind="header"] {
        display: none !important;
    }
    
    /* Fix for loading state */
    div.element-container:not(:has(div[data-testid])) {
        visibility: hidden;
    }
    
    /* Modern container layout */
    .main .block-container {
        padding: 2rem 1.5rem;
        max-width: 1100px;
        margin: 0 auto;
    }
    
    /* Modern message containers with subtle animations */
    .chat-message {
        padding: 1.5rem;
        border-radius: 18px;
        margin-bottom: 1.25rem;
        color: #FFFFFF;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        min-height: 30px;
        width: 100%;
        box-sizing: border-box;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .chat-message:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    .user-message {
        background: linear-gradient(135deg, #FF6E00 0%, #FF8B33 100%);
        margin-left: 2rem;
        margin-right: 0.5rem;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #0095B6 0%, #00AFD7 100%);
        margin-right: 2rem;
        margin-left: 0.5rem;
    }
    
    /* Modern user icons */
    .user-icon, .assistant-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        margin-right: 12px;
        flex-shrink: 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .user-icon {
        background-color: #FFFFFF;
        color: #FF6E00;
    }
    
    .assistant-icon {
        background-color: #000000;
        color: #FFFFFF;
        font-size: 0.8rem;
        font-weight: bold;
        letter-spacing: -1px;
        border: 2px solid #E63946; /* Red border representing Amsterdam flag's red stripes */
    }
    
    /* Chat header with flexbox */
    .chat-header {
        display: flex;
        align-items: center;
        margin-bottom: 0.75rem;
    }
    
    /* Modern source references */
    .source-reference {
        color: #FFFFFF;
        font-weight: 600;
        background-color: rgba(255, 192, 0, 0.8);
        padding: 4px 10px;
        border-radius: 20px;
        display: inline-block;
        margin: 0 4px;
        font-size: 0.85rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Modern chat input container */
    .stChatInput {
        padding: 15px;
        background-color: rgba(0,0,0,0.15);
        border-radius: 16px;
        margin-top: 1.5rem;
        backdrop-filter: blur(10px);
    }
    
    /* Modern custom spinner */
    div.stSpinner > div {
        border-top-color: #FFC000 !important;
        border-left-color: #FFC000 !important;
        border-bottom-color: #FFC000 !important;
        border-right-color: transparent !important;
    }
    
    /* Make spinner visible during loading */
    .stSpinner {
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    /* Hide default Streamlit elements */
    footer {
        display: none !important;
    }
    
    /* Modern title styling - dark blue */
    .title-container {
        padding: 2rem 1rem;
        background: linear-gradient(135deg, #00688F 0%, #004B6B 100%);
        margin-bottom: 2rem;
        text-align: center;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .title-container h1 {
        color: #FFC000 !important;
        margin: 0;
        padding: 0;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    .title-container p {
        color: #00AFD7;
        margin: 0;
        padding-top: 0.75rem;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Modern chat input styling - dark blue */
    div[data-testid="stChatInput"] > div {
        border-radius: 30px;
        border: 2px solid rgba(0, 175, 215, 0.6);
        background-color: rgba(0, 75, 107, 0.6);
        transition: all 0.3s ease;
        backdrop-filter: blur(8px);
    }
    
    div[data-testid="stChatInput"] > div:focus-within {
        border-color: #00AFD7;
        box-shadow: 0 0 0 3px rgba(0, 175, 215, 0.3);
    }
    
    /* Modern sidebar styling - dark blue */
    section[data-testid="stSidebar"] {
        width: 320px !important;
        background: linear-gradient(180deg, #004B6B 0%, #003A54 100%);
        box-shadow: 5px 0 15px rgba(0,0,0,0.2);
        padding: 2rem 1.5rem !important;
    }
    
    /* Make the sidebar not move the main content */
    section[data-testid="stSidebar"][aria-expanded="true"] + section.main {
        margin-left: 320px;
    }
    
    /* Modern button styling */
    .stButton button {
        background: linear-gradient(135deg, #FF6E00 0%, #FF8324 100%);
        color: white;
        font-weight: 600;
        border-radius: 30px;
        border: none;
        width: 100%;
        padding: 0.6rem 1.5rem;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 4px 8px rgba(255, 110, 0, 0.3);
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #FF8324 0%, #FFA500 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(255, 110, 0, 0.4);
    }
    
    .stButton button:active {
        transform: translateY(1px);
    }
    
    /* Modern API key input styling - dark blue */
    .stTextInput > div > div > input {
        background-color: rgba(0, 65, 92, 0.7);
        color: #FFFFFF;
        border: 2px solid rgba(0, 175, 215, 0.5);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00AFD7;
        box-shadow: 0 0 0 3px rgba(0, 175, 215, 0.3);
    }
    
    /* Modern status elements */
    .stSuccess, .stInfo, .stWarning, .stError {
        background-color: rgba(0, 0, 0, 0.2);
        color: #FFFFFF;
        border-radius: 12px;
        padding: 1rem;
        backdrop-filter: blur(5px);
        border-left: 4px solid;
    }
    
    .stSuccess {
        border-left-color: #2ECC71;
    }
    
    .stInfo {
        border-left-color: #3498DB;
    }
    
    .stWarning {
        border-left-color: #F39C12;
    }
    
    .stError {
        border-left-color: #E74C3C;
    }
    
    /* Modern Expander styling - dark blue */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #FFC000;
        background-color: rgba(0, 65, 92, 0.5);
        border-radius: 10px;
        padding: 0.75rem 1rem !important;
        transition: background-color 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: rgba(0, 65, 92, 0.8);
    }
    
    .streamlit-expanderContent {
        border: 1px solid rgba(0, 65, 92, 0.5);
        border-top: none;
        border-radius: 0 0 10px 10px;
        padding: 1rem !important;
    }
    
    /* Modern divider */
    hr {
        margin: 1.5rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, 
            rgba(0,175,215,0) 0%, 
            rgba(0,175,215,0.5) 50%, 
            rgba(0,175,215,0) 100%);
    }
    
    /* Map styling - simpler approach */
    .map-title {
        font-size: 0.9rem;
        text-align: center;
        margin-bottom: 10px;
        color: #FFC000;
    }
    
    /* Simple column adjustments */
    .st-emotion-cache-keje6w {
        column-gap: 1rem;
    }
    
    /* Chat message in map layout */
    .chat-message-with-map {
        margin-right: 1rem;
    }
    
    /* SVG Map styling */
    .country {
        fill: #375170;
        stroke: #FFFFFF;
        stroke-width: 0.5;
        transition: fill 0.3s ease;
    }
    
    .country:hover {
        fill: #4A6C94;
    }
    
    .country.highlighted {
        fill: #FF6E00;
    }
    
    .country.highlighted:hover {
        fill: #FFC000;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .title-container h1 {
            font-size: 1.8rem;
        }
        
        .main .block-container {
            padding: 1rem 0.75rem;
        }
        
        .chat-message {
            padding: 1rem;
            border-radius: 15px;
            margin-bottom: 1rem;
        }
        
        .user-message {
            margin-left: 0.5rem;
        }
        
        .assistant-message {
            margin-right: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Custom title with consistent styling
st.markdown("""
<div class="title-container">
    <h1>UNFPA Document Assistant</h1>
    <p>Ask questions about UNFPA documents and reports</p>
    <p style="margin-top: 12px; font-size: 0.85rem; opacity: 0.7;">Developed by Laurent Smeets as an MVP for an interview with ADC</p>
</div>
""", unsafe_allow_html=True)

# Function to detect countries in text
def detect_countries(text):
    """Detect full country names in text"""
    detected_countries = []
    
    # Simple approach: check if any country name appears in the text
    for country in st.session_state.country_data:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(country) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            detected_countries.append(country)
    
    return detected_countries

# Function to create a choropleth map with colored countries
def generate_choropleth_map(countries, key_suffix='default'):
    """Generate a choropleth map with highlighted countries using Plotly"""
    if not countries:
        return False
        
    # Create a DataFrame for the choropleth with an ISO country column and value
    data = []
    for country in countries:
        data.append({
            'Country': country,
            'Mentioned': 1  # Value to determine color intensity
        })
    
    df = pd.DataFrame(data)
    
    # Create the choropleth map
    fig = px.choropleth(
        df,
        locations='Country', 
        locationmode='country names',
        color='Mentioned',
        color_continuous_scale=[[0, '#375170'], [1, '#FF6E00']],  # UNFPA colors
        range_color=[0, 1],
        labels={'Mentioned': 'Mentioned in response'},
        title='Countries Mentioned',
        projection='natural earth',
        height=400
    )
    
    # Update layout to match the UNFPA app theme
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_showscale=False,
        font=dict(
            family="Inter, sans-serif",
            size=12,
            color="#FFFFFF"
        ),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular',
            landcolor='#375170',  # Base color for non-highlighted countries
            coastlinecolor='#FFFFFF',
            countrycolor='#FFFFFF',
            showcountries=True,
            countrywidth=0.5,
            lataxis=dict(range=[-60, 90]),  # Adjusted to focus on populated areas
            bgcolor='rgba(0,0,0,0)'
        )
    )
    
    # Create the list of country names for display
    country_str = ", ".join(countries)
    
    # Display the map in a container with custom styling
    st.markdown(f"<div class='map-title'>Countries Mentioned: {country_str}</div>", unsafe_allow_html=True)
    
    # Use a unique key for each chart to prevent duplicate ID errors
    # Since key_suffix may already include "map_", we'll use it directly
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=key_suffix)
    
    return True

# Function to process source annotations for better formatting
def format_source_references(text):
    """This helps highlight and format the source references"""
    pattern = r'\[\s*([0-9]+)\s*:\s*source\s*\]'
    return re.sub(pattern, r'<span class="source-reference">📚 Source \1</span>', text)

# Function to ensure thread exists
def ensure_thread():
    if not st.session_state.thread_id and st.session_state.client:
        try:
            thread = st.session_state.client.beta.threads.create()
            st.session_state.thread_id = thread.id
            return True
        except Exception as e:
            st.error(f"Error creating thread: {str(e)}")
            return False
    return True

# Function to run the assistant and wait for response
def run_assistant(thread_id, assistant_id):
    if not st.session_state.client:
        return "Error: OpenAI client not initialized."
    
    try:
        # Create a run
        run = st.session_state.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        # Poll for completion with timeout
        start_time = time.time()
        timeout = 120  # 2 minutes timeout
        
        while True:
            if time.time() - start_time > timeout:
                return "The assistant took too long to respond. Please try again with a simpler question."
            
            run_status = st.session_state.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "expired", "cancelled"]:
                error_message = getattr(run_status, "last_error", "Unknown error")
                return f"Error: {run_status.status}. Details: {error_message}"
            
            # Wait before polling again
            time.sleep(1)
        
        # Get messages (newest first)
        messages = st.session_state.client.beta.threads.messages.list(
            thread_id=thread_id
        )
        
        # Return the latest assistant message
        for message in messages.data:
            if message.role == "assistant":
                message_content = ""
                for content_part in message.content:
                    if content_part.type == "text":
                        message_content += content_part.text.value
                return message_content
        
        return "No response from assistant."
    except Exception as e:
        return f"Error running assistant: {str(e)}"

# Sidebar for settings
with st.sidebar:
    st.title("Settings")
    
    # Initialize api_key variable from environment
    api_key = os.environ.get("OPENAI_API_KEY", "")
    
    # Check if API key is already set in environment/secrets
    api_key_set = api_key != ""
    
    if api_key_set:
        st.success("✅ OpenAI API key is configured")
        use_custom_key = st.checkbox("Use custom API key instead", value=False)
        
        if use_custom_key:
            custom_key = st.text_input("Enter custom OpenAI API Key", type="password", key="api_key_custom")
            if custom_key:
                api_key = custom_key
                os.environ["OPENAI_API_KEY"] = api_key
                if st.session_state.client is None:
                    st.session_state.client = OpenAI(api_key=api_key)
        else:
            # Make sure client is initialized with the configured key
            if st.session_state.client is None:
                st.session_state.client = OpenAI(api_key=api_key)
    else:
        # Original API key input for when no key is configured
        api_key = st.text_input("OpenAI API Key", type="password", key="api_key")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            if st.session_state.client is None:
                st.session_state.client = OpenAI(api_key=api_key)
    
    st.divider()
    
    # Controls section
    st.subheader("Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Chat", key="new_thread"):
            if st.session_state.client:
                try:
                    thread = st.session_state.client.beta.threads.create()
                    st.session_state.thread_id = thread.id
                    st.session_state.messages = []
                    st.success("New chat started!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("Clear Chat", key="clear_chat"):
            st.session_state.messages = []
            st.success("Chat cleared!")
            st.rerun()
    
    # Instructions
    st.divider()
    with st.expander("How to Use", expanded=False):
        st.write("1. Enter your OpenAI API key")
        st.write("2. Ask questions about UNFPA documents")
        st.write("3. Look for source references marked with 📚")

# Check if API key is provided
if not api_key:
    st.info("Please enter your OpenAI API key in the sidebar to start.")
else:
    # Ensure thread exists
    if not st.session_state.thread_id:
        if ensure_thread():
            st.info("Your document assistant is ready! What would you like to know?")
    
    # Display chat messages in a container to avoid layout shifts
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            role_class = "user-message" if message["role"] == "user" else "assistant-message"
            role_label = "You" if message["role"] == "user" else "Assistant"
            icon_class = "user-icon" if message["role"] == "user" else "assistant-icon"
            icon_content = "👤" if message["role"] == "user" else "XXX"
            
            # Format content to highlight sources
            content = message["content"]
            if message["role"] == "assistant":
                content = format_source_references(content)
                
                # Detect countries in assistant's response
                detected_countries = detect_countries(content)
                
                # Track which messages already have maps
                if "mapped_messages" not in st.session_state:
                    st.session_state.mapped_messages = set()
                
                # Get message index
                message_idx = st.session_state.messages.index(message)
                
                # Use columns layout for messages with countries
                if detected_countries and message_idx not in st.session_state.mapped_messages:
                    st.session_state.mapped_messages.add(message_idx)
                    
                    # Display the message first
                    st.markdown(f"""
                        <div class='chat-message {role_class} chat-message-with-map'>
                            <div class='chat-header'>
                                <div class='{icon_class}'>{icon_content}</div>
                                <b>{role_label}</b>
                            </div>
                            <div>{content}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Then display the map in a separate container
                    with st.container():
                        st.markdown("<hr style='margin: 10px 0; opacity: 0.2;'>", unsafe_allow_html=True)
                        st.markdown("<h4 style='color: #FFC000; text-align: center; margin-bottom: 10px;'>Geographic Context</h4>", unsafe_allow_html=True)
                        generate_choropleth_map(detected_countries, message_idx)
                else:
                    # Regular message display without map
                    st.markdown(f"""
                        <div class='chat-message {role_class}'>
                            <div class='chat-header'>
                                <div class='{icon_class}'>{icon_content}</div>
                                <b>{role_label}</b>
                            </div>
                            <div>{content}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='chat-message {role_class}'>
                        <div class='chat-header'>
                            <div class='{icon_class}'>{icon_content}</div>
                            <b>{role_label}</b>
                        </div>
                        <div>{content}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Input for new queries with better loading state handling
    user_query = st.chat_input("Ask about UNFPA documents...")
    
    if user_query:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.session_state.loading_state = True
        
        # Force rerun to show the user message immediately
        st.rerun()
    
    # Handle assistant response after rerun if loading state is active
    if st.session_state.loading_state:
        # Add message to thread
        if ensure_thread():
            try:
                st.session_state.client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=st.session_state.messages[-1]["content"]
                )
                
                # Get assistant response
                with st.spinner("Processing your request..."):
                    response = run_assistant(st.session_state.thread_id, ASSISTANT_ID)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Reset loading state
                st.session_state.loading_state = False
                
                # Force refresh to update UI
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})
                st.session_state.loading_state = False
                st.rerun()