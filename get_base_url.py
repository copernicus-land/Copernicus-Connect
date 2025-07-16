import requests
import re
from urllib.parse import urlparse, urlunparse


class GetBaseURL:
    BASE_URL = "https://moi-be.wekeo.eu/api/dataset"

    def get_layer_data(self, dataset_id):
        data = self._fetch_dataset(dataset_id)
        if not data:
            return None

        urls = self.extract_cmens_hrefs(data)
        service_type = "wmts" if urls else "wms"       

        if any("request=getcapabilities" in url.lower() for url in urls):
            return {
                "dataset_id": dataset_id,
                "capabilities_url": urls,
                "product": data.get("title", "Unknown product"),
                "type": service_type
            }

        layer_info = self._extract_layer_info(data)
        if layer_info:         
            urls = self._build_capabilities_urls(layer_info)

            if urls:                
                return {
                    "dataset_id": dataset_id,
                    "capabilities_url": urls,
                    "product": data.get("title", "Unknown product"),
                    "type": layer_info[0]["baseServices"][0]["service_type"].lower() if layer_info[0]["baseServices"] else "wms"
                }
        
        if not urls:
            urls = self.extract_getcapabilities_urls(data)
            if urls:
                service_type = "wmts" if "wmts" in urls[0].lower() else "wms"

        if urls:
            return {
                "dataset_id": dataset_id,
                "capabilities_url": urls,
                "product": "",
                "type": service_type
            }

    def transform_giolandpublic(self, url):
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")
        try:
            parts.remove("rest")
        except ValueError:
            pass
        if parts[-1].lower() in ["mapserver", "imageserver"]:
            parts.append("WMSServer")
        new_path = "/" + "/".join(parts) + "/"
        return urlunparse((parsed.scheme, parsed.netloc, new_path, '', '', ''))

    def transform_dataset_id(self, dataset_id):
        parts = dataset_id.split(":")
        if len(parts)>4:
            if parts[4].startswith("cmems"):
                return ":".join(parts[:4])
            elif parts[1] == "MO":
                return ":".join(parts[:4])
            else:
                return dataset_id
        else:
            return dataset_id
        
                 
        # return ":".join(parts[:4]) if len(parts) > 4 and parts[4].startswith("cmems") else dataset_id
        # return ":".join(parts[:4]) if len(parts) > 4  else dataset_id

    def _fetch_dataset(self, dataset_id):
        dataset_id = self.transform_dataset_id(dataset_id)
        url = f"{self.BASE_URL}/{dataset_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to fetch data for {dataset_id}: {e}")
            return None

    def _detect_service_type(self, base_url):
        path = base_url.lower()
        if "discomap.eea.europa.eu/arcgis/rest/services/giolandpublic/" in path:
            return self.transform_giolandpublic(base_url), "wms"
        if "geoserver.vlcc.geoville" in path:
            return base_url + "wms", "wms"
        if "wmts.marine.copernicus.eu" in path:
            return base_url + "teroWmts", "wmts"
        if "wmts" in path:
            return base_url, "wmts"
        if "wms" in path:
            return base_url, "wms"
        return base_url, "wms" 

    def _extract_layer_info(self, data):
        layers = data.get("layers", {})
        base_services = []

        for layer in layers.values():
            urls = layer.get("timeSpecificUrls", []) or layer.get("wmtsUrl", [])
            if isinstance(urls, str):
                urls = [urls]
            for full_url in urls:
                parsed = urlparse(full_url)
                path_parts = parsed.path.rstrip("/").split("/")

                SERVICE_ENDPOINTS = {"WMSServer", "WMS", "WFS", "MapServer", "FeatureServer"}
                if len(path_parts) > 1:
                    if path_parts[-1] in SERVICE_ENDPOINTS:
                        base_path = "/".join(path_parts) + "/"  # Behold hele stien
                    else:
                        base_path = "/".join(path_parts[:-1]) + "/"
                    clean_url = urlunparse((parsed.scheme, parsed.netloc, base_path, '', '', ''))
                    service_url, service_type = self._detect_service_type(clean_url)
                    if not any(s["service_url"] == service_url for s in base_services):
                        if service_url.startswith("https://image.discomap.eea.europa.eu/arcgis/rest/"):
                            service_url = self.transform_giolandpublic(service_url)
                        base_services.append({
                            "url": clean_url,
                            "service_url": service_url,
                            "service_type": service_type
                        })

        return [{"baseServices": base_services}]

    def _build_capabilities_urls(self, layer_info):
        urls = []
        for item in layer_info:
            for service in item.get("baseServices", []):
                url = service["service_url"]
                if "?" not in url:
                    url += "?"
                if "request=GetCapabilities" not in url.lower():
                    url += "request=GetCapabilities&service=" + service["service_type"].upper()
                urls.append(url)
        return urls

    def extract_cmens_hrefs(self, data):
        hrefs = []
        for dataset in data.get("stacData", {}).values():
            href = dataset.get("assets", {}).get("wmts", {}).get("href")
            if href:
                hrefs.append(href)
        return hrefs

    def extract_getcapabilities_urls(self, metadata):
        raw_metadata = metadata.get("rawMetadata", "")
        matches = re.findall(r"<gmd:URL>(.*?)</gmd:URL>", raw_metadata)
        return [url.replace("&amp;", "&") for url in matches if "GetCapabilities" in url]
