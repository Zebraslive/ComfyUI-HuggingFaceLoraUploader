import os
from huggingface_hub import HfApi, create_repo
from huggingface_hub.utils import RepositoryNotFoundError, HfHubHTTPError as HuggingFaceHTTPError

class HuggingFaceVideoUploader:
    CATEGORY = "Uploaders/HuggingFace"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status_message",)
    FUNCTION = "upload_video_to_hf"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": "", "multiline": False, "placeholder": "Path to generated video"}),
                "hf_token": ("STRING", {"default": "hf_YOUR_HUGGINGFACE_TOKEN_HERE", "multiline": False}),
                "repo_id": ("STRING", {"default": "username/repo_name", "multiline": False}),
                "commit_message": ("STRING", {"default": "Upload video via ComfyUI", "multiline": True}),
            },
            "optional": {
                "path_in_repo": ("STRING", {"default": "", "multiline": False, "placeholder": "e.g., videos/ (optional)"}),
                "create_repo_if_not_exists": ("BOOLEAN", {"default": True}),
                "private_repo": ("BOOLEAN", {"default": False}),
            }
        }

    def upload_video_to_hf(self, video_path, hf_token, repo_id, commit_message,
                           path_in_repo="", create_repo_if_not_exists=True, private_repo=False):
        if not video_path or not os.path.exists(video_path):
            return (f"Error: Video file not found at '{video_path}'.",)
        if not hf_token or hf_token == "hf_YOUR_HUGGINGFACE_TOKEN_HERE" or not hf_token.startswith("hf_"):
            return ("Error: Hugging Face token is missing, invalid, or is the default placeholder.",)
        if not repo_id or repo_id == "username/repo_name" or "/" not in repo_id:
            return ("Error: Invalid Hugging Face repository ID. Should be 'username/repo_name' or 'org/repo_name'.",)

        print(f"HFVideoUploader: Uploading '{video_path}' to HF repo '{repo_id}'.")
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
                if e_http_info.response.status_code == 401:
                    return (f"Error: HF authentication failed (401) checking repo. Check token.",)
                return (f"Error checking HF repo info for {repo_id}: {str(e_http_info)}",)

            if not repo_exists and create_repo_if_not_exists:
                create_repo(repo_id, token=hf_token, private=private_repo, repo_type="model", exist_ok=True)

            filename_for_repo = os.path.basename(video_path)
            _path_in_repo_cleaned = path_in_repo.strip("/")
            final_path_in_repo = f"{_path_in_repo_cleaned}/{filename_for_repo}" if _path_in_repo_cleaned else filename_for_repo

            api.upload_file(
                path_or_fileobj=video_path,
                path_in_repo=final_path_in_repo,
                repo_id=repo_id,
                repo_type="model",
                commit_message=commit_message,
            )
            uploaded_url = f"https://huggingface.co/{repo_id}/blob/main/{final_path_in_repo.lstrip('/')}"
            success_message = f"Successfully uploaded video to {uploaded_url}"
            print(f"HFVideoUploader: {success_message}")
            return (success_message,)
        except HuggingFaceHTTPError as e_http_upload:
            status_code = e_http_upload.response.status_code
            if status_code == 401:
                return (f"HF auth error (401) during upload. Check token/permissions for '{repo_id}'.",)
            if status_code == 403:
                return (f"HF permission error (403) during upload. Ensure token has write access to '{repo_id}'.",)
            return (f"HF API HTTP error during upload: {str(e_http_upload)} (Status: {status_code})",)
        except Exception as e:
            error_message = f"Unexpected error during Hugging Face op: {str(e)}"
            print(f"HFVideoUploader: {error_message}")
            return (error_message,)

# Registration for ComfyUI
NODE_CLASS_MAPPINGS = {
    "HuggingFaceVideoUploader": HuggingFaceVideoUploader,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "HuggingFaceVideoUploader": "Hugging Face Video Uploader",
}

print("--------------------------------------------------------------")
print("--- ComfyUI Video Uploader Node Loaded ---")
print("--- Available Uploader: HuggingFace ---")
print("--------------------------------------------------------------")
