file_names = [
    r'D:\warm-hollows-62602\app.py', 
    r'D:\warm-hollows-62602\templates\base.html', 
    r'Z:\D:\warm-hollows-62602templates\cto_application.html', 
    r'D:\warm-hollows-62602\templates\leave_application.html', 
    r'D:\warm-hollows-62602\templates\login.html', 
    r'D:\warm-hollows-62602\templates\register.html', 
    r'D:\warm-hollows-62602\templates\submit_document.html', 
    r'D:\warm-hollows-62602\templates\travel_authority.html', 
    r'D:\warm-hollows-62602\templates\view_users.html',
    r'D:\warm-hollows-62602\templates\admin_dashboard.html',
    r'D:\warm-hollows-62602\templates\approver_dashboard.html',
    r'D:\warm-hollows-62602\templates\approved_applications.html',
    r'D:\warm-hollows-62602\templates\change_password.html',
    r'D:\warm-hollows-62602\templates\document_tracker.html',
    r'D:\warm-hollows-62602\templates\recommended_applications.html',
    r'D:\warm-hollows-62602\templates\recommender_dashboard.html',
    r'D:\warm-hollows-62602\templates\user_dashboard.html',
    r'D:\warm-hollows-62602\templates\recommended_head.html',    
    r'D:\warm-hollows-62602\templates\unit_head_dashboard.html',
]

# Open the output file in write mode
with open('full_program.txt', 'w', encoding='utf-8') as outfile:
    for fname in file_names:
        try:
            with open(fname, 'r', encoding='utf-8') as infile:
                # Write the content of each file to the output file
                outfile.write(infile.read())
                outfile.write("\n\n")  # Add a newline to separate contents of each file
        except FileNotFoundError:
            print(f"File {fname} not found, skipping.")
        except Exception as e:
            print(f"An error occurred while processing {fname}: {e}")

print("All tabs saved to full_program.txt")
