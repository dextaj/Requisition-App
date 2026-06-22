/* ============================================================
   Church Teachers College — Approver Signatures
   Run once in SSMS against ChurchTeachersCollegeDB.

   One signature per user (HOD / VP / Principal, or anyone).
   The image bytes live in the database (VARBINARY(MAX)), not on a
   file share, so they travel with backups and need no path access
   from client machines.

   UserID is both PK and FK, which enforces exactly one signature
   per user. ON DELETE CASCADE removes the signature if the user is
   deleted.

   NOTE: UserID is INT to match Administration.Users.UserID. If that
   column is a different type, change it here to match before running.
   ============================================================ */

IF OBJECT_ID('Administration.UserSignatures', 'U') IS NULL
BEGIN
    CREATE TABLE Administration.UserSignatures
    (
        UserID        INT             NOT NULL,
        SignatureData VARBINARY(MAX)  NOT NULL,   -- raw image bytes (PNG/JPG)
        ContentType   NVARCHAR(50)    NULL,       -- e.g. 'image/png'
        UpdatedDate   DATETIME2       NOT NULL
            CONSTRAINT DF_UserSignatures_Updated DEFAULT SYSUTCDATETIME(),
        UpdatedBy     INT             NULL,        -- who last set it (optional)
        CONSTRAINT PK_UserSignatures PRIMARY KEY (UserID),
        CONSTRAINT FK_UserSignatures_User
            FOREIGN KEY (UserID)
            REFERENCES Administration.Users (UserID)
            ON DELETE CASCADE
    );
END;
GO
