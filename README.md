# ComfyUI LoRA Uploaders
﻿
This custom node pack for ComfyUI provides tools to upload your locally trained or downloaded LoRA model files to popular model sharing platforms: Hugging Face Hub and ModelScope.
﻿
**Current Version: v0.2.0**
﻿
## Features
﻿
*   **Automatic Local LoRA Detection**: Nodes automatically scan ComfyUI's configured LoRA model directories and display available LoRA files in a dropdown list.
*   **Multi-Platform Support**:
*   Upload to **Hugging Face Hub**.
*   Upload to **ModelScope (魔搭)**.
*   **Repository Management**:
*   Option to automatically create a new repository if the target repository does not exist.
*   Support for creating public or private repositories.
*   **Flexible Path & Commit Settings**:
*   Allows specifying the storage path for LoRA files within the remote repository.
*   Enables custom commit messages for each upload.
*   **Status Feedback**: Nodes output the upload status (success or failure, along with error messages) directly in ComfyUI.
*   **Improved ModelScope Uploader (as of v0.2.0)**:
*   Uses ModelScope's recommended HTTP-based `upload_folder` API, which is more stable and **no longer requires local Git user.name/email configuration**.
*   Handles repository creation and metadata (visibility, license, Chinese name) more robustly.
﻿
## Installation
﻿
1.  Clone this repository into your `ComfyUI/custom_nodes/` directory:
```bash
git clone <your_repository_url_here> ComfyUI-LoraUploaders # Replace <your_repository_url_here>
```
Alternatively, download the source codeforestry (e.g., as a ZIP file) and extract it to `ComfyUI/custom_nodes/ComfyUI-LoraUploaders`.
2.  Ensure you have the necessary Python libraries installed. If you have a `requirements.txt` in this repository, you can install them via:
```bash
cd ComfyUI/custom_nodes/ComfyUI-LoraUploaders
pip install -r requirements.txt
```
(This node pack primarily relies on `huggingface-hub` and `modelscope` libraries, which you might already have if you use tools from these platforms.)
3.  Restart ComfyUI.
﻿
## Nodes Included
﻿
### 1. Hugging Face LoRA Uploader
﻿
This node allows users to upload LoRA model files to a specified Hugging Face Model Hub repository.
﻿
**How to Use (Hugging Face LoRA Uploader):**
﻿
1.  In the ComfyUI canvas, right-click -> "Add Node" -> "Uploaders/HuggingFace" -> "Hugging Face LoRA Uploader".
2.  Configure the node inputs:
*   **`lora_name`**: Select the local LoRA model you want to upload from the dropdown list.
*   **`hf_token` (Hugging Face Token)**: Paste your Hugging Face User Access Token. **Important: This token needs "write" permissions.** Create one at `Hugging Face Settings -> Access Tokens`.
*   **Security Warning**: This token will be saved in plain text in your workflow JSON! Handle workflow files containing this token carefully.
*   **`repo_id` (Repository ID)**: Your Hugging Face repository ID (e.g., `username/repo_name` or `org/repo_name`).
*   **`commit_message`**: Git commit message for this upload.
*   **`path_in_repo` (Optional)**: Subfolder path within the Hugging Face repository (e.g., `loras/`). If empty, uploads to the root.
*   **`create_repo_if_not_exists` (Optional)**: If checked (default True), creates the repository if it doesn't exist.
*   **`private_repo` (Optional)**: If creating a new repository, this determines if it's private.
3.  Connect or run the workflow. The `status_message` output will show the result. Check the console for detailed logs.
﻿
---
﻿
### 2. ModelScope LoRA Uploader (HTTP)
﻿
This node allows users to upload LoRA model files, along with a basic `configuration.json` and `README.md`, to a specified ModelScope repository using their HTTP API.
﻿
**Key Improvements:**
*   Uses ModelScope's stable HTTP upload method.
*   **No local Git configuration (user.name/email) needed!**
*   Handles repository creation, visibility, license, and Chinese name settings.
﻿
**How to Use (ModelScope LoRA Uploader):**
﻿
1.  In the ComfyUI canvas, right-click -> "Add Node" -> "Uploaders/ModelScope" -> "ModelScope LoRA Uploader (HTTP)".
2.  Configure the node inputs:
*   **`lora_name`**: Select the local LoRA model to upload.
*   **`modelscope_token`**: Your ModelScope Access Token. Obtain from `ModelScope Personal Center -> Access Tokens`.
*   **`repo_id` (Repository ID)**: Your ModelScope repository ID (e.g., `your_username/your_model_name` or `your_org/model_id`).
*   **`commit_message`**: A message describing this version/upload.
*   **`visibility_str`**: Set repository visibility (`public` or `private`).
*   **`chinese_name` (Optional)**: A Chinese name for your model on ModelScope.
*   **`license_str` (Optional)**: Select a license for your model (e.g., "Apache License 2.0", "MIT License"). Choose "Other (Set on ModelScope)" if you prefer to set it on the platform later or if your desired license isn't listed.
*   **`create_repo_if_not_exists` (Optional)**: If checked (default True), creates the repository on ModelScope if it doesn't exist, using the provided visibility, license, and Chinese name.
*   **`revision` (Optional)**: The branch to upload to (e.g., `master`, `main`). Defaults to `master`.
*   **`path_in_repo` (Optional)**: Subfolder path within the ModelScope repository where files will be placed (e.g., `lora_files/`). If empty, uploads to the root.
3.  Connect or run the workflow. The `status_message` output will show the result. Check the console for detailed logs. The node will create a temporary directory for staging files (`configuration.json`, `README.md`, and the LoRA file) and clean it up after the upload.
﻿
## General Notes
﻿
*   Ensure your Access Tokens have sufficient permissions for the intended operations (read, write, create repo).
*   Uploading large files may take some time; please be patient.
*   **Security**: Be extremely careful with workflow `.json` files if they contain your access tokens, as these are saved in plain text. Avoid sharing workflows with embedded tokens or use a secrets management solution if available in your ComfyUI setup.
*   Check the ComfyUI console/terminal window for more detailed logs during the upload process.
﻿
## Troubleshooting
﻿
*   **Node Not Loading**:
*   Ensure you have the `huggingface-hub` and `modelscope` Python libraries installed in your ComfyUI's Python environment.
*   Check the ComfyUI console for any `ImportError` messages when starting up.
*   **Upload Failures**:
*   Verify your access token is correct and has "write" permissions.
*   Check your internet connection.
*   Ensure the `repo_id` format is correct for the respective platform.
*   For ModelScope, if you encounter issues with specific license constants, the dropdown might have fewer options. This is to ensure compatibility with your installed `modelscope` SDK version.
﻿