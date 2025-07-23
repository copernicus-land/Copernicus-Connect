# Copernicus Connect

**Copernicus Connect** is a QGIS plugin that makes it easy to browse, download, and visualise Copernicus data directly in QGIS.

It provides a user-friendly interface for discovering and querying datasets from the [WEkEO platform](https://wekeo.copernicus.eu/) using the Harmonized Data Access (HDA) API. The plugin also supports adding WMS and WMTS services to your QGIS project.

> To request data from WEkEO, you need a free user account, which can be created at [https://wekeo.copernicus.eu/register](https://wekeo.copernicus.eu/register).

You can download the plugin as a ZIP file and install it in QGIS via the Plugin Installer:

1. **Download**  
   Go to the project’s “Releases” on GitHub and download the latest ZIP package (e.g., `Copernicus Connect 0.7.zip`).

2. **Extract**  
   Unzip the downloaded file. You will get a folder named `<repo-name>-<tag>` (e.g., `Copernicus-Connect-0.7-beta/`).

3. **Re-zip the root folder**  
   QGIS needs the plugin’s files (like __init__.py, metadata.txt, etc.) to be the first items you see when opening the ZIP. GitHub’s release ZIP always wraps everything in an extra folder, so you must zip only the plugin folder itself—this way its files end up right at the ZIP’s root.

3. In QGIS, go to **Plugins ▶ Manage and Install Plugins…**.  

4. Select the **Install from ZIP** tab, browse to the modified ZIP file, and click **Install Plugin**.  

Note: You cannot install GitHub’s original ZIP directly in QGIS because it contains an extra parent folder. That’s why you need to re‑zip the root folder before installation.
