# beets-gaana Plugin Development Guide

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup (2-3 minutes)
- Install beets framework and dependencies:
  - `pip install --user beets` -- takes 30-60 seconds. NEVER CANCEL. Set timeout to 5+ minutes.
  - `pip install --user -e .` -- installs plugin in editable mode, takes 10-20 seconds
- Test plugin loads correctly:
  - `python -c "from beetsplug.gaana import GaanaPlugin; print('Plugin loads successfully')"`
- Test with beets framework:
  - Create basic config file with `plugins: gaana` and `gaana: baseurl: http://example.com:8000`
  - Run `BEETSDIR=/path/to/config beet version` to verify plugin loads

### Key Dependencies and Versions
- Python 3.12+ (tested with 3.12.3)
- beets >= 1.6.0 (tested with 2.4.0)
- requests library (for API calls)
- pillow (for image processing)
- External GaanaPy API service (required for functionality)

### Build and Test Process (No separate build required)
- This is a pure Python plugin - no compilation needed
- Installation via `pip install -e .` makes code changes immediately active
- Plugin loading test: `python -c "from beetsplug.gaana import GaanaPlugin"`
- Integration test: Set `BEETSDIR` environment variable and run `beet version`

### Configuration Requirements
Create a config.yaml file with:
```yaml
directory: /path/to/music
library: /path/to/beets.db
plugins: gaana
gaana:
    baseurl: http://192.168.2.60:8000
```

### Validation Scenarios
- **ALWAYS** test plugin loading after code changes:
  - `python -c "from beetsplug.gaana import GaanaPlugin; print('Plugin loads successfully')"`
- **ALWAYS** test beets integration after changes:
  - `BEETSDIR=/path/to/config beet version` should show "plugins: gaana"
- **CRITICAL**: The plugin requires an external GaanaPy API service running at the configured baseurl
- Test commands run quickly (under 5 seconds) - no long-running builds or tests

### Common Issues and Solutions
- **Import Error on Distance class**: Fixed in current version - Distance is imported from `beets.autotag.distance`
- **Missing get_distance function**: Fixed in current version - uses `track_distance` function with proper parameters
- **Plugin not loading**: Check that `plugins: gaana` is in your beets config.yaml
- **Missing baseurl error**: Plugin requires `gaana.baseurl` configuration setting

### Repository Structure
```
.
├── README.md              # Basic installation and configuration instructions
├── setup.py              # Python package definition with dependencies
├── beetsplug/            # Plugin directory
│   ├── __init__.py       # Package init (standard beets plugin structure)
│   └── gaana.py          # Main plugin implementation (338 lines)
├── LICENSE               # MIT license
└── .gitignore           # Standard Python gitignore
```

### Key Files to Know
- `beetsplug/gaana.py`: Main plugin implementation
  - `GaanaPlugin` class: Main plugin class inheriting from `BeetsPlugin`
  - API endpoint constants (lines 42-48): SONG_SEARCH, ALBUM_SEARCH, etc.
  - Core methods: `get_albums()`, `get_tracks()`, `candidates()`, `item_candidates()`
  - Metadata conversion: `get_album_info()`, `_get_track()`
- `setup.py`: Dependencies: beets>=1.6.0, requests, pillow

### Plugin Functionality
- Adds Gaana music service as metadata source for beets autotagger
- Searches albums and tracks using external GaanaPy API
- Extracts metadata: artists, albums, track info, play counts, genres
- Supports album and individual track matching
- Handles cover art URLs and metadata validation
- Provides playlist import functionality

### Development Workflow
1. Make code changes in `beetsplug/gaana.py`
2. Test plugin loading: `python -c "from beetsplug.gaana import GaanaPlugin"`
3. Test beets integration: `BEETSDIR=/config/path beet version`
4. For API testing, ensure GaanaPy service is running at configured baseurl
5. Changes are immediately active due to editable installation

### No CI/CD Pipeline
- No existing GitHub Actions or automated testing
- No linting configuration files (no .flake8, .pylintrc, etc.)
- No existing test suite
- Manual validation is required for all changes

### Timing Expectations
- Fresh setup with existing Python: 2-3 minutes
- Plugin import test: < 5 seconds  
- Beets integration test: < 5 seconds
- No long-running builds - this is a simple Python plugin
- Network timeouts may occur during pip install if PyPI is slow - wait up to 5 minutes

### External Dependencies
- **CRITICAL**: Requires GaanaPy API service running at configured baseurl
- Plugin will fail gracefully if GaanaPy service is unavailable
- API endpoints: `/songs/search`, `/albums/search`, `/artists/search`, etc.
- Service provides JSON responses with track/album metadata

## Common Commands and Expected Outputs

### Repository Root Structure
```bash
$ ls -la
total 36
drwxr-xr-x 4 runner runner 4096 Sep 14 14:33 .
drwxr-xr-x 3 runner runner 4096 Sep 14 14:32 ..
drwxrwxr-x 7 runner runner 4096 Sep 14 14:33 .git
-rw-rw-r-- 1 runner runner   66 Sep 14 14:33 .gitattributes
-rw-rw-r-- 1 runner runner 2763 Sep 14 14:33 .gitignore
-rw-rw-r-- 1 runner runner 1067 Sep 14 14:33 LICENSE
-rw-rw-r-- 1 runner runner  769 Sep 14 14:33 README.md
drwxrwxr-x 2 runner runner 4096 Sep 14 14:33 beetsplug
-rw-rw-r-- 1 runner runner  443 Sep 14 14:33 setup.py
```

### Python Files in Repository
```bash
$ find . -name "*.py" | sort
./beetsplug/__init__.py
./beetsplug/gaana.py
./setup.py
```

### Plugin Directory Contents
```bash
$ ls -la beetsplug/
__init__.py    # Standard namespace package init
gaana.py       # Main plugin implementation (338 lines)
```

### Sample setup.py Content
```python
setup(
    name='beets-gaana',
    version='0.1',
    description='beets plugin to use Gaana for metadata',
    install_requires=[
        'beets>=1.6.0',
        'requests',
        'pillow',
    ],
)
```

### Quick Validation Commands
- Check Python version: `python --version` → `Python 3.12.3`
- Test plugin import: `python -c "from beetsplug.gaana import GaanaPlugin"` → No output = success
- Check beets version after setup: `beet version` → Should show "plugins: gaana"

### Install Commands and Timing
```bash
# Full setup from scratch (2-3 minutes)
$ time pip install --user beets && pip install --user -e .
# Typical output shows "Successfully installed beets-2.4.0" with dependencies
# Real time: ~2-3 minutes with network, 30 seconds if cached

# Test plugin loads
$ python -c "from beetsplug.gaana import GaanaPlugin; print('Plugin loads successfully')"
Plugin loads successfully
```