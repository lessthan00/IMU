pip install pyinstaller

# 清理之前的编译
Remove-Item dist, build, jlc_gerber -Recurse -ErrorAction Ignore

# 执行编译
pyinstaller --onefile --name "2jlc" --add-data "GerberX2.json" --hidden-import=shutil --hidden-import=csv 2jlc.py
