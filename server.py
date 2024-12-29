import pandas as pd
import random
import json
import urllib.request
from flask import Flask, render_template_string, request

app = Flask(__name__)

headers = {'Content-Type': 'application/json'}
lms_url = "http://martin-peime-j4005i-c:9000/jsonrpc.js"

def send_request(params):
    json_data = {
        "id": 1,
        "method": "slim.request",
        "params": params
    }
    post_data = json.dumps(json_data).encode('utf-8')
    req = urllib.request.Request(lms_url, post_data, headers)
    with urllib.request.urlopen(req) as response:
        result = response.read()
        return json.loads(result.decode("utf-8"))
    return None

def get_player():
    players = send_request(["", ["players", "status"]])
    if players and players['result']['count'] > 0:
        return players['result']['players_loop'][0]['playerid']
    return None

def get_titles():
    if player_id:
        res = send_request(["", ["titles", 0, 99999, "tags:agAlyuc"]])
        if res and 'result' in res and res['result'] and 'titles_loop' in res['result']:
            titles = res['result']['titles_loop']
            df = pd.DataFrame(titles)
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
            df = df[df['year'] > 1940]
            df = df[~df['genre'].isin(["Hörbuch", "Audiobook", "Unknown", "Speech", "Classical", "Comedy", "Keine Stilrichtung", "Audiobuch", "Humor"])]
            df.reset_index(drop=True, inplace=True)
            return df
    return None

player_id = 'b8:27:eb:f4:cd:65'
#player_id = get_player()
df_titles = get_titles()
nr_of_tracks = len(df_titles)
current_index = -1

@app.route('/')
def index():
    return render_template_string('''
        <h1>Welcome! Press 'Next' to play a random song.</h1>
        <form action="/next" method="post">
            <button type="submit" style="width:180px;height:60px;">Next</button>
        </form>
    ''')

@app.route('/next', methods=['POST'])
def next_song():
    global current_index
    if player_id and nr_of_tracks > 0:
        current_index = random.randint(0, nr_of_tracks - 1)
        send_request([f"{player_id}", ['playlist', 'play', f'{df_titles.iloc[current_index]["url"]}']])
        return render_template_string('''
            <h1>Now Playing...</h1>
            <form action="/reveal" method="post">
            <button type="submit" style="width:180px;height:60px;">Reveal Title</button>
            </form>
        ''')
    return "Error: No tracks available."

@app.route('/reveal', methods=['POST'])
def reveal_title():
    if current_index > -1:
        track_info = df_titles.iloc[current_index]
        return render_template_string('''
            <table>
                <tr><th>Title</th><td style="font-size: 24px;">{{ track_info['title'] }}</td></tr>
                <tr><th>Artist</th><td style="font-size: 24px;">{{ track_info['artist'] }}</td></tr>
                <tr><th>Album</th><td style="font-size: 24px;">{{ track_info['album'] }}</td></tr>
                <tr><th>Year</th><td style="font-size: 48px;">{{ track_info['year'] }}</td></tr>
                <tr><th>Cover Art</th><td><img src="{{ cover_url }}" style="height: 300px; width: 300px;"></td></tr>
            </table>
            <form action="/next" method="post">
                <button type="submit" style="width:180px;height:60px;">Next</button>
            </form>
        ''', track_info=track_info, cover_url=f"{lms_url.split('jsonrpc')[0]}music/{track_info['coverid']}/cover.jpg")
    return "Error: No track selected."

if __name__ == '__main__':
    app.run('0.0.0.0',8050)