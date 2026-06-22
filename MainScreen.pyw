import pyodbc
import tkinter as tk
from tkinter import ttk
import subprocess
import sys

root = tk.Tk() 
root.title("Main Screen")
root.geometry("1500x1000")

def userApplication():
  userpath = subprocess.Popen([sys.executable,r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\User.pyw"],
    stdout=subprocess.PIPE,
    text=True)
  userpath .communicate()
  
def requisitionApplication():
  requisitionpath = subprocess.Popen([sys.executable,r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\RequisitionApplication.pyw"],
    stdout=subprocess.PIPE,
    text=True)
  requisitionpath.communicate()

def selectItem(a):
  curItem = existingUserTree.focus()
  selectList = (existingUserTree.item(curItem))
  documentNumber = selectList['values'][2]  
  userPath = subprocess.Popen([sys.executable,r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\User.pyw"],
    stdout=subprocess.PIPE,
    text=True)
  userPath.communicate()  

def keywordSelection(event):
  selectedIndices = keywordListbox.curselection()
  selectedItems = ",".join([keywordListbox.get(i) for i in selectedIndices])  
  #return (selectedItems)  
  keyword_window = tk.Toplevel(root)
  keyword_window.title("Keyword Information")
  keyword_window.geometry("600x700")

  def addKeywordFields():
    
    delVar = tk.BooleanVar()  
    disableVar = tk.BooleanVar()
  
    #del_var.append(delvar)
    #disable_var.append(disableVar)     
  
    informationFrame = tk.Frame(addFrame, bg = "gray90", relief = "sunken", borderwidth=5)
    informationFrame.pack(fill=tk.X)
  
    spaceLabel1 = tk.Label(informationFrame, width = 3 )
    spaceLabel1.pack(side=tk.LEFT)
  
    deleteName = f"Option {len(del_var)}"
    addDelRow = tk.Checkbutton(informationFrame, variable = delVar, command=set) 
    addDelRow.pack(side=tk.LEFT) 
  
    spaceLabel2 = tk.Label(informationFrame, width = 3 )
    spaceLabel2.pack(side=tk.LEFT)
  
    addIdEntry = tk.Entry(informationFrame, width=8, bg = "gray90", font= "Verdana 12", state = "readonly")
    addIdEntry.pack(side=tk.LEFT)

    addKeywordDescription = tk.Entry(informationFrame, width = 32, bg = "gray90", font= "Verdana 12", state = "readonly")
    addKeywordDescription.pack(side=tk.LEFT)
  
    spaceLabel3 = tk.Label(informationFrame, width = 3 )
    spaceLabel3.pack(side=tk.LEFT)
  
    addDisableCheck = tk.Checkbutton(informationFrame, variable = disableVar, command=set) 
    addDisableCheck.pack(side=tk.LEFT)

    spaceLabel4 = tk.Label(informationFrame, width = 3 )
    spaceLabel4.pack(side=tk.LEFT)
    
  def closeWindow():
    keyword_window.destroy()
    keyword_window.update()
  
  #Header
  header_frame = tk.Frame(keyword_window, bg="lightblue", height=50, relief="raised", borderwidth=5)
  header_frame.pack(fill=tk.X)  
    
  mainFrame = tk.Frame(keyword_window, bg = "bisque2", relief = "raised", borderwidth=5)
  mainFrame.pack(fill=tk.BOTH, expand=True, pady = 20)

  footer_frame = tk.Frame(keyword_window, bg="lightgray", height=50, relief='raised', borderwidth=5)
  footer_frame.pack(fill=tk.X)

  headerLabel = tk.Label(header_frame, text = "Keyword Information", fg = "black", font = "Algerian 20",  bg = "light blue")
  headerLabel.pack()
  
  entryVar = tk.StringVar()  

  keywordFrame = tk.Frame(mainFrame, bg = "bisque2", relief = "raised", borderwidth=5)
  keywordFrame.pack(fill=tk.X, pady = 10)

  keywordLabel = tk.Label(keywordFrame, text = "Keyword Name", bg="bisque2", fg = "black", font = "Algerian 12")
  keywordLabel.pack(side=tk.LEFT, pady = 5)

  keywordEntry = tk.Entry(keywordFrame, textvariable = entryVar, width=30, bg = "gray90", font= "Verdana 12", state = "readonly")
  keywordEntry.pack(side=tk.LEFT, pady = 5)

  label_frame = tk.Frame(mainFrame, bg="lightgray", height=50, borderwidth=5)
  label_frame.pack(fill=tk.X)

  defaultFrame = tk.Frame(mainFrame, bg = "gray90", height=50, relief='sunken', borderwidth=5)
  defaultFrame.pack(fill=tk.X)

  addFrame = tk.Frame(mainFrame, bg = "bisque2", relief = "sunken", borderwidth=5)
  addFrame.pack(fill=tk.X)

  buttonFrame = tk.Frame(mainFrame, bg = "bisque2", relief = "sunken", borderwidth=5)
  buttonFrame.pack(fill=tk.X)

  deleteLabel = tk.Label(label_frame, text = "Delete", width = 8, height = 2, bg="lightgray", fg = "black", font = "Algerian 12", relief = "solid", borderwidth=1)
  deleteLabel.pack(side=tk.LEFT)
 
  IDLabel = tk.Label(label_frame, text = "ID", width = 8, height = 2, fg = "black", font = "Algerian 12", bg="lightgray", relief = "solid", borderwidth=1 )
  IDLabel.pack(side=tk.LEFT)
  
  discriptionLabel = tk.Label(label_frame, text = "Description", width = 32, height = 2, font = "Algerian 12", bg = "bisque2", relief = "solid", borderwidth=1)
  discriptionLabel.pack(side=tk.LEFT)
  
  disableLabel = tk.Label(label_frame, text = "Disable", width = 8, height = 2, font = "Algerian 12", bg = "bisque2",  relief = "solid", borderwidth=1)
  disableLabel.pack(side=tk.LEFT)
  

  del_var = []
  disable_var = []  
  entry_list = []
  keywordEntry.config(state = 'normal')   
  entryVar.set(selectedItems)
  keywordEntry.config(state = 'readonly') 

  conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
  cursor = conn.cursor()
  cursor.execute("SELECT Id, keywordName, isActive  FROM Keywords." + "" + selectedItems + "")
  rows = cursor.fetchall()
  conn.close()
  
  if rows != []:
    for i, row in enumerate(rows):
      #entry = tk.Entry(root)
      #entry.grid(row=i, column=0)
      #entry.insert(0, row[0]) # Populating the widget [12]
      iDVar = tk.StringVar()
      delVar = tk.BooleanVar()
      disableVar = tk.BooleanVar()
      
      leftLabel = tk.Label(defaultFrame, width = 3)
      leftLabel.grid(row=i, column=0, padx=1) 
  
      delRow = tk.Checkbutton(defaultFrame, variable = delVar, command=set) 
      delRow.grid(row=i, column=1) 

      rightLabel = tk.Label(defaultFrame, width = 3)
      rightLabel.grid(row=i, column=2, padx=1)

      idEntry = tk.Entry(defaultFrame, textvariable = iDVar, width=8, bg = "gray90", font= "Verdana 12", state = "readonly")
      idEntry.grid(row=i, column = 3)
      idEntry.config(state = 'normal')   
      iDVar.set(row[0])
      idEntry.config(state = 'readonly') 
      
      
      keywordDescription = tk.Entry(defaultFrame, width = 32, bg = "gray90", font= "Verdana 12")
      keywordDescription.grid(row=i, column = 4)
      keywordDescription.insert(0, row[1])
      
      spaceLabel1 = tk.Label(defaultFrame, width = 3, bg = "gray90")
      spaceLabel1.grid(row=i, column = 5)

      disableCheck = tk.Checkbutton(defaultFrame, variable = disableVar, command=set) 
      disableCheck.grid(row=i, column = 6)
      
      spaceLabel5 = tk.Label(defaultFrame, width = 3, bg = "gray90")
      spaceLabel5.grid(row=i, column = 7)
      
      # Optionally store in a list to access later
      entry_list.append(idEntry)
      entry_list.append(keywordDescription)
      entry_list.append(disableCheck)
      #idEntry.insert(0, row[0])
      #keywordDescription.insert(0, row[1])
      #addKeywordFields()
      #keywordListbox.insert(tk.END, keywordNames)
      
  
  addButton = tk.Button(buttonFrame, text="Add Keyword", command=addKeywordFields, height = 2, font= "Verdana 12", relief = "raised", bg = "deep sky blue")
  addButton.pack(side=tk.RIGHT)

  cancelButton = tk.Button(footer_frame, text="Close", command=closeWindow, height = 2, width = 15, font= "Verdana 12", bg = "red3")
  cancelButton.pack(padx=2, side=tk.RIGHT)

  saveButton = tk.Button(footer_frame, text="Save", command=set, height = 2, width = 15, font= "Verdana 12", bg = "deep sky blue")
  saveButton.pack(padx=2, side=tk.RIGHT)  
  
#Header
header_frame = tk.Frame(root, bg="lightblue", height=100, relief="raised", borderwidth=5)
header_frame.pack(fill=tk.X)

# Main form Frame
main_frame = tk.Frame(root,  relief='raised', borderwidth=5, bg = "bisque2")
main_frame.pack(fill=tk.BOTH, expand=True)

footer_frame = tk.Frame(root, bg="lightgray", height=50, relief='raised', borderwidth=5)
footer_frame.pack(fill=tk.X)

applicationFrame = tk.Frame(main_frame, relief='raised', borderwidth=0, bg = "bisque2")    
applicationFrame.grid(row=0, column=0, rowspan = 4, padx=30, pady=30, sticky="NSEW")

#userProfile = tk.LabelFrame(main_frame, text= "User Profile", fg = "black", font = "Algerian 14", relief='sunken', borderwidth=5, bg = "bisque2")   
#userProfile.grid(row=0, column=1, padx=40, pady=30, sticky="NSEW")

#def adminInformation():
adminFrame = tk.Frame(applicationFrame, relief='raised', borderwidth=5, bg = "bisque2")  
adminFrame.grid(row=2, column=0, padx=10, pady=10, sticky="NSEW")

#userFrame = LabelFrame(adminFrame, text="User Information", fg = "black", font = "Algerian 14")  
#userFrame.grid(row=0, column=0, padx=5, pady=5, sticky="NSEW")
keywordLabel = tk.Label(main_frame, text = "Keyword Information", fg = "black", font = "Algerian 20",  bg = "bisque2")
keywordLabel.grid(row=1, column=0, sticky="S")
  
keywordFrame = tk.Frame(adminFrame, relief='sunken', borderwidth=5, bg = "bisque2")  
keywordFrame.grid(row=2, column=0, padx=10, pady=20, sticky="NSEW")

headerLabel = tk.Label(header_frame, text = "Administration", fg = "black", font = "Algerian 40",  bg = "light blue")
headerLabel.pack()
 
userLabel = tk.Label(main_frame, text = "User Information", fg = "black", font = "Algerian 20",  bg = "bisque2")
userLabel.grid(row=0, column=1, sticky="S")
  
#def userInformation():
    # Clear existing data in the TreeView
userProfile = tk.Frame(main_frame, relief='sunken', borderwidth=5, bg = "bisque2")
userProfile.grid(row=2, column=1, sticky="NSEW")

userVar = tk.BooleanVar()

newUser = tk.Checkbutton(main_frame, text="New User", variable = userVar, command=userApplication, fg="black",font="Verdana 12", bg = "bisque2") 
newUser.grid(row = 1, column = 1, padx = 5, pady = 20, sticky="W")

style = ttk.Style()
style.theme_use('clam') 
style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'), background="grey", relief = "sunken")
style.configure('Treeview', fieldbackground="light blue", foreground="black",font="Verdana 14")     
    
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
existingUserTree.grid(row=0, column=0, sticky="NSEW", padx=3, pady=3) 
   
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

existingUserTree.bind('<<TreeviewSelect>>', selectItem) 


'''adminButton = Button(applicationFrame, text = "Administration", command = adminInformation,
                height = 2, width = 13,fg = "black", font = "Algerian 10",
                bd = 2, relief = "groove")                
adminButton.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)'''
reqButton = tk.Button(adminFrame, text = "Requisition", command = requisitionApplication,
               bg = "light blue", height = 4, width = 13, fg = "black", font = "Algerian 14",  
               bd = 2, relief = "groove")                
reqButton.grid(row=0, column=0, sticky="NSEW", padx=20, pady=20)

keywordListbox = tk.Listbox(keywordFrame, fg = "black", bg = "light blue", font = "Verdana 14")
keywordListbox.grid(row=0, column=0, sticky="NSEW", padx=5, pady=20)

keywordListbox.bind('<<ListboxSelect>>', keywordSelection)
  
conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')               
cursor = conn.cursor()
cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'Keywords' AND TABLE_TYPE = 'BASE TABLE'")
rows = cursor.fetchall()
conn.close()
if rows != []:
  for row in rows:
    keywordNames = f"{row[0]}"
    keywordListbox.insert(tk.END, keywordNames)
    
def closeWindow():
  root.destroy()
  root.update()
    
closeButton =  tk.Button(footer_frame, text = "Close", command = closeWindow, 
                width = 20, height = 2, fg = "black", font = "Algerian 12",
                relief = "groove")                
closeButton.pack(side = "bottom", anchor="se", pady=5)


'''userButton =  tk.Button(adminFrame, text = "User Information",command = userApplication, 
                height = 2, fg = "black", font = "Algerian 12",
                bd = 2, relief = "groove")                
userButton.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5) 

keywordButton =  tk.Button(adminFrame, text = "Keyword Information",command = set, 
                height = 2, fg = "black", font = "Algerian 12",
                bd = 2, relief = "groove")                
keywordButton.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)'''     

'''main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)'''

# Configure root grid
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

root.mainloop()