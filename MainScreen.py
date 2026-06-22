import pyodbc
import tkinter as tk
from tkinter import ttk
import subprocess
import sys

root = tk.Tk() 
root.title("Main Screen")
root.geometry("1000x800")

def userApplication():
  userpath = subprocess.Popen([sys.executable,r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\userInformation.pyw"],
    stdout=subprocess.PIPE,
    text=True)
  userpath .communicate()
  
def requisitionApplication():
  requisitionpath = subprocess.Popen([sys.executable,r"C:\Users\chris\AppData\Local\Programs\Python\Python314\ChurchTeachersCollege\PythonApplication1\RequisitionApplication.pyw"],
    stdout=subprocess.PIPE,
    text=True)
  requisitionpath.communicate()
  
  

# Main form Frame
main_frame = tk.LabelFrame(root, text="Main", relief='raised', borderwidth=5, bg = "light blue", fg = "black")
main_frame.pack(fill=tk.BOTH, expand=True, pady = 20)

applicationFrame = tk.LabelFrame(main_frame, text="Application", relief='raised', borderwidth=5, bg = "bisque2", font = "Algerian 20")    
applicationFrame.grid(row=0, column=0, padx=10, pady=10, sticky="NSEW")

userProfile = tk.LabelFrame(main_frame, text= "User Profile", fg = "black", font = "Algerian 14")   
userProfile.grid(row=0, column=1)

#def adminInformation():
adminFrame = tk.LabelFrame(applicationFrame, text="Administration", relief='raised', borderwidth=5, bg = "bisque2", fg = "black", font = "Algerian 14")  
adminFrame.grid(row=2, column=0, padx=10, pady=10, sticky="NSEW")

#userFrame = LabelFrame(adminFrame, text="User Information", fg = "black", font = "Algerian 14")  
#userFrame.grid(row=0, column=0, padx=5, pady=5, sticky="NSEW")
  
#keywordFrame = LabelFrame(adminFrame, text="Administration", fg = "black", font = "Algerian 14")  
#keywordFrame.grid(row=1, column=0, padx=10, pady=10, sticky="NSEW") 
  
  
'''def userInformation():
    # Clear existing data in the TreeView
    userProfile = tk.LabelFrame(main_frame, text="User Profile", fg = "black", font = "Verdana 14")
    userProfile.grid(row=0, column=1, padx=5, pady=5, sticky="NSEW")
  
    style = ttk.Style()
    style.theme_use('clam') 
    style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'), background="grey")
    style.configure('Treeview', fieldbackground="grey", foreground="black",font="Verdana 12")    
    existingUserTree = ttk.Treeview(userProfile, columns=('UserID', 'FirstName', 'LastName', 'UserName', 'Email'))     
    existingUserTree.heading("UserID", text="User ID")
    existingUserTree.heading("FirstName", text="First Name")
    existingUserTree.heading("LastName", text="Last Name")
    existingUserTree.heading("UserName", text="User Name")
    existingUserTree.heading("Email", text="Email")
  
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
        existingUserTree.grid(row=0, column=0, padx=5, pady=5, sticky="NSEW")'''        
          


'''adminButton = Button(applicationFrame, text = "Administration", command = adminInformation,
                height = 2, width = 13,fg = "black", font = "Algerian 10",
                bd = 2, relief = "groove")                
adminButton.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)'''
reqButton = tk.Button(applicationFrame, text = "Requisition", command = requisitionApplication,
               height = 2, width = 13,fg = "black", font = "Algerian 12",  
               bd = 2, relief = "groove")                
reqButton.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)

userButton =  tk.Button(adminFrame, text = "User Information",command = userApplication, 
                height = 2, fg = "black", font = "Algerian 12",
                bd = 2, relief = "groove")                
userButton.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5) 

keywordButton =  tk.Button(adminFrame, text = "Keyword Information",command = set, 
                height = 2, fg = "black", font = "Algerian 12",
                bd = 2, relief = "groove")                
keywordButton.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)     

'''main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)'''

# Configure root grid
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

root.mainloop()