# Minimal version of owslib_wmts.py – handles WMTS metadata parsing and ignores empty dimensions

from urllib.parse import urlparse, urlunparse, urlencode, parse_qs, ParseResult

from owslib.util import testXMLValue, Authentication, openURL
from owslib.ows import ServiceIdentification, ServiceProvider, OperationsMetadata
from xml.etree.ElementTree import Element, ElementTree, fromstring

# Fallback-implementation af getXMLTree (for OWSLib < 0.33.0)
def getXMLTree(xml):
    """
    Return an ElementTree from an XML string, Element or ElementTree.
    """
    if isinstance(xml, ElementTree):
        return xml
    elif isinstance(xml, Element):
        tree = ElementTree()
        tree._setroot(xml)
        return tree
    elif isinstance(xml, str):
        return ElementTree(fromstring(xml))
    else:
        raise TypeError("Expecting an XML string or ElementTree object.")


_WMTS_NS = '{http://www.opengis.net/wmts/1.0}'
_OWS_NS = '{http://www.opengis.net/ows/1.1}'
_XLINK_NS = '{http://www.w3.org/1999/xlink}'

_LAYER_TAG = _WMTS_NS + 'Layer'
_IDENTIFIER_TAG = _OWS_NS + 'Identifier'
_TITLE_TAG = _OWS_NS + 'Title'
_ABSTRACT_TAG = _OWS_NS + 'Abstract'
_FORMAT_TAG = _WMTS_NS + 'Format'
_STYLE_TAG = _WMTS_NS + 'Style'
_RESOURCE_URL_TAG = _WMTS_NS + 'ResourceURL'
_TILE_MATRIX_SET_LINK_TAG = _WMTS_NS + 'TileMatrixSetLink'
_TILE_MATRIX_SET_TAG = _WMTS_NS + 'TileMatrixSet'
_DIMENSION_TAG = _WMTS_NS + 'Dimension'
_DIMENSION_VALUE_TAG = _WMTS_NS + 'Value'

_SERVICE_IDENTIFICATION_TAG = _OWS_NS + 'ServiceIdentification'
_SERVICE_PROVIDER_TAG = _OWS_NS + 'ServiceProvider'
_OPERATIONS_METADATA_TAG = _OWS_NS + 'OperationsMetadata'
_CONTENTS_TAG = _WMTS_NS + 'Contents'


class ContentMetadata:
    def __init__(self, elem: Element):
        self.id = testXMLValue(elem.find(_IDENTIFIER_TAG))
        self.title = testXMLValue(elem.find(_TITLE_TAG))
        self.abstract = testXMLValue(elem.find(_ABSTRACT_TAG))
        self.formats = [f.text for f in elem.findall(_FORMAT_TAG)]
        self.styles = [s.find(_IDENTIFIER_TAG).text for s in elem.findall(_STYLE_TAG) if s.find(_IDENTIFIER_TAG) is not None]
        self.resourceURLs = [r.attrib for r in elem.findall(_RESOURCE_URL_TAG)]

        self.tilematrixsetlinks = []
        for link in elem.findall(_TILE_MATRIX_SET_LINK_TAG):
            tms = link.find(_TILE_MATRIX_SET_TAG)
            if tms is not None and tms.text:
                self.tilematrixsetlinks.append(tms.text.strip())

        self.dimensions = {}
        for dim in elem.findall(_DIMENSION_TAG):
            identifier = dim.find(_IDENTIFIER_TAG)
            if identifier is None:
                continue
            values = [v.text for v in dim.findall(_DIMENSION_VALUE_TAG) if v.text]
            if not values:
                print(f"Ignorerer Dimension '{identifier.text}' uden værdier.")
                continue
            self.dimensions[identifier.text] = values


class WebMapTileService:
    def __init__(self, url, version='1.0.0', username=None, password=None, headers=None, cookies=None):
        self.url = url
        self.version = version
        self.headers = headers
        self.cookies = cookies
        self.auth = Authentication(username, password)
        self.contents = {}
        self.identification = None
        self.provider = None
        self.operations = []

        reader = WMTSCapabilitiesReader(self.version, url, headers=headers, auth=self.auth, cookies=cookies)
        self._capabilities = reader.read(self.url)

        self._build_metadata()

    def _build_metadata(self):
        caps = self._capabilities.find(_CONTENTS_TAG)
        for layer_elem in caps.findall(_LAYER_TAG):
            cm = ContentMetadata(layer_elem)
            if cm.id:
                self.contents[cm.id] = cm

        ident = self._capabilities.find(_SERVICE_IDENTIFICATION_TAG)
        if ident is not None:
            self.identification = ServiceIdentification(ident)

        provider = self._capabilities.find(_SERVICE_PROVIDER_TAG)
        if provider is not None:
            self.provider = ServiceProvider(provider)

        ops = self._capabilities.find(_OPERATIONS_METADATA_TAG)
        if ops is not None:
            for elem in ops:
                self.operations.append(OperationsMetadata(elem))


class WMTSCapabilitiesReader:
    def __init__(self, version='1.0.0', url=None, headers=None, auth=None, cookies=None):
        self.version = version
        self.url = url
        self.headers = headers
        self.auth = auth
        self.cookies = cookies

    def capabilities_url(self, service_url):
        pieces = urlparse(service_url)
        args = parse_qs(pieces.query)
        args.setdefault('service', ['WMTS'])
        args.setdefault('request', ['GetCapabilities'])
        args.setdefault('version', [self.version])
        query = urlencode(args, doseq=True)
        pieces = ParseResult(pieces.scheme, pieces.netloc, pieces.path, pieces.params, query, pieces.fragment)
        return urlunparse(pieces)

    def read(self, service_url):
        getcaprequest = self.capabilities_url(service_url)
        spliturl = getcaprequest.split('?')
        u = openURL(spliturl[0], spliturl[1], method='Get',
            cookies=self.cookies, headers=self.headers, auth=self.auth)

        xml_content = u.read()  # læs stream-indholdet som bytes
        return getXMLTree(xml_content.decode("utf-8"))  # parse som XML string
