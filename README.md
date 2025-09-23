# Copernicus Connect

**Copernicus Connect** is a QGIS plugin that makes it easy to browse, download, and visualise Copernicus data directly in QGIS.

It provides a user-friendly interface for discovering and querying datasets from the [WEkEO platform](https://wekeo.copernicus.eu/) using the Harmonized Data Access (HDA) API. The plugin also supports adding WMS and WMTS services to your QGIS project.

> To request data from WEkEO, you need a free user account, which can be created at [https://wekeo.copernicus.eu/register](https://wekeo.copernicus.eu/register).

You can download the plugin as a ZIP file and install it in QGIS via the Plugin Installer:

1. **Download** Go to the project’s “[Releases](https://github.com/copernicus-land/Copernicus-Connect/releases)” on GitHub and download the latest ZIP package (e.g., `Copernicus-Connect 10.zip`).
2. In QGIS, go to **Plugins ▶ Manage and Install Plugins…**.
3. Select the **Install from ZIP** tab, browse to the downloaded ZIP file, and click **Install Plugin**.

#### Workaround: Update credentials in `.hdarc`

If you experience login issues, you can manually check and update the credentials stored in the hidden `.hdarc` file.

- **Windows**The file is located at:

  ```
  C:\Users\[your username]\.hdarc
  ```

  Make sure that *“Show hidden files”* is enabled in Windows Explorer.
- **Linux**The file is located in your home directory:

  ```
  ~/.hdarc
  ```
- **macOS**
  The file is also located in your home directory:

  ```
  ~/.hdarc
  ```

Open the `.hdarc` file with a text editor (e.g., Notepad on Windows, nano/vi on Linux, or TextEdit on macOS) and update the `username` and `password` values so they match your WEkEO account.
After saving the changes, the login should work correctly.

### Manual installation of `hda` or `owslib` for QGIS

If the automatic installation of required Python packages fails inside QGIS, you can install them manually.Follow these steps:

1. **Locate your QGIS Python environment**

   - Open QGIS
   - Go to **Plugins → Python Console**
   - Run the following command to check the active Python path:
     ```python
     import sys
     print(sys.executable)
     ```
   - This will show you the Python executable used by QGIS (e.g., something like `C:\OSGeo4W\apps\Python39\python.exe` on Windows).
2. **Open a terminal/command prompt with that Python**

   - On **Windows**:Open `OSGeo4W Shell` or `cmd.exe`, then run the path you found above. Example:

     ```bash
     C:\OSGeo4W\apps\Python39\python.exe -m pip install hda
     ```
   - On **Linux/macOS**:
     Use the QGIS Python executable, for example:

     ```bash
     /usr/bin/qgis3 --noplugin --code "import sys; print(sys.executable)"
     ```

     Then install with:

     ```bash
     /path/to/qgis/python -m pip install hda
     ```
3. **Install `hda` or `owslib`**

   - To install **hda**:
     ```bash
     python -m pip install hda
     ```
   - To install **owslib**:
     ```bash
     python -m pip install owslib
     ```
4. **Verify the installation inside QGIS**

   - Restart QGIS.
   - Open the **Python Console** again and run:
     ```python
     import hda
     import owslib
     print("Modules installed successfully")
     ```
   - If no error appears, the installation was successful.

---

**Tip:**
If you are behind a proxy or corporate firewall, you may need to configure pip to use a proxy, e.g.:

```bash
python -m pip install hda --proxy http://user:password@proxyserver:port

```
