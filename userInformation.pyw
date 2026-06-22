import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import pyodbc
from tkinter.messagebox import showinfo



def userApplication():
  userpath = subprocess.Popen([sys.executable,r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\User.pyw"],
    stdout=subprocess.PIPE,
    text=True)
  userpath .communicate()
  
def closeWindow():
  root.destroy()
  root.update()

userVar = tk.BooleanVar()
main_frame = tk.LabelFrame(root, text="Main", relief='raised', borderwidth=5, bg = "bisque2", fg = "black")
main_frame.pack(fill=tk.BOTH, expand=True, pady = 20)

userProfile = tk.LabelFrame(main_frame,text="User Profile", relief='raised', borderwidth=5, bg = "light blue", fg = "black", font = "Verdana 14")
userProfile.grid(row=1, column=0, padx=60, pady=5, sticky="NSEW")

buttonFrame = tk.Frame(main_frame, relief='raised', borderwidth=5, bg = "bisque2")
buttonFrame.grid(row=2, column=0, padx=60, pady=40, sticky="NSEW")

newUser = tk.Checkbutton(main_frame, text="New User", variable = userVar, command=userApplication, fg="black",font="Verdana 12", bg = "bisque2") 
newUser.grid(row = 0, column = 0, padx = 60, pady = 20, sticky="W")
  
style = ttk.Style()
style.theme_use('clam') 
style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'), background="grey")
style.configure('Treeview', fieldbackground="grey", foreground="black",font="Verdana 14")     
    
columns = ("UserID","FirstName", "LastName", "UserName", "Email")       
existingUserTree = ttk.Treeview(userProfile, columns= columns, show = 'headings')    
    
existingUserTree.heading("FirstName", text="First Name")
existingUserTree.heading("LastName", text="Last Name")
existingUserTree.heading("UserName", text="User Name")
existingUserTree.heading("Email", text="Email")
  
existingUserTree.column("#0", width=0, stretch=tk.NO)
existingUserTree.column("UserID", width=0, stretch=tk.NO)
existingUserTree.column("FirstName")
existingUserTree.column("LastName")
existingUserTree.column("UserName")
existingUserTree.column("Email")
existingUserTree.grid(row=0, column=0, sticky="NSEW", padx=20) 
   
#Connect to the database and fetch data
conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
cursor = conn.cursor()
cursor.execute("SELECT * FROM ChurchTeachersCollegeDB.Administration.USERS")
rows = cursor.fetchall()
count= 0
for item in existingUserTree.get_children():
  existingUserTree.delete(item)     
for row in rows:     
  existingUserTree.insert('', 'end', iid=count, text='', values=(row[0], row[1], row[2], row[3], row[4]))
  count += 1 
conn.close()

def selectItem(a):
  curItem = existingUserTree.focus()
  selectList = (existingUserTree.item(curItem))
  documentNumber = selectList['values'][2]  
  userPath = subprocess.Popen([sys.executable,r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\User.pyw"],
    stdout=subprocess.PIPE,
    text=True)
  userPath.communicate()  
existingUserTree.bind('<<TreeviewSelect>>', selectItem) 
 
cancelButton = tk.Button(buttonFrame, text="Close", command=closeWindow, height = 2, width = 15, foreground="black", font="Verdana 12", bg = "pale violet red")
cancelButton.pack(padx=2, side=tk.RIGHT) 

root.mainloop()