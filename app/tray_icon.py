"""
System Tray Icon for SyncBackup v1.1

Autor: Goran Zajec
Web stranica: https://svejedobro.hr
"""
import tkinter as tk
from tkinter import messagebox
try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
import threading

class SystemTrayIcon:
    """System tray icon for SyncBackup application"""
    
    def __init__(self, root):
        self.root = root
        self.icon = None
        self.running = False
        
        if not PYSTRAY_AVAILABLE:
            print("Warning: pystray not available. Tray icon disabled.")
            return
    
    def create_icon_image(self):
        """Create a simple icon image"""
        # Create a simple 64x64 icon
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        
        # Draw a folder shape
        draw.rectangle([10, 20, 54, 50], fill='white', outline='black')
        draw.rectangle([10, 15, 35, 25], fill='white', outline='black')
        
        # Draw "S" for SyncBackup
        draw.text((22, 28), "S", fill='blue')
        
        return image
    
    def show(self, root_window):
        """Show the main window"""
        root_window.deiconify()
        root_window.lift()
        root_window.focus_force()
    
    def quit_app(self, icon_obj):
        """Quit the application"""
        if messagebox.askyesno("Quit", "Are you sure you want to quit SyncBackup?"):
            self.running = False
            if icon_obj:
                icon_obj.stop()
            self.root.quit()
    
    def create_tray_icon(self):
        """Create system tray icon"""
        if not PYSTRAY_AVAILABLE:
            return
        
        image = self.create_icon_image()
        
        menu = Menu(
            MenuItem('Show', lambda: self.show(self.root)),
            MenuItem('Quit', self.quit_app)
        )
        
        self.icon = Icon("SyncBackup v1.2", image, "SyncBackup v1.2", menu)
        self.running = True
        
        # Run icon in separate thread
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
    
    def minimize_to_tray(self):
        """Minimize window to tray"""
        if PYSTRAY_AVAILABLE and self.icon:
            self.root.withdraw()
        else:
            # Fallback: just minimize normally
            self.root.iconify()
    
    def stop(self):
        """Stop the tray icon"""
        self.running = False
        if self.icon:
            self.icon.stop()

