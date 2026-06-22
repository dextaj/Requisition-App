
import os
import subprocess
import tkinter as tk
from tkinter import ttk
from tkinter import font
import sys
from functools import partial

# Create the main window
root = tk.Tk()
root.title("Main Applications")
root.geometry("1400x800")
root.option_add("*Font", 'Verdana 14')

# Create a custom font
custom_font = font.Font(family="Arial", size=12, weight="bold")

# Main form Frame
main_frame = tk.LabelFrame(root, text="Main", bg = "bisque2", relief='raised', borderwidth=5)
main_frame.grid(padx=10, pady=10)
main_frame.pack(fill=tk.BOTH, expand=True)


# Create the File menu with a submenu
logonUser = ttk.Entry(main_frame)
logonUser.grid(row=4, column=0)
logonUser.grid_remove()
logOnName = os.getlogin()

#Connect to the database and fetch data
conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
cursor = conn.cursor()
delCursor = conn.cursor()
cursor.execute("SELECT UserID, UserName, OSuser FROM Administration.LogOnUser")
logrows = cursor.fetchall()
deleteSql = "DELETE FROM Administration.LogOnUser WHERE UserName = " + "'" + logOnName + "'"
delCursor.execute(deleteSql)
conn.commit()
conn.close()
if logrows != []:
  for logrow in logrows:
    userName = logrow[1]
    osUser = logrow[2]    
    if osUser != None and osUser == logOnName:
      if userName != None:  
        logonUser.insert(0, userName)

#print (logonUser.get())
def addLogOnUserToDB(logrows, cursor, conn, docNumber):
  userID = logrow[0]
  userName = logonUser.get()
  osUser = logOnName
  conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
  cursor = conn.cursor()
  sqlLog = "INSERT INTO Administration.LogOnUser (UserID, UserName, OSuser, DocNumber) VALUES(?, ?, ?, ?)"
  args= (userID, userName, osUser, docNumber) 
  cursor.execute(sqlLog, args)    
  conn.commit()
  conn.close()
  
menubar = tk.Menu(root)

def requisition():
  requisitionpath = subprocess.Popen([sys.executable,r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\Requisition.pyw"],
    stdout=subprocess.PIPE,
    text=True)
  requisitionpath.communicate()
  
def userApplication():
  userpath = subprocess.Popen([sys.executable,r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\User.pyw"],
    stdout=subprocess.PIPE,
    text=True)
  userpath .communicate()

def requisitionRows():
  query = ""
  #Connect to the database and fetch data
  conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
  cursor = conn.cursor()  
  if requisitionSelect == "My Requisition":
    query = "SELECT * FROM ChurchTeachersCollegeDB.REQUISITION.REQUISITION_TABLE WHERE Assign_To = " + "'" + logonUser.get() + "'"
  else:     
    query = "SELECT * FROM ChurchTeachersCollegeDB.REQUISITION.REQUISITION_TABLE"  
  cursor.execute(query)    
  rows = cursor.fetchall()
  conn.close()  
  return rows

def requisitionInformation():
  #hideUser()
  global count 
  count= 0  
  assignedRequisition = tk.LabelFrame(main_frame, text= "Requisition", fg = "black", font = "Algerian 14", relief='sunken', borderwidth=5)
  assignedRequisition.grid(row=3, column=0, padx=5, pady=5, sticky="NSEW")
  assignedRequisition.grid()
    
  style = ttk.Style()
  style.theme_use('clam') 
  style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'), background="grey")
  style.configure('Treeview', fieldbackground="grey", foreground="black",font="Verdana 12")

  columns = ("Requisition_ID","Created_By", "Document_Number", "Site", "Category", "Maintenance", "Department", "Academic", "Comments", "Attachments")       
  assignedReqTree = ttk.Treeview(assignedRequisition, columns= columns, show = 'headings')
       
  assignedReqTree.heading("#0", text="")          
  assignedReqTree.heading("Requisition_ID", text="Requisition ID")
  assignedReqTree.heading("Created_By", text="Created By")
  assignedReqTree.heading("Document_Number", text="Number")
  assignedReqTree.heading("Site", text="Site")
  assignedReqTree.heading("Category", text="Category")
  assignedReqTree.heading("Maintenance", text="Maintenance")
  assignedReqTree.heading("Department", text="Department")
  assignedReqTree.heading("Academic", text="Academic")
  assignedReqTree.heading("Comments", text="Description")
  assignedReqTree.heading("Attachments", text="Attachments")
      
  assignedReqTree.column("#0", width=0, stretch=tk.NO)
  assignedReqTree.column("Requisition_ID", width=0, stretch=tk.NO)
  assignedReqTree.column("Created_By", width=0, stretch=tk.NO)
  assignedReqTree.column("Document_Number")
  assignedReqTree.column("Site")
  assignedReqTree.column("Category")
  assignedReqTree.column("Maintenance")
  assignedReqTree.column("Department")
  assignedReqTree.column("Academic")
  assignedReqTree.column("Comments") 
  assignedReqTree.column("Attachments") 

  for item in assignedReqTree.get_children():
    assignedReqTree.delete(item)     
  for row in requisitionRows():     
    assignedReqTree.insert('', 'end', iid=count, text='', values=(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))        
    count += 1                 
    #conn.close()   
    assignedReqTree.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)
    
'''def showRequisition(assignedRequisition):
  if requisitionSelect != "":
    assignedRequisition.grid() 

showRequisition(assignedRequisition)'''
    
def userInformation():
  # Clear existing data in the TreeView
  #assignedRequisition.grid_remove()  
  existingRow = tk.Label(main_frame, width = 25, bg = "bisque2")
  existingRow.grid(row=1, column=0, sticky="WE", padx=5, pady=5)  

  existingRow1 = tk.Label(main_frame, width = 25)
  existingRow1.grid(row=0, column=2, sticky="WE", padx=5, pady=5)
  
  existingColumn = tk.Label(main_frame, height = 2, bg = "bisque2")
  existingColumn.grid(row=0, column=0, sticky="WE", padx=5, pady=5)
  
  existingColumn1 = tk.Label(main_frame, height = 20, bg = "bisque2")
  existingColumn1.grid(row=2, column=0, sticky="WE", padx=5, pady=5)
  
  information_frame = tk.LabelFrame(main_frame, bg = "bisque2", relief='sunken', borderwidth=5)
  information_frame.grid(row=0, column=1, padx=10, pady=10, sticky="NSEW")

  informationLabel = tk.Label(information_frame, text = "User Information", font = "Algerian 20", bg = "bisque2")
  informationLabel.grid(row=0, column=0, sticky="WE", padx=5, pady=5)
    
  userProfile = tk.LabelFrame(main_frame, text="User Information", fg = "black", font = "Algerian 14")
  userProfile.grid(row=1, column=1, padx=5, pady=5, sticky="NSEW")    
  userProfile.grid()
  
  style = ttk.Style()
  style.theme_use('clam') 
  style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'), background="grey")
  style.configure('Treeview', fieldbackground="grey", foreground="black",font="Verdana 12")     
    
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
  
  for item in existingUserTree.get_children():
    existingUserTree.delete(item)
    
  #Connect to the database and fetch data
  conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM ChurchTeachersCollegeDB.Administration.USERS")
  rows = cursor.fetchall()     
    
  for row in rows:
    existingUserTree.insert('', 'end', values=row)           
    conn.close()   
    existingUserTree.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)
  
  
def hideUser():     
    #assignedRequisition.grid()
    existingRow.grid_forget()
    existingRow1.grid_forget()
    existingColumn.grid_forget()
    existingColumn1.grid_forget()
    userProfile.grid_forget()
    
def returnUser():
  #assignedRequisition.grid()
  existingRow.grid()
  existingRow1.grid()
  existingColumn.grid()
  existingColumn1.grid()
  
  userProfile.grid()
  
def hideRequisition():
  assignedRequisition.grid_forget()
  
def returnRequisition():
  ssignedRequisition.grid()
    
def requisitionSelect():
    # This function runs when a radiobutton in the Theme menu is clicked.
    # Only one theme can be selected at a time.
    selected = requisition_choice.get()
    if selected in ("My Requisition", "All Requisition"):
      user_choice.set(None)      
      #hideUser()
      #returnRequisition
      return requisitionInformation()
    #messagebox.showinfo("Theme Selected", f"You chose: {selected}")

def userSelect():
  selected = user_choice.get()
  if selected != None:
    requisition_choice.set("")
    #hideRequisition() 
    #returnUser()    
    if selected == "New User":
      return userApplication()
    elif selected == "Existing":
      return userInformation()  

#if requisition_choice.get() == "My Requisition":
#  print("true")

#print (requisitionSelect)  
#if requisitionSelect in ("My Requisition", "All Requisition"):   
 # assignedRequisition.grid()
      
# Create the Administration submenu
requisition_choice = tk.StringVar()
user_choice = tk.StringVar()

admin_menu = tk.Menu(menubar, tearoff=0)
user_submenu = tk.Menu(admin_menu, tearoff=0)
userProfile_submenu = tk.Menu(user_submenu, tearoff=0)
#userProfile_submenu.add_command(label="New User", command = userApplication, font= custom_font)
#userProfile_submenu.add_command(label="Existing", command = userInformation, font= custom_font)
userProfile_submenu.add_radiobutton(label="New User", variable = user_choice, value ="New User", command=userSelect, font= custom_font)
userProfile_submenu.add_radiobutton(label="Existing", variable = user_choice, value ="Existing", command=userSelect, font= custom_font)
admin_menu.add_cascade(label = "User Profile", menu=userProfile_submenu)
menubar.add_cascade(label="Administration", font= custom_font, menu=admin_menu)

# Create the Requisition submenu
requisition_Menu = tk.Menu(menubar, tearoff=0)
existRequisition_Menu = tk.Menu(requisition_Menu, tearoff=0)
requisition_Menu.add_command(label="New Requisition", command=requisitionApplication, font= custom_font)
#requisition_Menu.add_command(label="Existing Requisition", command=existingRequisitionInformation, font= custom_font)
#existRequisition_Menu.add_command(label="My Requisition", command = lambda:requisitionSelect("My Requisition"), font= custom_font)
#existRequisition_Menu.add_command(label="All Requisition", command = lambda:requisitionSelect("All Requisition"), font= custom_font)
existRequisition_Menu.add_radiobutton(label="My Requisition", variable=requisition_choice, value="My Requisition", command=requisitionSelect, font= custom_font)
existRequisition_Menu.add_radiobutton(label="All Requisition", variable = requisition_choice, value ="All Requisition", command=requisitionSelect, font= custom_font)
requisition_Menu.add_cascade(label="Existing Requisition", menu=existRequisition_Menu)
menubar.add_cascade(label="Requisition", menu=requisition_Menu)

menubar.add_command(label="Exit", command=root.quit, font= custom_font)

# Configure the menu bar
root.config(menu=menubar)
root.mainloop()