/* ============================================================
   Church Teachers College — Requisition approver columns
   Run once in SSMS against ChurchTeachersCollegeDB.

   Records WHICH user approved at each signing phase, so the
   printed requisition can show that person's stored signature
   image (Administration.UserSignatures, keyed on UserID).

   Set at submit time:
     HOD_Approver_ID        when leaving HOD Review
     VP_Approver_ID         when leaving VP Review / VP Approval
     Principal_Approver_ID  when leaving Principal Approval

   NOTE: INT to match Administration.Users.UserID.
   ============================================================ */

IF COL_LENGTH('REQUISITION.REQUISITION_TABLE', 'HOD_Approver_ID') IS NULL
    ALTER TABLE REQUISITION.REQUISITION_TABLE ADD HOD_Approver_ID INT NULL;
GO
IF COL_LENGTH('REQUISITION.REQUISITION_TABLE', 'VP_Approver_ID') IS NULL
    ALTER TABLE REQUISITION.REQUISITION_TABLE ADD VP_Approver_ID INT NULL;
GO
IF COL_LENGTH('REQUISITION.REQUISITION_TABLE', 'Principal_Approver_ID') IS NULL
    ALTER TABLE REQUISITION.REQUISITION_TABLE ADD Principal_Approver_ID INT NULL;
GO

/* Optional referential integrity (uncomment if desired):
ALTER TABLE REQUISITION.REQUISITION_TABLE ADD CONSTRAINT FK_Req_HODApprover
    FOREIGN KEY (HOD_Approver_ID)       REFERENCES Administration.Users(UserID);
ALTER TABLE REQUISITION.REQUISITION_TABLE ADD CONSTRAINT FK_Req_VPApprover
    FOREIGN KEY (VP_Approver_ID)        REFERENCES Administration.Users(UserID);
ALTER TABLE REQUISITION.REQUISITION_TABLE ADD CONSTRAINT FK_Req_PrincipalApprover
    FOREIGN KEY (Principal_Approver_ID) REFERENCES Administration.Users(UserID);
GO
*/
