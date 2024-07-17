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
    st.markdown('<div class="logo-container"><img src="https://igtoolsapk.in/wp-content/uploads/2024/07/Youtube-Statistics-Logo-New.png" alt="YouTube Statistics Logo" class="logo"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="title">YouTube Channel Statistics</h1>', unsafe_allow_html=True)

    # Input section
    st.markdown("<div class='input-section'>", unsafe_allow_html=True)
    channel_input = st.text_input("YouTube Channel Username or Link", placeholder="Enter the YouTube channel username (e.g. @channelname) or link")
    st.markdown("</div>", unsafe_allow_html=True)

    # Button section
    st.markdown("""
    <div class="button-section">
        <button id="analyze-btn" class="stButton">
            <svg class="button-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
            Analyze
        </button>
        <button id="reset-btn" class="stButton">
            <svg class="button-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
            </svg>
            Reset
        </button>
    </div>
    """, unsafe_allow_html=True)

    # JavaScript for button functionality
    st.markdown("""
    <script>
        const analyzeBtn = document.getElementById('analyze-btn');
        const resetBtn = document.getElementById('reset-btn');
        
        analyzeBtn.addEventListener('click', function() {
            // Trigger Streamlit's analyze button click
            document.querySelector('.stButton button').click();
        });
        
        resetBtn.addEventListener('click', function() {
            // Trigger Streamlit's reset button click
            document.querySelectorAll('.stButton button')[1].click();
        });
    </script>
    """, unsafe_allow_html=True)

    if 'reset' not in st.session_state:
        st.session_state.reset = False

    if st.session_state.reset:
        st.experimental_rerun()

    if channel_input:
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

                # Engagement Metrics over Time
                st.markdown("<h2 class='section-header'>Engagement Metrics over Time</h2>", unsafe_allow_html=True)
                metrics_df = videos_df[['Published Date', 'Views Count', 'Likes Count', 'Comments Count', 'Title', 'Video URL']]
                metrics_df = metrics_df.sort_values('Published Date')
                fig_metrics = go.Figure()
                fig_metrics.add_trace(go.Scatter(x=metrics_df['Published Date'], y=metrics_df['Views Count'], mode='lines+markers', name='Views'))
                fig_metrics.add_trace(go.Scatter(x=metrics_df['Published Date'], y=metrics_df['Likes Count'], mode='lines+markers', name='Likes'))
                fig_metrics.add_trace(go.Scatter(x=metrics_df['Published Date'], y=metrics_df['Comments Count'], mode='lines+markers', name='Comments'))
                fig_metrics.update_layout(title='Engagement Metrics over Time', xaxis_title='Published Date', yaxis_title='Count', height=600)
                fig_metrics.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Date: %{x}<br>%{y:,} %{name}<br><a href="%{customdata[1]}">Watch Video</a>')
                fig_metrics.update_traces(customdata=metrics_df[['Title', 'Video URL']])
                st.plotly_chart(fig_metrics, use_container_width=True)

                # Viewers by Country Map
                st.markdown("<h2 class='section-header'>Viewers by Country</h2>", unsafe_allow_html=True)
                st.warning("Note: The YouTube API does not provide detailed geographic data for viewers. This map is a placeholder for future implementation.")
                
                # Placeholder for Viewers by Country Map
                placeholder_data = pd.DataFrame({
                    'country': ['United States', 'Canada', 'United Kingdom', 'Australia', 'Germany'],
                    'viewers': [1000, 500, 750, 300, 450]
                })
                fig_map = px.choropleth(placeholder_data, locations='country', locationmode='country names', color='viewers',
                                        title='Placeholder: Viewers by Country',
                                        color_continuous_scale='Viridis')
                fig_map.update_layout(height=600)
                st.plotly_chart(fig_map, use_container_width=True)

                # Comprehensive Video Table
                st.markdown("<h2 class='section-header'>Comprehensive Video Table</h2>", unsafe_allow_html=True)
                table_df = videos_df.drop(columns=['Thumbnail URL'])
                table_df['Title'] = table_df.apply(lambda row: f"<a href='{row['Video URL']}' target='_blank'>{row['Title']}</a>", axis=1)
                table_df = table_df.drop(columns=['Video URL'])
                st.markdown(table_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    # Footer
    st.markdown("""
    <div class="footer">
        Made with <span style="color: #e74c3c;">&#10084;</span> by <a href="https://www.linkedin.com/in/menajul-hoque/" target="_blank">Menajul Hoque</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
