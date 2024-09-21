file_names = [r'C:\Users\Administrator\Desktop\Locator\app.py', 
              r'C:\Users\Administrator\Desktop\Locator\templates\admin_dashboard.html', 
              r'C:\Users\Administrator\Desktop\Locator\templates\base.html', 
              r'C:\Users\Administrator\Desktop\Locator\templates\cto_application.html', 
              r'C:\Users\Administrator\Desktop\Locator\templates\leave_application.html', 
              r'C:\Users\Administrator\Desktop\Locator\templates\login.html', 
              r'C:\Users\Administrator\Desktop\Locator\templates\register.html', 
              r'C:\Users\Administrator\Desktop\Locator\templates\submit_document.html', 
              r'C:\Users\Administrator\Desktop\Locator\templates\travel_authority.html', 
              r'C:\Users\Administrator\Desktop\Locator\templates\view_users.html']

# Open the output file in write mode
with open('full_program.txt', 'w') as outfile:
    for fname in file_names:
        try:
            with open(fname) as infile:
                # Write the content of each file to the output file
                outfile.write(infile.read())
                outfile.write("\n\n")  # Add a newline to separate contents of each file
        except FileNotFoundError:
            print(f"File not found: {fname}")

print("All tabs saved to full_program.txt")
