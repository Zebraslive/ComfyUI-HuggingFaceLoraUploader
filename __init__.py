import os
import shutil
import json
import folder_paths

# --- Hugging Face Specific Imports ---
from huggingface_hub import HfApi, create_repo
from huggingface_hub.utils import RepositoryNotFoundError, HfHubHTTPError as HuggingFaceHTTPError

# --- ModelScope Specific Imports ---
from modelscope.hub.api import HubApi as ModelScopeHubApi
from modelscope.hub.constants import Licenses, ModelVisibility # For create_model
# Removed: from modelscope.utils.error import NotExistError as ModelScopeRepoNotFound

# --- Helper function to get LoRA files ---
def get_comfy_local_loras():
    lora_files = folder_paths.get_filename_list("loras")
    if not lora_files:
        return ["None (No LoRAs found - check paths)"]
    return ["None"] + sorted(list(set(lora_files)))

SHARED_LORA_FILES_LIST = get_comfy_local_loras()

# --- Hugging Face LoRA Uploader Node Class (No changes from previous working version) ---
class HuggingFaceLoraUploader:
    CATEGORY = "Uploaders/HuggingFace"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status_message",)
    FUNCTION = "upload_lora_to_hf"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        lora_choices = SHARED_LORA_FILES_LIST
        if lora_choices[0].startswith("None (No LoRAs found"):
             lora_choices = ["None (Ensure LoRA paths are set and files exist)"]
        return {
            "required": {
                "lora_name": (lora_choices, ),
                "hf_token": ("STRING", {"default": "hf_YOUR_HUGGINGFACE_TOKEN_HERE", "multiline": False}),
                "repo_id": ("STRING", {"default": "username/repo_name", "multiline": False}),
                "commit_message": ("STRING", {"default": "Upload LoRA model via ComfyUI", "multiline": True}),
            },
            "optional": {
                "path_in_repo": ("STRING", {"default": "", "multiline": False, "placeholder": "e.g., loras/ (optional)"}),
                "create_repo_if_not_exists": ("BOOLEAN", {"default": True}),
                "private_repo": ("BOOLEAN", {"default": False}),
            }
        }

    def _get_lora_full_path_comfy(self, lora_filename_from_list):
        return folder_paths.get_full_path("loras", lora_filename_from_list)

    def upload_lora_to_hf(self, lora_name, hf_token, repo_id, commit_message,
                          path_in_repo="", create_repo_if_not_exists=True, private_repo=False):
        if lora_name == "None" or lora_name.startswith("None (No LoRAs found"):
            return (f"Error: No LoRA selected or {lora_name}. Cannot proceed.",)
        if not hf_token or hf_token == "hf_YOUR_HUGGINGFACE_TOKEN_HERE" or not hf_token.startswith("hf_"):
            return ("Error: Hugging Face token is missing, invalid, or is the default placeholder.",)
        if not repo_id or repo_id == "username/repo_name" or "/" not in repo_id:
            return ("Error: Invalid Hugging Face repository ID. Should be 'username/repo_name' or 'org/repo_name'.",)

        full_lora_path = self._get_lora_full_path_comfy(lora_name)
        if not full_lora_path or not os.path.exists(full_lora_path):
            return (f"Error: LoRA file '{lora_name}' not found at resolved path '{full_lora_path}'.",)

        print(f"HFLoraUploader: Uploading '{lora_name}' to HF repo '{repo_id}'.")
        try:
            api = HfApi(token=hf_token)
            repo_exists = False
            try:
                api.repo_info(repo_id=repo_id, repo_type="model")
                repo_exists = True
            except RepositoryNotFoundError:
                if not create_repo_if_not_exists:
                    return (f"Error: HF Repo '{repo_id}' does not exist and 'create_repo_if_not_exists' is False.",)
            except HuggingFaceHTTPError as e_http_info:
                if e_http_info.response.status_code == 401: return (f"Error: HF authentication failed (401) checking repo. Check token.",)
                return (f"Error checking HF repo info for {repo_id}: {str(e_http_info)}",)

            if not repo_exists and create_repo_if_not_exists:
                create_repo(repo_id, token=hf_token, private=private_repo, repo_type="model", exist_ok=True)

            filename_for_repo = os.path.basename(lora_name)
            _path_in_repo_cleaned = path_in_repo.strip("/")
            final_path_in_repo = f"{_path_in_repo_cleaned}/{filename_for_repo}" if _path_in_repo_cleaned else filename_for_repo

            api.upload_file(
                path_or_fileobj=full_lora_path,
                path_in_repo=final_path_in_repo,
                repo_id=repo_id,
                repo_type="model",
                commit_message=commit_message,
            )
            uploaded_url = f"https://huggingface.co/{repo_id}/blob/main/{final_path_in_repo.lstrip('/')}"
            success_message = f"Successfully uploaded '{lora_name}' to {uploaded_url}"
            print(f"HFLoraUploader: {success_message}")
            return (success_message,)
        except HuggingFaceHTTPError as e_http_upload:
            status_code = e_http_upload.response.status_code
            if status_code == 401: return (f"HF auth error (401) during upload. Check token/permissions for '{repo_id}'.",)
            if status_code == 403: return (f"HF permission error (403) during upload. Ensure token has write access to '{repo_id}'.",)
            return (f"HF API HTTP error during upload: {str(e_http_upload)} (Status: {status_code})",)
        except Exception as e:
            error_message = f"Unexpected error during Hugging Face op: {str(e)}"
            print(f"HFLoraUploader: {error_message}")
            return (error_message,)

# --- ModelScope LoRA Uploader Node Class (Updated to use upload_folder) ---
class ModelScopeLoraUploader:
    CATEGORY = "Uploaders/ModelScope"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status_message",)
    FUNCTION = "execute_upload_to_modelscope"
    OUTPUT_NODE = True

    LICENSE_MAP = {
        "Apache License 2.0": Licenses.APACHE_V2,
        "MIT License": Licenses.MIT,
    }

    @classmethod
    def INPUT_TYPES(s):
        lora_choices = SHARED_LORA_FILES_LIST
        if lora_choices[0].startswith("None (No LoRAs found"):
             lora_choices = ["None (Ensure LoRA paths are set and files exist)"]
        license_options = list(s.LICENSE_MAP.keys()) + ["Other (Set on ModelScope)"]
        return {
            "required": {
                "lora_name": (lora_choices, ),
                "modelscope_token": ("STRING", {"multiline": False, "default": "YOUR_MODELSCOPE_TOKEN_HERE"}),
                "repo_id": ("STRING", {"multiline": False, "default": "your_username/your_model_name"}),
                "commit_message": ("STRING", {"multiline": True, "default": "Upload LoRA via ComfyUI"}),
                "visibility_str": (["public", "private"], {"default": "public"}),
            },
            "optional": {
                "chinese_name": ("STRING", {"multiline": False, "default": "", "placeholder": "模型中文名 (可选)"}),
                "license_str": (license_options, {"default": "Apache License 2.0"}),
                "create_repo_if_not_exists": ("BOOLEAN", {"default": True}),
                "revision": ("STRING", {"default": "master", "multiline": False, "placeholder": "上传到的分支 (e.g., master, main)"}),
                "path_in_repo": ("STRING", {"default": "", "multiline": False, "placeholder": "仓库内路径 (e.g., loras/, 可选)"}),
            }
        }

    def _get_lora_full_path_comfy(self, lora_filename_from_list):
        return folder_paths.get_full_path("loras", lora_filename_from_list)

    def execute_upload_to_modelscope(self, lora_name, modelscope_token, repo_id, commit_message,
                                     visibility_str, chinese_name="", license_str="Apache License 2.0",
                                     create_repo_if_not_exists=True, revision="master", path_in_repo=""):

        if lora_name == "None" or lora_name.startswith("None (No LoRAs found"):
            return (f"Error: No LoRA selected or {lora_name}. Cannot proceed.",)
        if not modelscope_token or modelscope_token == "YOUR_MODELSCOPE_TOKEN_HERE":
            return ("Error: ModelScope Token is missing or is the default placeholder.",)
        if not repo_id or "/" not in repo_id:
            return ("Error: Invalid ModelScope Repo ID. Expected format: 'namespace/model_name'.",)

        ms_visibility = ModelVisibility.PUBLIC if visibility_str == "public" else ModelVisibility.PRIVATE
        ms_license = self.LICENSE_MAP.get(license_str)

        full_lora_path = self._get_lora_full_path_comfy(lora_name)
        if not full_lora_path or not os.path.exists(full_lora_path):
            return (f"Error: LoRA file '{lora_name}' not found at resolved path '{full_lora_path}'.",)

        print(f"MSLoraUploader: Preparing to upload '{lora_name}' to MS repo '{repo_id}'.")
        unique_temp_suffix = repo_id.replace("/", "_") + "_" + os.path.splitext(os.path.basename(lora_name))[0]
        temp_upload_dir = os.path.join(folder_paths.get_temp_directory(), f"modelscope_upload_{unique_temp_suffix}")

        try:
            os.makedirs(temp_upload_dir, exist_ok=True)
            lora_filename_in_repo = os.path.basename(full_lora_path)
            shutil.copy(full_lora_path, os.path.join(temp_upload_dir, lora_filename_in_repo))

            config_data = {
                "model_type": "lora", "framework": "pytorch", "lora_filename": lora_filename_in_repo,
                "task": "text-to-image-synthesis",
            }
            if chinese_name: config_data["name"] = chinese_name
            with open(os.path.join(temp_upload_dir, "configuration.json"), "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            readme_content = f"# {repo_id.split('/')[-1] if '/' in repo_id else repo_id}\n\n"
            if chinese_name: readme_content += f"中文名称 (Chinese Name): {chinese_name}\n\n"
            readme_content += f"LoRA Model File: `{lora_filename_in_repo}`\n\n"
            readme_content += f"Uploaded via ComfyUI ModelScope Uploader.\n"
            readme_content += f"Original Commit Message: {commit_message}\n"
            with open(os.path.join(temp_upload_dir, "README.md"), "w", encoding="utf-8") as f:
                f.write(readme_content)

            api = ModelScopeHubApi()
            try:
                api.login(modelscope_token)
                print(f"MSLoraUploader: Successfully logged into ModelScope.")
            except Exception as e_login:
                return (f"ModelScope login failed: {str(e_login)}",)

            repo_actually_exists = False # Initialize before try block
            try:
                api.get_model(model_id=repo_id)
                repo_actually_exists = True
                print(f"MSLoraUploader: Repository '{repo_id}' already exists.")
            except Exception as e_repo_check: # Catch general exception for repo check
                error_str = str(e_repo_check).lower()
                # Keywords to infer "Not Found" type errors
                is_not_found_error = "not found" in error_str or \
                                     "does not exist" in error_str or \
                                     "no model" in error_str or \
                                     "no such" in error_str # General "no such file/directory"

                print(f"MSLoraUploader: Debug - Repo check for '{repo_id}' encountered: {type(e_repo_check).__name__} - {str(e_repo_check)}")

                if is_not_found_error:
                    print(f"MSLoraUploader: Repository '{repo_id}' not found (inferred from error).")
                    if not create_repo_if_not_exists:
                        return (f"Error: ModelScope repository '{repo_id}' does not exist and 'Create Repo If Not Exists' is False.",)
                    # repo_actually_exists remains False, so creation logic will proceed
                else:
                    # Not a "not found" error, so propagate this error
                    return (f"Error checking ModelScope repository '{repo_id}': {type(e_repo_check).__name__} - {str(e_repo_check)}",)
            
            if not repo_actually_exists and create_repo_if_not_exists:
                print(f"MSLoraUploader: Creating repository '{repo_id}' with visibility='{visibility_str}'...")
                try:
                    api.create_model(
                        model_id=repo_id,
                        visibility=ms_visibility,
                        license=ms_license if ms_license else Licenses.APACHE_2_0, # Default if "Other" or mapping failed
                        chinese_name=chinese_name if chinese_name else None,
                    )
                    print(f"MSLoraUploader: Repository '{repo_id}' created successfully.")
                except Exception as e_create:
                    return (f"Error creating ModelScope repository '{repo_id}': {str(e_create)}",)
            elif repo_actually_exists and create_repo_if_not_exists:
                 print(f"MSLoraUploader: Repository '{repo_id}' exists. Proceeding with upload.")
                 # Metadata update for existing repo is not explicitly handled here,
                 # assuming upload_folder will go to the existing repo.

            print(f"MSLoraUploader: Uploading contents of '{temp_upload_dir}' to '{repo_id}' (branch: {revision}, path_in_repo: '{path_in_repo or '/'}')...")
            api.upload_folder(
                repo_id=repo_id,
                folder_path=temp_upload_dir,
                path_in_repo=path_in_repo.strip("/"),
                commit_message=commit_message,
                revision=revision,
            )

            uploaded_url = f"https://www.modelscope.cn/models/{repo_id}/summary"
            success_message = f"Successfully uploaded files to ModelScope repository: {uploaded_url}"
            if path_in_repo:
                success_message += f" (Files are in subfolder: {path_in_repo.strip('/')})"
            print(f"MSLoraUploader: {success_message}")
            return (success_message,)

        except Exception as e:
            error_msg = f"ModelScope operation error: {str(e)}"
            print(f"MSLoraUploader: {error_msg}")
            return (error_msg,)
        finally:
            if os.path.exists(temp_upload_dir):
                try:
                    shutil.rmtree(temp_upload_dir)
                    print(f"MSLoraUploader: Cleaned up temporary directory '{temp_upload_dir}'.")
                except Exception as e_cleanup:
                    print(f"MSLoraUploader: Warning - Failed to clean temp dir '{temp_upload_dir}': {str(e_cleanup)}")

# --- ComfyUI Node Registration ---
NODE_CLASS_MAPPINGS = {
    "HuggingFaceLoraUploader": HuggingFaceLoraUploader,
    "ModelScopeLoraUploader": ModelScopeLoraUploader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HuggingFaceLoraUploader": "Hugging Face LoRA Uploader",
    "ModelScopeLoraUploader": "ModelScope LoRA Uploader (HTTP)"
}

# --- Startup Logging ---
print("--------------------------------------------------------------")
print("--- ComfyUI LoRA Uploaders Node Pack (HTTP for MS) Loaded ---")
print("--- Available Uploaders: HuggingFace, ModelScope (HTTP) ---")
if SHARED_LORA_FILES_LIST[0].startswith("None (No LoRAs found"):
    print("--- INFO: No LoRA files detected by ComfyUI.")
    print("---       Please check LoRA model paths in ComfyUI.")
else:
    actual_lora_count = len(SHARED_LORA_FILES_LIST) -1 if SHARED_LORA_FILES_LIST[0] == "None" else len(SHARED_LORA_FILES_LIST)
    if actual_lora_count > 0: print(f"--- INFO: Detected {actual_lora_count} LoRA(s).")
    else: print("--- INFO: No LoRA files detected by ComfyUI.")
print("--------------------------------------------------------------")

