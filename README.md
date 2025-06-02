# ComfyUI-HuggingFaceLoraUploader

This is a custom node for ComfyUI that allows users to automatically upload locally trained or downloaded LoRA model files to a specified Hugging Face Model Hub repository.

## Features

*   **Automatic Local LoRA Detection**: The node automatically scans ComfyUI's configured LoRA model directories (including subdirectories and paths defined in `extra_model_paths.yaml`) and displays available LoRA files in a dropdown list.
*   **Upload to Hugging Face Hub**: Users can select a LoRA model and upload it to a specified Hugging Face repository.
*   **Repository Management**:
    *   Option to automatically create a new repository if the target repository does not exist.
    *   Support for creating public or private repositories.
*   **Flexible Path Settings**: Allows specifying the storage path for LoRA files within the Hugging Face repository.
*   **Custom Commit Messages**: Enables users to write custom Git commit messages for each upload.
*   **Status Feedback**: The node outputs the upload status (success or failure, along with error messages).


## How to Use

1.  In the ComfyUI canvas, right-click -> "Add Node" -> "HuggingFace" -> "Hugging Face LoRA Uploader".
2.  Configure the node inputs:
    *   **`lora_name`**: Select the local LoRA model you want to upload from the dropdown list.
    *   **`hf_token` (Hugging Face Token)**: Paste your Hugging Face User Access Token. **Important: This token needs "write" permissions to create repositories and upload files.** You can create one on the Hugging Face website under `Settings -> Access Tokens`.
        *   **Security Warning**: This token will be saved in plain text in your workflow JSON file! Handle workflow files containing this token protein carefully and do not share them carelessly.
    *   **`repo_id` (Repository ID)**: Enter your Hugging Face repository ID in the format `username/repo_name` or `organization_name/repo_name`.
    *   **`commit_message`**: Write a Git commit message for this upload.
    *   **`path_in_repo` (Path in Repository - Optional)**: If you want to upload the LoRA to a subfolder within the Hugging Face repository, specify the path here (e.g., `sdxl_loras/` or `characters/style1/`). If left empty, the file will be uploaded to the repository root. The LoRA filename will be appended to this path.
    *   **`create_repo_if_not_exists` (Create Repo if Not Exists - Optional)**: If checked (default True), and the specified repository does not exist, the node will automatically create it.
    *   **`private_repo` (Private Repository - Optional)**: Only effective if `create_repo_if_not_exists` is checked and the repository needs to be created. This option determines if the newly created repository is private.
3.  Connect other nodes or run the workflow containing this node.
4.  After the node executes, the `status_message` output port will display the operation result. You can also check the ComfyUI console/terminal window for more detailed logs.


## Notes

*   Ensure your Hugging Face Token has sufficient permissions.
*   Uploading large files may take some time; please be patient.
*   Safely process workflow files containing your Hugging Face Token.
