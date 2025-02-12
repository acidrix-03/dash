import os

def encode_files_to_text(folder_path, output_file):
    with open(output_file, 'w') as out_file:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.py', '.html', '.css', '.js')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                    out_file.write(f'File: {file} (in {root})\n{content}\n\n')

folder_path = r'D:\warm-hollows-62602'
output_file = 'encoded_code.txt'
print('Success: Whole Program encoded to encoded_code.txt')

encode_files_to_text(folder_path, output_file)
