import streamlit as st
import http.client
import json
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from isodate import parse_duration
import re
import dateutil.parser

# Custom CSS to improve the look and feel
def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Function to extract channel name from input
def extract_channel_name(input_string):
    if input_string.startswith('https://www.youtube.com/'):
        match = re.search(r'@([\w-]+)', input_string)
        if match:
            return '@' + match.group(1)
    return input_string

# Function to get the channel ID using RapidAPI
def get_channel_id(channel_name):
    conn = http.client.HTTPSConnection("youtuber-success-estimator.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': st.secrets["rapidapi_key"],
        'x-rapidapi-host': "youtuber-success-estimator.p.rapidapi.com"
    }
    conn.request("GET", f"/api/v0/analytics/creators/estimator?channelName={channel_name}&channelType=youtube", headers=headers)
    res = conn.getresponse()
    data = res.read()
    response_data = json.loads(data.decode("utf-8"))
    return response_data['data']['channel']['id']

# Function to get the channel details and video data in a single API call
def get_channel_and_video_data(channel_id):
    url = f'https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&id={channel_id}&key={st.secrets["youtube_api_key"]}'
    response = requests.get(url)
    channel_data = response.json()

    uploads_playlist_id = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    videos = []
    next_page_token = None
    while True:
        playlist_url = f'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={uploads_playlist_id}&maxResults=50&key={st.secrets["youtube_api_key"]}'
        if next_page_token:
            playlist_url += f'&pageToken={next_page_token}'
        playlist_response = requests.get(playlist_url)
        playlist_data = playlist_response.json()

        video_ids = ','.join([item['contentDetails']['videoId'] for item in playlist_data['items']])
        videos_url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id={video_ids}&key={st.secrets["youtube_api_key"]}'
        videos_response = requests.get(videos_url)
        videos_data = videos_response.json()

        for video in videos_data['items']:
            video_id = video['id']
            video_title = video['snippet']['title']
            video_published_at = video['snippet']['publishedAt']
            view_count = int(video['statistics'].get('viewCount', 0))
            like_count = int(video['statistics'].get('likeCount', 0))
            comment_count = int(video['statistics'].get('commentCount', 0))
            duration = str(parse_duration(video['contentDetails']['duration']))
            thumbnail_url = video['snippet']['thumbnails']['medium']['url']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            videos.append([video_title, duration, view_count, like_count, comment_count, video_published_at, thumbnail_url, video_url])

        next_page_token = playlist_data.get('nextPageToken')
        if not next_page_token:
            break

    return channel_data, videos

def generate_insights_and_suggestions(channel_title, subscribers, total_views, video_count, channel_created_on, videos_df):
    prompt = f"""
    Act as an Expert of Analyzing Youtube Channels by analyzing different Charts of a Youtube Channel and Analyze the following YouTube channel statistics and provide insights and suggestions for better engagement:

    Channel Name: {channel_title}
    Subscribers: {subscribers:,}
    Total Views: {total_views:,}
    Video Count: {video_count:,}
    Channel Created On: {channel_created_on}

    Top 5 Videos by Views:
    {videos_df.nlargest(5, 'Views Count')[['Title', 'Views Count']].to_string(index=False)}

    Top 5 Liked Videos:
    {videos_df.nlargest(5, 'Likes Count')[['Title', 'Likes Count']].to_string(index=False)}

    Video Upload Frequency (last 12 months):
    {videos_df['Month'].value_counts().sort_index().to_string()}

    Based on this data, provide:
    1. 3-5 key insights about the channel's performance
    2. 5-7 actionable suggestions for improving engagement and growing the channel

    Format the output as two separate lists: one for Insights and one for Suggestions. Each list should be prefixed with either "Insights:" or "Suggestions:" respectively.
    """

    insights_and_suggestions = generate_response_with_gemini(prompt)
    return insights_and_suggestions

def generate_response_with_gemini(prompt):
    api_key = st.secrets["gemini_api_key"]
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"

    headers = {
        'Content-Type': 'application/json'
    }

    body = {
        'contents': [
            {
                'parts': [
                    { 'text': prompt }
                ]
            }
        ]
    }

    response = requests.post(api_url, headers=headers, json=body)
    data = response.json()

    if response.status_code == 200:
        return data['candidates'][0]['content']['parts'][0]['text']
    else:
        raise Exception(f"Error generating response from Gemini API: {data}")

def main():
    st.set_page_config(layout="wide", page_title="YouTube Channel Statistics")

    # Load custom CSS
    local_css("style.css")

    # Page header with logo
    st.markdown('<div class="logo-container"><img src="https://igtoolsapk.in/wp-content/uploads/2024/07/Youtube-Statistics-Logo-New.png" alt="YouTube Statistics Logo" class="logo"></div>', unsafe_allow_html=True)
    st.markdown("<h1 class='title' title='Get detailed statistics about your favorite YouTube channels'>YouTube Channel Statistics</h1>", unsafe_allow_html=True)

    # Initialize session state for channel input
    if 'channel_input' not in st.session_state:
        st.session_state.channel_input = ''

    # Input section
    st.markdown("<div class='input-section'>", unsafe_allow_html=True)
    channel_input = st.text_input("YouTube Channel Username or Link", value=st.session_state.channel_input, placeholder="Enter the YouTube channel username (e.g. @channelname) or link")
    st.markdown("</div>", unsafe_allow_html=True)

    # Create columns for buttons
    col1, col2, col3 = st.columns([1.5, 0.32, 2])

    with col2:
        analyze_button = st.button("Analyze", key="analyze", help="Click to analyze the channel")

    with col3:
        reset_button = st.button("Reset", key="reset", help="Click to reset the input")

    if reset_button:
        st.session_state.channel_input = ''
        st.rerun()

    if analyze_button and channel_input:
        st.session_state.channel_input = channel_input
        try:
            with st.spinner("Analyzing channel data..."):
                # Extract channel name from input
                channel_name = extract_channel_name(channel_input)

                # Step 1: Get the channel ID using RapidAPI
                channel_id = get_channel_id(channel_name)

                # Step 2: Use the channel ID to get detailed channel information and video data
                channel_details, videos_data = get_channel_and_video_data(channel_id)

                channel_title = channel_details['items'][0]['snippet']['title']
                subscribers = int(channel_details['items'][0]['statistics']['subscriberCount'])
                total_views = int(channel_details['items'][0]['statistics']['viewCount'])
                video_count = int(channel_details['items'][0]['statistics']['videoCount'])
                channel_created_on = None
                for fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ'):
                    try:
                        channel_created_on = datetime.strptime(channel_details['items'][0]['snippet']['publishedAt'], fmt)
                        break
                    except ValueError:
                        pass

                if channel_created_on is not None:
                    channel_created_on = channel_created_on.strftime("%B %d, %Y")
                else:
                    raise ValueError(f'No valid date format found for {channel_details["items"][0]["snippet"]["publishedAt"]}')

                # Display Channel Overview
                st.markdown("<h2 class='section-header'>Channel Overview</h2>", unsafe_allow_html=True)
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.markdown(f"<div class='metric-box channel-name' style='background-color: #f0f8ff;'><h3>Channel Name</h3><p>{channel_title}</p></div>", unsafe_allow_html=True)
                col2.markdown(f"<div class='metric-box subscribers' style='background-color: #f5f5dc;'><h3>Subscribers</h3><p>{subscribers:,}</p></div>", unsafe_allow_html=True)
                col3.markdown(f"<div class='metric-box total-views' style='background-color: #ffe4e1;'><h3>Total Views</h3><p>{total_views:,}</p></div>", unsafe_allow_html=True)
                col4.markdown(f"<div class='metric-box video-count' style='background-color: #fafad2;'><h3>Video Count</h3><p>{video_count:,}</p></div>", unsafe_allow_html=True)
                col5.markdown(f"<div class='metric-box channel-created' style='background-color: #e6e6fa;'><h3>Channel Created On</h3><p>{channel_created_on}</p></div>", unsafe_allow_html=True)

                # Create DataFrame for videos data
                videos_df = pd.DataFrame(videos_data, columns=['Title', 'Duration', 'Views Count', 'Likes Count', 'Comments Count', 'Published Date', 'Thumbnail URL', 'Video URL'])
                videos_df['Published Date'] = videos_df['Published Date'].apply(dateutil.parser.parse)

                # Most Recent and Most Popular Videos
                st.markdown("<h2 class='section-header'>Featured Videos</h2>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)

                with col1:
                    most_recent = videos_df.iloc[0]
                    st.markdown("<h3>Most Recent Video</h3>", unsafe_allow_html=True)
                    st.markdown(f"""
                        <div class='video-container' style='width: 100%; height: 0; padding-bottom: 56.25%; position: relative;'>
                            <a href='{most_recent['Video URL']}' target='_blank'>
                                <img src='{most_recent['Thumbnail URL']}' alt='Most Recent Video Thumbnail' style='position: absolute; width: 100%; height: 100%; object-fit: cover;'>
                                <div class='play-button' style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);'></div>
                            </a>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"<p><a href='{most_recent['Video URL']}' target='_blank'>{most_recent['Title']}</a></p>", unsafe_allow_html=True)

                with col2:
                    most_popular = videos_df.nlargest(1, 'Views Count').iloc[0]
                    st.markdown("<h3>Most Popular Video</h3>", unsafe_allow_html=True)
                    st.markdown(f"""
                        <div class='video-container' style='width: 100%; height: 0; padding-bottom: 56.25%; position: relative;'>
                            <a href='{most_popular['Video URL']}' target='_blank'>
                                <img src='{most_popular['Thumbnail URL']}' alt='Most Popular Video Thumbnail' style='position: absolute; width: 100%; height: 100%; object-fit: cover;'>
                                <div class='play-button' style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);'></div>
                            </a>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"<p><a href='{most_popular['Video URL']}' target='_blank'>{most_popular['Title']}</a></p>", unsafe_allow_html=True)

                # Top 5 Videos by Views and Top 5 Liked Videos
                st.markdown("<h2 class='section-header'>Top 5 Videos</h2>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)

                with col1:
                    top_5_views = videos_df.nlargest(5, 'Views Count')
                    fig_views = px.bar(top_5_views, x='Title', y='Views Count', title='Top 5 Videos by Views')
                    fig_views.update_layout(xaxis_tickangle=-45, height=500)
                    fig_views.update_traces(marker_color='#4CAF50', hovertemplate='<b>%{x}</b><br>Views: %{y:,}<br><a href="%{customdata[0]}">Watch Video</a>')
                    fig_views.update_traces(customdata=top_5_views[['Video URL']])
                    fig_views.update_xaxes(title_text='', ticktext=[f'<a href="{url}">{title}</a>' for title, url in zip(top_5_views['Title'], top_5_views['Video URL'])], tickvals=top_5_views['Title'])
                    st.plotly_chart(fig_views, use_container_width=True)

                with col2:
                    top_5_likes = videos_df.nlargest(5, 'Likes Count')
                    fig_likes = px.bar(top_5_likes, x='Title', y='Likes Count', title='Top 5 Liked Videos')
                    fig_likes.update_layout(xaxis_tickangle=-45, height=500)
                    fig_likes.update_traces(marker_color='#2196F3', hovertemplate='<b>%{x}</b><br>Likes: %{y:,}<br><a href="%{customdata[0]}">Watch Video</a>')
                    fig_likes.update_traces(customdata=top_5_likes[['Video URL']])
                    fig_likes.update_xaxes(title_text='', ticktext=[f'<a href="{url}">{title}</a>' for title, url in zip(top_5_likes['Title'], top_5_likes['Video URL'])], tickvals=top_5_likes['Title'])
                    st.plotly_chart(fig_likes, use_container_width=True)

                # Video Performance by Time
                st.markdown("<h2 class='section-header'>Video Performance by Time</h2>", unsafe_allow_html=True)
                fig_performance = px.line(videos_df.sort_values('Published Date'),
                                          x='Published Date', y='Views Count',
                                          hover_data=['Title'],
                                          title='Video Performance by Time')
                fig_performance.update_layout(height=600)
                fig_performance.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Date: %{x}<br>Views: %{y:,}<br><a href="%{customdata[1]}">Watch Video</a>')
                fig_performance.update_traces(customdata=videos_df[['Title', 'Video URL']])
                st.plotly_chart(fig_performance, use_container_width=True)

                # Video Upload Frequency Bar Chart
                st.markdown("<h2 class='section-header'>Video Upload Frequency</h2>", unsafe_allow_html=True)

                # Create a DataFrame with all 12 months
                all_months = pd.DataFrame({'Month': pd.date_range(start='2021-01-01', end='2021-12-31', freq='MS').strftime('%b')})

                # Extract the month from 'Published Date' and count the number of videos in each month
                videos_df['Month'] = videos_df['Published Date'].dt.strftime('%b')
                video_upload_frequency = videos_df['Month'].value_counts().reset_index()
                video_upload_frequency.columns = ['Month', 'Number of Videos']

                # Merge the DataFrame with all 12 months with the video upload frequency DataFrame
                video_upload_frequency = pd.merge(all_months, video_upload_frequency, on='Month', how='left').fillna(0)

                # Create the bar chart
                fig_upload_frequency = px.bar(video_upload_frequency, x='Month', y='Number of Videos',
                                              labels={'x': 'Month', 'y': 'Number of Videos'},
                                              title='Video Upload Frequency',
                                              color='Number of Videos',
                                              color_continuous_scale=px.colors.sequential.Plasma)
                fig_upload_frequency.update_layout(height=600)
                st.plotly_chart(fig_upload_frequency, use_container_width=True)

                # Engagement Metrics over Time
                st.markdown("<h2 class='section-header'>Engagement Metrics over Time</h2>", unsafe_allow_html=True)
                metrics_df = videos_df[['Published Date', 'Views Count', 'Likes Count', 'Comments Count', 'Title', 'Video URL']]
                metrics_df['Year'] = metrics_df['Published Date'].dt.year

                # Remove the 'Published Date' column from the DataFrame
                metrics_df = metrics_df.drop(columns=['Published Date'])

                # Group the data by year and calculate the sum of each metric
                grouped_metrics_df = metrics_df.groupby('Year').sum().reset_index()

                # Create a stacked area chart for each metric
                fig_metrics = go.Figure()
                fig_metrics.add_trace(go.Scatter(x=grouped_metrics_df['Year'], y=grouped_metrics_df['Views Count'], name='Views', fill='tozeroy', mode='none', stackgroup='one', marker_color='#4CAF50'))
                fig_metrics.add_trace(go.Scatter(x=grouped_metrics_df['Year'], y=grouped_metrics_df['Likes Count'], name='Likes', fill='tonexty', mode='none', stackgroup='one', marker_color='#2196F3'))
                fig_metrics.add_trace(go.Scatter(x=grouped_metrics_df['Year'], y=grouped_metrics_df['Comments Count'], name='Comments', fill='tonexty', mode='none', stackgroup='one', marker_color='#FFC107'))

                # Update layout
                fig_metrics.update_layout(title='Engagement Metrics over Time', xaxis_title='Year', yaxis_title='Count', height=600)

                # Update hover template
                fig_metrics.update_traces(hovertemplate='%{y:,} %{name}<br>Year: %{x}')

                # Show the chart
                st.plotly_chart(fig_metrics, use_container_width=True)

                # Comprehensive Video Table
                st.markdown("<h2 class='section-header'>Comprehensive Video Table</h2>", unsafe_allow_html=True)
                table_df = videos_df.drop(columns=['Thumbnail URL', 'Video URL'])

                # Apply CSS styles to the table
                st.markdown("""
                <style>
                .dataframe {
                    width: auto;
                    border-collapse: collapse;
                }

                .dataframe th {
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }

                .dataframe td {
                    border: 1px solid #ddd;
                    padding: 8px;
                }

                .dataframe tr:nth-child(even) {
                    background-color: #f2f2f2;
                }
                </style>
                """, unsafe_allow_html=True)

                # Display the table
                st.dataframe(table_df)

                # Generate insights and suggestions
                st.markdown("<h2 class='section-header'>AI Generated Insights and Suggestions</h2>", unsafe_allow_html=True)
                with st.spinner("Generating insights and suggestions..."):
                    insights_and_suggestions = generate_insights_and_suggestions(
                        channel_title, subscribers, total_views, video_count, channel_created_on, videos_df
                    )
                    
                # Split insights and suggestions
                insights, suggestions = insights_and_suggestions.split("Suggestions:")
                insights = insights.replace("Insights:", "").strip()
                suggestions = suggestions.strip()
            
                # Create two columns for insights and suggestions
                col1, col2 = st.columns(2)
            
                # Display insights in the first column
                with col1:
                    st.markdown("<div class='insights-box'><div class='box-title'>Insights</div><ul>", unsafe_allow_html=True)
                    insights_lines = insights.split("\n")
                    for line in insights_lines:
                        st.markdown(f"<li>{line}</li>", unsafe_allow_html=True)
                    st.markdown("</ul></div>", unsafe_allow_html=True)
            
                # Display suggestions in the second column
                with col2:
                    st.markdown("<div class='suggestions-box'><div class='box-title'>Suggestions</div><ul>", unsafe_allow_html=True)
                    suggestions_lines = suggestions.split("\n")
                    for line in suggestions_lines:
                        st.markdown(f"<li>{line}</li>", unsafe_allow_html=True)
                    st.markdown("</ul></div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("This could be due to an invalid channel name or API limitations. Please try again with a different channel or later.")

    # Footer
    st.markdown("""
    <div class="footer">
        Made with <span style="color: #e74c3c;">&#10084;</span> by <a href="https://www.linkedin.com/in/menajul-hoque/" target="_blank">Menajul Hoque</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
