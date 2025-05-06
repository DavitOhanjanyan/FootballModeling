import git
import os

# Replace these with your local repo path and remote repo URL
local_repo_path = '/path/to/your/local/repo'
remote_repo_url = 'https://github.com/username/repository.git'  # GitHub Repo URL
folder_path = '/path/to/your/folder'  # Path to the folder to upload

# Initialize the repository object
repo = git.Repo(local_repo_path)

# Check if the folder exists, if not, create it
if not os.path.exists(folder_path):
    print(f"Folder {folder_path} does not exist.")
    exit()

# Copy the folder into the local repo directory (if not already inside)
folder_name = os.path.basename(folder_path)
destination = os.path.join(local_repo_path, folder_name)

# Optional: Use shutil to copy the folder if you need to move it
import shutil
shutil.copytree(folder_path, destination)

# Add the folder to Git (it automatically adds all new files inside the folder)
repo.git.add(folder_name)

# Commit the changes
repo.git.commit('-m', 'Add folder to GitHub repository')

# Push the changes to the remote GitHub repository
origin = repo.remotes.origin
origin.push()

print(f"Folder {folder_name} uploaded successfully to GitHub repository.")
