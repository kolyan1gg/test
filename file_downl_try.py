def get_vit_file():

    import os
    import wget

    # Define the file path and the download URL
    file_path = 'vit_base_patch32_state_dict.pth'  # Replace with your file path
    download_url = 'https://github.com/kolyan1gg/test/raw/main/vit_base_patch32_state_dict.pth'  # Replace with your file URL

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"File not found. Downloading from {download_url}")
        wget.download(download_url, file_path)
    else:
        print(f"File already exists at {file_path}")