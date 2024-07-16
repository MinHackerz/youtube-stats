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

# Function to get the channel videos
def get_channel_videos(channel_id):
    url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults=50&order=date&type=video&key={st.secrets["youtube_api_key"]}'
    response = requests.get(url)
    return response.json()

# Function to get video details
def get_video_details(video_id):
    url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id={video_id}&key={st.secrets["youtube_api_key"]}'
    response = requests.get(url)
    return response.json()

def main():
    st.set_page_config(layout="wide", page_title="YouTube Channel Statistics")

    # Load custom CSS
    local_css("style.css")

    # Page header
    st.markdown('<div class="title-box"><h1 class="title">YouTube Channel Statistics</h1></div>', unsafe_allow_html=True)

    # Input section
    st.markdown("<div class='input-section'>", unsafe_allow_html=True)
    channel_input = st.text_input("YouTube Channel Username or Link", placeholder="Enter the YouTube channel username (e.g. @channelname) or link")
    st.markdown("</div>", unsafe_allow_html=True)

    # Button section
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='button-section'>", unsafe_allow_html=True)
        analyze_button = st.button("Analyze", key="analyze")
        st.markdown("</div>", unsafe_allow_html=True)

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

                # Step 3: Use the channel ID to get the channel's videos
                channel_videos = get_channel_videos(channel_id)
                videos_data = []
                for video in channel_videos['items']:
                    video_id = video['id']['videoId']
                    video_title = video['snippet']['title']
                    video_published_at = video['snippet']['publishedAt']
                    video_details = get_video_details(video_id)
                    view_count = int(video_details['items'][0]['statistics']['viewCount'])
                    like_count = int(video_details['items'][0]['statistics']['likeCount'])
                    comment_count = int(video_details['items'][0]['statistics']['commentCount'])
                    duration = str(parse_duration(video_details['items'][0]['contentDetails']['duration']))
                    videos_data.append([video_id, video_title, duration, view_count, like_count, comment_count, video_published_at])

                # Create DataFrame for videos data
                videos_df = pd.DataFrame(videos_data, columns=['Video ID', 'Title', 'Duration', 'Views Count', 'Likes Count', 'Comments Count', 'Published Date'])
                videos_df['Published Date'] = pd.to_datetime(videos_df['Published Date'])

                # Top 5 Videos by Views and Top 5 Liked Videos
                st.markdown("<h2 class='section-header'>Top 5 Videos</h2>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)

                with col1:
                    top_5_views = videos_df.nlargest(5, 'Views Count')
                    fig_views = px.bar(top_5_views, x='Title', y='Views Count', title='Top 5 Videos by Views')
                    fig_views.update_layout(xaxis_tickangle=-45, height=500)
                    fig_views.update_traces(marker_color='#4CAF50')
                    st.plotly_chart(fig_views, use_container_width=True)

                with col2:
                    top_5_likes = videos_df.nlargest(5, 'Likes Count')
                    fig_likes = px.bar(top_5_likes, x='Title', y='Likes Count', title='Top 5 Liked Videos')
                    fig_likes.update_layout(xaxis_tickangle=-45, height=500)
                    fig_likes.update_traces(marker_color='#2196F3')
                    st.plotly_chart(fig_likes, use_container_width=True)

                # Video Performance by Time
                st.markdown("<h2 class='section-header'>Video Performance by Time</h2>", unsafe_allow_html=True)
                fig_performance = px.line(videos_df.sort_values('Published Date'),
                                          x='Published Date', y='Views Count',
                                          hover_data=['Title'],
                                          title='Video Performance by Time')
                fig_performance.update_layout(height=600)
                st.plotly_chart(fig_performance, use_container_width=True)

                # Engagement Metrics over Time
                st.markdown("<h2 class='section-header'>Engagement Metrics over Time</h2>", unsafe_allow_html=True)
                metrics_df = videos_df[['Published Date', 'Views Count', 'Likes Count', 'Comments Count']]
                metrics_df = metrics_df.sort_values('Published Date')
                fig_metrics = go.Figure()
                fig_metrics.add_trace(go.Scatter(x=metrics_df['Published Date'], y=metrics_df['Views Count'], mode='lines+markers', name='Views'))
                fig_metrics.add_trace(go.Scatter(x=metrics_df['Published Date'], y=metrics_df['Likes Count'], mode='lines+markers', name='Likes'))
                fig_metrics.add_trace(go.Scatter(x=metrics_df['Published Date'], y=metrics_df['Comments Count'], mode='lines+markers', name='Comments'))
                fig_metrics.update_layout(title='Engagement Metrics over Time', xaxis_title='Published Date', yaxis_title='Count', height=600)
                st.plotly_chart(fig_metrics, use_container_width=True)

                # Comprehensive Video Table
                st.markdown("<h2 class='section-header'>Comprehensive Video Table</h2>", unsafe_allow_html=True)
                st.dataframe(videos_df.style.highlight_max(axis=0), use_container_width=True)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    # Footer
    st.markdown("""
    <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f8f9fa;
            color: #343a40;
            text-align: center;
            padding: 10px 0;
            font-size: 14px;
        }
    </style>
    <div class="footer">
        Made with <span style="color: #e74c3c;">&#10084;</span> by <a href="https://www.linkedin.com/in/menajul-hoque/" target="_blank">Menajul Hoque</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
