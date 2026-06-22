import tkinter as tk
#from tkinter import *
from tkinter import ttk#
import pyodbc
import os
import subprocess
import sys

root = tk.Tk()
root.title("Requisition Screen")
root.geometry("1400x800")

def requisitionScreen():
  addLogOnUserToDB("")
  requisitionpath = subprocess.Popen([sys.executable,r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\Test.pyw"],
    stdout=subprocess.PIPE,
    text=True)
  requisitionpath.communicate()

reqList = ('My Requisitions', 'All Requisitions')
optionVariable = tk.Variable(value=reqList)
  
rqFrame = tk.LabelFrame(root, text="Requisition Information", fg = "black", bg = "bisque2", relief='raised', borderwidth=5, font = "Algerian 20")  
rqFrame.grid(row=0, column=0, padx=5, pady=5, sticky="NSEW")

newButton = tk.Button(rqFrame, text = "New Requisition", command = requisitionScreen,
                fg = "black", font = "Algerian 14",)  
newButton.grid(row=0, column=0, sticky="W", padx=5, pady=5, columnspan = 1)

reqListbox = tk.Listbox(rqFrame, listvariable=optionVariable, height=3, fg = "black", font = "Verdana 14")
reqListbox.grid(row=1, column=0, sticky="W", padx=5, pady=5)
reqListbox.selection_set(0) 
#print(os.getcwd())

logonUser = ttk.Entry(rqFrame)
logonUser.grid(row=4, column=0)
logonUser.grid_remove()
logOnName = os.getlogin()

#Connect to the database and fetch data
conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
cursor = conn.cursor()
cursor.execute("SELECT UserID, UserName, OSuser FROM Administration.LogOnUser")
logrows = cursor.fetchall()
conn.close()
if logrows != []:
  for logrow in logrows:
    userName = logrow[1]
    osUser = logrow[2]    
    if osUser != None and osUser == logOnName:
      if userName != None:  
        logonUser.insert(0, userName)
def deleteLogOnUserFromDB():
    with pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;'
                        r'Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;') as conn:
        cursor = conn.cursor()        
        cursor.execute("DELETE FROM Administration.LogOnUser WHERE OSuser = ?", (logOnName,))
        conn.commit()
#print (logonUser.get())
def addLogOnUserToDB(docNumber):
  
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
  #print (osUser)        
#print (logonUser.get()) 


  
def requisitionWindow():
  os.system(r"ChurchTeachersCollege\PythonApplication1\test.pyw")
  windows_path = r'C:\Users\chris\AppData\Local\Programs\Python\Python314\Church Teachers College\PythonApplication1\Test.pyw'
  with open(windows_path, 'r', encoding='utf-8') as f:
    file = f.read()
    os.system(file)
    #subprocess.call(file)
    
def allRequisitionSelection():
  "SELECT * FROM ChurchTeachersCollegeDB.REQUISITION.REQUISITION_TABLE"
    
def myRequisitionSelection():
  "SELECT * FROM ChurchTeachersCollegeDB.REQUISITION.REQUISITION_TABLE WHERE Assign_To = " + "'" + logonUser.get() + "'"
  
'''def listBoxSelection(event):
  selectedIndices = reqListbox.curselection()
  selectedItems = ",".join([reqListbox.get(i) for i in selectedIndices])
  def labelText():
    text = ""
    if listBoxSelection == "My Requisition":
      text = "My Requisition"
    else:
      text = "All Requisition"
    return text  
  return (selectedItems)    
reqListbox.bind('<<ListboxSelect>>', listBoxSelection)'''

'''def requisitionRows():
  query = ""
  #Connect to the database and fetch data
  conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
  cursor = conn.cursor()  
  if listBoxSelection == "My Requisition":
    query = "SELECT * FROM ChurchTeachersCollegeDB.REQUISITION.REQUISITION_TABLE WHERE Assign_To = " + "'" + logonUser.get() + "'"
  else:     
    query = "SELECT * FROM ChurchTeachersCollegeDB.REQUISITION.REQUISITION_TABLE"  
  cursor.execute(query)    
  rows = cursor.fetchall()
  conn.close()  
  return rows'''
def requisitionRows():
  query = ""  
  def listBoxSelection(event):
    selectedIndices = reqListbox.curselection()
    selectedItems = ",".join([reqListbox.get(i) for i in selectedIndices])
    requisitionEntry.delete(0, tk.END) 
    requisitionEntry.insert(0, selectedItems)
  reqListbox.bind('<<ListboxSelect>>', listBoxSelection)
  
  viewChoice = requisitionEntry.get() 
  if viewChoice in ("", "My Requisition"):    
    query = "SELECT * FROM ChurchTeachersCollegeDB.REQUISITION.REQUISITION_TABLE WHERE Assign_To = 'John Doe'" #" + "'" + logonUser.get() + "'"
  else:
    query = "SELECT * FROM ChurchTeachersCollegeDB.REQUISITION.REQUISITION_TABLE"
      #Connect to the database and fetch data
  conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
  cursor = conn.cursor()  
  cursor.execute(query)    
  rows = cursor.fetchall()
  conn.close() 
  return rows
    
global count 
count= 0

def labelText():
  text = ""
  selectedIndices = reqListbox.curselection()
  selectedItems = ",".join([reqListbox.get(i) for i in selectedIndices])
  return selectedItems
  '''if selectedItems == "My Requisition":
    text = "My Requisition"
  else:
    text = "All Requisition"
  return text'''
#print (labelText()) 
requisitionEntry = tk.Entry(rqFrame, font = "Verdana 14")
requisitionEntry.grid(row=3, column=0, padx=5, pady=5, sticky="NSEW")

#print (labelText())
assignedRequisition = tk.LabelFrame(rqFrame, text= labelText(), fg = "black", font = "Algerian 14", relief='sunken', borderwidth=5)
assignedRequisition.grid(row=4, column=0, padx=5, pady=5, sticky="NSEW")
    
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

rows = requisitionRows()
if rows:
    for row in rows:
        assignedReqTree.insert('', 'end', iid=count, text='',
            values=(row[0], row[1], row[2], row[3], row[4],
                    row[5], row[6], row[7], row[8], row[9], row[10]))
        count += 1
assignedReqTree.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)  # move outside loop
  
def launch_separate_application(script_path):
    """Launches another Python script as an independent process."""
    try:
        # Using sys.executable ensures the correct Python environment is used
        subprocess.Popen([sys.executable, script_path])
    except FileNotFoundError:
        print(f"Could not find Python executable or script at {script_path}")
  
def selectItem(a):
  curItem = assignedReqTree.focus()
  selectList = (assignedReqTree.item(curItem))
  documentNumber = selectList['values'][2]  
  addLogOnUserToDB(documentNumber)        
  #os.system(r"ChurchTeachersCollege\PythonApplication1\Requisition.pyw")
  #requisitionpath = r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\Requisition.pyw"
  requisitionpath = subprocess.Popen([sys.executable,r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\Test.pyw"],
    stdout=subprocess.PIPE,
    text=True)
  requisitionpath.communicate()
  #with open(requisitionpath, 'r', encoding='utf-8') as f:
  #file = f.read()
  #os.system(file)
assignedReqTree.bind('<<TreeviewSelect>>', selectItem) 

buttonFrame = tk.LabelFrame(rqFrame, relief='sunken', borderwidth=5, bg = "bisque2")
buttonFrame.grid(row=5, column=0, sticky="EW", padx=5, pady=5)

saveLabel = tk.Label(buttonFrame, width = 175, bg = "bisque2")
saveLabel.grid(row=0, column=0, sticky="EW", padx=5, pady=5)

closeButton = tk.Button(buttonFrame, text = "Close", command = root.destroy,
                width= 10, height = 2, fg = "black", font = "Algerian 14")  
closeButton.grid(row=0, column=1, sticky="EW", padx=5, pady=5)  

root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

root.mainloop()
