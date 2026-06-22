import os
import pyodbc
import PIL
from tkinter import *
from tkinter import messagebox
from tkinter import PhotoImage

root = Tk()
root.title("Login Application")
root.geometry("800x400")

def Ok():    
  # Create a database or connect to one
  conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')
  # Create cursor
  cursor = conn.cursor()
    
  userName = userNameEntry.get()
  password = passwordEntry.get()
  sql = "SELECT UserName, Password_hash FROM Administration.Users"
  cursor.execute(sql)  
  rows = cursor.fetchall()    
  for row in rows:     
    if(userName != "" and password != "") :
      if(userName == row[0] and password == row[1]):
        messagebox.showinfo("","Login Success")
        os.system("python3 Application.py")
        root.destroy()
        return True    
      else :
        messagebox.showinfo("","Incorrent Username and or Password")
        return False
    conn.close()

login_frame = LabelFrame(root, text="Login Credentials", bg = "light blue", font = "Algerian 20")
login_frame.grid(row=0, column=0, padx=10, pady=10, sticky="NSEW")

loginSpace = Label(login_frame, text = "", width=15, height=10, bg = "light blue")
loginSpace.grid(row=0, column=1, sticky="NSEW", rowspan = 3, columnspan = 1)

icon_frame = LabelFrame(login_frame)
icon_frame.grid(row=1, column=2, padx=10, pady=10, sticky="NSEW")

iconImg = PhotoImage(file=r"C:\Users\chris\Pictures\Log in\logInIcon.png")
iconImg = iconImg.subsample(4,4)
 
userImg = PhotoImage(file=r"C:\Users\chris\Pictures\Log in\userIcon.png")
userImg = userImg.subsample(50,50)

passwordImg = PhotoImage(file=r"C:\Users\chris\Pictures\Log in\passwordIcon.png")
passwordImg = passwordImg.subsample(10,10)

iconLabel = Label(icon_frame, image=iconImg, relief="groove")
iconLabel.grid(row=1, column=0, sticky="NSEW", rowspan = 3)

spaceLabel = Label(icon_frame, text = "", width=5)
spaceLabel.grid(row=1, column=1, sticky="NSEW", rowspan = 3, columnspan = 1)

userNameLabel = Label(icon_frame, image=userImg, relief="groove")
userNameLabel.grid(row=1, column=3, sticky="WE", padx=5, pady=5)

... userNameEntry = Entry(icon_frame, width=50, bg = "gray90")
... userNameEntry.grid(row=1, column=4, sticky="NSEW", padx=5, pady=5)
... 
... passwordLabel = Label(icon_frame, image=passwordImg)
... passwordLabel.grid(row=2, column=3, sticky="WE", padx=5, pady=5)
... 
... passwordEntry = Entry(icon_frame, width=50, bg = "gray90")
... passwordEntry.grid(row=2, column=4, sticky="NSEW", padx=5, pady=5)
... passwordEntry.config(show="*")
... 
... buttonFrame =LabelFrame(icon_frame)
... buttonFrame.grid(row=3, column=4, padx=5, pady=5, sticky="NSEW")
... 
... logOnButton = Button(buttonFrame, text="Login", command=Ok, width=10, fg = "black", font = "Verdana 14",
...                 bd = 2, bg = "burlywood1", relief = "groove")
... logOnButton.grid(row=0, column=3, sticky="NSEW", padx=5, pady=5)
... 
... clearButton = Button(buttonFrame, text="Clear", command=set, width=10, fg = "black", font = "Verdana 14",
...                 bd = 2, bg = "burlywood1", relief = "groove")
... clearButton.grid(row=0, column=4, sticky="NSEW", padx=5, pady=5)
... 
... if Ok():
...   os.system("python3 Application.py")
...   windows_path = r'C:\Users\chris\Desktop\Church Teachers College\PythonApplication1\Application.py'
...   with open(windows_path, 'r', encoding='utf-8') as f:
...     file = f.read()
...     os.system(file)
...     #break 
...   root.destroy()     
... 
... root.rowconfigure(0, weight=3)
... root.columnconfigure(0, weight=1)
... icon_frame.columnconfigure(1, weight=3)
... root.rowconfigure(1, weight=1)
... root.mainloop()
... 
