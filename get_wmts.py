from urllib.parse import urlparse, urlunparse
try:
    from .owslib_wmts_min import WebMapTileService
except ImportError as e:   
    from owslib_wmts_min import WebMapTileService 

class WMTSCapabilitiesParser:
    def __init__(self, url):
        self.original_url = url
        self.base_url = self._strip_query(url)
        self.wmts = None
        self.service_metadata = {}
        self.layers = []
        self._load_capabilities()

    def _strip_query(self, url):
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

    def _load_capabilities(self):
        try:
            self.wmts = WebMapTileService(self.original_url, version='1.0.0')

            self.service_metadata = {
                "title": getattr(self.wmts.identification, 'title', ''),
                "abstract": getattr(self.wmts.identification, 'abstract', ''),
                "provider": getattr(self.wmts.provider, 'name', '')
            }

            for layer_name, layer in self.wmts.contents.items():
                tilematrix_sets = layer.tilematrixsetlinks
                tilematrix_set = tilematrix_sets[0] if tilematrix_sets else "EPSG:3857"

                formats = layer.formats
                image_format = "image/png"
                if image_format not in formats and formats:
                    image_format = formats[0]

                uri = (
                    f"contextualWMSLegend=0"
                    f"&crs={tilematrix_set}"
                    f"&dpiMode=7"
                    f"&format={image_format}"
                    f"&layers={layer_name}"
                    f"&styles="
                    f"&tileMatrixSet={tilematrix_set}"
                    f"&url={self.base_url}"
                )

                self.layers.append({
                    "name": layer_name,
                    "title": layer.title,
                    "tilematrix_set": tilematrix_set,
                    "format": image_format,
                    "qgis_uri": uri,
                    "type": "wms"
                })

        except Exception as e:
            raise RuntimeError(f"Fejl ved hentning/parsing af WMTS: {e}")

    def get_service_metadata(self):
        return self.service_metadata

    def get_layers(self):
        return self.layers
