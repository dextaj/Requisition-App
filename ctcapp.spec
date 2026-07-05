# ctcapp.spec — builds the CTC Requisition desktop app as a folder of .exes.
# Run with:  pyinstaller ctcapp.spec
block_cipher = None

SCREENS = [
    ("login",            "login.pyw"),
    ("AdminScreen",      "AdminScreen.pyw"),
    ("RequisitionScreen","RequisitionScreen.pyw"),
    ("RequisitionForm",  "RequisitionForm.pyw"),
    ("User",             "User.pyw"),
]

# Bundle the assets folder into every screen so logos resolve when frozen.
datas = [("assets", "assets")]

# Hidden imports PyInstaller sometimes misses for these libraries.
hiddenimports = ["PIL._tkinter_finder"]

analyses, exes = [], []
for name, script in SCREENS:
    a = Analysis(
        [script],
        pathex=["."],
        binaries=[],
        datas=datas,
        hiddenimports=hiddenimports,
        hookspath=[],
        runtime_hooks=[],
        excludes=[],
        cipher=block_cipher,
    )
    analyses.append(a)
    pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
    exe = EXE(
        pyz, a.scripts, [],
        exclude_binaries=True,
        name=name,
        console=False,           # windowed app, no console window
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
    )
    exes.append((exe, a))

# Collect everything into one shared folder: dist/CTCApp/
COLLECT(
    *[item for pair in exes for item in (pair[0], pair[1].binaries,
                                         pair[1].zipfiles, pair[1].datas)],
    strip=False, upx=False, name="CTCApp",
)