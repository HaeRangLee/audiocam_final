import cv2
import os
import datetime
import time
import ast
import math
from playsound import playsound
import tkinter as tk
from tkinter import messagebox
import threading
from PIL import Image, ImageTk
import numpy as np

import speech_recognition as sr

from qr import upload_image_to_github

NUM_PICTURE = 5
NUM_SAVE = 4
PHOTO_FRAME_KEY = ""
CAMERA_INDEX = 0
file_path_정답 = "C:/Users/hylee/Downloads/answer.mp3"
file_path_카메라 = "C:/Users/hylee/Downloads/camera.mp3"

PHOTO_FRAME_DICT = {
    "치즈": 'D:/hr_workspace/audiocam/audiocam/templates/ydp4cuts_brown_fixed_png.png',
    #"치즈": "D:/hr_workspace/audiocam/audiocam/templates/ydp4cuts_brown_fixed.png",
    "김치": "D:/hr_workspace/audiocam/audiocam/templates/ydp4cuts_sky_fixed_png.png",
}


def print_picture(fname):
    # os.system(f"lpr {fname}")
    os.system(f"mspaint /pt {fname}")

def listen_for_signal():
    global PHOTO_FRAME_KEY
    r = sr.Recognizer() # 객체 설정
    mic = sr.Microphone() # 마이크 설정 : 일단은 컴에 있는 마이크로 설정
    with mic as source:
        print("Adjusting for ambient noise...")
        r.adjust_for_ambient_noise(source) 

    while True: # 무한 루프로 계속 듣기: 이해될 때까지. 다만... 
        with mic as source:
            print("Listening for signal...")
            audio = r.listen(source)
        try:
            print("Recognizing audio...")
            text = r.recognize_google(audio, language='ko-KR')
            print(f"You said: {text}")
            if "치즈" in text or "김치" in text:  # lower() : 소문자로 바꾸기
                print("signal detected!")
                playsound(file_path_정답)
                if "치즈" in text:
                    PHOTO_FRAME_KEY = "치즈"
                if "김치" in text:
                    PHOTO_FRAME_KEY = "김치"
                threading.Thread(target=take_pictures_thread).start()
                return

        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
        
def take_pictures_thread():    
    # Now take 4 pictures
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        messagebox.showerror("Error", "Failed to open camera")
        return
    pictures = []
    countdown_time_default = 30000
    countdown_time =30000
    picture_interval = 5000
    preview_interval = 50

#12초 동안 찍을 수 있음


    preview_window = tk.Toplevel(root)
    preview_window.title("camera Preview")
    preview_label = tk.Label(preview_window)
    preview_label.pack()

    time_label = tk.Label(preview_window, text = f'Time left : {int(round(countdown_time%picture_interval, 0))} seconds')
    time_label.pack()
    
    shot_label = tk.Label(preview_window, text = f'남은 사진 : {countdown_time//picture_interval+1}')
    shot_label.pack()

    def update_preview():
        nonlocal countdown_time
        ret, frame = cap.read()
        if ret : 
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            img.thumbnail((1920, 1080))
            imgtk = ImageTk.PhotoImage(image = img)
            preview_label.imgtk = imgtk
            preview_label.configure(image = imgtk)
            
            if countdown_time > 0 :
                countdown_time -= preview_interval
                time_label.config(text= f'Time left : {int(round((countdown_time%picture_interval)/1000, 0))}', font = ('Arial', 40))
                shot_label.config(text = f'남은 사진 : {countdown_time//picture_interval+1}장', font = ('Arial', 40))
            else:
                cap.release()
                preview_window.destroy()    
                root.after(0, display_pictures, pictures)
                return
            
            if countdown_time % picture_interval == 0:
                playsound(file_path_카메라)
                pictures.append(frame)
                print_time = int((countdown_time_default - countdown_time)/1000)
                
                #저장될 때 1초가 늦어지는 걸 보정하는 부분
                print(f"Picture taken at {print_time} seconds.")
        
        preview_window.after(preview_interval, update_preview)
        #왜인지는 모르겠으나... 실제 시간과 다르게 가서 보정한 것임.

    update_preview()


def display_pictures(pictures): # pictures is a list of cv2 images
    if not pictures:
        messagebox.showerror("Error", "No pictures to display")
        return
    display_window = tk.Toplevel(root)
    display_window.title(f"Select Best {NUM_SAVE} Pictures")

    frame = tk.Frame(display_window) # Make a frame inside display_window!
    frame.pack(padx=10, pady=10)

    images = []
    selected_indices =  []

    def on_select(idx):
        if idx not in selected_indices and len(selected_indices) < NUM_SAVE:
            selected_indices.append(idx)
            btns[idx].config(relief=tk.SUNKEN)
        elif idx in selected_indices:
            selected_indices.remove(idx)
            btns[idx].config(relief=tk.RAISED)

        # Enable the confirm button only when SELECTED_PICS images are selected
        if len(selected_indices) == NUM_SAVE:
            confirm_button.config(state=tk.NORMAL)
        else:
            confirm_button.config(state=tk.DISABLED)
    
    btns = []
    for idx, pic in enumerate(pictures):
        cv2image = cv2.cvtColor(pic, cv2.COLOR_BGR2RGBA) # BGR: OpenCV, RGBA: PIL. So should change the order of the channels or you'll get crazy colors.
        img = Image.fromarray(cv2image)
        img.thumbnail((200, 200))
        imgtk = ImageTk.PhotoImage(image=img)
        images.append(imgtk) # Keep a reference to prevent garbage collection
        # Create a button with the image
        btn = tk.Button(frame, image=imgtk,command=lambda idx=idx: on_select(idx))
        btn.grid(row=0, column=idx) # images are buttons, and they are placed in a single row.
        btns.append(btn)

    def confirm_selection():
        if len(selected_indices) == NUM_SAVE:
            selected_pics = [pictures[i] for i in selected_indices]
            display_window.destroy()
            # Adjust each selected picture
            adjust_imaging(selected_pics)

    def adjust_imaging(images):
        adjusted_images = []

        alpha = 1.1
        beta = 20
        saturation_increase = 10
        d = 5
        sigmaColor = 50
        sigmaSpace = 50
        gamma = 1.2
        
        for image in images:
            adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
            hsv = cv2.cvtColor(adjusted, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            s = cv2.add(s, saturation_increase)
            hsv_enhanced = cv2.merge((h, s, v))
            color_enhanced = cv2.cvtColor(hsv_enhanced, cv2.COLOR_HSV2BGR)
            smoothed = cv2.bilateralFilter(color_enhanced, d=d, sigmaColor=sigmaColor, sigmaSpace=sigmaSpace)

            invGamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(256)]).astype("uint8")
            final_image = cv2.LUT(smoothed, table)
            adjusted_images.append(final_image)
        
        composite_image(adjusted_images)
    
    confirm_button = tk.Button(display_window, text="Confirm Selection", state=tk.DISABLED, command=confirm_selection)
    confirm_button.pack(pady=10)

    # Keep a references to prevent garbage collection: save to display_window.images !!!
    display_window.images = images

def composite_image(adjusted_images): # 영랑네컷
    # add a save button to save the composite image
    def save_and_print_composite():
        print("let's save and print!")
        now = datetime.datetime.now().strftime("%m%d_%H%M")
        save_path = f"composite_image_{now}.png"
        final_composite.save(save_path)
        print(f"Composite image saved as {save_path}")
        os.system(f'mspaint /pt {save_path}')
        download_url, qr_fpath = upload_image_to_github(save_path)

        #print_picture(save_path)
        print(f"Composite image sent to printer")

        root.after(0, display_qr_code, qr_fpath)

    frame_path = PHOTO_FRAME_DICT[PHOTO_FRAME_KEY]
    if not os.path.exists(frame_path):
        messagebox.showerror("Frame Error", f"Frame image {frame_path} not found.")
        return
    
    # Load the frame (not a tkinker object lol)
    photo_frame = Image.open(frame_path).convert("RGBA") # PIL image.
    
    # Create a base image with the same size as the photo frame, transparent background
    base_image = Image.new("RGBA", photo_frame.size, (255, 255, 255, 0))
    
    # Define the positions (top-left corners) where images will be pasted
    positions = [(71, 68), (737, 68), (71, 608), (741, 608)]  # Positions for 1st, 2nd, 3rd, 4th images
    
    # Define the target size for each image
    frame_size = (660, 523)  # Width, Height
    
    # Define the aspect ratio of the frame rectangle
    target_aspect = frame_size[0] / frame_size[1]  # 654 / 523 ≈ 1.25

    for i, pos in enumerate(positions):
        if i >= len(adjusted_images):
            print(f"Only {len(adjusted_images)} images provided. Skipping remaining positions.")
            break  # Prevents IndexError if there are fewer images than positions
        
        img = adjusted_images[i]
        
        # Validate image dimensions
        if img.shape[1] < 1 or img.shape[0] < 1:
            print(f"Image {i+1} has invalid dimensions. Skipping.")
            continue
        
        # Convert OpenCV image (BGR) to PIL image (RGBA)
        try:
            cv2image = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        except Exception as e:
            print(f"Error converting image {i+1} from BGR to RGBA: {e}")
            continue
        
        pil_image = Image.fromarray(cv2image)
        
        # Get original image size
        img_w, img_h = pil_image.size
        img_aspect = img_w / img_h
        
        # Center crop to maintain aspect ratio
        if img_aspect > target_aspect:
            # Image is wider than target aspect ratio
            new_width = int(target_aspect * img_h)
            left = (img_w - new_width) // 2
            right = left + new_width
            top = 0
            bottom = img_h
        else:
            # Image is taller than target aspect ratio
            new_height = int(img_w / target_aspect)
            top = (img_h - new_height) // 2
            bottom = top + new_height
            left = 0
            right = img_w
        
        # Crop the image
        pil_image_cropped = pil_image.crop((left, top, right, bottom))
        
        # Resize the image to fit the frame rectangle
        pil_image_resized = pil_image_cropped.resize(frame_size, Image.BILINEAR)
        
        # Optional: Add a border or other effects here if desired
        
        # Paste the image onto the composite image at the specified position
        # Use the image itself as the mask to preserve transparency
        base_image.paste(pil_image_resized, pos, pil_image_resized)
    
    final_composite = Image.alpha_composite(base_image, photo_frame)
    
    # Create a new Tkinter window to display the final image
    composite_window = tk.Toplevel(root)
    composite_window.title("Final Image")

    frame = tk.Frame(composite_window) # Make a frame inside display_window!
    frame.pack(padx=10, pady=10)
    
    # Optionally, you can set the window size based on the composite image size -> but it's too big!!
    composite_window.geometry(f"{int(photo_frame.width/3)+100}x{int(photo_frame.height/3)+100}")
    
    # Convert the composite PIL image to a format Tkinter can display
    final_composite_thumbnail = final_composite.copy()
    final_composite_thumbnail.thumbnail((int(final_composite.width/3),int(final_composite.height/3)))
    tk_image = ImageTk.PhotoImage(final_composite_thumbnail)
    
    # Create a label to hold the image
    label = tk.Label(frame, image=tk_image)
    label.image = tk_image  # Keep a reference to prevent garbage collection
    label.pack()
    save_button = tk.Button(frame, text="Save and Print Image", command=lambda: [save_and_print_composite(), composite_window.destroy()])
    save_button.pack(pady=10)

def display_qr_code(qr_fpath):
    qr_window = tk.Toplevel(root)
    qr_window.title("Thank You!")
    qr_window.geometry("600x600")  # Adjust the size as needed

    frame = tk.Frame(qr_window)
    frame.pack(padx=10, pady=10)

    # Load the 'Thank You!' image
    try:
        qr_img = Image.open(qr_fpath)  # Ensure this file exists
    except FileNotFoundError:
        messagebox.showerror("Image Not Found", "The 'thank_you.png' image was not found.")
        qr_window.destroy()
        return

    tk_qr_img = ImageTk.PhotoImage(qr_img)

    label = tk.Label(frame, image=tk_qr_img)
    label.image = tk_qr_img  # Keep a reference to prevent garbage collection
    label.pack()

    # Optionally, add a button to close the window
    close_button = tk.Button(frame, text="Close", command=qr_window.destroy)
    close_button.pack(pady=10)

if __name__ == "__main__":
    # listen_for_cheese()
    root = tk.Tk()
    root.title("Camera App")
    take_pictures_button = tk.Button(root, text="Start", command=listen_for_signal, foreground="#000000", background="#a80000", padx=30, pady=30, font=("Helvetica", 100))
    take_pictures_button.pack()
    root.mainloop()
