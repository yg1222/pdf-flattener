import os
import sys
import fitz
import os
import logging
import tkinter as tk
from tkinter import filedialog, StringVar, OptionMenu
from PIL import Image
from fpdf import FPDF

# Creating a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Creating handlers for sys.stdout and sys.stderr
stdout_handler = logging.StreamHandler(sys.stdout)
stderr_handler = logging.StreamHandler(sys.stderr)
file_handler = logging.FileHandler('app.log')

# Setting logging levels for the handlers
stdout_handler.setLevel(logging.INFO)
stderr_handler.setLevel(logging.ERROR)
file_handler.setLevel(logging.DEBUG)

# Creating formatters and add them to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stdout_handler.setFormatter(formatter)
stderr_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Adding the handlers to the logger
logger.addHandler(stdout_handler)
logger.addHandler(stderr_handler)
logger.addHandler(file_handler)

# Initializations
input_files = []
icon_path = None

# Setting behaviors according to the type of environment
if getattr(sys, 'frozen', False):
    # Running in a frozen, compiled, bundled environment like in a PyInstaller bundle
    # Joining multiple directories
    icon_path = os.path.join(sys._MEIPASS, 'assets', 'images', 'icon.ico')
    temp_image_dir = os.path.join(sys._MEIPASS, 'temp_image_dir')
    # Redirect stderr and stdout to a log file
    sys.stderr = open('error_stream.log', 'w')
    sys.stdout = open('output_stream.log', 'w')
else:
    # Running in a normal Python environment
    icon_path = 'assets/images/icon.ico'
    temp_image_dir = 'temp_image_dir'


def select_files():
    global input_files
    path_list = []
    # Open a file dialog to select multiple files
    file_paths = filedialog.askopenfilenames()
    for path in file_paths:
        path_list.append(path)
    input_files = path_list
    # Show flatten button
    flatten_button.pack(pady=(5, 10))


def pdf_to_images(pdf_path, image_folder, dpi):
    logging.info("Conversion step 1: Converting pdf to images")
    pdf_document = fitz.open(pdf_path)
    images = []

    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        zoom_x = dpi / 150.0
        zoom_y = dpi / 150.0
        mat = fitz.Matrix(zoom_x, zoom_y)
        image = page.get_pixmap(matrix=mat)
        image_path = f"{image_folder}/page_{page_num + 1}.png"
        
        image.save(image_path)
        # resize and overwrite image_path file if the user provides a width
        if output_width.get():
            logging.info("------------Resizing page:")
            image_path = resize_compress(image_path)
        images.append(image_path)
    return images

def resize_compress(image_path):
    image = Image.open(image_path)
    width, height = image.size
    logging.info ("Original width: "+ str(width))
    logging.info ("Original height: "+ str(height))
    ratio = width/height
    logging.info("Calculated ratio based on the width selected: " + str(ratio))
    # new_width = 1200
    new_width = int(output_width.get())
    new_height = float(new_width/ratio)
    logging.info (f"New width: {new_width}\nNew height: {new_height}\n------------")      
    resized_image = image.resize((int(new_width), int(new_height)))
    # overwrite image_path
    resized_image.save(image_path)
    return image_path

def images_to_pdf(images, output_pdf_path):
    logging.info("Converting images to pdf")
    # Check for user's overwrite prefference
    if overwrite_var.get() == False:
        logging.info("Not overwriting file")
        output_pdf_path = append_flag(output_pdf_path, 1)
        logging.debug(output_pdf_path)
    elif overwrite_var.get() == True:
        logging.info("Overwriting file")
    pdf = FPDF()
    for image in images:
        pdf.add_page()
        pdf.image(image, 0, 0, 210, 297)  # A4 size
    pdf.output(output_pdf_path)

def start():
    global input_files
    logging.debug("start")
    logging.debug("DPI: " + (dpi_select_var.get()))
    logging.info("Overwrite selected: "+ str(overwrite_var.get()))
    # Select_files() returns a list of file paths
    pdf_files = input_files

    for pdf_file_path in pdf_files:
        # Flatten each PDF and overwrite the original file
        # Convert PDF to images
        if not os.path.exists(temp_image_dir):
            os.makedirs(temp_image_dir)
        images = pdf_to_images(pdf_file_path, temp_image_dir, dpi=int(dpi_select_var.get()))

        # Recreate PDF from images
        images_to_pdf(images, pdf_file_path)

        # Remove the images folder
        for image_path in images:
            os.remove(image_path)
        os.rmdir(temp_image_dir)
    logging.info("Complete")
    # Hide flatten button
    flatten_button.pack_forget()
    input_files = []

original_base = None
def append_flag(file_path, counter):   
    global original_base  
    logging.debug(counter) 
    base, ext = os.path.splitext(file_path)
    if counter == 1:
        original_base = base
        logging.debug(original_base)    
    file_path = f"{original_base}_f_{counter}{ext}"   
    logging.debug("FIle path exists: " + str(os.path.exists(file_path)))
    if os.path.exists(file_path):
        file_path = append_flag(file_path, counter=counter+1)
    return file_path

def validate_width(*args):
    try:
        int(output_width.get())
    except ValueError:
        logging.error(f"{ValueError} occurred while validating the width input")
        output_width.delete(0, tk.END)  # Clear invalid input


# Main application window
root = tk.Tk()
root.title("PDF Flattener by Cogni-Bridge")
root.geometry("500x450") 
root.configure(bg="#F1EFEF")
root.iconbitmap(default=icon_path)

# Set the title font and size
title_font = ("Arial", 16, "bold")
title_label = tk.Label(root, text="Cogni-Bridge PDF Flattener", font=title_font)
title_label.pack(pady=(10, 10))

# Informational label
info_label = tk.Label(root, text="Process: The PDF is converted based on the selected DPI \nand optionally resized to the specified width (in pixels) if provided.", font=("Arial", 8))
info_label.pack(pady=(10, 10))

# DPI selection
dpi_frame = tk.Frame(root)
dpi_frame.pack(pady=(0, 10))
dpi_label = tk.Label(dpi_frame, text="Select DPI:", font=("Arial", 12))
dpi_label.grid(row=0, column=0, padx=(0, 10))
dpi_select_var = StringVar()
dpi_select_var.set("600")
dpi_options = ["150", "300", "450", "600", "800", "1200"]
dpi_entry = OptionMenu(dpi_frame, dpi_select_var, *dpi_options)
dpi_entry.grid(row=0, column=1)

# Image width input
width_label = tk.Label(root, text="Enter width (optional):", font=("Arial", 12))
width_label.pack(pady=(10, 0))
output_width = tk.Entry(root)
output_width.pack(pady=(0, 20))
output_width.bind("<KeyRelease>", validate_width)  # Validate on key release

# Checkbox for file overwrite
overwrite_var = tk.BooleanVar()
overwrite_checkbox = tk.Checkbutton(root, text="Overwrite files", variable=overwrite_var)
overwrite_checkbox.pack(pady=(0, 20))

# Button to select PDF files
select_files_button = tk.Button(root, text="Select PDF file(s)", command=select_files, font=("Arial", 14), bg="#CCC8AA", fg="#191717")
select_files_button.pack(pady=(5, 10))

# Button start conversion
flatten_button = tk.Button(root, text="Flatten PDF file(s)", command=start, font=("Arial", 14), bg="#CCC8AA", fg="#191717")

# Run the tkinter main loop
root.mainloop()
