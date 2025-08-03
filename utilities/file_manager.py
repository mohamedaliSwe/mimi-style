import os
from werkzeug.utils import secure_filename


# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ALLOWED_DOC_EXTENSIONS = {"pdf", "doc", "docx", "txt"}


def is_allowed_file(filename, allowed_extensions):
    """Check if file has allowed extension"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def save_file(file, upload_folder, allowed_extensions):
    """Save uploaded file to specified folder"""
    try:
        if not file or file.filename == "":
            return None

        filename = secure_filename(file.filename)

        if not is_allowed_file(filename, allowed_extensions):
            return None

        os.makedirs(upload_folder, exist_ok=True)
        save_path = os.path.join(upload_folder, filename)
        file.save(save_path)
        return filename
    except Exception as e:
        return {f"Message": "Error saving file {file_path_or_url}: {str(e)}"}, 500


def delete_file(file_path_or_url):
    """Delete a file from the file system"""
    try:
        file_path = file_path_or_url

        if file_path_or_url.startswith("/uploads/") or file_path_or_url.startswith(
            "uploads/"
        ):
            if file_path_or_url.startswith("/"):
                file_path_or_url = file_path_or_url[1:]

            try:
                from flask import current_app

                app_root = current_app.root_path
            except:
                app_root = os.getcwd()

            file_path = os.path.join(app_root, file_path_or_url)

        if os.path.exists(file_path):
            os.remove(file_path)

            try:
                parent_dir = os.path.dirname(file_path)
                while parent_dir and parent_dir != os.path.dirname(parent_dir):
                    try:
                        os.rmdir(parent_dir)
                        parent_dir = os.path.dirname(parent_dir)
                    except OSError:
                        break
            except:
                pass

            return True
        else:
            return False

    except Exception as e:
        return {f"Message": "Error deleting file {file_path_or_url}: {str(e)}"}, 500
