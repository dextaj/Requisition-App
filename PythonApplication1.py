import os
import pyodbc
from tkinter import *
from tkinter import messagebox

root = Tk()
root.title("Login Screen")
root.geometry("500x400")

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
    '''if(userName == "" and password == "") :
      messagebox.showinfo("", "Blank Not allowed")
      return False'''
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

login_frame = LabelFrame(root, text="Login Form", bg = "light blue")
login_frame.grid(row=0, column=0, padx=10, pady=10, sticky="NSEW")

userNameLabel = Label(login_frame, text="UserName", fg = "black", font = "Verdana 14", bg = "ivory4")#.place(x=10, y=10)
userNameLabel.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)

userNameEntry = Entry(login_frame, width=50, bg = "gray90")
userNameEntry.grid(row=1, column=1, sticky="NSEW", padx=5, pady=5)

passwordLabel = Label(login_frame, text="Password", fg = "black", font = "Verdana 14")#.place(x=10, y=40)
passwordLabel.grid(row=2, column=0, sticky="NSEW", padx=5, pady=5)

passwordEntry = Entry(login_frame, width=50, bg = "gray90")
passwordEntry.grid(row=2, column=1, sticky="NSEW", padx=5, pady=5)
passwordEntry.config(show="*")

logOnButton = Button(login_frame, text="Login", command=Ok, height = 3, width = 13, fg = "black", font = "Verdana 14",
                bd = 2, bg = "burlywood1", relief = "groove")#.place(x=10, y=100)
logOnButton.grid(row=3, column=1, sticky="NSEW", padx=5, pady=5)

spaceFrame =LabelFrame(login_frame, bg = "light blue")
spaceFrame.grid(row=4, column=4, padx=10, pady=10, sticky="NSEW")

#spaceLabel =  Label(spaceFrame, bg = "light blue")#.place(x=10, y=10)
#spaceLabel.grid(row=0, column=2, sticky="NSEW", padx=5, pady=5)

if Ok():
  #os.system("python3 main_kinter.py")
  windows_path = r'C:\Users\chris\Desktop\Church Teachers College\PythonApplication1\Application.py'
  with open(windows_path, 'r', encoding='utf-8') as f:
    file = f.read()
    os.system(file)
    #break 
  root.destroy()     

spaceFrame.columnconfigure(0, weight = 10)
root.rowconfigure(0, weight=3)
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
root.mainloop()

