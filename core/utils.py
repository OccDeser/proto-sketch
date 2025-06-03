from pathlib import Path
from importlib.resources import files


def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        base = files("proto_sketch")
        return str(base / "data" / relative_path)
    except Exception:
        return str(Path(__file__).parent / "data" / relative_path)