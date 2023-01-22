import argparse
import pylast
import pprint
import datetime
import os
import json

def main(artist_name, album_limit):

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

    artist = network.get_artist(artist_name)
    albums = artist.get_top_albums(limit=album_limit)
    album_id = 1
    songlist_id = 1
    song_id = 1

    for album in albums:
        album_playcount = album.item.get_playcount()
        album_listener_count = album.item.get_listener_count()
        album_table[album_id] = {
            "name" : album.item.get_name(),
            "album_listener_count": album_listener_count,
        }
        print("Parsing data for album: ")
        pprint.pprint(album_table[album_id])
        tracklist = album.item.get_tracks()

        for j, track in enumerate(tracklist):
            track_name = track.get_name()
            #print(f"{track_name=}")
            delta_t=datetime.timedelta(seconds=track.get_duration()/1000)
            duration = f"{delta_t.seconds//60:02}:{delta_t.seconds%60:02}"
            #print(f"{duration=}")
            listener_count=track.get_listener_count()
            playcount = track.get_playcount()
            songlist_table[songlist_id] = {
                "album_id": album_id,
                "song_id": song_id,
            }
            songlist_id += 1
            song_table[song_id] = {
                "song_id": song_id,
                "song_name": track.get_name(),
                "duration": duration,
                "listener_count": listener_count,
            }
            
            song_id += 1

        album_id += 1

    # album_table 
    # songlist_table 
    # songs_table 
    tables = [
        ("album", album_table),
        ("songlist", songlist_table),
        ("song", song_table)
    ]
    for table_name, table in tables:
        print(json.dumps(table, indent=4))
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
                print(insert_stmt)
                fp.write(insert_stmt)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artist", help="artist to fetch top albums", default="The Rolling Stones")
    parser.add_argument("--album_limit", help="max number of albums", default=8)
    args = parser.parse_args()
    pprint.pprint(args)
    main(args.artist, args.album_limit)
    