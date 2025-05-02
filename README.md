# Bob the Whisky Expert

**Bob the Whisky Expert** is a Streamlit-based web application that provides personalized whisky recommendations. Powered by the Gemini AI model, Bob fetches a user's bar data from the BAXUS API, leverages a dataset of whisky bottles, and offers expert recommendations with images. The app features a polished UI, chat history management, and secure configuration via environment variables.

## Features

- **Personalized Recommendations**: Bob analyzes your bar (via BAXUS API) and recommends whiskies based on a dataset with columns: `id`, `name`, `size`, `proof`, `abv`, `spirit_type`, `brand_id`, `popularity`, `image_url`, `avg_msrp`, `fair_price`, `shelf_price`, `total_score`, `wishlist_count`, `vote_count`, `bar_count`, `ranking`.
- **Image Display**: Recommendations include bottle images from the dataset's `image_url`.
- **Chat Interface**: Interactive chat with Bob, maintaining context from the last 5 messages.
- **Chat History Management**:
  - Saves chats as `<username>_<timestamp>.json` in `chat_histories/`.
  - Sidebar displays clickable chat histories, editable titles, and controls (new chat, clear selected, clear all).
- **Secure Configuration**: Uses a `.env` file for Gemini API key and dataset path.
- **Polished UI**: Custom CSS for a clean, responsive interface with styled sidebar, main page, and chat.
- **Main Page Login**: Username input and "Fetch Bar Data" button to load bar data.

## Prerequisites

- **Python**: 3.8 or higher.
- **Dependencies**: Listed in `requirements.txt`.
- **Gemini API Key**: Obtain from Google Cloud for Gemini AI.
- **Dataset**: `bottles_dataset.csv` with the specified columns.
- **BAXUS API Access**: Ensure the API (`http://services.baxus.co/api/bar/user/{username}`) is accessible.

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Omerhrr/bob-whisky.git
   cd bob-whiskey
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install streamlit requests pandas google-generativeai python-dotenv
   ```

4. **Prepare the Dataset**:
   - Place `bottles_recommendation_dataset.csv` in the project root or update the path in `.env`.
   - Ensure it contains columns: `id`, `name`, `size`, `proof`, `abv`, `spirit_type`, `brand_id`, `popularity`, `image_url`, `avg_msrp`, `fair_price`, `shelf_price`, `total_score`, `wishlist_count`, `vote_count`, `bar_count`, `ranking`.

5. **Create .env File**:
   In the project root, create a `.env` file:
   ```
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   DATASET_PATH=bottles_recommendation_dataset.csv
   ```
   - Replace `your_actual_gemini_api_key_here` with your Gemini API key.
   - Adjust `DATASET_PATH` if the dataset is in a different location (relative or absolute path).

6. **Ensure File Permissions**:
   Grant write permissions for the `chat_histories/` directory to store chat history JSON files:
   ```bash
   mkdir -p chat_histories
   chmod -R u+w chat_histories
   ```

## Running the Application

1. **Activate the Virtual Environment** (if not already active):
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Run the Streamlit App**:
   ```bash
   streamlit run bob.py
   ```

3. **Access the App**:
   Open your browser and navigate to http://localhost:8501.

## Usage

### Log In:
- On the main page, enter your BAXUS username (e.g., `carriebaxus`) in the input field.
- Click `Fetch Bar Data` to retrieve your bar from the BAXUS API.
- A table displays your bar's bottles (columns like name, spirit, etc., based on API data).

### Chat with Bob:
- Use the chat input to ask questions (e.g., "What should I add to my collection?").
- Bob responds with recommendations, including bottle images (via `image_url`).
- Recommendations consider your bar and the dataset, factoring in `spirit_type`, `brand_id`, `proof`, `avg_msrp`, `popularity`, and `total_score`.

### Manage Chat Histories:
- **Sidebar**: View all chat histories for your username as clickable buttons (e.g., "Bourbon Recommendations (20250502_123456)").
- **Edit Title**: Update the current chat's title in the "Current Chat Title" input.
- **Controls**:
  - **Start New Chat**: Begin a fresh conversation.
  - **Clear Selected**: Delete the current chat.
  - **Clear All Histories**: Remove all chats for the username.
- Chats are saved as `<username>_<timestamp>.json` in `chat_histories/`.

### View Recommendations:
- Recommendations appear in the chat with images and details (e.g., "Blanton's Single Barrel (Bourbon, $74.99)").
- Bob explains why each bottle suits your collection, using dataset metrics like popularity and scores.

## Project Structure

```
bob-the-whisky-expert/
├── bob.py                    # Main Streamlit application
├── bottles_dataset.csv       # Dataset with bottle details
├── .env                      # Environment variables (API key, dataset path)
├── chat_histories/           # Directory for chat history JSON files
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Implementation Details

### Tech Stack:
- **Streamlit**: Web framework for the UI.
- **Google Generative AI (Gemini)**: Powers Bob's responses.
- **Pandas**: Handles dataset and bar data processing.
- **Requests**: Fetches bar data from BAXUS API.
- **python-dotenv**: Loads `.env` for secure configuration.

### Key Components:
- **Recommendation Logic** (`compute_recommendations`):
  - Compares user's bar to the dataset using similarity metrics (spirit type, brand, proof, price, popularity, total score).
  - Handles missing columns in bar data (e.g., `total_score`, `popularity`) by using dataset means.
  - Returns top 3 recommendations, excluding bottles already in the user's bar.

- **Chat History**:
  - Stored as JSON files (`<username>_<timestamp>.json`) in `chat_histories/`.
  - Metadata (`chat_metadata.json`) tracks titles and timestamps.
  - Sidebar loads histories dynamically based on username.

- **Image Display**:
  - Extracts recommended bottle names from Bob's response.
  - Matches to dataset's `image_url` and renders with `st.image`.

- **UI Styling**:
  - Custom CSS for sidebar (blue buttons, light background), main page (orange buttons, card layout), and chat (user/assistant message styles).
  - Responsive design with rounded corners, shadows, and hover effects.

- **Error Handling**:
  - Validates `.env` variables at startup.
  - Gracefully handles missing bar data columns.
  - Catches API and Gemini errors, displaying user-friendly messages.

## Troubleshooting

- **KeyError: 'total_score'**:
  - Ensure `bottles_dataset.csv` has all required columns.
  - Verify the BAXUS API response; it may lack `total_score` or `popularity`. The code handles this by using dataset means.

- **Missing Environment Variables**:
  - Check `.env` for `GEMINI_API_KEY` and `DATASET_PATH`.
  - Ensure no trailing spaces or quotes in `.env` values.

- **API Errors**:
  - Confirm the BAXUS API URL is accessible.
  - Check your network connection or API credentials.

- **Image Not Displaying**:
  - Verify `image_url` in `bottles_dataset.csv` contains valid URLs.
  - Ensure internet access for fetching images.

## Future Enhancements

- Add a search bar for chat histories.
- Allow sorting chat histories by title.
- Display bottle images in the bar data table.
- Add loading indicators for API calls and image fetching.
- Implement logging to debug API response structures.
