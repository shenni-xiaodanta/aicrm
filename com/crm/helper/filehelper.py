"""上传文件通用规则。"""
from pathlib import Path

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_FILES = 10
ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".txt", ".csv",
    ".zip", ".rar", ".7z",
}


def file_suffix(filename):
    """返回小写扩展名，如 .pdf。"""
    return Path((filename or "").strip()).suffix.lower()
