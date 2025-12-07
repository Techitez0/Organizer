<p align="center">
  <img src="https://github.com/user-attachments/assets/06f85aba-abba-49a0-a332-f00c3c70439a" alt="Screenshot (600)" width="517" height="440"/>
</p>



# 📁 Moomin Discipline: Automated File Sorter

**Moomin Discipline** is a lightweight, robust, and silent utility designed to automatically organize files as they appear in a specified source directory (like your **Downloads** folder).  
It runs in the background, minimizing clutter and ensuring your workspace remains organized, accessible, and ready for action.

The application is controlled via a simple **Graphical User Interface (GUI)** and a **System Tray Icon**, making it highly discreet and easy to manage.

---

## ✨ Features
- **Continuous Monitoring**: Uses the `watchdog` library for real-time file monitoring.  
- **Intelligent Categorization**: Files are automatically moved into categorized folders (Images, Documents, Audio, Videos, etc.).  
- **Robust Moving Logic**: Implements retry logic, file lock handling, and explicit deletion fixes to prevent duplication and handle incomplete downloads gracefully.  
- **Strict Cleanup Loop**: Periodic background thread catches and moves any files missed by real-time events (e.g., instant `.ico` and converted files).  
- **Silent Operation**: Runs in the background and is controlled via a System Tray Icon.  
- **User-Friendly GUI**: Built with `customtkinter`, allowing users to view status, toggle monitoring, and change Source/Target directories easily.  

---

## 🚀 Installation and Setup

### Prerequisites
You need **Python 3.8+** and the following libraries installed:

```bash
pip install -r requirements.txt
```
---
# 📂 File Structure
Ensure the following files are placed in the same project directory (e.g., C:\Users\Asad\Documents\MoominDiscipline):

app_ui.py → Main application and UI controller

file_sorter_logic.py → Core monitoring engine

organizer.ico → Executable Icon

organizer_tray.png → System Tray Icon (recommended: convert a copy of your ICO to PNG for best tray stability)

# Compile the App
Run the following command from the project directory:
```bash
pyinstaller --noconsole --onefile --icon="organizer.ico" --add-data "organizer.ico;." app_ui.py

```
