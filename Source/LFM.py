import requests
from datetime import datetime
from typing import Dict, Any, Optional
from rich import print
from rich.console import Console
from rich.text import Text
from rich.style import Style
from rich.prompt import Prompt


API_KEY = 'meowpurr'
API_URL = 'https://ws.audioscrobbler.com/2.0/'
DEFAULT_AVG_TRACK_LENGTH = 210  # avg sec
PAGE_LIMIT = 1000

console = Console()


def fetch_lastfm_data(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        console.print(f"[red]API request failed:[/] {str(e)}", style="bold")
        raise


def fetch_user_info(username: str) -> Dict[str, Any]:
    return fetch_lastfm_data({
        'method': 'user.getinfo',
        'user': username,
        'api_key': API_KEY,
        'format': 'json'
    })


def fetch_recent_tracks(username: str, limit: int = 2) -> Dict[str, Any]:
    return fetch_lastfm_data({
        'method': 'user.getrecenttracks',
        'user': username,
        'api_key': API_KEY,
        'format': 'json',
        'limit': limit
    })


def calculate_total_time_spent(username: str) -> int:
    total_seconds = 0
    page = 1
    
    while True:
        data = fetch_lastfm_data({
            'method': 'user.gettoptracks',
            'user': username,
            'api_key': API_KEY,
            'format': 'json',
            'limit': PAGE_LIMIT,
            'page': page
        })
        
        tracks = data.get('toptracks', {}).get('track', [])
        if not tracks:
            break

        for track in tracks:
            playcount = int(track.get('playcount', 0))
            duration = int(track.get('duration', 0)) or DEFAULT_AVG_TRACK_LENGTH
            total_seconds += playcount * duration

        page += 1
        
    return total_seconds


def format_time_duration(seconds: int) -> str:
    if seconds < 1:
        return "Not enough data"
        
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    total_hours = days * 24 + hours
    
    return f"{days}d {hours}h {minutes}m {seconds}s ({total_hours}h)"


def format_timestamp(timestamp: Optional[str]) -> str:
    if not timestamp:
        return "N/A"
        
    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError):
        return "N/A"


def create_stat_line(label: str, value: str, 
                    label_style: str = "#feca57", 
                    value_style: str = "#ff9ff3") -> Text:
    return Text(label, style=label_style) + Text(value, style=value_style)


def display_user_stats(user_info: Dict[str, Any], 
                      recent_tracks: Dict[str, Any], 
                      total_time: int) -> None:
    
    user = user_info.get('user', {})
    recent = recent_tracks.get('recenttracks', {}).get('track', [])
    
    username = user.get('name', 'Unknown')
    playcount = f"{int(user.get('playcount', '0')):,}"
    country = user.get('country', 'N/A')
    registered = format_timestamp(user.get('registered', {}).get('unixtime'))
 
    now_playing = recent[0] if recent else {}
    last_played = recent[1] if len(recent) > 1 else {}
    
    now_title = now_playing.get('name', 'Nothing playing')
    now_artist = now_playing.get('artist', {}).get('#text', '')
    last_title = last_played.get('name', 'None yet')
    last_artist = last_played.get('artist', {}).get('#text', '')
    
    time_pretty = format_time_duration(total_time)
    console.clear()

    console.print(
        Text("🌸  Last.fm User Statistics  🌸", 
             style=Style(color="#ff9ff3", bold=True, italic=True)),
        justify="center"
    )
    console.print()

    console.print(create_stat_line("👤 Username: ", username, value_style="#ff9ff3 bold"))
    console.print(create_stat_line("🌍 Country: ", country))
    console.print(create_stat_line("📅 Registered: ", registered))
    console.print(create_stat_line("🎵 Total Plays: ", playcount, value_style="#ff9ff3 bold"))
    console.print()

    console.print(
        Text("🎶 Now Playing: ", style="#1dd1a1 bold") +
        Text(now_title, style="#f368e0") +
        Text(" — ", style="#c8d6e5") +
        Text(now_artist, style="#ff9ff3 italic")
    )
    
    console.print(
        Text("⏮ Last Played: ", style="#1dd1a1") +
        Text(last_title, style="#f368e0") +
        Text(" — ", style="#c8d6e5") +
        Text(last_artist, style="#ff9ff3 italic")
    )
    console.print()
    
    # Listening time
    console.print(
        Text("⏳ Total Listening Time: ", style="#feca57 bold") +
        Text(time_pretty, style="#5f27cd bold")
    )
    
    console.print()
    console.print(
        Text("✨ You're pretty obsessed, aren't you?", 
             style=Style(color="#c8d6e5", italic=True)),
        justify="center"
    )


def main() -> None:
    username = Prompt.ask("[bold #f368e0]Enter Last.fm username[/]")
    console.print("[italic #1dd1a1]Fetching data...[/]")

    try:
        user_info = fetch_user_info(username)
        recent_tracks = fetch_recent_tracks(username)
        total_time = calculate_total_time_spent(username)
        display_user_stats(user_info, recent_tracks, total_time)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")


if __name__ == "__main__":
    main()
