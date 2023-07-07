"""
Adds Gaana support to the autotagger.
"""

import collections
import re
import time
from io import BytesIO

import requests
from beets.autotag.hooks import AlbumInfo, Distance, TrackInfo
from beets.dbcore import types
from beets.library import DateType
from beets.plugins import BeetsPlugin, get_distance
from PIL import Image


class GaanaPlugin(BeetsPlugin):
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
    ALBUM_SEARCH = '/albums/search?query='
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

    def album_distance(self, items, album_info, mapping):

        """Returns the album distance.
        """
        dist = Distance()
        if album_info.data_source == 'Gaana':
            dist.add('source', self.config['source_weight'].as_number())
        return dist

    def track_distance(self, item, track_info):

        """Returns the Gaana source weight and the maximum source weight
        for individual tracks.
        """
        return get_distance(
            data_source=self.data_source,
            info=track_info,
            config=self.config
        )

    def get_albums(self, query):
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
            albums = requests.get(url, timeout=30).json()
        except Exception as e:
            self._log.debug('Album Search Error: {}'.format(e))
        for album in albums:
            self._log.debug('Album: {}', album["title"])
            seokey = album["seokey"]
            album_url = f"{self.baseurl}{self.ALBUM_DETAILS}{seokey}"
            album_details = requests.get(album_url, timeout=30).json()
            album_info = self.get_album_info(album_details[0])
            albums.append(album_info)
        return albums

    def get_tracks(self, query):
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
        self._log.debug('Searching Gaana for: {}', query)
        try:
            data = self.jiosaavn.search_song(query)
        except Exception as e:
            self._log.debug('Invalid Search Error: {}'.format(e))
        for track in data["results"]:
            id = self.jiosaavn.create_identifier(track["perma_url"], 'song')
            song_details = self.jiosaavn.get_song_details(id)
            song_info = self._get_track(song_details["songs"][0])
            tracks.append(song_info)
        return tracks

    def candidates(self, items, artist, release, va_likely, extra_tags=None):
        """Returns a list of AlbumInfo objects for Gaana search results
        matching release and artist (if not various).
        """
        if va_likely:
            query = release
        else:
            query = f'{release} {artist}'
        try:
            return self.get_albums(query)
        except Exception as e:
            self._log.debug('Gaana Search Error: {}'.format(e))
            return []

    def item_candidates(self, item, artist, title):
        """Returns a list of TrackInfo objects for Gaana search results
        matching title and artist.
        """
        query = f'{title} {artist}'
        try:
            return self.get_tracks(query)
        except Exception as e:
            self._log.debug('Gaana Search Error: {}'.format(e))
            return []

    def get_album_info(self, item):
        """Returns an AlbumInfo object for a Gaana album.
        """
        album = item["title"].replace("&quot;", "\"")
        gaana_album_id = item["album_id"]
        gaana_seokey = item["seokey"]
        if item["release_date"] is not None:
            releasedate = item["release_date"].split("-")
            year = int(releasedate[0])
            month = int(releasedate[1])
            day = int(releasedate[2])
        url = item["images"]["urls"]["large_artwork"]
        if self.is_valid_image_url(url):
            cover_art_url = url
        if item["label"] is not None:
            label = item["label"]
        artists = item["artists"]
        gaana_artist_seokey = item["artist_seokeys"]
        artist_id = item["artist_ids"]
        songs = item["tracks"]
        gaana_play_count = self.parse_count(item["play_count"])
        gaana_fav_count = self.parse_count(item["favorite_count"])
        tracks = []
        medium_totals = collections.defaultdict(int)
        for i, song in enumerate(songs, start=1):
            track = self._get_track(song)
            track.index = i
            medium_totals[track.medium] += 1
            tracks.append(track)
        for track in tracks:
            track.medium_total = medium_totals[track.medium]
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
                         mediums=max(medium_totals.keys()),
                         data_source=self.data_source,
                         cover_art_url=cover_art_url,
                         label=label,
                         gaana_play_count=gaana_play_count,
                         gaana_fav_count=gaana_fav_count,
                         )

    def _get_track(self, track_data):
        """Convert a Gaana song object to a TrackInfo object.
        """
        if track_data['duration']:
            length = int(track_data['duration'].strip())
        artist = track_data['artists']
        if track_data['popularity']:
            play_count = int(track_data['popularity'].split("~")[0])
        elif track_data['play_count']:
            play_count = self.parse_count(track_data['play_count'])
        # Get album information for Gaana tracks

        print(track_data['title'].replace("&quot;", "\""))
        print(track_data['track_id'])
        print(track_data['seokey'])
        print(play_count)
        print(track_data['genres'])
        print(artist)
        print(track_data['album'].replace("&quot;", "\""))
        print(track_data["artist_ids"])
        print(track_data["artist_seokeys"])
        print(length)
        print(self.data_source)
        print(self.parse_count(track_data['favorite_count']))

        return TrackInfo(
            title=track_data['title'].replace("&quot;", "\""),
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
            gaana_track_fav_count=self.parse_count(track_data['favorite_count']),
            gaana_updated=time.time(),
        )

    def album_for_id(self, release_id):
        """Fetches an album by its Gaana ID and returns an AlbumInfo object
        """
        if 'gaana.com/album/' not in release_id:
            return None
        self._log.debug('Searching for album {0}', release_id)
        seokey = release_id.split("/")[-1]
        album_url = f"{self.baseurl}{self.ALBUM_DETAILS}{seokey}"
        album_details = requests.get(album_url, timeout=30).json()
        return self.get_album_info(album_details[0])

    def track_for_id(self, track_id=None):
        """Fetches a track by its Gaana ID and returns a TrackInfo object
        """
        if 'gaana.com/song/' not in track_id:
            return None
        self._log.debug('Searching for track {0}', track_id)
        seokey = track_id.split("/")[-1]
        song_url = f"{self.baseurl}{self.SONG_DETAILS}{seokey}"
        song_details = requests.get(song_url, timeout=30).json()
        return self._get_track(song_details[0])

    def is_valid_image_url(self, url):
        try:
            response = requests.get(url)
            Image.open(BytesIO(response.content))
            return True
        except Exception:
            return False

    def parse_count(self, str) -> int:
        # this function parses the play count from the string. The string usually has numbers such as 55K+ or 1.2M+
        # this function converts the string to an integer
        if str is None:
            return 0
        if str[-1] == '+':
            str = str[:-1]
        if str[-1] == 'K':
            return int(float(str[:-1]) * 1000)
        if str[-1] == 'M':
            return int(float(str[:-1]) * 1000000)
        return int(str)
