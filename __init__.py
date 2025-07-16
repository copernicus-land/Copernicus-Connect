from PyQt5.QtWidgets import QAction, QMessageBox
import traceback

def classFactory(iface):
    print(f"Inde i ClassFactory")
    try:
        from .install_dependencies import ensure_dependencies_installed
        
        ensure_dependencies_installed()
    except Exception as e:
        print("❌ Failed to install dependencies:")
        traceback.print_exc()
        try:
            QMessageBox.critical(None, "Dependency Error", f"Could not install required packages:\n\n{e}")
        except:
            pass  # Avoid crashing if GUI is not fully initialized
        return None


    from .plugin import CopernicusConnectPlugin
    return CopernicusConnectPlugin(iface)


    
