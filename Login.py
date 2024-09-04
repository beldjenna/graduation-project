import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import subprocess
import os

def open_main_app():
    # Close the login window
    login_window.destroy()
    
    # Open the main application
    subprocess.run(['python', 'Read.py'])

def login():
    username = username_entry.get()
    password = password_entry.get()
    
    # Check if the credentials are correct and open the main application
    if username == "admin" and password == "admin":
        open_main_app()
    else:
        error_label.config(text="Invalid credentials, please try again.")

# ================ login window ==================
login_window = ttk.Window(themename="darkly")
login_window.title("Login")
login_window.state("zoomed")

#================= label above the login frame ==================
label = ttk.Label(login_window, text="Ground Station", font=("yu gothic ui", 30, "bold"))
label.place(x=600, y=20)

# ================ login frame ==================
lgn_frame = ttk.Frame(login_window, width=950, height=600, cursor="hand2")
lgn_frame.place(x=200, y=70)


# ================ WELCOME label  ==================
heading = ttk.Label(lgn_frame, text="WELCOME", font=("yu gothic ui", 25, "bold"))
heading.place(x=80, y=30, width=300, height=60)

 
# ================ left side image  ==================
side_img = Image.open("C:/Users/DELL/PFE/Python_serial_COM/assets/vector.png")
tk_side_img = ImageTk.PhotoImage(side_img)
side_img_label = ttk.Label(lgn_frame, image=tk_side_img)
side_img_label.image = tk_side_img
side_img_label.place(x=5, y=100)

# ================ sign in image  ==================
sign_in_img = Image.open("C:/Users/DELL/PFE/Python_serial_COM/assets/hyy.png")
tk_sign_in_img = ImageTk.PhotoImage(sign_in_img)
sign_in_img_label = ttk.Label(lgn_frame, image=tk_sign_in_img)
sign_in_img_label.image = tk_sign_in_img
sign_in_img_label.place(x=620, y=130)

# ================ sign in label  ==================
sign_in_label = ttk.Label(lgn_frame, text="Sign In", font=("yu gothic ui", 17, "bold"))
sign_in_label.place(x=650, y=240)

# ================ username label  ==================
username_label = ttk.Label(lgn_frame, text="Username", font=("yu gothic ui", 13, "bold"), foreground="#4f4e4d")
username_label.place(x=550, y=300)

# ================ username entry  ==================
username_entry = ttk.Entry(lgn_frame, foreground="#6b6a69", font=("yu gothic ui", 12, "bold"), background="#040405")
username_entry.place(x=580, y=335, width=270)

# ================ username icon  ==================
username_icon = Image.open("C:/Users/DELL/PFE/Python_serial_COM/assets/username_icon.png")
tk_username_icon = ImageTk.PhotoImage(username_icon)
username_icon_label = ttk.Label(lgn_frame, image=tk_username_icon)
username_icon_label.image = tk_username_icon
username_icon_label.place(x=550, y=332)

# ================ password label  ==================
password_label = ttk.Label(lgn_frame, text="Password", font=("yu gothic ui", 13, "bold"), foreground="#4f4e4d")
password_label.place(x=550, y=380)

# ================ password entry  ==================
password_entry = ttk.Entry(lgn_frame, show="*", foreground="#6b6a69", font=("yu gothic ui", 12, "bold"), background="#040405")
password_entry.place(x=580, y=416, width=270)

# ================ password icon  ==================
password_icon = Image.open("C:/Users/DELL/PFE/Python_serial_COM/assets/password_icon.png")
tk_password_icon = ImageTk.PhotoImage(password_icon)
password_icon_label = ttk.Label(lgn_frame, image=tk_password_icon)
password_icon_label.image = tk_password_icon
password_icon_label.place(x=550, y=414)

# ================ login button  ==================
login_button = ttk.Button(lgn_frame, text="Login", command=login, style="primary-outline")
login_button.place(x=650, y=500, width=100)


# ================ error label  ==================
error_label = ttk.Label(lgn_frame, text="", bootstyle="danger")
error_label.place(x=600, y=470)



# Start the login window main loop
login_window.mainloop()