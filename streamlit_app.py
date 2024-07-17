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

# Function to get the channel details
def get_channel_details(channel_id):
    url = f'https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={channel_id}&key={st.secrets["youtube_api_key"]}'
    response = requests.get(url)
    return response.json()

# Function to get all channel videos
def get_all_channel_videos(channel_id):
    videos = []
    next_page_token = None
    while True:
        url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults=50&order=date&type=video&key={st.secrets["youtube_api_key"]}'
        if next_page_token:
            url += f'&pageToken={next_page_token}'
        response = requests.get(url)
        data = response.json()
        videos.extend(data['items'])
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break
    return videos

# Function to get video details
def get_video_details(video_id):
    url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id={video_id}&key={st.secrets["youtube_api_key"]}'
    response = requests.get(url)
    return response.json()

def main():
    st.set_page_config(layout="wide", page_title="YouTube Channel Statistics")

    # Load custom CSS
    local_css("style.css")

    # Page header with logo
    st.markdown("""
    <div style="text-align: center;">
        <img src="https://igtoolsapk.in/wp-content/uploads/2024/07/Youtube-Statistics-Logo-New.png" alt="YouTube Statistics Logo" style="width: 150px; height: 150px;">
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="title">YouTube Channel Statistics</h1>', unsafe_allow_html=True)

    # Input section
    st.markdown("<div class='input-section'>", unsafe_allow_html=True)
    channel_input = st.text_input("YouTube Channel Username or Link", placeholder="Enter the YouTube channel username (e.g. @channelname) or link")
    st.markdown("</div>", unsafe_allow_html=True)

    # Button section
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='button-section'>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Analyze", key="analyze")
        reset_button = st.button("🔄 Reset", key="reset")
        st.markdown("</div>", unsafe_allow_html=True)

    if reset_button:
        st.experimental_rerun()

    if analyze_button and channel_input:
        try:
            with st.spinner("Analyzing channel data..."):
                # Extract channel name from input
                channel_name = extract_channel_name(channel_input)

                # Step 1: Get the channel ID using RapidAPI
                channel_id = get_channel_id(channel_name)

                # Step 2: Use the channel ID to get detailed channel information
                channel_details = get_channel_details(channel_id)
                channel_title = channel_details['items'][0]['snippet']['title']
                subscribers = int(channel_details['items'][0]['statistics']['subscriberCount'])
                total_views = int(channel_details['items'][0]['statistics']['viewCount'])
                video_count = int(channel_details['items'][0]['statistics']['videoCount'])
                channel_created_on = datetime.strptime(channel_details['items'][0]['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").strftime("%B %d, %Y")

                # Display Channel Overview
                st.markdown("<h2 class='section-header'>Channel Overview</h2>", unsafe_allow_html=True)
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.markdown(f"<div class='metric-box channel-name'><h3>Channel Name</h3><p>{channel_title}</p></div>", unsafe_allow_html=True)
                col2.markdown(f"<div class='metric-box subscribers'><h3>Subscribers</h3><p>{subscribers:,}</p></div>", unsafe_allow_html=True)
                col3.markdown(f"<div class='metric-box total-views'><h3>Total Views</h3><p>{total_views:,}</p></div>", unsafe_allow_html=True)
                col4.markdown(f"<div class='metric-box video-count'><h3>Video Count</h3><p>{video_count:,}</p></div>", unsafe_allow_html=True)
                col5.markdown(f"<div class='metric-box channel-created'><h3>Channel Created On</h3><p>{channel_created_on}</p></div>", unsafe_allow_html=True)

                # Step 3: Use the channel ID to get all of the channel's videos
                channel_videos = get_all_channel_videos(channel_id)
                videos_data = []
                for video in channel_videos:
                    video_id = video['id']['videoId']
                    video_title = video['snippet']['title']
                    video_published_at = video['snippet']['publishedAt']
                    video_details = get_video_details(video_id)
                    view_count = int(video_details['items'][0]['statistics']['viewCount'])
                    like_count = int(video_details['items'][0]['statistics']['likeCount'])
                    comment_count = int(video_details['items'][0]['statistics']['commentCount'])
                    duration = str(parse_duration(video_details['items'][0]['contentDetails']['duration']))
                    thumbnail_url = video_details['items'][0]['snippet']['thumbnails']['medium']['url']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    videos_data.append([video_title, duration, view_count, like_count, comment_count, video_published_at, thumbnail_url, video_url])

                # Create DataFrame for videos data
                videos_df = pd.DataFrame(videos_data, columns=['Title', 'Duration', 'Views Count', 'Likes Count', 'Comments Count', 'Published Date', 'Thumbnail URL', 'Video URL'])
                videos_df['Published Date'] = pd.to_datetime(videos_df['Published Date'])

                # Most Recent and Most Popular Videos
                st.markdown("<h2 class='section-header'>Featured Videos</h2>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)

                with col1:
                    most_recent = videos_df.iloc[0]
                    st.markdown("<h3>Most Recent Video</h3>", unsafe_allow_html=True)
                    st.markdown(f"<div class='video-container'><a href='{most_recent['Video URL']}' target='_blank'><img src='{most_recent['Thumbnail URL']}' alt='Most Recent Video Thumbnail'><div class='play-button'></div></a></div>", unsafe_allow_html=True)
                    st.markdown(f"<p><a href='{most_recent['Video URL']}' target='_blank'>{most_recent['Title']}</a></p>", unsafe_allow_html=True)

                with col2:
                    most_popular = videos_df.nlargest(1, 'Views Count').iloc[0]
                    st.markdown("<h3>Most Popular Video</h3>", unsafe_allow_html=True)
                    st.markdown(f"<div class='video-container'><a href='{most_popular['Video URL']}' target='_blank'><img src='{most_popular['Thumbnail URL']}' alt='Most Popular Video Thumbnail'><div class='play-button'></div></a></div>", unsafe_allow_html=True)
                    st.markdown(f"<p><a href='{most_popular['Video URL']}' target='_blank'>{most_popular['Title']}</a></p>", unsafe_allow_html=True)

                # Top 5 Videos by Views and Top 5 Liked Videos
                st.markdown("<h2 class='section-header'>Top 5 Videos</h2>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                top_5_videos = videos_df.nlargest(5, 'Views Count')[['Title', 'Views Count', 'Video URL']]
                top_5_liked_videos = videos_df.nlargest(5, 'Likes Count')[['Title', 'Likes Count', 'Video URL']]
                
                with col1:
                    st.markdown("<h3>Top 5 Videos by Views</h3>", unsafe_allow_html=True)
                    for i, row in top_5_videos.iterrows():
                        st.markdown(f"<div class='metric-box'><a href='{row['Video URL']}' target='_blank'>{row['Title']}</a> - {row['Views Count']:,} Views</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<h3>Top 5 Liked Videos</h3>", unsafe_allow_html=True)
                    for i, row in top_5_liked_videos.iterrows():
                        st.markdown(f"<div class='metric-box'><a href='{row['Video URL']}' target='_blank'>{row['Title']}</a> - {row['Likes Count']:,} Likes</div>", unsafe_allow_html=True)

                # Time-Series Data of Views, Likes, and Comments
                st.markdown("<h2 class='section-header'>Videos Analysis Over Time</h2>", unsafe_allow_html=True)
                time_series_data = videos_df[['Published Date', 'Views Count', 'Likes Count', 'Comments Count']].copy()
                time_series_data.set_index('Published Date', inplace=True)
                time_series_data.sort_index(inplace=True)

                # Line chart for Views, Likes, and Comments over time
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=time_series_data.index, y=time_series_data['Views Count'], mode='lines+markers', name='Views Count', line=dict(color='royalblue')))
                fig.add_trace(go.Scatter(x=time_series_data.index, y=time_series_data['Likes Count'], mode='lines+markers', name='Likes Count', line=dict(color='firebrick')))
                fig.add_trace(go.Scatter(x=time_series_data.index, y=time_series_data['Comments Count'], mode='lines+markers', name='Comments Count', line=dict(color='green')))
                fig.update_layout(title='Views, Likes, and Comments Over Time', xaxis_title='Date', yaxis_title='Count')
                st.plotly_chart(fig, use_container_width=True)

                # Pie chart for Top 10 videos by views distribution
                top_10_videos = videos_df.nlargest(10, 'Views Count')
                fig = px.pie(top_10_videos, names='Title', values='Views Count', title='Top 10 Videos by Views Distribution')
                st.plotly_chart(fig, use_container_width=True)

                # Display full data table
                st.markdown("<h2 class='section-header'>Full Videos Data</h2>", unsafe_allow_html=True)
                st.dataframe(videos_df[['Title', 'Duration', 'Views Count', 'Likes Count', 'Comments Count', 'Published Date']])

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
