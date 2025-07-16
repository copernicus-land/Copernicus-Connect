from owslib.wms import WebMapService
from urllib.parse import urlparse, urlunparse

class WMSCapabilitiesParser:
    def __init__(self, url):
        self.original_url = url
        self.base_url = self._strip_query(url)
        self.wms = None
        self.service_metadata = {}
        self.layers = []
        self._load_capabilities()

    def _strip_query(self, url):
        """Fjerner query-parametre fra WMS URL."""
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

    def _load_capabilities(self):
        """Loader og parser GetCapabilities fra WMS."""
        try:
            self.wms = WebMapService(self.original_url, version='1.3.0')

            self.service_metadata = {
                "title": self.wms.identification.title,
                "abstract": self.wms.identification.abstract,
                "provider": self.wms.provider.name
            }

            getmap_formats = []
            for op in self.wms.operations:
                if op.name == "GetMap":
                    getmap_formats = op.formatOptions

            for name, layer in self.wms.contents.items():
                crs = self._get_crs(layer)
                style = self._get_first_style(layer)
                image_format = "image/png"
                if "image/png" not in getmap_formats and getmap_formats:
                    image_format = getmap_formats[0]

                uri = (
                    f"url={self.base_url}?"
                    f"&service=WMS"
                    f"&version=1.3.0"
                    f"&request=GetMap"
                    f"&layers={name}"
                    #f"&styles={style}"
                    f"&styles="
                    f"&crs={crs}"
                    f"&format={image_format}"
                )

                self.layers.append({
                    "name": name,
                    "title": layer.title,
                    "crs": crs,
                    "style": style,
                    "format": image_format,
                    "qgis_uri": uri
                })

        except Exception as e:
            return None

    def _get_crs(self, layer):
        """Returnerer ønsket eller fallback CRS."""
        if "EPSG:3857" in layer.crsOptions:
            return "EPSG:3857"
        elif "EPSG:4326" in layer.crsOptions:
            return "EPSG:4326"
        elif layer.crsOptions:
            return list(layer.crsOptions)[0]
        return "EPSG:4326"

    def _get_first_style(self, layer):
        """Returnerer første tilgængelige stil (eller blank)."""
        styles = layer.styles
        return next(iter(styles.keys()), "") if styles else ""

    def get_service_metadata(self):
        """Returnerer metadata om selve tjenesten."""
        return self.service_metadata

    def get_layers(self):
        """Returnerer liste af lag med metadata og QGIS URI."""
        return self.layers
