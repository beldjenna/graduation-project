import serial
import struct
import cv2
import numpy as np
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.toast import ToastNotification
from PIL import Image, ImageTk
import time
# from tkinter import ttk
# from tkinter.scrolledtext import ScrolledText


# Global variable to store the full image
full_image = None


def clearData():
    # Clear the text widgets
    textWidget.delete(1.0, tk.END)
    auxTextWidget.delete(1.0, tk.END)

    # Clear the image label
    imgLabel.config(image="")

    # Reset the progress bar and the progress label
    progress["value"] = 0
    progressLabel.config(text="0%")

    # Disable the show full image button
    showImageButton.config(state="disabled")

    # disable the clear button
    clearButton.config(state="disabled")

    # change the text of the save image button
    saveImageButton.config(text="Save Image")

    # Disable the save image button
    saveImageButton.config(state="disabled")

    # Enable the read data button
    readButton.config(state="normal")

    # Hide the label above the image
    label_3.config(text="")


def openSerialPort():
    # Open the Serial port 
    ser = serial.Serial(port='COM4', baudrate=9600)

    return ser

def readNumSegments(ser):

    # format for the number of segments 
    num_segments_format = '<I'
    num_segments_size = struct.calcsize(num_segments_format)# 4 bytes

    # Read the number of segments
    num_segments = ser.read(num_segments_size)
    

    # Unpack the number of segments
    numSegments = struct.unpack(num_segments_format, num_segments)[0]
    print(f"Number of Segments: {numSegments}")
    
    return numSegments

def decodeImage(image_data):

    # Convert the byte array to a numpy array
    image_array = np.frombuffer(image_data, dtype=np.uint8)

    # Decode the numpy array to an image 
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    # Check if the image is valid
    if image is not None:
        print("Image Decoded Successfully")

        return image

    else:
        print("failed to decode image")

def readAuxData(ser, number):
    # Define the format for the aux data
    aux_data_format = '<3f4f2i3f'
    aux_data_size = struct.calcsize(aux_data_format)#size in bytes

    # Read the auxiliary data
    aux_data = ser.read(aux_data_size)

    # write the aux data to a file
    writeToFile("Aux", number, aux_data)


    # Unpack the auxiliary data
    velocity_x, velocity_y, velocity_z, q0, q1, q2, q3 , gps_week, gps_tow, pos_x, pos_y, pos_z = struct.unpack(aux_data_format, aux_data)

    # Print the auxiliary data
    print(f"Velocity: (x={velocity_x}, y={velocity_y}, z={velocity_z})")
    print(f"Attitude: (q0={q0}, q1={q1}, q2={q2}, q3={q3})")
    print(f"GPS Week: {gps_week}") # the number of weeks since the start of the GPS epoch
    print(f"GPS TOW: {gps_tow}") # the time of week in seconds
    print(f"Position: (x={pos_x}, y={pos_y}, z={pos_z})")
    print("----------------------------------------")

    aux_data_dict = {
        "Velocity": (velocity_x, velocity_y, velocity_z),
        "Attitude": (q0, q1, q2, q3),
        "GPS Week": gps_week,
        "GPS TOW": gps_tow,
        "Position": (pos_x, pos_y, pos_z)
    }

    return aux_data_dict

def writeToFile(type, number, data):
    # if the input was a frame header 
    if (type == "Frame"):
        with open(f"C:\\Users\DELL\PFE\Python_serial_COM\Frame_headers\Frame_{number}.txt", "wb") as f:
            f.write(data)
            f.close()
    
    # if the input was a packet header
    elif (type == "Packet"):
        with open(f"C:\\Users\DELL\PFE\Python_serial_COM\Packet_headers\Packet_{number}.txt", "wb") as f:
            f.write(data)
            f.close()
        

    # if the input was auxiliary data
    elif (type == "Aux"):
        with open(f"C:\\Users\DELL\PFE\Python_serial_COM\Aux_data\Aux_{number}.txt", "wb") as f:
            f.write(data)
            f.close()

    # if the input was an image segment
    elif (type == "Image"):
        with open(f"C:\\Users\DELL\PFE\Python_serial_COM\Image_segments\Segment_{number}.txt", "wb") as f:
            f.write(data)
            f.close()

    # if the input was invalid
    else:
        print("Invalid type")
        return


def readData():

    # Disable the clear button 
    clearButton.config(state="disabled")

    # Open the serial port
    ser = openSerialPort()

    time.sleep(1)

    # Send the selected image to the microcontroller
    ser.write(bytes(selectedImage.get(), 'utf-8'))

    time.sleep(3)

    # Define the format for the sync marker 
    sync_marker_format = '<I'

    # Define the format for the Primary Frame Header
    frame_header_format = '<HBBH'

    # Define the format for the packet header
    packet_header_format = '<HHH'

    # calculate the sizes of the formats
    sync_marker_size = struct.calcsize(sync_marker_format) # 4 bytes
    frame_header_size = struct.calcsize(frame_header_format) # 6 bytes
    packet_header_size = struct.calcsize(packet_header_format) # 6 bytes

    # Image data collection
    image_data = bytearray()

    # Read the number of segments
    numSegments = readNumSegments(ser)

    # List to store all the information
    all_info = [] 

    # Initialize the progress bar
    progress["maximum"] = numSegments

    for i in range(numSegments):
        # Read the sync marker 
        sync_marker = ser.read(sync_marker_size)# in binary
        if not sync_marker:
            break

        # Unpack the sync marker
        syncMarker = struct.unpack(sync_marker_format, sync_marker)[0] #tuple
        print(f"Sync Marker: {hex(syncMarker)}")
    

        # Read the primary frame header
        frame_header = ser.read(frame_header_size)
        if not frame_header:
            break
        # write the frame header to a file
        writeToFile("Frame", i, frame_header)


        # Read the packet header
        packet_header = ser.read(packet_header_size)
        if not packet_header:
            break
        # write the packet header to a file
        writeToFile("Packet", i, packet_header)


        # Unpack the headers
        primHead = struct.unpack(frame_header_format, frame_header)
        packHead = struct.unpack(packet_header_format, packet_header)


        # Extract the packet length to read the image segment data
        segment_size = packHead[2] + 1
        segment_data = ser.read(segment_size)
        if not segment_data:
            break
        # write the image segment to a file
        writeToFile("Image", i, segment_data)


        # display the frame header information 
        versionNo = primHead[0] >> 14
        scID = (primHead[0] >> 4) & 0x3FF
        virtchanID = (primHead[0] >> 1) & 0x7
        operationalControl = primHead[0] & 0x1

        masterChannelFrameCount = primHead[1]
        virtualChannelFrameCount = primHead[2]

        secHeaderFlag = (primHead[3] >> 15) & 0x1
        syncFlag = (primHead[3] >> 14) & 0x1
        packetOrderFlag = (primHead[3] >> 13) & 0x1
        segLengthID = (primHead[3] >> 11) & 0x3
        firstHeaderPointer = primHead[3] & 0x7FF

        print(f"frame number: {i}")
        print("----------------------------------------")
        print(f"Version Number: {versionNo}")
        print(f"Spacecraft ID: {scID}")
        print(f"Virtual Channel ID: {virtchanID}")
        print(f"Operational Control: {operationalControl}")
        print(f"Master Channel Frame Count: {masterChannelFrameCount}")
        print(f"Virtual Channel Frame Count: {virtualChannelFrameCount}")
        print(f"Secondary Header Flag: {secHeaderFlag}")
        print(f"Sync Flag: {syncFlag}")
        print(f"Packet Order Flag: {packetOrderFlag}")
        print(f"Segment Length ID: {segLengthID}")
        print(f"First Header Pointer: {firstHeaderPointer}")
        print("----------------------------------------")

        # Display the packet header information
        versionNumber = packHead[0] >> 13
        type = (packHead[0] >> 12) & 0x1
        dataFieldHeaderFlag = (packHead[0] >> 11) & 0x1
        appProcessID = packHead[0] & 0x7FF

        segmentationFlags = (packHead[1] >> 14) & 0x3
        sourceSeqCount = packHead[1] & 0x3FFF

        packetLength = (packHead[2] + 1)

        print(f"Version Number: {versionNumber}")
        print(f"Type: {type}")
        print(f"Data Field Header Flag: {dataFieldHeaderFlag}")
        print(f"Application Process ID: {appProcessID}")
        print(f"Segmentation Flags: {segmentationFlags}")
        print(f"Source Sequence Count: {sourceSeqCount}")
        print(f"Packet Length: {packetLength}")
        print("----------------------------------------")

        # Read the auxiliary data into a dictionary
        aux_data_dict = readAuxData(ser, i)
        
        # Append the segment data to the image data
        image_data.extend(segment_data)# byte array

        # print(f"Segment Data: {segment_data}")
        print(f"Received Segment: {len(segment_data)} bytes")

        # put all the information in a dictionary
        frame_info = {
            "Frame Number": i,
            "Sync Marker": hex(syncMarker),
            "Primary Frame Header":{
                "Version Number": versionNo,
                "Spacecraft ID": scID,
                "Virtual Channel ID": virtchanID,
                "Operational Control": operationalControl,
                "Master Channel Frame Count": masterChannelFrameCount,
                "Virtual Channel Frame Count": virtualChannelFrameCount,
                "Secondary Header Flag": secHeaderFlag,
                "Sync Flag": syncFlag,
                "Packet Order Flag": packetOrderFlag,
                "Segment Length ID": segLengthID,
                "First Header Pointer": firstHeaderPointer
            },
            "Packet Header":{
                "Version Number": versionNumber,
                "Type": type,
                "Data Field Header Flag": dataFieldHeaderFlag,
                "Application Process ID": appProcessID,
                "Segmentation Flags": segmentationFlags,
                "Source Sequence Count": sourceSeqCount,
                "Packet Length": packetLength
            },
            "Auxiliary Data": aux_data_dict                               
        }

        # Collect all the frames into one list 
        all_info.append(frame_info)

        # Update the progress bar
        progress["value"] = i + 1
        # Update the progress label
        progressLabel.config(text=f"{int((i+1)/numSegments * 100)}%")
        mainWindow.update_idletasks()

    # Decode the image
    image = decodeImage(image_data)

    return all_info, image
    

def displayText(textWidget, auxTextWidget, all_info):

    # display the information in the all_info list 
    for frame in all_info:
        textWidget.insert(tk.END, f"Frame Number: {frame['Frame Number']}\n")
        textWidget.insert(tk.END, f"Sync Marker: {frame['Sync Marker']}\n")

        # Display the primary frame header information
        textWidget.insert(tk.END, "Primary Frame Header\n")
        for key, value in frame["Primary Frame Header"].items():
            textWidget.insert(tk.END, f"{key}: {value}\n")
        textWidget.insert(tk.END, "--------------------------------------------\n")

        # Display the packet header information
        textWidget.insert(tk.END, "Packet Header\n")
        for key, value in frame["Packet Header"].items():
            textWidget.insert(tk.END, f"{key}: {value}\n")
        textWidget.insert(tk.END, "===================================================\n", "Bold")


        # Display the auxiliary data information
        auxTextWidget.insert(tk.END, f"Auxiliary Data : {frame['Frame Number']}\n")
        for key, value in frame["Auxiliary Data"].items():
            auxTextWidget.insert(tk.END, f"{key}: {value}\n")
        auxTextWidget.insert(tk.END, "--------------------------------------------\n")

        
def displayImage(imgLabel, image):
    if image is not None:
        # Convert the image to RGB (OpenCV uses BGR by default)
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Convert the image to a PIL image
        img_pil = Image.fromarray(img_rgb)

        # Resize the image
        img_pil.thumbnail((250, 250))

        # Convert the PIL image to a Tkinter compatible PhotoImage
        img_tk = ImageTk.PhotoImage(img_pil)

        # Display the label
        label_3.pack(side="top")
        label_3.config(text="Image")

        # Set the image on the label
        imgLabel.config(image=img_tk)
        imgLabel.image = img_tk 

        # disable the read data button 
        readButton.config(state="disabled")       


def readAndUpdateData():
    all_info, image = readData()
    displayText(textWidget, auxTextWidget, all_info)
    displayImage(imgLabel, image)

    # Enable the clear button
    clearButton.config(state="normal")

    # Store the full image in the global variable "full_image"
    global full_image
    full_image = image

    # Enable the show full image button
    showImageButton.config(state="normal")

    # Enable the save image button
    saveImageButton.config(state="normal")


def mainLayout(mainWindow, columns, rows):
    # define the grid layout
    for i in range(columns):
        mainWindow.grid_columnconfigure(i, weight=1)

    for i in range(rows):
        mainWindow.grid_rowconfigure(i, weight=1)


def showFullImage():
    cv2.imshow("Full Image", full_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def saveImage():
    # Save the full image
    cv2.imwrite("C:\\Users\\DELL\\PFE\\Python_serial_COM\\Full_image\\Full_Image.jpg", full_image)

    # change the text of the button
    saveImageButton.config(text="Saved Successfully")

    # Create a toast notification
    toast = ToastNotification( 
        title="Image Saved", 
        message="The image has been saved successfully", 
        duration=3000,
        bootstyle="SUCCESS")

    # Display a toast notification
    toast.show_toast()




# create the main window
mainWindow = ttk.Window(themename="darkly")
mainWindow.title("CCSDS Image Decoder")
mainWindow.state("zoomed")

# Define the grid layout with 4 columns and 6 rows
mainLayout(mainWindow, 4, 6)

# create a scrolled text widget
textWidget = ScrolledText(mainWindow, width=80, height=30, autohide="true", hbar="true", bootstyle="Light")
textWidget.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
label_1 = ttk.Label(mainWindow, text="Header field vlaues", font=("yu gothic ui", 20, "bold"))
label_1.grid(row=0, column=0, columnspan=2, padx=10, pady=10)


# Create a text style
textWidget.tag_config("Bold", font=("Helvetica", 12, "bold"))

# Create a scrolled text widget for the auxiliary data 
auxTextWidget = ScrolledText(mainWindow, width=50, height=20, autohide="true", hbar="true", bootstyle="Light")
auxTextWidget.grid(row=1, column=3, padx=10, pady=10)
label_2 = ttk.Label(mainWindow, text="Auxiliary Data", font=("yu gothic ui", 20, "bold"))
label_2.grid(row=0, column=3, padx=10, pady=10)

# create an image label
imgFrame = ttk.Frame(mainWindow, height=900, width=900, cursor="hand2")
imgFrame.grid(row=1, column=2, padx=10, pady=10)
imgLabel = ttk.Label(imgFrame)
imgLabel.pack(fill="both", expand="true", side="bottom")
label_3 = ttk.Label(imgFrame, text="", font=("yu gothic ui", 20, "bold"), padding=10)



# Add a button to show the full image
showImageButton = ttk.Button(mainWindow, text="Show Full Image", command=showFullImage, bootstyle="primary-outline")
showImageButton.grid(row=2, column=2, padx=10, pady=10)
showImageButton.config(state="disabled")    

# Add a button to save the full image
saveImageButton = ttk.Button(mainWindow, text="Save Image", command=saveImage, bootstyle="primary-outline")
saveImageButton.grid(row=4, column=2, padx=10, pady=10)
saveImageButton.config(state="disabled")


# Add a button to trigger the process
readButton = ttk.Button(mainWindow, text="Read Data", command=readAndUpdateData, bootstyle="success-outline")
readButton.grid(row=2, column=0, padx=10, pady=10, sticky="e")

# Add a progressbar 
progress = ttk.Progressbar(mainWindow, orient="horizontal", length=200, mode="determinate",style="danger-striped")
progress.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

# Add a label to display the progress
progressLabel = ttk.Label(mainWindow, text="0%", style="danger")
progressLabel.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

# Add a button to clear everything
clearButton = ttk.Button(mainWindow, text="    Clear    ", command=clearData, bootstyle="danger-outline")
clearButton.grid(row=2, column=1, padx=10, pady=10, sticky="w")
clearButton.config(state="disabled")

# Variable to store the selected image
selectedImage = tk.StringVar(master=mainWindow, value="")


# Create radio buttons to select image
oran = ttk.Radiobutton(mainWindow, text="Oran", variable=selectedImage, value="1")
france = ttk.Radiobutton(mainWindow, text="France", variable=selectedImage, value="2")
cairo = ttk.Radiobutton(mainWindow, text="Cairo", variable=selectedImage, value="3")

# Add the radio buttons to the grid
oran.grid(row=2, column=3, padx=5, pady=10, sticky="w")
france.grid(row=2, column=3, padx=5, pady=10)
cairo.grid(row=2, column=3, padx=5, pady=10, sticky="e")



# Start the main loop
mainWindow.mainloop()