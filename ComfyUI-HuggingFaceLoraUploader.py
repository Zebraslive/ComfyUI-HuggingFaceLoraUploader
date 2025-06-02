import os
import folder_paths # ComfyUI's path management
from huggingface_hub import HfApi, create_repo
from huggingface_hub.utils import RepositoryNotFoundError, HfHubHTTPError # More specific errors

# --- Helper function to get LoRA files using ComfyUI's standard method ---
def get_comfy_local_loras():
    """Scans for LoRA files using ComfyUI's internal method."""
    # folder_paths.get_filename_list("loras") returns a list of LoRA filenames
    # (e.g., "my_lora.safetensors" or "SDXL/my_lora.safetensors") from all configured LoRA paths.
    lora_files = folder_paths.get_filename_list("loras")
    if not lora_files: # Returns None if no files/paths are found
        return ["No LoRAs found (check LoRA paths in ComfyUI)"]
    # get_filename_list usually returns unique and sorted names
    return sorted(list(set(lora_files))) # Ensure uniqueness and sort

# --- Custom Node Class ---
class HuggingFaceLoraUploader:
    CATEGORY = "HuggingFace" # Or "Utils/HuggingFace"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status_message",)
    FUNCTION = "upload_lora_to_hf"
    OUTPUT_NODE = True # Indicates this node performs an action

    # Load the LoRA file list at the class level. This is done once when ComfyUI loads this script.
    LORA_FILES_LIST = get_comfy_local_loras()

    @classmethod
    def INPUT_TYPES(cls):
        # Use the class-level list for the dropdown options
        lora_choices = cls.LORA_FILES_LIST
        if not lora_choices or lora_choices[0].startswith("No LoRAs found"):
             lora_choices = ["No LoRAs found (ensure LoRA paths are set and files exist)"]

        return {
            "required": {
                "lora_name": (lora_choices, ), # Select from pre-scanned LoRAs
                "hf_token": ("STRING", {"default": "hf_YOUR_HUGGINGFACE_TOKEN_HERE", "multiline": False}),
                "repo_id": ("STRING", {"default": "username/repo_name", "multiline": False}),
                "commit_message": ("STRING", {"default": "Upload LoRA model", "multiline": True}),
            },
            "optional": {
                "path_in_repo": ("STRING", {"default": "", "multiline": False, "placeholder": "e.g., loras/ (optional)"}),
                "create_repo_if_not_exists": ("BOOLEAN", {"default": True}), # ComfyUI's boolean type
                "private_repo": ("BOOLEAN", {"default": False}), # Used if create_repo_if_not_exists is True
            }
        }

    def _get_lora_full_path_comfy(self, lora_filename_from_list):
        """
        Gets the full path of a given LoRA filename using ComfyUI's method.
        'lora_filename_from_list' is the exact string from folder_paths.get_filename_list("loras").
        This name can already include subdirectories (e.g., "SDXL/my_lora.safetensors").
        """
        return folder_paths.get_full_path("loras", lora_filename_from_list)

    def upload_lora_to_hf(self, lora_name, hf_token, repo_id, commit_message,
                          path_in_repo="", create_repo_if_not_exists=True, private_repo=False):
        
        if lora_name.startswith("No LoRAs found"):
            return (f"Error: {lora_name}. Cannot proceed.",)
        if not hf_token or hf_token == "hf_YOUR_HUGGINGFACE_TOKEN_HERE" or not hf_token.startswith("hf_"):
            return ("Error: Hugging Face token is missing, invalid, or is the default placeholder.",)
        if not repo_id or repo_id == "username/repo_name" or "/" not in repo_id:
            return ("Error: Invalid Hugging Face repository ID. Should be 'username/repo_name' or 'org/repo_name'.",)

        full_lora_path = self._get_lora_full_path_comfy(lora_name)
        
        if not full_lora_path or not os.path.exists(full_lora_path):
            return (f"Error: LoRA file '{lora_name}' not found at resolved path '{full_lora_path}'. It might have been moved or deleted after ComfyUI startup.",)

        print(f"HuggingFaceLoraUploader: Preparing to upload '{lora_name}' (from '{full_lora_path}') to '{repo_id}'.")

        try:
            api = HfApi(token=hf_token)
            
            repo_exists = False
            try:
                api.repo_info(repo_id=repo_id, repo_type="model")
                repo_exists = True
                print(f"HuggingFaceLoraUploader: Repository '{repo_id}' found.")
            except RepositoryNotFoundError:
                print(f"HuggingFaceLoraUploader: Repository '{repo_id}' not found.")
                if not create_repo_if_not_exists:
                    return (f"Error: Repository '{repo_id}' does not exist and 'create_repo_if_not_exists' is False.",)
            except HfHubHTTPError as e_http_info:
                if e_http_info.response.status_code == 401:
                     return (f"Error: Hugging Face authentication failed (401) while checking repo. Check your token.",)
                return (f"Error checking repository info for {repo_id}: {str(e_http_info)}",)
            
            if not repo_exists and create_repo_if_not_exists:
                print(f"HuggingFaceLoraUploader: Creating repository '{repo_id}' (private={private_repo})...")
                create_repo(repo_id, token=hf_token, private=private_repo, repo_type="model", exist_ok=True)
                print(f"HuggingFaceLoraUploader: Repository '{repo_id}' created successfully.")

            filename_for_repo = os.path.basename(lora_name) 
            
            _path_in_repo_cleaned = path_in_repo.strip("/")
            if _path_in_repo_cleaned:
                final_path_in_repo = f"{_path_in_repo_cleaned}/{filename_for_repo}"
            else:
                final_path_in_repo = filename_for_repo

            print(f"HuggingFaceLoraUploader: Uploading '{full_lora_path}' to '{repo_id}' at repo path '{final_path_in_repo}'...")
            
            api.upload_file(
                path_or_fileobj=full_lora_path,
                path_in_repo=final_path_in_repo,
                repo_id=repo_id,
                repo_type="model",
                commit_message=commit_message,
            )
            
            uploaded_url = f"https://huggingface.co/{repo_id}/blob/main/{final_path_in_repo}"
            
            success_message = f"Successfully uploaded '{lora_name}' to {uploaded_url}"
            print(f"HuggingFaceLoraUploader: {success_message}")
            return (success_message,)

        except HfHubHTTPError as e_http_upload:
            status_code = e_http_upload.response.status_code
            if status_code == 401:
                return (f"Hugging Face authentication error (401) during upload. Check your token and its permissions for '{repo_id}'.",)
            elif status_code == 403:
                return (f"Hugging Face permission error (403) during upload. Ensure token has write access to '{repo_id}'.",)
            return (f"Hugging Face API HTTP error during upload: {str(e_http_upload)} (Status: {status_code})",)
        except Exception as e:
            error_message = f"An unexpected error occurred during Hugging Face operation: {str(e)}"
            print(f"HuggingFaceLoraUploader: {error_message}")
            return (error_message,)


# --- ComfyUI Node Registration ---
NODE_CLASS_MAPPINGS = {
    "HuggingFaceLoraUploader": HuggingFaceLoraUploader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HuggingFaceLoraUploader": "Hugging Face LoRA Uploader"
}

# --- Startup Logging ---
print("---------------------------------------------------")
print("--- Hugging Face LoRA Uploader Node Loaded ---")
if not HuggingFaceLoraUploader.LORA_FILES_LIST or \
   HuggingFaceLoraUploader.LORA_FILES_LIST[0].startswith("No LoRAs found"):
    print("--- INFO: No LoRA files detected by ComfyUI's folder_paths.get_filename_list('loras').")
    print("---       Please check your LoRA model paths in ComfyUI (main models/loras or extra_model_paths.yaml).")
    print("---       The LoRA selection dropdown in the node will be empty or show an error message.")
else:
    print(f"--- INFO: Detected {len(HuggingFaceLoraUploader.LORA_FILES_LIST)} LoRA(s). First few: {HuggingFaceLoraUploader.LORA_FILES_LIST[:3]}")
print("---------------------------------------------------")
