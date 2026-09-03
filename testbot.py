import os

# Check musik folder
music_dir = "music"

if os.path.exists(music_dir):
    files = os.listdir(music_dir)
    print(f"✅ Folder '{music_dir}' ada")
    print(f"File: {files}")
else:
    print(f"❌ Folder '{music_dir}' tidak ada!")