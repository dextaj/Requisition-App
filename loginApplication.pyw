import os
import pyodbc
import tkinter as tk
import subprocess
from tkinter import messagebox
from tkinter import PhotoImage
import sys
import bcrypt
from pathlib import Path

root = tk.Tk()
root.title("Login Application")
root.geometry("800x400")

def addLogOnUserToDB():
  loginUserID = userID.get()
  firstLastName = userFirstLast.get()
  osUser = os.getlogin()
  conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')
  # Create cursor
  cursor = conn.cursor()  
  sqlLog = "INSERT INTO Administration.LogOnUser (UserID, UserName, OSuser) VALUES(?, ?, ?)"
  args= (loginUserID, firstLastName, osUser) 
  cursor.execute(sqlLog, args)    
  conn.commit()
  conn.close()
  #print (osUser)
  
  
def sendUserToFile(row):
  try:
       with open('UserLog.txt', 'a') as file:
         file.write(row[2] + " " + row[3] + '\n')
  except IOError as e:
    messagebox.showError("","Error writing to file")

def login():
  loginName = userNameEntry.get()
  password = passwordEntry.get()    
  # Create a database or connect to one
  conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')
  # Create cursor
  cursor = conn.cursor()  
  cursor.execute ("SELECT * FROM Administration.Users WHERE UserName = ? AND Password_hash = ?", (loginName, password))   
  result = cursor.fetchone()
  conn.close()  
  if result and bcrypt.checkpw(password.encode(), result[4]):      
    messagebox.showinfo("","Login Success")
    #addLogOnUserToDB()
    root.destroy()    
    logonToApplication()        
  else :
    messagebox.showinfo("","Incorrent Username and or Password")

# Launching the next screen
def logonToApplication():
    main_screen = BASE_DIR / "MainScreen.pyw"
    windows_path = subprocess.Popen(
        [sys.executable, str(main_screen)],
        stdout=subprocess.PIPE,
        text=True
    )
    windows_path.communicate()  

def clearFields():
    userNameEntry.delete(0, tk.END)
    passwordEntry.delete(0, tk.END)
    userNameEntry.focus_set()  # puts cursor back in the username field 

BASE_DIR = Path(r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\assets").parent
ASSETS_DIR = BASE_DIR / "assets"    

login_frame = tk.LabelFrame(root, text="Login Credentials", bg = "light blue", relief='raised', borderwidth=5, font = "Algerian 20")
login_frame.grid(row=0, column=0, padx=10, pady=10, sticky="NSEW")

loginSpace = tk.Label(login_frame, text = "", width=15, height=10, bg = "light blue")
loginSpace.grid(row=0, column=1, sticky="NSEW", rowspan = 3, columnspan = 1)

icon_frame = tk.Frame(login_frame, relief='raised', borderwidth=5)
icon_frame.grid(row=1, column=2, padx=10, pady=10, sticky="NSEW")

iconImg = tk.PhotoImage(file=ASSETS_DIR / "logInIcon.png")
userImg = tk.PhotoImage(file=ASSETS_DIR / "userIcon.png")
passwordImg = tk.PhotoImage(file=ASSETS_DIR / "passwordIcon.png")

#iconImg = tk.PhotoImage(file=r"C:\Users\chris\Pictures\Log in\logInIcon.png")
iconImg = iconImg.subsample(4,4)
 
#userImg = tk.PhotoImage(file=r"C:\Users\chris\Pictures\Log in\userIcon.png")
userImg = userImg.subsample(50,50)

#passwordImg = tk.PhotoImage(file=r"C:\Users\chris\Pictures\Log in\passwordIcon.png")
passwordImg = passwordImg.subsample(10,10)

iconLabel = tk.Label(icon_frame, image=iconImg, relief="groove")
iconLabel.grid(row=1, column=0, sticky="NSEW", rowspan = 3)

spaceLabel = tk.Label(icon_frame, text = "", width=5)
spaceLabel.grid(row=1, column=1, sticky="NSEW", rowspan = 3, columnspan = 1)

userNameLabel = tk.Label(icon_frame, image=userImg, relief="groove")
userNameLabel.grid(row=1, column=3, sticky="WE", padx=5, pady=5)

userNameEntry = tk.Entry(icon_frame, width=30, bg = "gray90", font= "Verdana 12")
userNameEntry.grid(row=1, column=4, sticky="NSEW", padx=5, pady=5)
userNameEntry.focus_set()

passwordLabel = tk.Label(icon_frame, image=passwordImg)
passwordLabel.grid(row=2, column=3, sticky="WE", padx=5, pady=5)

passwordEntry = tk.Entry(icon_frame, width=30, bg = "gray90")
passwordEntry.grid(row=2, column=4, sticky="NSEW", padx=5, pady=5)
passwordEntry.config(show="*")
userID = tk.Entry(icon_frame)

userID.grid(row=2, column=4, sticky="NSEW", padx=5, pady=5)
userID.grid_remove()
userFirstLast = tk.Entry(icon_frame)
userFirstLast.grid(row=2, column=4, sticky="NSEW", padx=5, pady=5)
userFirstLast.grid_remove()

buttonFrame = tk.LabelFrame(icon_frame, relief='raised', borderwidth=5)
buttonFrame.grid(row=3, column=4, padx=5, pady=5, sticky="NSEW")

logOnButton = tk.Button(buttonFrame, text="Login", command=login, width=10, fg = "black", font = "Verdana 14",
                bd = 2, bg = "burlywood1", relief = "groove")
logOnButton.grid(row=0, column=3, sticky="NSEW", padx=5, pady=5)

clearButton = tk.Button(buttonFrame, text="Clear", command=clearFields, width=10, fg = "black", font = "Verdana 14",
                bd = 2, bg = "burlywood1", relief = "groove")
clearButton.grid(row=0, column=4, sticky="NSEW", padx=5, pady=5)


root.rowconfigure(0, weight=3)
root.columnconfigure(0, weight=1)
icon_frame.columnconfigure(1, weight=3)
root.rowconfigure(1, weight=1)
root.mainloop()

