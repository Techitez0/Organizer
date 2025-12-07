import os
import shutil
import time
import threading # <-- New import for the cleanup loop
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# === CONFIGURATION ===
DEFAULT_SOURCE_DIR = r"C:\Users\Asad\Downloads"
DEFAULT_TARGET_DIR = r"C:\Users\Asad\Documents\here"

# --- CATEGORY MAPPING ---
FILE_CATEGORIES = {
    "Images": ('.jpeg', '.jpg', '.png', '.gif', '.bmp', '.tiff', '.ico', '.webp'), # <-- .ico is here
    "Documents": ('.pdf', '.doc', '.docx', '.txt', '.rtf', '.xls', '.xlsx', '.ppt', '.pptx'),
    "Audio": ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'),
    "Videos": ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv'),
    "Installers": ('.exe', '.msi', '.dmg', '.pkg'),
    "Compressed": ('.zip', '.rar', '.7z', '.tar', '.gz'),
    "Code & Scripts": ('.py', '.java', '.c', '.cpp', '.html', '.css', '.js', '.ipynb', '.sh'),
}

# --- ROBUSTNESS SETTINGS ---
MAX_ATTEMPTS = 5
WAIT_TIME = 2
CLEANUP_INTERVAL = 5 # Seconds between cleanup checks

# --- Utility Function ---
def _move_single_file(file_path, target_base_dir):
    # ... (Keep this function exactly as it was in the last update) ...
    item_name = os.path.basename(file_path)
    
    # Ignore folders and temporary/incomplete files
    if os.path.isdir(file_path) or item_name.startswith('~') or item_name.endswith(('.tmp', '.crdownload', '.part')):
        return
    
    time.sleep(0.5) 
    
    for attempt in range(MAX_ATTEMPTS):
        try:
            # 1. Categorization Logic
            _, extension = os.path.splitext(item_name)
            extension = extension.lower() 
            destination_folder_name = "Other" 

            for category, extensions in FILE_CATEGORIES.items():
                if extension in extensions:
                    destination_folder_name = category
                    break 
            
            # 2. Define and Create Destination Path
            destination_dir = os.path.join(target_base_dir, destination_folder_name)
            os.makedirs(destination_dir, exist_ok=True)
            destination_path = os.path.join(destination_dir, item_name)

            # 3. Attempt to move the file (Copy + Delete)
            shutil.move(file_path, destination_path) 
            print(f"[Sorter Logic] MOVED SUCCESSFULLY: {item_name} -> {destination_folder_name}")
            return # Success!

        except shutil.Error as e:
            # Handle specific case: file copied, but delete failed (duplicate issue)
            if os.path.exists(destination_path):
                try:
                    os.remove(file_path)
                    print(f"[Sorter Logic] Explicit deletion of {item_name} from source successful.")
                    return # Success after explicit delete!
                except Exception as del_e:
                    print(f"[Sorter Logic] Explicit deletion failed: {del_e}. Retrying move/delete process.")
            
            # Standard retry logic for other errors
            if attempt < MAX_ATTEMPTS - 1:
                print(f"[Sorter Logic] Failed to move {item_name} (attempt {attempt + 1}). Retrying in {WAIT_TIME}s...")
                time.sleep(WAIT_TIME)
            else:
                print(f"[Sorter Logic] FAILED TO MOVE/DELETE {item_name} after {MAX_ATTEMPTS} attempts. Final Error: {e}")
        
        except Exception as e:
            if attempt < MAX_ATTEMPTS - 1:
                 print(f"[Sorter Logic] Generic error with {item_name}: {e}. Retrying in {WAIT_TIME}s...")
                 time.sleep(WAIT_TIME)
            else:
                 print(f"[Sorter Logic] FAILED TO MOVE/DELETE {item_name} after {MAX_ATTEMPTS} attempts. Final Error: {e}")


# === WATCHDOG EVENT HANDLER CLASS (Stricter Wait) ===
class SorterEventHandler(FileSystemEventHandler):
    def __init__(self, target_base_dir):
        super().__init__()
        self.target_base_dir = target_base_dir

    def on_created(self, event):
        if not event.is_directory:
            item_name = os.path.basename(event.src_path)
            # Apply strict wait for immediate files (like ICOs)
            if not item_name.endswith(('.tmp', '.crdownload', '.part')):
                time.sleep(1.5)  
            
            _move_single_file(event.src_path, self.target_base_dir)

    def on_renamed(self, event):
        if not event.is_directory:
            _move_single_file(event.dest_path, self.target_base_dir) 


# === MAIN FILE SORTER CLASS (With Periodic Cleanup) ===
class FileSorter:
    def __init__(self, source_dir=DEFAULT_SOURCE_DIR, target_dir=DEFAULT_TARGET_DIR):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.observer = None
        self.running = False
        self._stop_event = threading.Event() # For stopping the cleanup loop

    # --- NEW PERIODIC CLEANUP METHOD ---
    def _check_for_missed_files(self):
        while not self._stop_event.is_set():
            time.sleep(CLEANUP_INTERVAL)
            if not self.running: continue # Don't check if monitoring is paused

            print(f"[Cleanup] Running periodic check for missed files in {self.source_dir}...")
            
            # Iterate through all items in the source directory
            for item_name in os.listdir(self.source_dir):
                file_path = os.path.join(self.source_dir, item_name)
                
                # We only check files that look complete (not temp/incomplete)
                if not os.path.isdir(file_path) and not item_name.endswith(('.crdownload', '.part')):
                    # Use a separate thread so cleanup doesn't block the main loop
                    threading.Thread(target=_move_single_file, args=(file_path, self.target_dir), daemon=True).start()
                    # Print status for visibility in console
                    print(f"[Cleanup] Found and queued for move: {item_name}")

    def start_monitoring(self):
        if self.running: return

        if not os.path.isdir(self.source_dir):
            print(f"[FileSorter] Error: Source directory not found: {self.source_dir}")
            return
        if not os.path.isdir(self.target_dir):
            os.makedirs(self.target_dir, exist_ok=True)

        # 1. Start Watchdog Observer
        self.observer = Observer()
        event_handler = SorterEventHandler(self.target_dir)
        self.observer.schedule(event_handler, self.source_dir, recursive=False)
        self.observer.start()

        # 2. Start Cleanup Thread (New)
        self._stop_event.clear()
        self.cleanup_thread = threading.Thread(target=self._check_for_missed_files, daemon=True)
        self.cleanup_thread.start()
        
        self.running = True
        print(f"[FileSorter] Started monitoring and cleanup loop for: {self.source_dir}")

    def stop_monitoring(self):
        if not self.running: return
        
        # 1. Stop Watchdog Observer
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # 2. Stop Cleanup Thread (New)
        self._stop_event.set()
        if self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=1)
            
        self.running = False
        print("[FileSorter] Stopped monitoring.")

    def is_running(self):
        return self.running

    def get_status(self):
        return "Monitoring" if self.running else "Stopped"
        
    def set_dirs(self, source, target):
        self.source_dir = source
        self.target_dir = target
        print(f"[FileSorter] Directories updated: Source='{source}', Target='{target}'")