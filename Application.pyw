import os
import tkinter as tk
from tkinter import *
from tkinter import ttk

root = tk.Tk()
root.geometry("800x600")

    
# Main form Frame
main_frame = LabelFrame(root, text="Application Form", bg = "light blue")
main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="NSEW")

def requisitionApplication():
  os.system("python3 Requisition.py")
  windows_path = r'C:\Users\chris\source\repos\PythonApplication2\PythonApplication2.py'
  with open(windows_path, 'r', encoding='utf-8') as f:
    file = f.read()
    os.system(file)    
   
def adminApplication():
  os.system("python3 Administration.py")
  windows_path = r'C:\Users\chris\AppData\Local\Programs\Python\Python314\Church Teachers College\PythonApplication1\Administration.py'
  with open(windows_path, 'r', encoding='utf-8') as f:
    file = f.read()
    os.system(file)    
    
adminButton = Button(main_frame, text = "Administration", command = adminApplication,
                height = 3, width = 13, fg = "black", font = "Algerian 20",
                bd = 2, bg = "burlywood1", relief = "groove")                
adminButton.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)
reqButton = Button(main_frame, text = "Requisition", command = requisitionApplication,
                height = 3, width = 13, fg = "black", font = "Algerian 20",
                bd = 2, bg = "burlywood1", relief = "groove")                
reqButton.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)

space1Button = Button(main_frame, text = "", command = set,
                height = 3, width = 13, fg = "black", font = "Algerian 20",
                bd = 2, bg = "burlywood1", relief = "groove")                
space1Button.grid(row=2, column=0, sticky="NSEW", padx=5, pady=5)

space2Button = Button(main_frame, text = "", command = set,
                height = 3, width = 13, fg = "black", font = "Algerian 20",
                bd = 2, bg = "burlywood1", relief = "groove")                
space2Button.grid(row=3, column=0, sticky="NSEW", padx=5, pady=5)

'''space3Button = Button(main_frame, text = "", command = set,
                height = 3, width = 13, fg = "black", font = "Verdana 14",
                bd = 2, bg = "burlywood1", relief = "groove")                
space3Button.grid(row=4, column=0, sticky="NSEW", padx=5, pady=5)

space4Button = Button(main_frame, text = "", command = set,
                height = 3, width = 13, fg = "black", font = "Verdana 14",
                bd = 2, bg = "burlywood1", relief = "groove")                
space4Button.grid(row=5, column=0, sticky="NSEW", padx=5, pady=5)

space5Button = Button(main_frame, text = "Administration", command = set,
                height = 3, width = 13, fg = "black", font = "Verdana 14",
                bd = 2, bg = "light blue", relief = "groove")                
space5Button.grid(row=0, column=1, sticky="E", padx=5, pady=5)

space6Button = Button(main_frame, text = "Requisition", command = set,
                height = 3, width = 13, fg = "black", font = "Verdana 14",
                bd = 2, bg = "light blue", relief = "groove")                
space6Button.grid(row=0, column=2, sticky="E", padx=5, pady=5)'''

main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

# Configure root grid
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)



root.mainloop()