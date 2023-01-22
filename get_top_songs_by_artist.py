import argparse
import pylast
import pprint
import datetime
import os
import json

def fetch_top_albums(artist_name, album_limit):

    # You have to have your own unique two values for API_KEY and API_SECRET
    # Obtain yours from https://www.last.fm/api/account/create for Last.fm

    API_KEY = os.environ.get("FM_API_KEY") 
    API_SECRET = os.environ.get("FM_API_SECRET")

    network = pylast.LastFMNetwork(
        api_key=API_KEY,
        api_secret=API_SECRET,

    )

    album_table = {}
    songlist_table = {}
    song_table = {}

    print(f"Querying the last.fm for the top {album_limit} album{'s' if album_limit > 1 else ''} from {artist_name}...")

    artist = network.get_artist(artist_name)
    albums = artist.get_top_albums(limit=album_limit)

    print(f"Found {len(albums)} album{'s' if len(albums) > 1 else ''}.")
    
    album_id = 1
    songlist_id = 1
    song_id = 1

    for album in albums:
        album_table[album_id] = {
            "album_name" : album.item.get_name(),
            "album_listener_count": album.item.get_listener_count(),
        }
        tracks = album.item.get_tracks()
        print(f"Parsing {len(tracks)} track{'s' if len(tracks) > 1 else ''} from album \"{album_table[album_id]['album_name']}\"")
        for track in tracks:
            # Parse duration into hh:mm:ss so it can be read into mysql TIME type as string
            delta_t=datetime.timedelta(seconds=track.get_duration()/1000)
            duration = f"{delta_t.seconds//3600:02}:{delta_t.seconds//60:02}:{delta_t.seconds%60:02}"
            songlist_table[songlist_id] = {
                "album_id": album_id,
                "song_id": song_id,
            }
            song_table[song_id] = {
                "song_name": track.get_name(),
                "duration": duration,
                "listener_count": track.get_listener_count(),
            }
            songlist_id += 1
            song_id += 1
        album_id += 1

    tables = [
        ("album", album_table),
        ("songlist", songlist_table),
        ("song", song_table)
    ]
    for table_name, table in tables:
        with open(f"{table_name}_table.json", "w") as fp:
            json.dump(table, fp, indent=4)

    for table_name, table in tables:
        with open(f"{table_name}_table.sql", "w") as fp:
            for id, rec in sorted(table.items()):
                keylist = sorted(rec.keys())
                insert_stmt = f"INSERT INTO {table_name} "
                insert_stmt += f"({table_name}_id, {', '.join(keylist)})"
                value_strs = [repr(rec[k]) for k in keylist]
                insert_stmt += f" VALUES ({id}, {', '.join(value_strs)});\n"
                fp.write(insert_stmt)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artist", help="artist to fetch top albums", default="The Rolling Stones")
    parser.add_argument("--limit", type=int, help="max number of albums", default=8)
    args = parser.parse_args()
    pprint.pprint(args)
    fetch_top_albums(args.artist, args.limit)
    