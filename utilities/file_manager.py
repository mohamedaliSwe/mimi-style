import os
from werkzeug.utils import secure_filename


# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ALLOWED_DOC_EXTENSIONS = {"pdf", "doc", "docx", "txt"}


def is_allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def save_file(file, upload_folder, allowed_extensions):
    if not file or file.filename == "":
        return None

    filename = secure_filename(file.filename)

    if not is_allowed_file(filename, allowed_extensions):
        return None

    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)
    file.save(save_path)
    return filename
