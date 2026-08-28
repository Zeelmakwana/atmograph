@echo off
"c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\atmograph-ai\backend\venv\Scripts\python.exe" "c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\regression_run.py" > "c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\regression_stdout.txt" 2> "c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\regression_stderr.txt"
echo EXIT_CODE=%ERRORLEVEL% >> "c:\Users\ADMIN\OneDrive\Desktop\AtmoGraph AI\regression_stdout.txt"
