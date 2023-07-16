import os
import sys
sys.path.insert(0, './temp')
from delocate.fuse import fuse_wheels

directory_path = os.path.join(os.getcwd(), 'temp')
files = os.listdir(directory_path)
wheel_files = [f for f in files if f.endswith('.whl')]
base_name = wheel_files[0].split("-macosx")[0]
final_binary = os.path.join(directory_path, f'{base_name}-macosx_11_0_universal2.whl')
full_paths = [os.path.join(directory_path, file) for file in wheel_files]
fuse_wheels(*full_paths, final_binary)
print(final_binary)
