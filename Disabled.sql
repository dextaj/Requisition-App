DECLARE @sql NVARCHAR(MAX) = N'';
DECLARE @body NVARCHAR(MAX) = N'';
DECLARE @isFirst BIT = 1;

-- Build dynamic UNION queries
SELECT 
    @body = @body +
    CASE WHEN @isFirst = 1 THEN '' ELSE CHAR(10) + 'UNION ALL' + CHAR(10) END +
    '
SELECT
    tu.[ETQ ID],
    tu.[Name],
    tu.[Email],
    tu.[Date Modified],
    tu.[Days],
    tu.[Manager ID],
    tu.[Manager Name],
    tu.[Manager Email],

    tu.[Group Pseudo-User?],
    tu.[System Pseudo-User?],
    tu.[HRIS Deleted?],
    tu.[Disabled?],
    tu.[Training Only?],

    ' +
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM sys.columns rc
            WHERE rc.object_id = parent_table.object_id
              AND rc.name = 'ETQ$RECORD_NUMBER'
        )
        THEN 'CAST(t.[ETQ$RECORD_NUMBER] AS NVARCHAR(255))'
        ELSE 'CAST(NULL AS NVARCHAR(255))'
    END + ' AS [ETQ$RECORD_NUMBER],

    CAST(t.[ETQ$NUMBER] AS NVARCHAR(255)) AS [ETQ$NUMBER],

    CASE
        WHEN phase.PHASE_TYPE = 0 THEN ''Normal''
        WHEN phase.PHASE_TYPE = 1 THEN ''Completed''
        WHEN phase.PHASE_TYPE = 2 THEN ''Archived''
        WHEN phase.PHASE_TYPE = 3 THEN ''Voided''
        WHEN phase.PHASE_TYPE = 5 THEN ''Awaiting Release''
        ELSE ''Unknown''
    END AS [Phase Type DESCRIPTION],

    phase.DISPLAY_NAME AS [Phase],

    N''' + REPLACE(parent_schema.name, '''', '''''') + ''' AS [Schema Name],
    N''' + REPLACE(parent_table.name, '''', '''''') + ''' AS [Table Name],
    N''' + REPLACE(parent_column.name, '''', '''''') + ''' AS [User FK Column],

    CASE
        WHEN ''' + parent_column.name + ''' = ''ETQ$ASSIGNED'' THEN ''Current Assignee''
        WHEN ''' + parent_column.name + ''' LIKE ''%OWNER%'' THEN ''Owner''
        ELSE ''Other''
    END AS [User FK Column Category]

FROM ' + QUOTENAME(parent_schema.name) + '.' + QUOTENAME(parent_table.name) + ' AS t

INNER JOIN TargetUsers tu
    ON t.' + QUOTENAME(parent_column.name) + ' = tu.[ETQ ID]

INNER JOIN ENGINE.PHASE_SETTINGS phase
    ON t.[ETQ$CURRENT_PHASE] = phase.PHASE_ID
    AND phase.PHASE_TYPE NOT IN (2,3)
    AND phase.DISPLAY_NAME NOT LIKE ''Complete%''
    AND phase.DISPLAY_NAME NOT LIKE ''Close%''
    AND phase.DISPLAY_NAME NOT LIKE ''Cancel%''
    AND phase.DISPLAY_NAME NOT LIKE ''Accept%''
'
    +

    -- Conditional ASN join (safe)
    CASE 
        WHEN EXISTS (
            SELECT 1
            FROM sys.tables t2
            JOIN sys.schemas s2 ON t2.schema_id = s2.schema_id
            WHERE t2.name = '_ASN'
              AND s2.name = parent_schema.name
        )
        THEN '
INNER JOIN ' + QUOTENAME(parent_schema.name) + '.[_ASN] cu
    ON tu.[ETQ ID] = cu.ETQ$ASSIGNED
'
        ELSE ''
    END,

    @isFirst = 0
FROM sys.foreign_key_columns fkc
JOIN sys.foreign_keys fk
    ON fk.object_id = fkc.constraint_object_id
JOIN sys.tables parent_table
    ON parent_table.object_id = fkc.parent_object_id
JOIN sys.schemas parent_schema
    ON parent_schema.schema_id = parent_table.schema_id
JOIN sys.columns parent_column
    ON parent_column.object_id = fkc.parent_object_id
   AND parent_column.column_id = fkc.parent_column_id
JOIN sys.tables referenced_table
    ON referenced_table.object_id = fkc.referenced_object_id
JOIN sys.schemas referenced_schema
    ON referenced_schema.schema_id = referenced_table.schema_id
JOIN sys.columns referenced_column
    ON referenced_column.object_id = fkc.referenced_object_id
   AND referenced_column.column_id = fkc.referenced_column_id

WHERE
    referenced_schema.name = 'ENGINE'
    AND referenced_table.name = 'USER_SETTINGS'
    AND referenced_column.name = 'USER_ID'

    -- Exclude archive schemas
    AND parent_schema.name NOT LIKE '%ARC'

    -- Relevant FK columns: current assignee + owners only (past assignees removed)
    AND (
        parent_column.name = 'ETQ$ASSIGNED'
        OR parent_column.name LIKE '%OWNER%'
    )

    AND parent_column.name NOT LIKE '%ORIGINAL%'
    AND parent_column.name <> 'INVESTIGATION_ASSIGNEES_ID'

    -- Ensure record tables
    AND EXISTS (
        SELECT 1 FROM sys.columns x
        WHERE x.object_id = parent_table.object_id
          AND x.name = 'ETQ$NUMBER'
    )
    AND EXISTS (
        SELECT 1 FROM sys.columns x
        WHERE x.object_id = parent_table.object_id
          AND x.name = 'ETQ$CURRENT_PHASE'
    );

-- Handle empty result
IF @body = ''
BEGIN
    SELECT 'No matching user FK columns were found.' AS [Message];
    RETURN;
END;

-- Final query
SET @sql = '
WITH TargetUsers AS
(
    SELECT 
        u.USER_ID AS [ETQ ID],
        u.DISPLAY_NAME AS [Name],
        u.EMAIL AS [Email],
        u.ETQ$MODIFIED_DATE AS [Date Modified],
        DATEDIFF(day, u.ETQ$MODIFIED_DATE, GETDATE()) AS [Days],

        u.REPORTS_TO_ID AS [Manager ID],
        mgr.DISPLAY_NAME AS [Manager Name],
        mgr.EMAIL AS [Manager Email],

        CASE WHEN u.IS_GROUP = 1 THEN ''Yes'' ELSE ''No'' END AS [Group Pseudo-User?],
        CASE WHEN u.EMAIL LIKE ''%etq.com'' THEN ''Yes'' ELSE ''No'' END AS [System Pseudo-User?],
        CASE WHEN u.DISPLAY_NAME LIKE ''??%'' THEN ''Yes'' ELSE ''No'' END AS [HRIS Deleted?],
        CASE WHEN u.IS_DISABLED = 1 THEN ''Yes'' ELSE ''No'' END AS [Disabled?],
        CASE WHEN u.IS_TRAINING_ONLY = 1 THEN ''Yes'' ELSE ''No'' END AS [Training Only?]

    FROM ENGINE.USER_SETTINGS u
    LEFT JOIN ENGINE.USER_SETTINGS mgr
        ON u.REPORTS_TO_ID = mgr.USER_ID

    WHERE u.DISPLAY_NAME LIKE ''??%''
)

' + @body + '

ORDER BY
    [Name],
    [Schema Name],
    [Table Name],
    [User FK Column],
    [ETQ$NUMBER];
';

EXEC sp_executesql @sql;