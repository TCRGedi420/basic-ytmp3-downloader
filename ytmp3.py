import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pytube import YouTube
from pytube.exceptions import RegexMatchError
import os
from moviepy.editor import AudioFileClip
import re
from PIL import Image, ImageTk
import threading
import webbrowser
import eyed3
import requests
import io

# Define the global destination variable
downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
destination = os.path.join(downloads_folder, 'YTMP3_Downloads')

# Global variable to store total_size
total_size = [0]

def create_destination_folder():
    if not os.path.exists(destination):
        os.makedirs(destination)
        print(f"Folder created: {destination}")

def clean_filename(title):
    # Remove invalid characters from the title
    cleaned_title = re.sub(r'[\\/*?:"<>|]', '', title)
    return cleaned_title

def download_mp3():
    def download_thread():
        try:
            yt = YouTube(video_url)

            # Display metadata information
            title_label.config(text=f"Title: {yt.title}")
            author_label.config(text=f"Author: {yt.author}")
            duration_label.config(text=f"Duration: {yt.length // 60}:{yt.length % 60:02}")

            # Get the high-quality thumbnail URL
            thumbnail_url = yt.thumbnail_url

            # Download the stream with the highest audio quality in MP4 format
            audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
            total_size[0] = audio_stream.filesize

            # Download the stream and save it as an MP4 file
            mp4_filename = 'temp_audio.mp4'
            mp4_path = os.path.join(destination, mp4_filename)
            audio_stream.download(output_path=destination, filename=mp4_filename)

            # Use the high-quality thumbnail URL directly
            thumbnail_response = requests.get(thumbnail_url, stream=True)
            thumbnail = Image.open(io.BytesIO(thumbnail_response.content))

            # Convert the downloaded MP4 file to MP3 using the moviepy library
            mp3_filename = f'{clean_filename(yt.title)}.mp3'
            mp3_path = os.path.join(destination, mp3_filename)
            audio_clip = AudioFileClip(mp4_path)
            audio_clip.write_audiofile(mp3_path, codec='libmp3lame', ffmpeg_params=['-q:a', '0'])

            # Remove the temporary MP4 file
            os.remove(mp4_path)

            # Use eyed3 to set album artwork (thumbnail) and add metadata
            audiofile = eyed3.load(mp3_path)
            thumbnail_bytes = io.BytesIO()
            thumbnail.save(thumbnail_bytes, format='JPEG')
            thumbnail_bytes.seek(0)
            audiofile.tag.images.set(3, thumbnail_bytes.read(), 'image/jpeg')
            
            # Set Album and Artist metadata
            audiofile.tag.album = yt.author
            audiofile.tag.artist = yt.author
            audiofile.tag.comments.set("Downloaded with YTMp3.py")

            audiofile.tag.save()

            # Update the table with the downloaded MP3 information
            update_table(yt.title, yt.author, f"{yt.length // 60}:{yt.length % 60:02}", "Download Complete")

        except RegexMatchError:
            log_text.insert(tk.END, "Invalid YouTube URL\n")
            # Update the table with the error status
            update_table(video_url, "", "", "Invalid YouTube URL")

    video_url = entry.get()

    # Start download thread
    download_thread_instance = threading.Thread(target=download_thread)
    download_thread_instance.start()

def update_table(title, artist, duration, status):
    table.insert("", "end", values=(title, artist, duration, status), tags=status)


def open_location():
    # Open Explorer to the file location
    webbrowser.open(destination)

def paste_from_clipboard():
    # Paste content from clipboard into the entry field
    entry.delete(0, tk.END)
    entry.insert(0, root.clipboard_get())

def about():
    messagebox.showinfo("About", "Created with ChatGPT by TCR Gedi")

def exit_program():
    root.destroy()

def draw_gradient(canvas):
    # Create a white gradient background
    for i in range(256):
        color = "#{:02X}{:02X}{:02X}".format(i, i, i)
        canvas.create_line(0, i, root.winfo_width(), i, fill=color)

def show_file_location_help():
    messagebox.showinfo("File Location Help", "Go to 'File -> Open Location' and you can see the folder location of the downloaded MP3s.")

def show_how_it_works_help():
    help_text = (
        "The code runs on these packages and dependencies:\n\n"
        "- tkinter: GUI (Graphical User Interface) library for creating the application window, labels, buttons, and other widgets.\n\n"
        "- ttk (themed tkinter): Provides access to the Tk themed widget set.\n\n"
        "- messagebox: Part of tkinter, used for displaying information or prompting the user with messages.\n\n"
        "- scrolledtext: A widget that provides a scrollable text area.\n\n"
        "- pytube: A library for downloading YouTube videos.\n\n"
        "- pytube.exceptions: Specific exceptions related to pytube, such as RegexMatchError.\n\n"
        "- os: Provides a way of using operating system-dependent functionality, used for file and directory manipulation.\n\n"
        "- moviepy.editor: A library for video editing. In this code, it's used for converting downloaded MP4 files to MP3.\n\n"
        "- re (regular expressions): A module for regular expressions. Used for cleaning file names by removing invalid characters.\n\n"
        "- PIL (Python Imaging Library): A library for opening, manipulating, and saving many different image file formats.\n\n"
        "- ImageTk: A module in PIL that provides Tkinter-compatible photo images.\n\n"
        "- requests: Used for making HTTP requests, in this case, for downloading YouTube video thumbnails.\n\n"
        "- threading: Allows the code to run multiple threads concurrently. Used for running the download process in a separate thread.\n\n"
        "- webbrowser: Provides a high-level interface to display web-based documents to users. Used for opening the file location in the default file explorer."
    )
    messagebox.showinfo("How Does This Work? Help", help_text)

# Check if 'mp3lists' folder exists, create it if not
create_destination_folder()

# Create the main window
root = tk.Tk()
root.title("YouTube to MP3 Downloader")

# Set fixed window size
root.geometry("1080x480")  # Increased width for the table

# Create a canvas with a white gradient background
canvas = tk.Canvas(root, width=root.winfo_width(), height=root.winfo_height(), highlightthickness=0)
canvas.pack(fill=tk.BOTH, expand=True)
draw_gradient(canvas)

# Create and place widgets
frame = tk.Frame(root, bg="white", padx=10, pady=10)
frame.pack(pady=10)

label = tk.Label(frame, text="Enter YouTube Video URL:")
label.grid(row=0, column=0)

entry = tk.Entry(frame, width=40)
entry.grid(row=0, column=1)

# Paste from clipboard button
paste_button = tk.Button(frame, text="Paste from Clipboard", command=paste_from_clipboard)
paste_button.grid(row=0, column=2, padx=10)

download_button = tk.Button(frame, text="Download MP3", command=download_mp3)
download_button.grid(row=0, column=3, padx=10)

# Metadata display
title_label = tk.Label(root, text="Title:")
title_label.pack(pady=5)

author_label = tk.Label(root, text="Author:")
author_label.pack(pady=5)

duration_label = tk.Label(root, text="Duration:")
duration_label.pack(pady=5)

# Table for downloaded MP3s
columns = ("Title", "Author", "Duration", "Status")
table = ttk.Treeview(root, columns=columns, show="headings")

# Set column headings
for col in columns:
    table.heading(col, text=col)

# Set column widths evenly
col_width = 200  # Adjust as needed
for col in columns:
    table.column(col, width=col_width)

# Add a tag for the "Download Complete" status to set a green background
table.tag_configure("Download Complete", background="#C6EFCE")

table.pack(pady=10)

status_var = tk.StringVar()
status_label = tk.Label(root, textvariable=status_var)
status_label.pack(pady=10)

# Menu bar
menu_bar = tk.Menu(root)

# File menu
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open Location", command=open_location)
file_menu.add_command(label="Exit", command=exit_program)
menu_bar.add_cascade(label="File", menu=file_menu)

# Help menu
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="File Location", command=show_file_location_help)
help_menu.add_command(label="How does this work?", command=show_how_it_works_help)
menu_bar.add_cascade(label="Help", menu=help_menu)

# About menu
menu_bar.add_command(label="About", command=about)

# Set the menu bar
root.config(menu=menu_bar)

# Start the GUI event loop
root.mainloop()
