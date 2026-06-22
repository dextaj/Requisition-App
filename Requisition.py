import pyodbc
import tkinter as tk
from tkinter import *
from tkinter import ttk
#

root = tk.Tk()
root.title("Requisition Screen")
root.geometry("1000x800")
  
rqFrame = LabelFrame(root, text="Requisition Form", fg = "black", font = "Verdana 14")  
rqFrame.grid(row=0, column=0, padx=5, pady=5, sticky="NSEW") 

siteList = ['', 'Main campus', 'Brownstown', 'Farm']
site_var = tk.StringVar()  
site_var.set(siteList[0]) 

categoryList = ['', 'Transport', 'Infrastructure', 'household', 'Kitchen', 'Office supplies']
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

rqInfoFrame = LabelFrame(rqFrame, text="Requisition Information", fg = "black", font = "Verdana 14")
rqInfoFrame.grid(row=4, column=6, padx=5, pady=5, sticky="NSEW")  
  
createdBy_label = Label(rqInfoFrame, text="Created By:", fg = "black", font = "Verdana 14")
createdBy_label.grid(row=2, column=0, sticky="EW", padx=5, pady=5)  
createdBy_entry = Entry(rqInfoFrame, width=50)
createdBy_entry.grid(row=2, column=1, sticky="E", padx=5, pady=5)

number_label = Label(rqInfoFrame, text="Number:", fg = "black", font = "Verdana 14")
number_label.grid(row=4, column=0, sticky="EW", padx=5, pady=5)
docNumber_entry = Entry(rqInfoFrame, width=50)
docNumber_entry.grid(row=4, column=1, sticky="E", padx=5, pady=5)  

site_label = Label(rqInfoFrame, text="Site:", fg = "black", font = "Verdana 14")
site_label.grid(row=4, column=2, sticky="EW", padx=5, pady=5)
site_entry = ttk.Combobox(rqInfoFrame, values= siteList, state="readonly", width=50)  
site_entry.grid(row=4, column=3, sticky="Ew", padx=5, pady=5)
  
category_label = Label(rqInfoFrame, text="Category:", fg = "black", font = "Verdana 14")
category_label.grid(row=6, column=0, sticky="NSEW", padx=5, pady=5)
category_entry = ttk.Combobox(rqInfoFrame, values= categoryList, state="readonly", width=50)
category_entry.grid(row=6, column=1, sticky="NSEW", padx=5, pady=5)
  
def addMaintenance(event):
  if category_entry.get() == "Infrastructure":
    maintenance_label = Label(rqInfoFrame, text="Maintenance:", fg = "black", font = "Verdana 14")
    maintenance_label.grid(row=8, column=0, sticky="NSEW", padx=5, pady=5)
    maintenance_entry = ttk.Combobox(rqInfoFrame, values= maintenanceList, state="readonly", width=50)
    maintenance_entry.grid(row=8, column=1, sticky="NSEW", padx=5, pady=5)
  else:
    maintenance_label.destroy()
    maintenance_entry.destroy()
category_entry.bind('<<ComboboxSelected>>', addMaintenance, "+")
  
dept_label = Label(rqInfoFrame, text="Department & Units", fg = "black", font = "Verdana 14")
dept_label.grid(row=6, column=2, sticky="NSEW", padx=5, pady=5)
dept_entry = ttk.Combobox(rqInfoFrame, values= deptList, state="readonly", width=50)
dept_entry.grid(row=6, column=3, sticky="NSEW", padx=5, pady=5)

def addAcademic(event):
  if dept_entry.get() == "Academic":
    academic_label = Label(rqInfoFrame, text="Academic Department:", fg = "black", font = "Verdana 14")
    academic_label.grid(row=8, column=2, sticky="NSEW", padx=5, pady=5)
    academic_entry = ttk.Combobox(rqInfoFrame, values= academicList, state="readonly", width=50)
    academic_entry.grid(row=8, column=3, sticky="NSEW", padx=5, pady=5)
dept_entry.bind('<<ComboboxSelected>>', addAcademic, "+")

comment_label = Label(rqInfoFrame, text="Comment", fg = "black", font = "Verdana 14")
comment_label.grid(row=10, column=0, sticky="NSEW", padx=5, pady=5)
comment_entry = Entry(rqInfoFrame)
comment_entry.grid(row=10, column=1, sticky="NSEW", padx=5, pady=5)
  
attachments_label = Label(rqInfoFrame, text="Attachments:", fg = "black", font = "Verdana 14")
attachments_label.grid(row=10, column=2, sticky="NSEW", padx=5, pady=5)
attachments_entry = Entry(rqInfoFrame)
attachments_entry.grid(row=10, column=3, sticky="NSEW", padx=5, pady=5)

saveReqButton = Button(rqInfoFrame, text = "Save", command = set,
                fg = "black", font = "Verdana 14",)  
saveReqButton.grid(row=12, column=1, sticky="EW", padx=5, pady=5)
  
  
'''history_Frame = LabelFrame(rq_window, text="History", fg = "black", font = "Verdana 14")  
history_Frame.grid(row=1, column=0, padx=5, pady=5, sticky="EW")
  
phase_label = Label(history_Frame, text="Phase:", fg = "black", font = "Verdana 14")
phase_label.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)
phase_entry = Entry(history_Frame, width=50)
phase_entry.grid(row=1, column=1, sticky="NSEW", padx=5, pady=5)
  
submitted_label = Label(history_Frame, text="Submitted On:", fg = "black", font = "Verdana 14")
submitted_label.grid(row=1, column=2, sticky="NSEW", padx=5, pady=5)  
submitted_entry = Entry(history_Frame, width=50)
submitted_entry.grid(row=1, column=3, sticky="NSEW", padx=5, pady=5)

assignedTo_label = Label(history_Frame, text="Assigned To", fg = "black", font = "Verdana 14")
assignedTo_label.grid(row=2, column=0, sticky="NSEW", padx=5, pady=5)
assignedTo_entry = Entry(history_Frame)
assignedTo_entry.grid(row=2, column=1, sticky="NSEW", padx=5, pady=5)
  
completed_label = Label(history_Frame, text="Completed:", fg = "black", font = "Verdana 14")
completed_label.grid(row=2, column=2, sticky="NSEW", padx=5, pady=5)
completed_entry = Entry(history_Frame)
completed_entry.grid(row=2, column=3, sticky="NSEW", padx=5, pady=5)'''

root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

root.mainloop()
