# List of file names (representing tabs)
file_names = [
    r'Z:\Drix Office Docs\ProgramX\warm-hollows-62602\app.py', 
    r'Z:\Drix Office Docs\ProgramX\warm-hollows-62602\templates\base.html', 
    r'Z:\Drix Office Docs\ProgramX\warm-hollows-62602\templates\cto_application.html', 
    r'Z:\Drix Office Docs\ProgramX\warm-hollows-62602\templates\leave_application.html', 
    r'Z:\Drix Office Docs\ProgramX\warm-hollows-62602\templates\login.html', 
    r'Z:\Drix Office Docs\ProgramX\warm-hollows-62602\templates\register.html', 
    r'Z:\Drix Office Docs\ProgramX\warm-hollows-62602\templates\submit_document.html', 
    r'Z:\Drix Office Docs\ProgramX\warm-hollows-62602\templates\travel_authority.html', 
    r'Z:\Drix Office Docs\ProgramX\warm-hollows-62602\templates\view_users.html'
]

# Open the output file in write mode
with open('full_program.txt', 'w') as outfile:
    for fname in file_names:
        with open(fname) as infile:
            # Write the content of each file to the output file
            outfile.write(infile.read())
            outfile.write("\n\n")  # Add a newline to separate contents of each file

print("All tabs saved to full_program.txt")
