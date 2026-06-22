import tkinter as tk
from tkinter import *
from tkinter import ttk

root = tk.Tk()
root.title("User Information")
root.geometry("1000x800")

userFrame = LabelFrame(root, text="New User", fg = "black", font = "Verdana 14")  
userFrame.grid(row=0, column=0, padx=5, pady=5, sticky="EW")

firstName_label = Label(userFrame, text="First Name:", fg = "black", font = "Verdana 14")
firstName_label.grid(row=1, column=0, sticky="E", padx=5, pady=5)
firstName_entry = Entry(userFrame, width=50)
firstName_entry.grid(row=1, column=1, sticky="NSEW", padx=5, pady=5)

lastName_label = Label(userFrame, text="Last Name:", fg = "black", font = "Verdana 14")
lastName_label.grid(row=1, column=3, sticky="E", padx=5, pady=5)  
lastName_entry = Entry(userFrame, width=50)
lastName_entry.grid(row=1, column=4, sticky="NSEW", padx=5, pady=5)

email_label = Label(userFrame, text="Email:", fg = "black", font = "Verdana 14")
email_label.grid(row=2, column=0, sticky="E", padx=5, pady=5)
email_entry = Entry(userFrame)
email_entry.grid(row=2, column=1, sticky="NSEW", padx=5, pady=5)
  
userName_label = Label(userFrame, text="User Name:", fg = "black", font = "Verdana 14")
userName_label.grid(row=2, column=3, sticky="E", padx=5, pady=5)
userName_entry = Entry(userFrame)
userName_entry.grid(row=2, column=4, sticky="NSEW", padx=5, pady=5)
  
password_label = Label(userFrame, text="Password:", fg = "black", font = "Verdana 14")
password_label.grid(row=3, column=0, sticky="E", padx=5, pady=5)
password_entry = Entry(userFrame)
password_entry.grid(row=3, column=1, sticky="NSEW", padx=5, pady=5)
  
'''  def addNewUser():
    # Create a database or connect to one
    conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')
    # Create cursor
    cursor = conn.cursor()
    # Insert into table
    firstName = firstName_entry.get()
    lastName = lastName_entry.get()
    email = email_entry.get()
    userName = userName_entry.get()
    password = password_entry.get()
    sql = "INSERT INTO Administration.Users(FirstName, LastName, Email, UserName, Password_hash) VALUES(?, ?, ?, ?, ?)"
    args= (firstName, lastName, email, userName, password) 
    cursor.execute(sql, args)
    # Commit changes
    conn.commit()
    #Close Connection
    conn.close()

    # Clear the text boxes
    firstName_entry.delete(0, END)
    lastName_entry.delete(0, END)
    email_entry.delete(0, END)
    userName_entry.delete(0, END)
    password_entry.delete(0, END)'''
saveUser_Button =  Button(userFrame, text = "Save",command = set, #addNewUser, 
              fg = "black", font = "Verdana 14",
              bd = 2, bg = "light blue", relief = "groove")                
saveUser_Button.grid(row=4, column=1, sticky="EW", padx=5, pady=5) 
  
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
root.mainloop()
  

