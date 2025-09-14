# Copilot Instructions for beets-gaana

## Repository Overview

This is a plugin for [beets](https://github.com/beetbox/beets) that adds support for Gaana, a popular Indian music streaming service, as a metadata source. The plugin allows beets to fetch comprehensive metadata including album information, track details, artist data, and cover art from Gaana's API.

## Architecture & Key Components

### Core Files
- `beetsplug/gaana.py` - Main plugin implementation
- `beetsplug/__init__.py` - Package initialization
- `setup.py` - Package configuration and dependencies
- `README.md` - Installation and configuration documentation

### Plugin Structure
The plugin follows the beets plugin architecture with these key components:

1. **GaanaPlugin Class** - Main plugin class inheriting from `BeetsPlugin`
2. **Metadata Types** - Custom database fields for Gaana-specific data
3. **Search Methods** - Album and track search functionality
4. **Info Parsers** - Convert Gaana API responses to beets data structures
5. **Distance Calculation** - Metadata matching confidence scoring

## Key Features

### Metadata Support
- Album information (title, artist, release date, label)
- Track details (title, artist, duration, popularity)
- Additional Gaana-specific fields (seokey, play counts, favorites)
- Cover art URL retrieval and validation
- Playlist import functionality

### Search Capabilities
- Album search with query sanitization
- Track search with fuzzy matching
- Artist information retrieval
- ID-based lookups for albums and tracks

## Development Guidelines

### Code Style & Conventions

1. **Follow PEP 8** - Standard Python style guidelines
2. **Use descriptive variable names** - Prefer clarity over brevity
3. **Add comprehensive docstrings** - Document all public methods
4. **Handle exceptions gracefully** - Log errors and provide fallbacks
5. **Maintain backwards compatibility** - Preserve existing API behavior

### Common Patterns

#### API Request Pattern
```python
try:
    response = requests.get(url, timeout=30)
    data = response.json()
except Exception as e:
    self._log.debug('API Error: {}'.format(e))
    return []
```

#### Query Sanitization
```python
# Strip non-word characters and medium information
query = re.sub(r'(?u)\W+', ' ', query)
query = re.sub(r'(?i)\b(CD|disc)\s*\d+', '', query)
```

#### Metadata Conversion
```python
# Always handle missing data gracefully
title = track_data.get('title', '').replace("&quot;", "\"")
length = int(track_data['duration'].strip()) if track_data['duration'] else None
```

### Error Handling Best Practices

1. **Log at appropriate levels** - Use `self._log.debug()` for detailed info
2. **Provide meaningful error messages** - Include context for debugging  
3. **Return empty collections on failure** - Don't break the beets workflow
4. **Handle network timeouts** - Set reasonable timeout values (30s)
5. **Validate data before processing** - Check for None values and required fields

### Configuration Management

The plugin requires a `baseurl` configuration pointing to a GaanaPy API instance:

```yaml
gaana:
    baseurl: http://192.168.2.60:8000
    source_weight: 0.5
```

### Testing Approach

When adding new functionality:

1. **Manual Testing** - Test with real Gaana API responses
2. **Edge Case Handling** - Test with missing/malformed data
3. **Network Resilience** - Test timeout and connection error scenarios
4. **Unicode Support** - Test with non-ASCII track/album names
5. **Query Sanitization** - Test with special characters and medium info

### Performance Considerations

1. **Batch API Calls** - Minimize individual requests where possible
2. **Implement Caching** - Consider caching frequently accessed data
3. **Optimize Query Strings** - Remove unnecessary terms that reduce matches
4. **Handle Rate Limits** - Respect API rate limiting if implemented
5. **Image Validation** - Verify cover art URLs before storing

### Dependencies

- `beets>=1.6.0` - Core beets functionality
- `requests` - HTTP client for API calls
- `pillow` - Image processing for cover art validation
- External dependency: GaanaPy API server

### API Endpoints Used

- `/songs/search?query=` - Track search
- `/albums/search?limit=5&query=` - Album search  
- `/artists/search?query=` - Artist search
- `/songs/info?seokey=` - Track details
- `/albums/info?seokey=` - Album details
- `/playlists/info?seokey=` - Playlist details

### Data Flow

1. **Search Request** - User initiates import/search
2. **Query Sanitization** - Clean and optimize search terms
3. **API Call** - Request data from GaanaPy server
4. **Response Processing** - Parse JSON and extract metadata
5. **Data Conversion** - Convert to beets data structures
6. **Distance Calculation** - Score metadata matches
7. **User Selection** - Present options to user
8. **Import** - Store selected metadata in beets database

### Common Issues & Solutions

1. **Missing baseurl** - Ensure GaanaPy server URL is configured
2. **Network timeouts** - Check server availability and network connectivity
3. **No search results** - Query may be too specific, try broader terms
4. **Invalid image URLs** - Image validation prevents broken cover art
5. **Encoding issues** - Handle HTML entities in track/album titles

### Future Enhancement Areas

1. **Caching Layer** - Add local caching for API responses
2. **Batch Operations** - Support bulk album/track processing
3. **Enhanced Matching** - Improve metadata matching algorithms
4. **Configuration Validation** - Validate baseurl on plugin load
5. **Async Operations** - Add async support for better performance

## Examples

### Basic Plugin Usage
```python
# In beets config.yaml
plugins: gaana

gaana:
    baseurl: http://localhost:8000
    source_weight: 0.5
```

### Custom Metadata Fields
```python
# Access Gaana-specific metadata
track.gaana_track_id
track.gaana_seokey  
track.gaana_track_popularity
album.gaana_album_id
album.gaana_play_count
```

### Search Implementation
```python
def get_albums(self, query):
    """Search for albums with proper error handling"""
    query = re.sub(r'(?u)\W+', ' ', query)  # Sanitize
    url = f"{self.baseurl}{self.ALBUM_SEARCH}\"{query}\""
    
    try:
        data = requests.get(url, timeout=30).json()
        return [self.get_album_info(item) for item in data]
    except Exception as e:
        self._log.debug('Search Error: {}'.format(e))
        return []
```

This plugin provides a robust integration between beets and Gaana, enabling users to enrich their music libraries with comprehensive metadata from one of India's largest music platforms.