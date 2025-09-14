"""
Adds Gaana support to the autotagger.
"""

import collections
import re
import time
from io import BytesIO
from typing import Sequence

import requests
from PIL import Image
from beets import importer
from beets.autotag.hooks import AlbumInfo, TrackInfo, Item
from beets.dbcore import types
from beets.library import DateType
from beets.plugins import MetadataSourcePlugin


def extend_reimport_fresh_fields_item() -> None:
    """Extend the REIMPORT_FRESH_FIELDS_ITEM list so that these fields
    are updated during reimport."""
    importer.REIMPORT_FRESH_FIELDS_ITEM.extend([
        'gaana_track_id', 'gaana_track_seokey', 'gaana_track_popularity',
        'gaana_genres', 'gaana_track_fav_count', 'gaana_fav_count',
        'gaana_updated'
    ])

class GaanaPlugin(MetadataSourcePlugin):
    data_source = 'Gaana'

    item_types = {
        'gaana_seokey': types.STRING,
        'gaana_play_count': types.INTEGER,
        'gaana_album_id': types.INTEGER,
        'gaana_fav_count': types.INTEGER,
        'gaana_track_popularity': types.INTEGER,
        'gaana_updated': DateType(),
        'cover_art_url': types.STRING,
    }

    SONG_SEARCH = '/songs/search?query='
    ALBUM_SEARCH = '/albums/search?limit=5&query='
    ARTIST_SEARCH = '/artists/search?query='
    SONG_DETAILS = '/songs/info?seokey='
    ALBUM_DETAILS = '/albums/info?seokey='
    ARTIST_DETAILS = '/artists/info?seokey='
    PLAYLIST_DETAILS = '/playlists/info?seokey='

    def __init__(self):
        super().__init__()
        self.config.add({
            'source_weight': 0.5,
        })
        try:
            self.baseurl = self.config["baseurl"].as_str()
        except Exception as e:
            self._log.error('Gaana baseurl not set: {}'.format(e))

    

    def get_albums(self, query: str) -> list:
        """Returns a list of AlbumInfo objects for a Gaana search query.
        """
        # Strip non-word characters from query. Things like "!" and "-" can
        # cause a query to return no results, even if they match the artist or
        # album title. Use `re.UNICODE` flag to avoid stripping non-english
        # word characters.
        query = re.sub(r'(?u)\W+', ' ', query)
        # Strip medium information from query, Things like "CD1" and "disk 1"
        # can also negate an otherwise positive result.
        query = re.sub(r'(?i)\b(CD|disc)\s*\d+', '', query)
        albums = []
        self._log.debug('Searching Gaana for Album: {}', query)
        url = f"{self.baseurl}{self.ALBUM_SEARCH}\"{query}\""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self._log.error('Album Search Error: {}'.format(e))
            return []
        tot_alb = len(data)
        for i, album in enumerate(data):
            seokey = album["seokey"]
            album_url = f"{self.baseurl}{self.ALBUM_DETAILS}{seokey}"
            album_details = requests.get(album_url, timeout=30).json()
            album_info = self.get_album_info(album_details[0])
            albums.append(album_info)
            self._log.debug(
                'Processed album {} of {}: {}'.format(i+1,
                                                      tot_alb,
                                                      album["title"]))
        return albums

    def get_tracks(self, query: str) -> list:
        """Returns a list of TrackInfo objects for a Gaana search query.
        """
        # Strip non-word characters from query. Things like "!" and "-" can
        # cause a query to return no results, even if they match the artist or
        # album title. Use `re.UNICODE` flag to avoid stripping non-english
        # word characters.
        query = re.sub(r'(?u)\W+', ' ', query)
        # Strip medium information from query, Things like "CD1" and "disk 1"
        # can also negate an otherwise positive result.
        query = re.sub(r'(?i)\b(CD|disc)\s*\d+', '', query)
        tracks = []
        self._log.debug('Searching Gaana for track: {}', query)
        url = f"{self.baseurl}{self.SONG_SEARCH}\"{query}\""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self._log.error('Invalid track Search Error: {}'.format(e))
            return []
        tot_trk = len(data)
        for i, track in enumerate(data):
            seokey = track["seokey"]
            song_url = f"{self.baseurl}{self.SONG_DETAILS}{seokey}"
            song_details = requests.get(song_url, timeout=30).json()
            self._log.debug('Track: {}', song_details)
            song_info = self._get_track(song_details[0])
            tracks.append(song_info)
            self._log.debug(
                'Processed track {} of {}: {}'.format(i+1,
                                                      tot_trk,
                                                      track["title"]))
        return tracks

    def candidates(self, items: Sequence[Item], artist: str, album: str, va_likely: bool):
        """Returns a list of AlbumInfo objects for Gaana search results
        matching release and artist (if not various).
        """
        if va_likely:
            query = album
        else:
            query = f'{album} {artist}'
        try:
            return self.get_albums(query)
        except Exception as e:
            self._log.debug('Gaana Search Error: {}'.format(e))
            return []

    def item_candidates(self, item: Item, artist: str, title: str):
        """Returns a list of TrackInfo objects for Gaana search results
        matching title and artist.
        """
        try:
            query = f'{title} {artist}'
        except:
            return []
        try:
            return self.get_tracks(query)
        except Exception as e:
            self._log.debug('Gaana Item Search Error: {}'.format(e))
            return []

    def get_album_info(self, item: dict) -> AlbumInfo:
        """Returns an AlbumInfo object for a Gaana album.
        """
        album = item.get("title").replace("&quot;", "\"")
        gaana_album_id = item["album_id"]
        gaana_seokey = item["seokey"]
        year, month, day = None, None, None
        label = None
        if item.get("release_date"):
            releasedate = item["release_date"].split("-")
            if len(releasedate) == 3:
                year = int(releasedate[0])
                month = int(releasedate[1])
                day = int(releasedate[2])
        url = item["images"]["urls"]["large_artwork"]
        if self.is_valid_image_url(url):
            cover_art_url = url
        else:
            cover_art_url = None
        if item.get("label"):
            label = item["label"]
        artists = item["artists"]
        gaana_artist_seokey = item["artist_seokeys"]
        artist_id = item["artist_ids"]
        songs = item["tracks"]
        gaana_play_count = self.parse_count(item["play_count"])
        gaana_fav_count = self.parse_count(item["favorite_count"])
        tracks = []
        medium_totals = collections.defaultdict(int)
        if len(songs) > 0:
            for i, song in enumerate(songs, start=1):
                track = self._get_track(song)
                track.index = i
                medium_totals[track.medium] += 1
                tracks.append(track)
        for track in tracks:
            track.medium_total = medium_totals[track.medium]
        if len(songs) > 0:
            mediums = max(medium_totals.keys())
        else:
            mediums = 0
        return AlbumInfo(album=album,
                         album_id=gaana_album_id,
                         gaana_album_id=gaana_album_id,
                         gaana_seokey=gaana_seokey,
                         artist=artists,
                         artist_id=artist_id,
                         gaana_artist_seokey=gaana_artist_seokey,
                         gaana_artist_id=artist_id,
                         tracks=tracks,
                         year=year,
                         month=month,
                         day=day,
                         mediums=mediums,
                         data_source=self.data_source,
                         cover_art_url=cover_art_url,
                         label=label,
                         gaana_play_count=gaana_play_count,
                         gaana_fav_count=gaana_fav_count,
                         )

    def _get_track(self, track_data: dict) -> TrackInfo:
        """Convert a Gaana song object to a TrackInfo object.
        """
        if track_data['duration']:
            length = int(track_data['duration'].strip())
        else:
            length = None
        artist = track_data['artists']
        if track_data['popularity']:
            play_count = int(track_data['popularity'].split("~")[0])
        elif track_data['play_count']:
            play_count = self.parse_count(track_data['play_count'])
        else:
            play_count = None
        if isinstance(track_data['favorite_count'], int):
            gaana_track_fav_count = track_data['favorite_count']
        else:
            gaana_track_fav_count = self.parse_count(
                track_data['favorite_count'])
        # Get album information for Gaana tracks
        return TrackInfo(
            title=track_data.get('title').replace("&quot;", "\""),
            track_id=track_data['track_id'],
            gaana_track_id=track_data['track_id'],
            gaana_track_seokey=track_data['seokey'],
            gaana_track_popularity=play_count,
            gaana_genres=track_data['genres'],
            artist=artist,
            album=track_data['album'].replace("&quot;", "\""),
            gaana_artist_id=track_data["artist_ids"],
            gaana_artist_seokey=track_data["artist_seokeys"],
            length=length,
            data_source=self.data_source,
            gaana_track_fav_count=gaana_track_fav_count,
            gaana_updated=time.time(),
        )

    def album_for_id(self, album_id: str) -> AlbumInfo | None:
        """Fetches an album by its Gaana ID and returns an AlbumInfo object
        """
        if 'gaana.com/album/' not in album_id:
            return None
        self._log.debug('Searching for album {0}', album_id)
        seokey = album_id.split("/")[-1]
        album_url = f"{self.baseurl}{self.ALBUM_DETAILS}{seokey}"
        try:
            response = requests.get(album_url, timeout=30)
            response.raise_for_status()
            album_details = response.json()
        except Exception as e:
            self._log.error('Error fetching album by ID: {}'.format(e))
            return None
        return self.get_album_info(album_details[0])

    def track_for_id(self, track_id: str) -> TrackInfo | None:
        """Fetches a track by its Gaana ID and returns a TrackInfo object
        """
        if 'gaana.com/song/' in track_id:
            self._log.debug('Searching for track {0}', track_id)
            seokey = track_id.split("/")[-1]
            song_url = f"{self.baseurl}{self.SONG_DETAILS}{seokey}"
            try:
                response = requests.get(song_url, timeout=30)
                response.raise_for_status()
                song_details = response.json()
            except Exception as e:
                self._log.error('Error fetching track by ID: {}'.format(e))
                return None
            return self._get_track(song_details[0])
        else:
            return None

    def is_valid_image_url(self, url: str) -> bool:
        try:
            response = requests.get(url)
            response.raise_for_status()
            Image.open(BytesIO(response.content))
            return True
        except Exception:
            return False

    def parse_count(self, str_val: str) -> int:
        # this function parses the play count from the string.
        if not str_val:
            return 0
        str_val = str(str_val).strip()
        if str_val.startswith('<'):
            str_val = str_val[1:]
        if str_val.endswith('+'):
            str_val = str_val[:-1]
        if str_val.endswith('K'):
            try:
                return int(float(str_val[:-1]) * 1000)
            except ValueError:
                return 0
        if str_val.endswith('M'):
            try:
                return int(float(str_val[:-1]) * 1000000)
            except ValueError:
                return 0
        try:
            return int(str_val)
        except ValueError:
            return 0

    def import_gaana_playlist(self, url: str) -> list:
        """This function returns a list of tracks in a Gaana playlist."""
        song_list = []
        if "/playlist/" not in url:
            self._log.error("Invalid Gaana playlist URL: {0}", url)
            return song_list
        else:
            seokey = url.split("/")[-1]
            plst_url = f"{self.baseurl}{self.PLAYLIST_DETAILS}{seokey}"
            try:
                response = requests.get(plst_url, timeout=30)
                response.raise_for_status()
                songs = response.json()
            except Exception as e:
                self._log.error("Error fetching playlist: {0}", e)
                return song_list
            for song in songs:
                # Find and store the song title
                title = song['title'].replace("&quot;", "\"")
                artist = song['artists']
                album = song['album'].replace("&quot;", "\"")
                # Create a dictionary with the song information
                song_dict = {"title": title.strip(),
                             "artist": artist.strip(),
                             "album": album.strip()}
                # Append the dictionary to the list of songs
                song_list.append(song_dict)
        return song_list
