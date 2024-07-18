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

def main():
    st.set_page_config(layout="wide", page_title="YouTube Channel Statistics")

    # Load custom CSS
    local_css("style.css")

    # Page header with logo
    st.markdown('<div class="logo-container"><img src="https://igtoolsapk.in/wp-content/uploads/2024/07/Youtube-Statistics-Logo-New.png" alt="YouTube Statistics Logo" class="logo"></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="title">YouTube Channel Statistics</h1>', unsafe_allow_html=True)

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
                channel_created_on = datetime.strptime(channel_details['items'][0]['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%S%z").strftime("%B %d, %Y")

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
                videos_df['Published Date'] = pd.to_datetime(videos_df['Published Date'], format='%Y-%m-%dT%H:%M:%S%z')

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

                # Video Upload Frequency Bar Chart
                st.markdown("<h2 class='section-header'>Video Upload Frequency</h2>", unsafe_allow_html=True)
                videos_df['Month'] = videos_df['Published Date'].dt.month
                video_upload_frequency = videos_df['Month'].value_counts().sort_index()
                fig_upload_frequency = px.bar(video_upload_frequency, x=video_upload_frequency.index, y=video_upload_frequency.values,
                                              labels={'x': 'Month', 'y': 'Number of Videos'},
                                              title='Video Upload Frequency',
                                              color_discrete_sequence=['#1f77b4'])
                fig_upload_frequency.update_layout(height=600)
                st.plotly_chart(fig_upload_frequency, use_container_width=True)

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

                # Comprehensive Video Table
                st.markdown("<h2 class='section-header'>Comprehensive Video Table</h2>", unsafe_allow_html=True)
                table_df = videos_df.drop(columns=['Thumbnail URL', 'Video URL'])
                st.dataframe(table_df)

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
