#import pyodbc
import os
import tkinter as tk
from tkinter import *
from tkinter import ttk  

root = tk.Tk()
root.title("Administration Screen")
root.geometry("1000x800") 

optionList = ['', 'New user', 'New keyword']
choice_var = tk.StringVar()  
choice_var.set(optionList[0])   
  
adminFrame = LabelFrame(root, text="Administration Form", fg = "black")  
adminFrame.grid(row=0, column=0, padx=10, pady=10, sticky="NSEW")
  
optionFrame = LabelFrame(adminFrame, text="New Profile", fg = "black", font = "Verdana 14")  
optionFrame.grid(row=0, column=0, padx=5, pady=5, sticky="EW")

def userApplication():  
  os.system("python3 User.py")
  windows_path = r'C:\Users\chris\AppData\Local\Programs\Python\Python314\Church Teachers College\PythonApplication1\User.py'
  with open(windows_path, 'r', encoding='utf-8') as f:
    file = f.read()
    os.system(file)    
  
#newProfile_lbl = Label(optionFrame, text="Select new profile:", fg = "black", font = "Verdana 10")
#newProfile_lbl.grid(row=0, column=0, sticky="E", padx=5, pady=5)
  
#newProfile_opt = OptionMenu(optionFrame, choice_var, *optionList)                                                                        
#newProfile_opt.grid(row=0, column=1, padx=5, pady=5, sticky="NSEW")

newUserButton  = Button(optionFrame, text = "Add New User", command = userApplication,
                fg = "black", font = "Verdana 14",
                bd = 2, bg = "light blue", relief = "groove") 
newUserButton .grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)  

profileFrame = LabelFrame(adminFrame, text="Profile", fg = "black", font = "Verdana 14")
profileFrame.grid(row=2, column=0, padx=5, pady=5, sticky="EW")
  
  
button = Button(profileFrame, text = "Keyword", command = set,
                fg = "black", font = "Verdana 14",
                bd = 2, bg = "light blue", relief = "groove")                
button.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5) 
  
'''def user_data():
  # Clear existing data in the TreeView
  userFrame = LabelFrame(adminFrame, text="New Information", fg = "black", font = "Verdana 14")
  userFrame.grid(row=3, column=0, padx=5, pady=5, sticky="NSEW")
  
  style = ttk.Style()
  style.theme_use('clam') 
  style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'), background="grey")
  style.configure('Treeview', fieldbackground="grey", foreground="black",font="Verdana 12")    
  existingUserTree = ttk.Treeview(userFrame, columns=('UserID', 'FirstName', 'LastName', 'UserName', 'Email'))     
  existingUserTree.heading("UserID", text="User ID")
  existingUserTree.heading("FirstName", text="First Name")
  existingUserTree.heading("LastName", text="Last Name")
  existingUserTree.heading("UserName", text="User Name")
  existingUserTree.heading("Email", text="Email")
  
  for item in existingUserTree.get_children():
    existingUserTree.delete(item)
    
    # Connect to the database and fetch data
    conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ChurchTeachersCollegeDB.Administration.USERS")
    rows = cursor.fetchall()     
    
    for row in rows:
      existingUserTree.insert('', 'end', values=row)           
      conn.close()   
      existingUserTree.grid(row=0, column=0, padx=5, pady=5, sticky="NSEW")'''
'''conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
cursor = conn.cursor()
cursor.execute("SELECT * FROM ChurchTeachersCollegeDB.Administration.USERS")
rows = cursor.fetchall()     
    
#for row in rows:
  #existingUserTree.insert('', 'end', values=row)           
  conn.close()   
      
  print (row) 
userButton = Button(profileFrame, text = "Existing Users", command = user_data,
                fg = "black", font = "Verdana 14",
                bd = 2, bg = "light blue", relief = "groove")                
userButton.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)'''
    


 # Configure root grid
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

root.mainloop()