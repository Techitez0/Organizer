import customtkinter
import pystray
from PIL import Image
import threading
import os
import sys

# Import the core logic from the other file
from file_sorter_logic import FileSorter, DEFAULT_SOURCE_DIR, DEFAULT_TARGET_DIR

# === CONFIGURATION FOR UI ===
APP_NAME = "Moomin Discipline"
ICON_PATH = "sorter_icon.png" 

# --- Kawaii Theme Settings ---
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("green")


class SorterApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("400x300")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.hide_window) 

        self.sorter = FileSorter()
        self.sorter_thread = None

        self.create_widgets()
        self.create_system_tray()

        self.start_monitoring_logic()
        self.update_status_display()

    def create_widgets(self):
        self.control_frame = customtkinter.CTkFrame(self)
        self.control_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.status_label = customtkinter.CTkLabel(self.control_frame, text="Status: Loading...", font=("Roboto", 16, "bold"))
        self.status_label.pack(pady=10)

        self.source_label = customtkinter.CTkLabel(self.control_frame, text=f"Source: {self.sorter.source_dir}", wraplength=300)
        self.source_label.pack(pady=5)
        
        self.target_label = customtkinter.CTkLabel(self.control_frame, text=f"Target: {self.sorter.target_dir}", wraplength=300)
        self.target_label.pack(pady=5)

        self.toggle_button = customtkinter.CTkButton(self.control_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.toggle_button.pack(pady=10)

        self.settings_button = customtkinter.CTkButton(self.control_frame, text="Change Folders", command=self.show_settings_window)
        self.settings_button.pack(pady=5)
        
        self.exit_button = customtkinter.CTkButton(self.control_frame, text="Exit App", command=self.exit_app, fg_color="red")
        self.exit_button.pack(pady=10)

    def update_status_display(self):
        status_text = self.sorter.get_status()
        self.status_label.configure(text=f"Status: {status_text}")
        self.source_label.configure(text=f"Source: {self.sorter.source_dir}")
        self.target_label.configure(text=f"Target: {self.sorter.target_dir}")
        self.toggle_button.configure(text="Stop Monitoring" if self.sorter.is_running() else "Start Monitoring")
        self.toggle_button.configure(fg_color="#3a7ebf" if self.sorter.is_running() else customtkinter.get_default_color_theme())
        self.tray_icon.menu = self.create_tray_menu()

    def toggle_monitoring(self):
        if self.sorter.is_running():
            self.stop_monitoring_logic()
        else:
            self.start_monitoring_logic()
        self.update_status_display()

    def start_monitoring_logic(self):
        if not self.sorter.is_running():
            self.sorter_thread = threading.Thread(target=self.sorter.start_monitoring, daemon=True)
            self.sorter_thread.start()
            self.update_status_display()

    def stop_monitoring_logic(self):
        if self.sorter.is_running():
            self.sorter.stop_monitoring()
            if self.sorter_thread:
                self.sorter_thread.join(timeout=5)
            self.sorter_thread = None
            self.update_status_display()
            
    def show_settings_window(self):
        if not hasattr(self, "settings_window") or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        self.settings_window.focus()

    def hide_window(self):
        self.withdraw()
        
    def show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def exit_app(self, icon=None, item=None):
        self.stop_monitoring_logic()
        if self.tray_icon:
            self.tray_icon.stop()
        self.quit()
        sys.exit()

    def create_system_tray(self):
        try:
            image = Image.open(ICON_PATH)
            self.tray_icon = pystray.Icon(APP_NAME, image, APP_NAME, menu=self.create_tray_menu())
            self.tray_icon.run_detached()
        except FileNotFoundError:
            image = Image.new('RGB', (64, 64), color = 'green')
            self.tray_icon = pystray.Icon(APP_NAME, image, APP_NAME, menu=self.create_tray_menu())
            self.tray_icon.run_detached()


    def create_tray_menu(self):
        menu_items = [
            pystray.MenuItem("Show " + APP_NAME, self.show_window),
            pystray.MenuItem("Status: " + self.sorter.get_status(), self.show_window, enabled=False),
            pystray.MenuItem("Toggle Monitoring", self.toggle_monitoring),
            pystray.MenuItem("Exit", self.exit_app)
        ]
        return pystray.Menu(*menu_items)


class SettingsWindow(customtkinter.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Change Folder Settings")
        self.geometry("450x300")
        self.transient(master) 
        self.grab_set() 

        self.master_app = master

        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        customtkinter.CTkLabel(self, text="Source Folder:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.source_entry = customtkinter.CTkEntry(self, width=300)
        self.source_entry.insert(0, self.master_app.sorter.source_dir)
        self.source_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        customtkinter.CTkLabel(self, text="Target Folder:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.target_entry = customtkinter.CTkEntry(self, width=300)
        self.target_entry.insert(0, self.master_app.sorter.target_dir)
        self.target_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.save_button = customtkinter.CTkButton(self, text="Save Settings", command=self.save_settings)
        self.save_button.grid(row=2, column=0, columnspan=2, pady=20)
        
        self.reset_button = customtkinter.CTkButton(self, text="Reset to Defaults", command=self.reset_to_defaults, fg_color="gray")
        self.reset_button.grid(row=3, column=0, columnspan=2, pady=5)


    def save_settings(self):
        new_source = self.source_entry.get()
        new_target = self.target_entry.get()

        if not os.path.isdir(new_source):
            customtkinter.CTkMessageBox.show_warning("Invalid Source", "The source folder path does not exist.")
            return

        was_running = self.master_app.sorter.is_running()
        if was_running: self.master_app.stop_monitoring_logic()
        
        self.master_app.sorter.set_dirs(new_source, new_target)
        
        if was_running: self.master_app.start_monitoring_logic()

        self.master_app.update_status_display()
        self.destroy()
        
    def reset_to_defaults(self):
        self.source_entry.delete(0, customtkinter.END)
        self.source_entry.insert(0, DEFAULT_SOURCE_DIR)
        self.target_entry.delete(0, customtkinter.END)
        self.target_entry.insert(0, DEFAULT_TARGET_DIR)


if __name__ == "__main__":
    app = SorterApp()
    app.show_window()
    app.mainloop()