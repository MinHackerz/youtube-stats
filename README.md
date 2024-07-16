# YouTube Channel Statistics

This is a Streamlit app that allows users to analyze the statistics of a YouTube channel. The app provides a comprehensive overview of the channel, including the number of subscribers, total views, and video count. It also displays graphs showing the top 5 videos by views and top 5 liked videos, video performance by time, and engagement metrics over time. Additionally, the app displays a comprehensive video table with all the retrieved columns and their records.

## Features

- Input field for YouTube channel username or link
- Analyze button to retrieve and display channel statistics
- Channel Overview section with data cards for channel name, subscribers, total views, video count, and channel creation date
- Top 5 Videos by Views and Top 5 Liked Videos graphs
- Video Performance by Time graph
- Engagement Metrics over Time graph
- Comprehensive Video Table

## Usage

1. Clone the repository to your local machine.
2. Install the required dependencies by running `pip install -r requirements.txt`.
3. Create a `.streamlit/secrets.toml` file in the project directory and add your API keys as follows:

```
YOUTUBE_API_KEY = "your_youtube_data_api_v3_key_here"
RAPIDAPI_KEY = "your_rapidapi_key_here"
```

4. Run the app by executing `streamlit run streamlit_app.py` in the terminal.
5. Enter the YouTube channel username or link in the input field and click the Analyze button to retrieve and display the channel statistics.

## Code Structure

The code is structured as follows:

- `streamlit_app.py`: The main Streamlit app file that contains the code for the app's layout, functionality, and data retrieval.
- `style.css`: A CSS file that contains the custom styles for the app.
- `requirements.txt`: A file that lists the required dependencies for the app.

## Credits

This project was created by [Menajul Hoque](https://www.linkedin.com/in/menajul-hoque/). The code is based on the Streamlit documentation and various online resources.
