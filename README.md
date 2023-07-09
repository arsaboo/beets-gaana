# beets-gaana
A plugin for [beets](https://github.com/beetbox/beets) to use Gaana as a metadata source.

## Installation

Install the plugin using `pip`:

```shell
pip install git+https://github.com/arsaboo/beets-gaana.git
```

Then, [configure](#configuration) the plugin in your
[`config.yaml`](https://beets.readthedocs.io/en/latest/plugins/index.html) file.

## Configuration

Add `gaana` to your list of enabled plugins and configure the baseurl where the Gaana API is installed.

```yaml
plugins: gaana
```

This plugin requires the [GaanaPy](https://github.com/ZingyTomato/GaanaPy) library. See the link to configure the same. Once you have installed the library, add the baseurl in your config as below:
```yaml
gaana:
    baseurl: http://192.168.2.60:8000
```
