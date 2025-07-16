import io
import sys
import site
import importlib
import platform
import subprocess
import os
from PyQt5.QtWidgets import QMessageBox

REQUIRED_PACKAGES = {
    "wheel": "",
    "hda": "",
    "owslib": ""
}

_failed_packages = []  

def ensure_dependencies_installed(iface=None):
    """
    Tries to install/upgrade all required packages.
    If any fail, they are skipped and noted for later summary.
    """
    for package, version_spec in REQUIRED_PACKAGES.items():
        package_spec = f"{package}{version_spec}"
        try:
            _install_package(package_spec, iface)
            _activate_package_in_session(package)
        except Exception as e:
            _failed_packages.append(package_spec)
            print(f"❌ Failed to install {package_spec}: {e}")

    if _failed_packages:
        _show_summary_dialog(iface)


def _install_package(package_spec, iface=None):
    """
    Installs or upgrades a package using pip.
    Uses the correct Python executable depending on platform.
    """
    try:
        system = platform.system().lower()
        python_exec = sys.executable  # default fallback

        if system == "windows":
            # sys.executable → qgis.exe → need to find python.exe
            qgis_dir = os.path.dirname(sys.executable)
            candidate = os.path.join(qgis_dir, "python.exe")
            if os.path.exists(candidate):
                python_exec = candidate
            else:
                raise RuntimeError("Could not locate QGIS Python interpreter (python.exe)")

        elif system == "darwin":
            # macOS: QGIS bundle → look for bin/python3
            candidate = os.path.join(os.path.dirname(sys.executable), "bin", "python3")
            if os.path.exists(candidate):
                python_exec = candidate
            else:
                raise RuntimeError("Could not locate QGIS Python (python3) in bundle")

        # On Linux (or fallback): use sys.executable
        print(f"🔧 Installing: {package_spec} using {python_exec}")

        args = [python_exec, "-m", "pip", "install", "--upgrade", package_spec]

        if system == "linux":
            args.insert(5, "--break-system-packages")

        
        startupinfo = None
        if platform.system().lower() == "windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo  # <-- suppress console window
        )

        if process.returncode != 0:
            raise RuntimeError(process.stderr.strip())

        print(process.stdout.strip())
        print(f"✅ Successfully installed: {package_spec}")

    except Exception as e:
        _show_error_dialog(package_spec, iface, e)
        raise



def _activate_package_in_session(package):
    """
    Ensures the package is available in the current session.
    """
    if site.USER_SITE not in sys.path:
        site.addsitedir(site.USER_SITE)

    importlib.invalidate_caches()
    try:
        importlib.import_module(package)
        print(f"🚀 Package '{package}' is now available.")
    except ImportError as e:
        print(f"❗ Could not import '{package}' after installation: {e}")


def _show_error_dialog(package_spec, iface, exception):
    """
    Shows a message box when a single package fails to install.
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Dependency Installation Failed")
    msg.setText(f"Could not install:\n{package_spec}")
    msg.setInformativeText("Please install it manually in the Python Console.")
    msg.setDetailedText(f"Error:\n{exception}\n\nTry:\npip install {package_spec} --break-system-packages")

    open_console_btn = msg.addButton("Open Python Console", QMessageBox.ActionRole)
    msg.addButton(QMessageBox.Close)
    msg.exec_()

    if iface and msg.clickedButton() == open_console_btn:
        iface.actionShowPythonDialog().trigger()


def _show_summary_dialog(iface=None):
    """
    Shows one final popup listing all failed packages.
    """
    failed_list = "\n".join(_failed_packages)
    summary = QMessageBox()
    summary.setIcon(QMessageBox.Warning)
    summary.setWindowTitle("Missing Dependencies")
    summary.setText("The following packages could not be installed:")
    summary.setDetailedText(failed_list)
    summary.addButton(QMessageBox.Ok)
    summary.exec_()
