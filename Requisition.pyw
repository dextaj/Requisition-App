import tkinter as tk
import pyodbc
from tkinter import font, ttk, messagebox, END
import os
import re
from tkinter import scrolledtext
from tkinter import filedialog
import shutil

root = tk.Tk()
root.title("Requisition Screen")
root.geometry("1500x1500")

def populateFields(row):  
  count= 0
  sIndex = 0
  cIndex = 0
  mIndex = 0
  dIndex = 0
  aIndex = 0
  #for row in rows:
  createdBy_entry.insert(0, row[1])  
  docNumber_entry.config(state = 'normal')   
  doc_var.set(row[2])
  docNumber_entry.config(state = 'readonly')
  if row[3] in siteList:
    site_entry.current(siteList.index(row[3]))
  else:
    site_entry.current(0)  
  if row[4] in categoryList:
    category_entry.current(categoryList.index(row[4]))
  else:
    category_entry.current(0)  
  if row[5] in maintenanceList:
    maintenance_entry.current(maintenanceList.index(row[5]))
  else:
    maintenance_entry.current(0)  
  if row[6] in deptList:
    dept_entry.current(deptList.index(row[6]))
  else:
    dept_entry.current(0)  
  if row[7] in academicList:
    academic_entry.current(academicList.index(row[7]))
  else:
    academic_entry.current(0)        
  
def pouplateTreeview(historyTree, row):
  count= 0
  for item in historyTree.get_children():
     historyTree.delete(item)        
  historyTree.insert('', 'end', iid=count, text='', values=(row[1], row[10], row[11], row[12], row[13]))
  # increment counter
  count += 1 
  
def change_img(lbl, img):
  lbl.config(image = img)
  lbl.image = img  

#Assignment window
def assignmentInformation(): 
  assignment_window = tk.Toplevel(root)
  assignment_window.title("Assignment Information")
  assignment_window.geometry("500x400")
  from datetime import date
  
  dateVar = tk.StringVar()
  today = date.today()
  
  def closeWindow():
    assignment_window.destroy()
    assignment_window.update()
  
  userList = []
  with pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;') as conn:
    cursor = conn.cursor()
    sql = "SELECT UserID, FirstName, LastName FROM Administration.Users"
    cursor.execute(sql)
    userRows = cursor.fetchall()
    for userRow in userRows:
        userName = userRow[1] + " " + userRow[2]
        userList.append(userName)
    conn.close() 
    
  optionVariable = tk.Variable()
  optionVariable.set(userList[0])
  
  mainFrame = tk.Frame(assignment_window, bg = "bisque2", relief = "raised", borderwidth=5)
  mainFrame.pack(fill=tk.BOTH, expand=True, pady = 20)
  
  assignmentFrame = tk.Frame(mainFrame, bg = "bisque2", relief = "raised", borderwidth=5)
  assignmentFrame.grid(row=1, column=0, sticky="NSEW", padx=5, pady=20)
  
  buttonFrame = tk.Frame(mainFrame, bg = "bisque2", relief = "raised", borderwidth=5)
  buttonFrame.grid(row=2, column=0, sticky="NSEW", padx=5, pady=10)
  
  spaceLabel = tk.Label(mainFrame, text = "Assigned", font = "Algerian 20", bg = "bisque2")
  spaceLabel.grid(row=0, column=0, sticky="NSEW", padx=5, pady=20)
  
  phaseLabel = tk.Label(assignmentFrame, text="Assign to Phase", fg = "black", font = "Verdana 14", bg = "bisque2")
  phaseLabel.grid(row=1, column=0, sticky="NS", padx=5, pady=10)
  phaseEntry = tk.Entry(assignmentFrame, font = "Verdana 14")
  phaseEntry.grid(row=1, column=1, sticky="NSEW", padx=5, pady=10)

  dateLabel = tk.Label(assignmentFrame, text="Date Assigned:", fg = "black", font = "Verdana 14", bg = "bisque2")
  dateLabel.grid(row=2, column=0, sticky="NSEW", padx=5, pady=10)
  dateEntry = tk.Entry(assignmentFrame, font = "Verdana 14")
  dateEntry.grid(row=2, column=1, sticky="NSEW", padx=5, pady=10)

  assigneeLabel = tk.Label(assignmentFrame, text="Assigned To", fg = "black", font = "Verdana 14", bg = "bisque2")
  assigneeLabel.grid(row=3, column=0, sticky="NSEW", padx=5, pady=10)
  assigneeEntry = ttk.Combobox(assignmentFrame, values= userList, state="readonly", font = ("Verdana", 14))  
  assigneeEntry.grid(row=3, column=1, sticky="NSEW", padx=5, pady=10)  
  
  dateEntry.config(state = 'normal')
  dateEntry.insert(0, today)
  dateEntry.config(state = 'readonly')
  
  nextPhase = nextEntry.get()
  
  phaseEntry.config(state = 'normal')
  phaseEntry.insert(0, nextPhase)
  phaseEntry.config(state = 'readonly')

  def saveRequisition():
    # Create a database or connect to one
    
    with pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;') as conn:
      # Create cursor
      cursor = conn.cursor()
      # Insert into table     
      createdBy = createdBy_entry.get()
      docNumber = docNumber_entry.get()
      site = site_entry.get()
      category = category_entry.get()
      maintenance = maintenance_var.get()
      department = dept_entry.get()
      academic = academic_var.get()
      #comment = comment_entry.get()
      #attachment = attachments_entry.get()
      nextPhase = phaseEntry.get()    
      assigned = assigneeEntry.get()
      completedDate = dateEntry.get()
      sql = "INSERT INTO REQUISITION.REQUISITION_TABLE "
      sql += "(Created_By, Document_Number, Site, Category, Maintenance, Department, Academic,"
      sql += "Comments, Attachments, Phase, Submit_Date, Assign_To, Complete_Date)" 
      sql += "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
      args= (createdBy, docNumber, site, category, maintenance, department,academic, comment, attachment, nextPhase, completedDate, assigned, completedDate) 
      cursor.execute(sql, args)
      # Commit changes
      conn.commit()
      #Close Connection
      conn.close()
    
    createdBy_entry.delete(1.0, end)
    docNumber_entry.delete(0, end)
    site_entry.delete(0, end)
    category_entry.delete(0, end)
    maintenance_var.delete(0, end)
    dept_entry.delete(0, end)
    academic_var.delete(0, end)
    #comment_entry.delete(0, end)
    #attachments_entry.delete(0, end)
    phaseEntry.delete(0, end)    
    assigneeEntry.delete(0, end)
    dateEntry.delete(0, end)
    
    root.destroy()
    root.update()
    
  saveButton = tk.Button(buttonFrame, text="Save", command=saveRequisition, height = 2, width = 15, bg = "deep sky blue")
  saveButton.pack(padx=2, side=tk.RIGHT)
  cancelButton = tk.Button(buttonFrame, text="Cancel", command=closeWindow, height = 2, width = 15, bg = "red3")
  cancelButton.pack(padx=2, side=tk.RIGHT) 

def saveRequisitionDraft():
    with pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;') as conn:
        cursor = conn.cursor()
        createdBy = createdBy_entry.get()
        docNumber = docNumber_entry.get()
        site = site_entry.get()
        category = category_entry.get()
        maintenance = maintenance_var.get()
        department = dept_entry.get()
        academic = academic_var.get()
        sql = "INSERT INTO REQUISITION.REQUISITION_TABLE "
        sql += "(Created_By, Document_Number, Site, Category, Maintenance, Department, Academic, Phase) "
        sql += "VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
        args = (createdBy, docNumber, site, category, maintenance, department, academic, "Draft")
        cursor.execute(sql, args)
        conn.commit()
    messagebox.showinfo("Saved", "Requisition saved as Draft.")
    
def closeRequisition():
    root.destroy()
    root.update()
    
def make_frame_readonly(frame):
    for widget in frame.winfo_children():
        try:
            # Most widgets use the 'state' configuration
            widget.configure(state="disabled")
        except tk.TclError:
            # Some widgets might not have a 'state' (like Labels)
            pass


def browse_attachment():
    """Select a file and copy it to the attachments folder"""
    file_path = filedialog.askopenfilename(
        title="Select Attachment",
        filetypes=[
            ("All Files",       "*.*"),
            ("PDF Files",       "*.pdf"),
            ("Word Documents",  "*.docx"),
            ("Images",          "*.png *.jpg *.jpeg"),
        ]
    )

    if not file_path:
        return  # User cancelled

    try:
        # Create folder if it doesn't exist
        os.makedirs(ATTACHMENTS_FOLDER, exist_ok=True)

        # Copy file to attachments folder
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(ATTACHMENTS_FOLDER, file_name)
        shutil.copy2(file_path, dest_path)

        # Store just the filename in the entry
        attachments_entry.delete(0, END)
        attachments_entry.insert(0, file_name)

        messagebox.showinfo("Success", f"Attachment saved:\n{file_name}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to save attachment:\n{e}")
 
def open_attachment():
    """Retrieve and open the stored attachment"""
    file_name = attachments_entry.get().strip()

    if not file_name:
        messagebox.showwarning("No Attachment", "No attachment has been selected.")
        return

    file_path = os.path.join(ATTACHMENTS_FOLDER, file_name)

    if not os.path.exists(file_path):
        messagebox.showerror("Not Found", f"Attachment not found:\n{file_path}")
        return

    try:
        os.startfile(file_path)  # Opens with default application
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open attachment:\n{e}") 

PHASES_STANDARD  = ["Draft", "HOD Review", "VP Approval", "Principal Approval", "Procurement", "Accounts"]
PHASES_MAINTENANCE  = ["Draft", "HOD Review", "VP Review", "Maintenance Unit", "VP Approval", "Principal Approval", "Procurement", "Accounts"]
PHASES_TRANSPORT = ["Draft", "HOD Review", "VP Approval", "Accounts"]

def get_phases(category, maintenance=""):
    if category == "Transport":
        return PHASES_TRANSPORT
    elif maintenance:  # or maintenance == "True"
        return PHASES_MAINTENANCE
    else:
        return PHASES_STANDARD
        
def build_phase_tracker(parent, current_phase, category="", maintenance = ""):
    phases = get_phases(category, maintenance)
    frame = tk.Frame(parent, bg="bisque2")

    # If current_phase isn't in the list (e.g. stale value), default to 0
    idx = phases.index(current_phase) if current_phase in phases else 0

    for i, phase in enumerate(phases):
        col = i * 2

        if i < idx:
            state = "done"
            bg, fg, border = "#1D9E75", "white", "#1D9E75"
            symbol = "✓"
        elif i == idx:
            state = "active"
            bg, fg, border = "#E6F1FB", "#185FA5", "#378ADD"
            symbol = str(i + 1)
        else:
            state = "pending"
            bg, fg, border = "#F1EFE8", "#888780", "#B4B2A9"
            symbol = str(i + 1)

        c = tk.Canvas(frame, width=36, height=36,
                      bg="bisque2", highlightthickness=0)
        c.grid(row=0, column=col, padx=0)
        c.create_oval(2, 2, 34, 34, fill=bg, outline=border, width=2)
        c.create_text(18, 18, text=symbol, fill=fg,
                      font=("Verdana", 11, "bold"))

        lbl_color = "#0F6E56" if state == "done" else \
                    "#185FA5" if state == "active" else "#888780"
        tk.Label(frame, text=phase, bg="bisque2",
                 fg=lbl_color, font=("Verdana", 9),
                 wraplength=70, justify="center").grid(
                 row=1, column=col)

        if i < len(phases) - 1:
            line_color = "#1D9E75" if i < idx else "#B4B2A9"
            tk.Frame(frame, bg=line_color,
                     height=2, width=40).grid(
                     row=0, column=col + 1, sticky="EW")

    return frame 

def on_Maintenence_change():
    global tracker
    tracker.destroy()
    tracker = build_phase_tracker(
        processFrame,
        currentPhase,
        category_entry.get(),
        mvar.get()
    )
    tracker.pack(fill="x")

 #Header
header_frame = tk.Frame(root, bg="lightblue", height=100, relief="raised", borderwidth=5)
header_frame.pack(fill=tk.X) 
  
rqFrame = tk.Frame(root, bg = "bisque2")  
rqFrame.pack(fill=tk.BOTH, expand=True)
#rqFrame.grid(row=1, column=1, padx=5, pady=5, sticky="NSEW")

footer_frame = tk.Frame(root, bg="lightgray", height=40, relief='raised', borderwidth=5)
footer_frame.pack(fill=tk.X)

#spaceLabel = tk.Label(rqFrame, width= 10, height= 2, bg = "bisque2")
#spaceLabel.grid(row=0, column=0 ) 

#spaceLabel1 = tk.Label(rqFrame, width= 10, bg = "bisque2")
#spaceLabel1.grid(row=1, column=3)

headerLabel = tk.Label(header_frame, text = "Requisition Form", fg = "black", font = "Algerian 40",  bg = "light blue")
headerLabel.pack(pady = 10)

#tracker_container = tk.Frame(header_frame, bg="lightblue")
#tracker_container.pack(padx=20, pady=10) 

processFrame = tk.LabelFrame(rqFrame, relief='raised', borderwidth=5, bg = "bisque2") 
processFrame.pack(fill=tk.X)  

draftAssigned = tk.PhotoImage(file=r"C:\Users\chris\Pictures\assignedDraft.png")
draftAssigned = draftAssigned.subsample(3,3)

hodImgassigned = tk.PhotoImage(file=r"C:\Users\chris\Pictures\HODAssigned.png")
hodImgassigned = hodImgassigned.subsample(3,3)  
  
vpassigned = tk.PhotoImage(file=r"C:\Users\chris\Pictures\VPassigned.png")
vpassigned = vpassigned.subsample(3,3)

transportAssigned = tk.PhotoImage(file=r"C:\Users\chris\Pictures\categoryTransport.png")
transportAssigned = transportAssigned.subsample(3,3)
  
prinAssigned = tk.PhotoImage(file=r"C:\Users\chris\Pictures\principalAssigned.png")
prinAssigned = prinAssigned.subsample(3,3) 
  
procImgAssigned = tk.PhotoImage(file=r"C:\Users\chris\Pictures\procurementAssigned.png")
procImgAssigned = procImgAssigned.subsample(3,3)  
  
accountImg = tk.PhotoImage(file=r"C:\Users\chris\Pictures\completedImage.png")
accountImg = accountImg.subsample(8,8)    

#processLabel = tk.Label(processFrame, image = draftAssigned, relief="groove", bg = "bisque2")
#processLabel.pack(fill="x")

bigfont = font.Font(family="Helvetica",size=14)
root.option_add("*TCombobox*Listbox*Font", bigfont)
root.option_add("*TNotebook*Tab*Font", bigfont)
doc_var = tk.StringVar()
mvar = tk.BooleanVar()

siteList = ['', 'Main campus', 'Brownstown', 'Farm']
site_var = tk.StringVar()  
site_var.set(siteList[0]) 

request_option = tk.StringVar(value="Material Only")

categoryList = ['', 'Transport', 'Infrastructure', 'Household', 'Kitchen', 'Office Supplies']
category_var = tk.StringVar()
category_var.set(categoryList[0])

maintenanceList = ['Residential Facility', 'Classroom/ Lecture Space', 'Offices, Grounds']
maintenance_var = tk.StringVar()
maintenance_var.set(maintenanceList[0])

deptList = ['IT', 'Quality Assurance', 'Kitchen', 'Practicum', 'Data Protection', 'Research & Development', 'Student Services', 'Household', 'Library', 'Guidance & Counselling', 'Assessment & Intervention', 'Maintenance', 'Academic']
dept_var = tk.StringVar()
dept_var.set(deptList[0])

academicList = ['Language & Lictatures', 'General Education & Professional Studies', 'Technology', 'Natural Sciences', 'Inclusive Education & Childhood Studies', 'Humanities']
academic_var = tk.StringVar()
academic_var.set(academicList[0])

#combo_font = tk.Font(family="Verdana", size=14)

# 1. Create a Style object
style = ttk.Style()

# 2. Configure the 'TNotebook.Tab' style
# - padding=[left/right, top/bottom] -> top/bottom controls height
style.configure('Custom.TNotebook.Tab', 
                font=('Helvetica', 14, 'bold'), 
                padding=[10, 5]) 


# 3. Create the Notebook with the custom style
notebook = ttk.Notebook(rqFrame, style='Custom.TNotebook', height = 600)

# Adding dummy tabs
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
notebook.add(tab1, text="Requisition Request")
notebook.add(tab2, text="Maintenance Unit")

notebook.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(tab1)
scrollbar = tk.Scrollbar(tab1, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

# 2. Configure canvas
scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")#, width = 1500, height = 1200)
canvas.configure(yscrollcommand=scrollbar.set)

# 3. Layout
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

maintenanceCanvas = tk.Canvas(tab2)
maintenanceScrollbar = tk.Scrollbar(tab2, orient="vertical", command=maintenanceCanvas.yview)
maintenanceScrollable_frame = tk.Frame(maintenanceCanvas)

# 2. Configure canvas
maintenanceScrollable_frame.bind(
    "<Configure>",
    lambda e: maintenanceCanvas.configure(scrollregion=maintenanceCanvas.bbox("all"))
)

maintenanceCanvas.create_window((0, 0), window=maintenanceScrollable_frame, anchor="nw")#, width = 1500, height = 1200)
maintenanceCanvas.configure(yscrollcommand=maintenanceScrollbar.set)

# 3. Layout
maintenanceCanvas.pack(side="left", fill="both", expand=True)
maintenanceScrollbar.pack(side="right", fill="y")


rqInfoFrame = tk.LabelFrame(scrollable_frame, relief='raised', borderwidth=5, bg = "bisque2", fg = "black", font = "Algerian 16")
rqInfoFrame.grid(row=3, column=1, padx=10, pady=10, sticky="NSEW")
requestFrame = tk.Frame(rqInfoFrame)
requestFrame.grid(row = 6, column = 1, columnspan = 5, padx=10, pady=10, sticky="NSEW")

HODCommentFrame = tk.Frame(rqInfoFrame)
HODCommentFrame.grid(row = 7, column = 1, columnspan = 5, padx=10, pady=10, sticky="NSEW")

maintenanceFrame = tk.LabelFrame(maintenanceScrollable_frame, relief='raised', borderwidth=5, bg = "bisque2", fg = "black", font = "Algerian 16")
maintenanceFrame.pack(fill="both", expand=True)

scopeFrame = tk.Frame(maintenanceFrame)
scopeFrame.grid(row = 1, column = 1, columnspan = 5, padx=10, pady=10, sticky="NSEW")

materialFrame = tk.Frame(maintenanceFrame)
materialFrame.grid(row = 3, column = 1, columnspan = 5, padx=10, pady=10, sticky="NSEW")

VPReviewFrame = tk.Frame(rqInfoFrame)
VPReviewFrame.grid(row = 9, column = 1, columnspan = 5, padx=10, pady=10, sticky="NSEW")

VPApproveFrame = tk.Frame(maintenanceFrame)
VPApproveFrame.grid(row = 4, column = 1, columnspan = 5, padx=10, pady=10, sticky="NSEW")

principalFrame = tk.Frame(maintenanceFrame)
principalFrame.grid(row = 5, column = 1, columnspan = 5, padx=10, pady=10, sticky="NSEW")

number_label = tk.Label(rqInfoFrame, text="Number", fg = "black", font = "Algerian 14", bg = "bisque2")
number_label.grid(row=0, column=0, sticky="E", padx=5, pady=5)
docNumber_entry = tk.Entry(rqInfoFrame, textvariable = doc_var, width=15, font = ("Verdana", 14), state = 'readonly')
docNumber_entry.grid(row=0, column=1, sticky="NSEW", padx=5, pady=10)    

createdBy_label = tk.Label(rqInfoFrame, text="Created By", bg = "bisque2", fg = "black", font = "Algerian 14")
createdBy_label.grid(row=0, column=2, sticky="E", padx=2, pady=5)  
createdBy_entry = tk.Entry(rqInfoFrame, width=20, font = ("Verdana", 14))
createdBy_entry.grid(row=0, column=3, sticky="NSEW", padx=5, pady=10)

site_label = tk.Label(rqInfoFrame, text="Site", fg = "black", font = "Algerian 14", bg = "bisque2")
site_label.grid(row=0, column=4, sticky="E", padx=2, pady=5)
site_entry = ttk.Combobox(rqInfoFrame, values= siteList, state="readonly", font = ("Verdana", 14), width=15)  
site_entry.grid(row=0, column=5, sticky="NSEW", padx=5, pady=10)
  
category_label = tk.Label(rqInfoFrame, text="Category", fg = "black", font = "Algerian 14", bg = "bisque2")
category_label.grid(row=1, column=0, sticky="E", padx=5, pady=10)
category_entry = ttk.Combobox(rqInfoFrame, values= categoryList, textvariable = category_var, state="readonly", font = ("Verdana", 14), width=10)
category_entry.grid(row=1, column=1, sticky="NSEW", padx=5, pady=10)  

maintenance_label = tk.Label(rqInfoFrame, text="Maintenance:", fg = "black", font = "Algerian 14", bg = "bisque2")  
maintenance_label.grid(row=1, column=4, sticky="E", padx=5, pady=10) 
maintenance_entry = ttk.Combobox(rqInfoFrame, values= maintenanceList, textvariable = maintenance_var, state="readonly", font = ("Verdana", 14), width=10)
maintenance_entry.grid(row=1, column=5, sticky="NSEW", padx=5, pady=10)
maintenance_label.grid_remove()
maintenance_entry.grid_remove()  
def on_category_selected(event):
  selected = category_entry.get()
  if selected == "Infrastructure":    
    maintenance_label.grid()
    maintenance_entry.grid()      
  else:
    maintenance_entry.set("")        # Clear selection
    maintenance_label.grid_remove()
    maintenance_entry.grid_remove()  
category_entry.bind('<<ComboboxSelected>>', on_category_selected)
  
dept_label = tk.Label(rqInfoFrame, text="Dept & Units", fg = "black", font = "Algerian 14", bg = "bisque2")
dept_label.grid(row=1, column=2, sticky="E", padx=5, pady=5)
dept_entry = ttk.Combobox(rqInfoFrame, values= deptList, state="readonly", font = ("Verdana", 14), width=10)
dept_entry.grid(row=1, column=3, sticky="NSEW", padx=5, pady=10)

academic_label = tk.Label(rqInfoFrame, text="Academic Department:", fg = "black", font = "Algerian 14", bg = "bisque2")
academic_label.grid(row=3, column=0, sticky="NSEW", padx=5, pady=10)
academic_entry = ttk.Combobox(rqInfoFrame, values= academicList, textvariable = academic_var, state="readonly", font = ("Verdana", 14), width=10)
academic_entry.grid(row=3, column=1, columnspan = 3, sticky="NSEW", padx=5, pady=10)
academic_label.grid_remove()
academic_entry.grid_remove()
def on_department_selected(event):
  selected = dept_entry.get()
  if selected == "Academic":    
    academic_label.grid()
    academic_entry.grid()    
  else:
    academic_entry.set("")
    academic_label.grid_remove()
    academic_entry.grid_remove()    
dept_entry.bind('<<ComboboxSelected>>', on_department_selected)

supplierLabel = tk.Label(rqInfoFrame, text="Purchased At", fg = "black", font = "Algerian 14", bg = "bisque2")
supplierLabel.grid(row=4, column=0, sticky="E", padx=2, pady=5)
supplierEntry = tk.Entry(rqInfoFrame, width=2, font = "Verdana 14")
supplierEntry.grid(row=4, column=1, columnspan = 3, sticky="NSEW", padx=5, pady=5)

purposeLabel = tk.Label(rqInfoFrame, text="Purpose of Request", fg = "black", font = "Algerian 14", bg = "bisque2")
purposeLabel.grid(row=5, column=0, sticky="E", padx=5, pady=5)
purposeEntry = tk.Entry(rqInfoFrame,  width=5, font = "Verdana 14")
purposeEntry.grid(row=5, column=1, columnspan = 3, sticky="NSEW", padx=5, pady=5)

requestingLabel = tk.Label(rqInfoFrame, text = "Requesting", fg = "black", font = ("Algerian", 14), bg = "bisque2")
requestingLabel.grid(row=6, column=0, sticky="E", padx=5, pady=5)
requestingText = scrolledtext.ScrolledText(requestFrame, font = ("Verdana", 10), height=20)
requestingText.pack(fill=tk.X, padx = 5, pady = 5)

HODcomment_label = tk.Label(rqInfoFrame, text="HOD Comment", fg = "black", font = "Algerian 14", bg = "bisque2")
HODcomment_label.grid(row=7, column=0, sticky="E", padx=5, pady=5)
HODcomment_entry = scrolledtext.ScrolledText(HODCommentFrame, height = 2, font = ("Verdana", 14))
HODcomment_entry.grid(row=0, column=0, columnspan=5, padx=5, pady=5)

vpReviewerLabel = tk.Label(rqInfoFrame, text="VP Reviewer", fg = "black", font = "Algerian 14", bg = "bisque2")
vpReviewerLabel.grid(row=9, column=0, sticky="E", padx=5, pady=5)
vpReviewerText = scrolledtext.ScrolledText(VPReviewFrame, height = 2, font = ("Verdana", 14))
vpReviewerText.grid(row=0, column=0, columnspan=5, padx=5, pady=5)

ATTACHMENTS_FOLDER = os.path.join(
    os.environ.get('USERPROFILE', 'C:\\').encode('utf-8', errors='replace').decode('utf-8'),
    'ChurchTeachersCollege', 'Attachments'
)# Set your folder path  
attachments_label = tk.Label(rqInfoFrame, text="Attachments", fg = "black", font = "Algerian 14", bg = "bisque2")
attachments_label.grid(row=10, column=0, sticky="E", padx=5, pady=5)
attachments_entry = tk.Entry(rqInfoFrame, width=10, font = ("Verdana", 14))
attachments_entry.grid(row=10, column=1, sticky="NSEW", padx=5, pady=10)

nextEntry = tk.Entry(rqInfoFrame, font = ("Verdana", 20))
nextEntry.grid(row=8, column=0, padx=5, pady=5)
nextEntry.grid_remove() 

# Buttons to trigger browse and open
browse_button = tk.Button(rqInfoFrame, text="📎 Browse", command=browse_attachment)
browse_button.grid(row=10, column=2, pady=5, padx=0, sticky="W")

open_button = tk.Button(rqInfoFrame, text="📂 Open", command=open_attachment)
open_button.grid(row=10, column=3, padx=0, sticky="W")

#maintenance_check = tk.Checkbutton(rqInfoFrame, "Maintenance Unit", variable=mvar, command = on_Maintenence_change)
maintenance_check = tk.Checkbutton(
    rqInfoFrame,
    text="Maintenance Unit",
    variable=mvar,
    command=on_Maintenence_change
)
maintenance_check.grid(row=11, column=0, padx=5, pady=5)

requestType = tk.Label(maintenanceFrame, text = "Requesting", fg = "black", font = "Algerian 14", bg = "bisque2")
requestType.grid(row=0, column=0, sticky="E", padx=5, pady=5)

materialBtn = tk.Radiobutton(maintenanceFrame, text="Material Only", variable=request_option, value="Material Only",fg = "black", font = "Verdana 14", bg = "bisque2")
materialBtn.grid(row=0, column=1, sticky="NSEW", padx=5, pady=5)

laborBtn = tk.Radiobutton(maintenanceFrame, text="Labor Only", variable=request_option, value="Labor Only", fg = "black",  font = "Verdana 14", bg = "bisque2")
laborBtn.grid(row=0, column=2, sticky="NSEW", padx=5, pady=5)

bothBtn = tk.Radiobutton(maintenanceFrame, text="Material/Labor", variable=request_option, value="Material/Labor", fg = "black", font = "Verdana 14", bg = "bisque2")
bothBtn.grid(row=0, column=3, sticky="NSEW", padx=5, pady=5)

scopeLabel = tk.Label(maintenanceFrame, text = "Scope of Work", fg = "black", font = "Algerian 14", bg = "bisque2")
scopeLabel.grid(row=1, column=0, padx=5, pady=5, sticky="NSEW")

scopeText = scrolledtext.ScrolledText(scopeFrame, height = 5, font = ("Verdana", 14))
scopeText.grid(row=0, column=0, columnspan=5, padx=5, pady=5)

contractorLabel = tk.Label(maintenanceFrame, text="Contractor(s)", fg = "black", font = "Algerian 14", bg = "bisque2")
contractorLabel.grid(row=2, column=0, sticky="E", padx=2, pady=5)
contractorEntry = tk.Entry(maintenanceFrame, width=5, font = "Verdana 14")
contractorEntry.grid(row=2, column=1, columnspan = 5, sticky="NSEW", padx=5, pady=5)  

materialLabel = tk.Label(maintenanceFrame, text = "List of Materials", fg = "black", font = "Algerian 14", bg = "bisque2")
materialLabel.grid(row=3, column=0, padx=5, pady=5, sticky="NSEW")
materialText = scrolledtext.ScrolledText(materialFrame, height = 5, font = ("Verdana", 14))
materialText.grid(row=0, column=0, columnspan=5, padx=5, pady=5)

vpApproverComment = tk.Label(maintenanceFrame, text="VP Approver Comments", fg = "black", font = "Algerian 14", bg = "bisque2")
vpApproverComment.grid(row=4, column=0, sticky="NSEW", padx=5, pady=5)
vpApproverText = scrolledtext.ScrolledText(VPApproveFrame, height = 5, font = ("Verdana", 14))
vpApproverText.grid(row=0, column=0, columnspan=5, padx=5, pady=5)

principalComment = tk.Label(maintenanceFrame, text="Principal Comments", fg = "black", font = "Algerian 14", bg = "bisque2")
principalComment.grid(row=5, column=0,  sticky="NSEW", padx=5, pady=5)
principalText = scrolledtext.ScrolledText(principalFrame, height = 5, font = ("Verdana", 14))
principalText.grid(row=0, column=0, columnspan=5, padx=5, pady=5) 
  
history_Frame = tk.Frame(maintenanceFrame, relief='sunken', borderwidth=5, bg = "bisque2")  
history_Frame.grid(row=6, column=1, columnspan=6, sticky="NSEW", padx=5, pady=5)

historyLabel = tk.Label(history_Frame, text = "History", height= 1, fg = "black", font = "Algerian 14",bg = "bisque2")
historyLabel.grid(row=0, column=0 )

#historyColumn = tk.Label(history_Frame, width=20, bg = "bisque2")
#historyColumn.grid(row=1, column= 0)
  
#hstyle = ttk.Style()
style.theme_use('clam') 
style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'), background="grey")
style.configure('Treeview', fieldbackground="grey", foreground="black",font="Verdana 12")

columns = ("Requisition_ID", "Phase", "Submitted_Date", "Assigned_To", "Completed_Date")       
historyTree = ttk.Treeview(history_Frame, columns= columns, show = 'headings')          

historyTree.heading("#0", text="")
historyTree.heading("Requisition_ID", text="Requisition ID")      
historyTree.heading("Phase", text="Phase")
historyTree.heading("Submitted_Date", text="Submitted Date")
historyTree.heading("Assigned_To", text="Assigned To")
historyTree.heading("Completed_Date", text="Completed Date")
           
historyTree.column("#0", width=0, stretch=tk.NO)
historyTree.column("Requisition_ID", width=0, stretch=tk.NO)
historyTree.column("Phase", width=300)
historyTree.column("Submitted_Date", width=200)
historyTree.column("Assigned_To", width=300)
historyTree.column("Completed_Date", width=200)
historyTree.grid(row=1, column=0, sticky="NSEW", padx=5, pady=10)

#print(category)

#make_frame_readonly(rqInfoFrame)
#make_frame_readonly(requestFrame)
def on_category_change(event):
    global tracker
    tracker.destroy()
    tracker = build_phase_tracker(processFrame, currentPhase, category_entry.get(), mvar.get())
    tracker.pack(fill="x")

category_entry.bind('<<ComboboxSelected>>', on_category_change, "+")
    
logonUser = ttk.Entry(rqFrame)
logonUser.pack()
logonUser.pack_forget()
logOnName = os.getlogin()

#Connect to the database and fetch data
conn = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;')                
cursor = conn.cursor()
cursor.execute("SELECT UserID, UserName, OSuser, DocNumber FROM Administration.LogOnUser")
logrows = cursor.fetchall()
currentPhase = ""
docNumber = ""
if logrows != []:
  for logrow in logrows:
    userName = logrow[1]
    osUser = logrow[2]
    docNumber = logrow[3]    
    if osUser != None and osUser == logOnName:
      if userName != None:  
        logonUser.insert(0, userName)
      if docNumber != None:
        sql = "SELECT * FROM ChurchTeachersCollegeDB.REQUISITION.REQUISITION_TABLE WHERE Document_Number = ?"
        cursor.execute(sql, (docNumber,))
        rows = cursor.fetchall()
        for row in rows:
          populateFields(row)
          pouplateTreeview(historyTree, row)
          currentPhase = row[10]
  conn.close()
  '''
def load_user_session(logOnName):
    global currentPhase, docNumber

    try:
        with pyodbc.connect(
            r'Driver=ODBC Driver 18 for SQL Server;'
            r'Server=Chris;'
            r'Database=ChurchTeachersCollegeDB;'
            r'Trusted_Connection=yes;'
            r'Encrypt=Optional;'
        ) as conn:
            cursor = conn.cursor()

            # Get logged-on user record
            cursor.execute("""
                SELECT UserID, UserName, OSuser, DocNumber 
                FROM Administration.LogOnUser
                WHERE OSuser = ?
            """, (logOnName,))
            
            logrow = cursor.fetchone()  # No need to loop — match is unique

            if logrow is None:
                return  # No matching OS user found

            userName  = logrow[1]
            docNumber = logrow[3]

            if userName:
                logonUser.delete(0, END)
                logonUser.insert(0, userName)

            if docNumber:
                cursor.execute("""
                    SELECT * 
                    FROM ChurchTeachersCollegeDB.REQUISITION.REQUISITION_TABLE 
                    WHERE Document_Number = ?
                """, (docNumber,))

                rows = cursor.fetchall()

                for row in rows:
                    populateFields(row)
                    pouplateTreeview(historyTree, row)  # fix typo: populate
                    currentPhase = row[10]

    except pyodbc.Error as e:
        messagebox.showerror("Database Error", f"Failed to load user session:\n{e}")''' 
 
#load_user_session(logOnName)
documentNumber = ""
nextPhase = ""
#Process defined and next phase identified
#tracker = build_phase_tracker(processFrame, currentPhase, category_entry.get())
#tracker.pack(fill="x")
#if currentPhase in ([], "", "Draft"):
  #change_img(processLabel, draftAssigned)
  #nextPhase = "HOD Review"
#tracker.destroy()
tracker = build_phase_tracker(
    processFrame,
    currentPhase,
    category_entry.get(),
    mvar.get()   # add this
)
tracker.pack(fill="x")
'''elif currentPhase == "HOD Review":
  change_img(processLabel, hodImgassigned)
  nextPhase = "VP Approval"
elif currentPhase == "VP Approval":
  if category_entry.get() == "Transport":
    change_img(processLabel, transportAssigned)
    nextPhase = ""
  else:
    change_img(processLabel, VPassigned)
    nextPhase = "Procurement"
elif currentPhase == "Principal Approval":
  change_img(processLabel, prinAssigned)
  nextPhase = "Procurement"
elif currentPhase == "Procurement":
  change_img(processLabel, procImgAssigned)
  nextPhase = "Accounts"
else:
  change_img(processLabel, accountImg)'''
  
#Dynamically created document number
class numEntry:  
  def __init__(self, master):     
    #def documentNumber(self):    
    numberEntry = ""    
    docNumber = ""
    category_entry.get()    
    if docNumber != "":
      self.numberEntry = docNumber
      docNumber_entry.config(state = 'normal')   
      doc_var.set(self.numberEntry)
      docNumber_entry.config(state = 'readonly')
    def getPrefix(self, event=None):      
      prefix = ""
      counter = 0
      if docNumber == "":
        category = category_entry.get()
        if category != "":
          if category== "Transport":
            prefix = "TRAN-"
          elif category == "Infrastructure":
            prefix = "INFR-"
          elif category == "Household":
            prefix = "HSLD-"
          elif category == "Kitchen":
            prefix = "KTCN-"
          else:
            prefix = "OFFS-"  
        if prefix != "":      
          with  pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=Chris;Database=ChurchTeachersCollegeDB;Trusted_Connection=yes;encrypt=Optional;') as conn:              
            cursor = conn.cursor()
            sql = "SELECT MAX(Document_Number) FROM ChurchTeachersCollegeDB.REQUISITION.REQUISITION_TABLE WHERE Document_Number LIKE ?"
            cursor.execute(sql, (f"%{prefix}%",))
            row = cursor.fetchone()                     
            if row != None:
              lastNumber = row[0]
              if lastNumber != None:
                number = re.findall(r'\d+', lastNumber)
                for num in number:
                  counter = int(num)                
            else:
              counter = 0
            counter += 1
            self.numberEntry = f"{prefix}{counter:05d}"
        
          docNumber_entry.config(state = 'normal')   
          doc_var.set(self.numberEntry)
          docNumber_entry.config(state = 'readonly') 
    category_entry.bind('<<ComboboxSelected>>', getPrefix, "+")

nextEntry.insert(0, nextPhase)  
 
buttonFrame = tk.LabelFrame(rqFrame, relief='sunken', borderwidth=5, bg = "bisque2")
buttonFrame.pack(fill="x")

#saveLabel = tk.Label(buttonFrame, bg = "bisque2")
#saveLabel.grid(row=0, column=0, columnspan = 2,sticky="EW", padx=5, pady=5)

closeButton = tk.Button(buttonFrame, text = "Close", command = closeRequisition, relief='raised',
                borderwidth=5, width= 10, height = 1, fg = "black", font = "Algerian 14", bg = "red3")  
closeButton.pack(side = tk.RIGHT, padx=0, pady=0)

submitButton = tk.Button(buttonFrame, text = "Submit", command = assignmentInformation, relief='raised',
                borderwidth=5, width= 10, height = 1, fg = "black", font = "Algerian 14", bg = "lime green")  
submitButton.pack(side = tk.RIGHT, padx=0, pady=0)
  
saveReqButton = tk.Button(buttonFrame, text = "Save", command = saveRequisitionDraft, relief='raised',
                borderwidth=5, width= 10, height = 1, fg = "black", font = "Algerian 14", bg = "deep sky blue")  
saveReqButton.pack(side = tk.RIGHT, padx=0, pady=0)

notebook.rowconfigure(0, weight=1)
notebook.columnconfigure(0, weight=1)
rqInfoFrame.rowconfigure(0, weight=1)
rqInfoFrame.columnconfigure(0, weight=1)
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

numEntry(root)
root.mainloop()
