import sys
import os
import shutil
import base64
from flask import Flask,  request, jsonify, send_from_directory, send_file

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '../core'))

from parser import parser
from setting import Options
from svg import draw_protocol, global_setting, svg_hash_name

options = Options()
options.create_folder()
global_setting(options)

static_dir = os.path.join(current_dir, '../ui/build')
app = Flask(__name__, static_folder=static_dir)

WORKSPACE_DIR = '/workspace'
if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR)

def traverse_workspace(directory):
    items = {}
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            items[item] = {
                "type": "directory",
                "children": traverse_workspace(item_path)
            }
        elif os.path.isfile(item_path):
            items[item] = {'type': "file"}
    return items


def get_code(request):
    code = request.args.get('code')
    if not code:
        return None
    try:
        code = base64.b64decode(code).decode('utf-8')
    except Exception as e:
        return None
    code = code.replace("\r\n", "\n")  # Normalize line endings
    return code


# 路由：渲染 React 的首页
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# 路由：托管静态文件
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(app.static_folder, path)

# GET /draw 接口
@app.route('/draw', methods=['GET'])
def draw():
    code = get_code(request)
    if not code:
        return jsonify({"error": "Missing 'code' parameter"}), 400
    
    proto = parser.parse(code, debug=False)
    if not proto:
        return jsonify({"error": "Parsing failed"}), 400
    
    name = f"{proto.name}.svg"
    outfile = os.path.join(options.folder["output"], name)
    draw_protocol(proto, outfile)
    
    timestamp = os.path.getmtime(outfile)
    encodedName = base64.b64encode(name.encode('utf-8')).decode('utf-8')
    return jsonify({"link": f"/output?name={encodedName}&ts={timestamp}"})
    

# GET /format 接口
@app.route('/format', methods=['GET'])
def format_code():
    code = get_code(request)
    if not code:
        return jsonify({"error": "Missing 'code' parameter"}), 400
    
    proto = parser.parse(code, debug=False)
    if not proto:
        return jsonify({"error": "Parsing failed"}), 400
    
    proto.preprocess()
    result = {"result": proto.dump()}
    return jsonify(result)

# GET /output 接口
@app.route('/output', methods=['GET'])
def output():
    encodedName = request.args.get('name')
    if not encodedName:
        return jsonify({"error": "Missing 'name' parameter"}), 400
    
    try:
        name = base64.b64decode(encodedName).decode('utf-8')
    except Exception as e:
        return jsonify({"error": "Invalid base64 name"}), 400
    
    return send_file(os.path.join("..", options.folder["output"], name))


# GET /workspace 接口
@app.route('/workspace', methods=['GET'])
def get_workspace():
    # 获取工作区目录下的所有文件和子目录
    return jsonify(traverse_workspace(WORKSPACE_DIR))

# GET /workspace/<path:filename> 接口
@app.route('/workspace/<path:filename>', methods=['GET'])
def get_workspace_file(filename):
    # 获取工作区目录下的指定文件
    file_path = os.path.join(WORKSPACE_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    if os.path.isdir(file_path):
        return jsonify({"error": "Cannot access directory"}), 400
    
    return send_file(file_path)

# GET /workspace/create/<path:folder> 接口
@app.route('/workspace/create/<path:folder>', methods=['GET'])
def create_workspace_file(folder):
    # 创建工作区目录下的指定文件夹
    folder_path = os.path.join(WORKSPACE_DIR, folder)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return jsonify({"message": "Folder created successfully"}), 201

# GET /workspace/upload/<path:filename> 接口
@app.route('/workspace/upload/<path:filename>', methods=['GET'])
def upload_workspace_file(filename):
    # 上传文件到工作区目录
    file_path = os.path.join(WORKSPACE_DIR, filename)
    file_dir = os.path.dirname(file_path)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    if os.path.isfile(file_path) and not os.access(file_path, os.W_OK):
        return jsonify({"error": "File already exists and is not writable"}), 403

    code = get_code(request)
    if not code:
        return jsonify({"error": "Missing 'code' parameter"}), 400
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
    except Exception as e:
        return jsonify({"error": f"Failed to write file: {str(e)}"}), 500
    return jsonify({"message": "File uploaded successfully"}), 201

# GET /workspace/delete/<path:path> 接口
@app.route('/workspace/delete/<path:path>', methods=['GET'])
def delete_workspace_file(path):
    file_path = os.path.join(WORKSPACE_DIR, path)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
    except Exception as e:
        return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500
    return jsonify({"message": "File deleted successfully"}), 200

# GET /workspace/rename/ 接口
def rename_workspace_file():
    old_path = request.args.get('old')
    new_path = request.args.get('new')
    if not old_path or not new_path:
        return jsonify({"error": "Missing 'old' or 'new' parameter"}), 400
    
    old_file_path = os.path.join(WORKSPACE_DIR, old_path)
    new_file_path = os.path.join(WORKSPACE_DIR, new_path)
    
    if not os.path.exists(old_file_path):
        return jsonify({"error": "Old file not found"}), 404
    
    try:
        os.rename(old_file_path, new_file_path)
    except Exception as e:
        return jsonify({"error": f"Failed to rename file: {str(e)}"}), 500
    return jsonify({"message": "File renamed successfully"}), 200

# 启动应用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
