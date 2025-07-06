import os
import shutil
import glob

# 获取当前 Python 文件的目录路径
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def rename_and_move_pdf_files(base_path, dir_name, suffix, format):
    pdf_files = glob.glob(os.path.join(base_path, 'output', dir_name, rf'*.{format}'))

    pdf_dir = os.path.dirname(pdf_files[0])  # 取第一个文件的目录作为目标目录

    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        if len(filename.split('-')) > 1:
            new_filename = filename.split('-')[0] + rf"-{suffix}.{format}"
        else:
            new_filename = filename.replace(rf'.{format}', rf'-{suffix}.{format}')
        target_path = os.path.join(base_path, "output", new_filename)
        shutil.move(pdf_file, target_path)

    # 确认目录为空后再删除
    if os.path.exists(pdf_dir):
        if not os.listdir(pdf_dir):  # 检查目录是否为空
            os.rmdir(pdf_dir)       # 只删除空目录

rename_and_move_pdf_files(BASE_PATH, "pcb", "pcb","pdf")
rename_and_move_pdf_files(BASE_PATH, "schematic", "schematic","pdf")
rename_and_move_pdf_files(BASE_PATH, "schematic", "schematic","svg")
rename_and_move_pdf_files(BASE_PATH, "pcb", "pcb","svg")
