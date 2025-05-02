import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Verify environment variables

# the gemini api key is for testing purpose, will delete it after testing period
if not os.getenv('GEMINI_API_KEY') or not os.getenv('DATASET_PATH'):
    st.error("Missing environment variables. Please set GEMINI_API_KEY and DATASET_PATH in .env.")
    st.stop()

# Gemini setup using environment variable
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

# Load dataset and create summary
df_dataset = pd.read_csv(os.getenv('DATASET_PATH'))
spirit_types = [str(x) for x in df_dataset['spirit_type'].unique() if pd.notna(x)]
dataset_summary = (
    f"The dataset contains {len(df_dataset)} bottles with columns: {', '.join(df_dataset.columns)}. "
    f"Spirits include {', '.join(spirit_types)}. "
    f"Price range: ${df_dataset['avg_msrp'].min():.2f} to ${df_dataset['avg_msrp'].max():.2f}. "
    f"Proof range: {df_dataset['proof'].min()} to {df_dataset['proof'].max()}. "
    f"Popularity range: {df_dataset['popularity'].min()} to {df_dataset['popularity'].max()}. "
    f"Total score range: {df_dataset['total_score'].min()} to {df_dataset['total_score'].max()}. "
    f"Wishlist count range: {df_dataset['wishlist_count'].min()} to {df_dataset['wishlist_count'].max()}. "
    f"Ranking range: {df_dataset['ranking'].min()} to {df_dataset['ranking'].max()}."
)

# Custom CSS for UI polish
custom_css = """
<style>
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
    }
    .css-1d391kg h1, .css-1d391kg h2 {
        color: #2c3e50;
        font-family: 'Arial', sans-serif;
    }
    .css-1d391kg button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 8px 12px;
        margin: 5px 0;
        width: 100%;
        transition: background-color 0.3s;
    }
    .css-1d391kg button:hover {
        background-color: #2980b9;
    }
    .css-1d391kg input {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 8px;
    }

    /* Main page styling */
    .main {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .main h1 {
        color: #2c3e50;
        font-family: 'Georgia', serif;
        text-align: center;
    }
    .main h2 {
        color: #34495e;
        font-family: 'Arial', sans-serif;
    }
    .main .stTextInput > div > div > input {
        border: 1px solid #3498db;
        border-radius: 5px;
        padding: 10px;
    }
    .main .stButton > button {
        background-color: #e67e22;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        transition: background-color 0.3s;
    }
    .main .stButton > button:hover {
        background-color: #d35400;
    }

    /* Chat interface styling */
    .stChatMessage {
        background-color: #080d25;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stChatMessage.user {
        background-color: #2a5c94;
        color: #268bce;
        text-align: right;
    }
    .stChatMessage.assistant {
        background-color: #a726ce ;
        color: #26ce63;
        text-align: left;
    }
    .stChatMessage img {
        max-width: 100px;
        border-radius: 5px;
        margin: 5px;
    }
    .stTable {
        border-collapse: collapse;
        width: 100%;
    }
    .stTable th, .stTable td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .stTable th {
        background-color: #3498db;
        color: white;
    }
</style>
"""

# Inject CSS
st.markdown(custom_css, unsafe_allow_html=True)

# Define the recommendation function
def compute_recommendations(bar_data, df_dataset, top_n=3):
    if not bar_data:
        return []
    user_bottles = [b['product'] for b in bar_data]
    df_user = pd.DataFrame(user_bottles)
    
    # Fill missing values in df_user and df_dataset
    df_user = df_user.fillna({
        'proof': df_user['proof'].mean() if 'proof' in df_user else df_dataset['proof'].mean(),
        'average_msrp': df_user['average_msrp'].mean() if 'average_msrp' in df_user else df_dataset['avg_msrp'].mean(),
        'popularity': df_user['popularity'].mean() if 'popularity' in df_user else df_dataset['popularity'].mean(),
        'total_score': df_user['total_score'].mean() if 'total_score' in df_user else df_dataset['total_score'].mean()
    })
    df_dataset = df_dataset.fillna({
        'proof': df_dataset['proof'].mean(),
        'avg_msrp': df_dataset['avg_msrp'].mean(),
        'popularity': df_dataset['popularity'].mean(),
        'total_score': df_dataset['total_score'].mean()
    })
    
    # Normalize numerical attributes
    max_proof_diff = max(df_dataset['proof'].max(), df_user['proof'].max()) - min(df_dataset['proof'].min(), df_user['proof'].min()) if 'proof' in df_user else df_dataset['proof'].max() - df_dataset['proof'].min()
    max_price_diff = max(df_dataset['avg_msrp'].max(), df_user['average_msrp'].max()) - min(df_dataset['avg_msrp'].min(), df_user['average_msrp'].min()) if 'average_msrp' in df_user else df_dataset['avg_msrp'].max() - df_dataset['avg_msrp'].min()
    max_popularity_diff = max(df_dataset['popularity'].max(), df_user['popularity'].max()) - min(df_dataset['popularity'].min(), df_user['popularity'].min()) if 'popularity' in df_user else df_dataset['popularity'].max() - df_dataset['popularity'].min()
    max_score_diff = max(df_dataset['total_score'].max(), df_user['total_score'].max()) - min(df_dataset['total_score'].min(), df_user['total_score'].min()) if 'total_score' in df_user else df_dataset['total_score'].max() - df_dataset['total_score'].min()
    
    def similarity(b1, b2):
        spirit_sim = 1 if b1.get('spirit', '') == b2['spirit_type'] else 0
        brand_sim = 1 if b1.get('brand', '') == b2['brand_id'] else 0
        proof_diff = abs(float(b1.get('proof', df_dataset['proof'].mean())) - float(b2['proof'])) / max_proof_diff if max_proof_diff else 0
        price_diff = abs(float(b1.get('average_msrp', df_dataset['avg_msrp'].mean())) - float(b2['avg_msrp'])) / max_price_diff if max_price_diff else 0
        popularity_diff = abs(float(b1.get('popularity', df_dataset['popularity'].mean())) - float(b2['popularity'])) / max_popularity_diff if max_popularity_diff else 0
        score_diff = abs(float(b1.get('total_score', df_dataset['total_score'].mean())) - float(b2['total_score'])) / max_score_diff if max_score_diff else 0
        return (
            0.3 * spirit_sim +
            0.2 * brand_sim +
            0.15 * (1 - proof_diff) +
            0.15 * (1 - price_diff) +
            0.1 * (1 - popularity_diff) +
            0.1 * (1 - score_diff)
        )
    
    scores = []
    for _, dataset_row in df_dataset.iterrows():
        max_sim = max(similarity(user_row, dataset_row) for _, user_row in df_user.iterrows())
        scores.append(max_sim)
    
    df_dataset['score'] = scores
    user_ids = [b.get('id', '') for b in user_bottles]
    df_recommend = df_dataset[~df_dataset['id'].isin(user_ids)]
    return df_recommend.sort_values(by='score', ascending=False).head(top_n).to_dict('records')

# Directories and files
CHAT_DIR = Path("chat_histories")
CHAT_DIR.mkdir(exist_ok=True)
METADATA_FILE = CHAT_DIR / "chat_metadata.json"

# Initialize metadata
if not METADATA_FILE.exists():
    with open(METADATA_FILE, 'w') as f:
        json.dump({}, f)

# Load metadata
with open(METADATA_FILE, 'r') as f:
    metadata = json.load(f)

# Session state initialization
if 'bar_data' not in st.session_state:
    st.session_state.bar_data = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'chat_title' not in st.session_state:
    st.session_state.chat_title = "Untitled Chat"
if 'username' not in st.session_state:
    st.session_state.username = ""

# Main page
st.title("Bob the Whisky Expert")
st.write("Hi! I'm Bob, your whisky expert. Enter your BAXUS username to fetch your bar and start chatting.")

# Username input and Fetch Bar Data
username = st.text_input("BAXUS Username", value=st.session_state.username, placeholder="Enter your username")
if st.button("Fetch Bar Data"):
    if username:
        st.session_state.username = username
        url = f"http://services.baxus.co/api/bar/user/{username}"
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            st.session_state.bar_data = response.json()
            st.success("Bar data fetched successfully!")
            if st.session_state.bar_data:
                df_bar = pd.DataFrame([b['product'] for b in st.session_state.bar_data])
                st.write("Your current bar collection:")
                # Display only available columns
                display_columns = [col for col in ['name', 'spirit', 'brand', 'proof', 'average_msrp'] if col in df_bar.columns]
                st.table(df_bar[display_columns])
                bar_names = ", ".join(df_bar['name'].tolist())
                bob_message = f"I've noted your bar: {bar_names}. Ready to make recommendations based on this and my knowledge of {len(df_dataset)} bottles!"
                st.session_state.messages.append({"role": "assistant", "content": bob_message})
        except requests.RequestException as e:
            st.error(f"Error fetching bar data: {e}")
    else:
        st.error("Please enter a username.")

# Sidebar
with st.sidebar:
    st.header("Chat Management")
    
    # Chat histories
    st.subheader("Previous Chats")
    if st.session_state.username:
        meta = metadata.get(st.session_state.username, {})
        chat_files = list(CHAT_DIR.glob(f"{st.session_state.username}_*.json"))
        chat_options = [(meta.get(f.stem, {}).get('title', 'Untitled Chat'), f.stem) for f in chat_files if f.stem in meta]
        chat_options = sorted(chat_options, key=lambda x: x[1], reverse=True)
        
        for title, chat_id in chat_options:
            if st.button(f"{title} ({chat_id.split('_')[1]})", key=chat_id):
                chat_file = CHAT_DIR / f"{chat_id}.json"
                if chat_file.exists():
                    with open(chat_file, 'r') as f:
                        st.session_state.messages = json.load(f)
                    st.session_state.current_chat_id = chat_id
                    st.session_state.chat_title = meta.get(chat_id, {}).get('title', 'Untitled Chat')
                    st.rerun()
    else:
        st.write("Enter a username to view chat histories.")
    
    # Chat title input
    st.subheader("Current Chat Title")
    chat_title = st.text_input("Edit Chat Title", value=st.session_state.chat_title, key="chat_title_input")
    if chat_title != st.session_state.chat_title:
        st.session_state.chat_title = chat_title
        if st.session_state.username and st.session_state.current_chat_id:
            if st.session_state.username not in metadata:
                metadata[st.session_state.username] = {}
            metadata[st.session_state.username][st.session_state.current_chat_id] = {
                'title': chat_title,
                'timestamp': st.session_state.current_chat_id.split('_')[1]
            }
            with open(METADATA_FILE, 'w') as f:
                json.dump(metadata, f)
    
    # Chat controls
    st.subheader("Chat Controls")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start New Chat"):
            st.session_state.messages = []
            st.session_state.current_chat_id = f"{st.session_state.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if st.session_state.username else None
            st.session_state.chat_title = "Untitled Chat"
            st.success("Started a new chat!")
    with col2:
        if st.button("Clear Selected"):
            if st.session_state.current_chat_id:
                chat_file = CHAT_DIR / f"{st.session_state.current_chat_id}.json"
                if chat_file.exists():
                    chat_file.unlink()
                    if st.session_state.username in metadata and st.session_state.current_chat_id in metadata[st.session_state.username]:
                        del metadata[st.session_state.username][st.session_state.current_chat_id]
                        with open(METADATA_FILE, 'w') as f:
                            json.dump(metadata, f)
                    st.success("Selected chat deleted!")
                    st.session_state.messages = []
                    st.session_state.current_chat_id = None
                    st.session_state.chat_title = "Untitled Chat"
                    st.rerun()
    
    if st.button("Clear All Histories"):
        if st.session_state.username:
            for chat_file in CHAT_DIR.glob(f"{st.session_state.username}_*.json"):
                chat_file.unlink()
            if st.session_state.username in metadata:
                del metadata[st.session_state.username]
                with open(METADATA_FILE, 'w') as f:
                    json.dump(metadata, f)
            st.success("All chat histories deleted!")
            st.session_state.messages = []
            st.session_state.current_chat_id = None
            st.session_state.chat_title = "Untitled Chat"
            st.rerun()

# Main area: Bar data and chat
if st.session_state.bar_data:
    df_bar = pd.DataFrame([b['product'] for b in st.session_state.bar_data])
    st.write("Your Current Bar Collection:")
    display_columns = [col for col in ['name', 'spirit', 'brand', 'proof', 'average_msrp'] if col in df_bar.columns]
    st.table(df_bar[display_columns])

st.header("Chat with Bob")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "I recommend" in message["content"]:
            try:
                rec_start = message["content"].index("I recommend:") + 12
                rec_end = message["content"].index(".", rec_start)
                rec_text = message["content"][rec_start:rec_end]
                rec_bottles = [b.strip() for b in rec_text.split(",")]
                for bottle in rec_bottles:
                    bottle_name = bottle.split(" (")[0]
                    bottle_data = df_dataset[df_dataset['name'].str.contains(bottle_name, case=False, na=False)]
                    if not bottle_data.empty and pd.notna(bottle_data.iloc[0]['image_url']):
                        st.image(bottle_data.iloc[0]['image_url'], width=100, caption=bottle_name)
            except (ValueError, IndexError):
                pass

user_message = st.chat_input("Ask Bob for recommendations (e.g., 'What should I add to my collection?')")
if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)
    
    if st.session_state.bar_data is None:
        response = "Please provide your BAXUS username and fetch your bar data to start!"
    else:
        user_bottles = [b['product']['name'] for b in st.session_state.bar_data]
        recent_messages = st.session_state.messages[-5:]
        chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
        if "recommend" in user_message.lower() or "add to my collection" in user_message.lower():
            recommendations = compute_recommendations(st.session_state.bar_data, df_dataset)
            if not recommendations:
                response = "Looks like I couldn't find any recommendations. Do you have bottles in your bar?"
            else:
                recommended_bottles = ", ".join([f"{r['name']} ({r['spirit_type']}, ${r['avg_msrp']:.2f})" for r in recommendations])
                prompt = (
                    f"I'm Bob, a whisky expert. I know the user's bar: {', '.join(user_bottles)}. "
                    f"I have access to a dataset of {len(df_dataset)} bottles with details like name, spirit type, proof, price, popularity, and scores: {dataset_summary}. "
                    f"Recent chat: {chat_context}. "
                    f"Based on the user's bar, I recommend: {recommended_bottles}. "
                    "Explain in a friendly, expert tone why these bottles are great additions, considering their popularity, scores, and alignment with the user's collection."
                )
                try:
                    response = model.generate_content(prompt).text
                except Exception as e:
                    response = f"Sorry, I had trouble generating a response: {e}"
        else:
            prompt = (
                f"I'm Bob, a whisky expert. I know the user's bar: {', '.join(user_bottles)}. "
                f"I have access to a dataset of {len(df_dataset)} bottles with details like name, spirit type, proof, price, popularity, and scores: {dataset_summary}. "
                f"Recent chat: {chat_context}. "
                f"Respond to this user query in a friendly, expert tone: '{user_message}'"
            )
            try:
                response = model.generate_content(prompt).text
            except Exception as e:
                response = f"Sorry, I had trouble understanding that: {e}"
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
        if "I recommend" in response:
            try:
                rec_start = response.index("I recommend:") + 12
                rec_end = response.index(".", rec_start)
                rec_text = response[rec_start:rec_end]
                rec_bottles = [b.strip() for b in rec_text.split(",")]
                for bottle in rec_bottles:
                    bottle_name = bottle.split(" (")[0]
                    bottle_data = df_dataset[df_dataset['name'].str.contains(bottle_name, case=False, na=False)]
                    if not bottle_data.empty and pd.notna(bottle_data.iloc[0]['image_url']):
                        st.image(bottle_data.iloc[0]['image_url'], width=100, caption=bottle_name)
            except (ValueError, IndexError):
                pass
    
    # Save chat history
    if st.session_state.current_chat_id and st.session_state.username:
        chat_file = CHAT_DIR / f"{st.session_state.current_chat_id}.json"
        with open(chat_file, 'w') as f:
            json.dump(st.session_state.messages, f)
        # Update metadata
        if st.session_state.username not in metadata:
            metadata[st.session_state.username] = {}
        metadata[st.session_state.username][st.session_state.current_chat_id] = {
            'title': st.session_state.chat_title,
            'timestamp': st.session_state.current_chat_id.split('_')[1]
        }
        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f)