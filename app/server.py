import sys
import os
import base64
from flask import Flask, Response, request, jsonify, send_from_directory, send_file

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
    encodedCode = request.args.get('code')
    if not encodedCode:
        return jsonify({"error": "Missing 'code' parameter"}), 400
    
    try:
        code = base64.b64decode(encodedCode).decode('utf-8')
    except Exception as e:
        return jsonify({"error": "Invalid base64 code"}), 400
    
    code = code.replace("\r\n", "\n") # Normalize line endings
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
    encodedCode = request.args.get('code')
    if not encodedCode:
        return jsonify({"error": "Missing 'code' parameter"}), 400
    
    try:
        code = base64.b64decode(encodedCode).decode('utf-8')
    except Exception as e:
        return jsonify({"error": "Invalid base64 code"}), 400
    
    code = code.replace("\r\n", "\n") # Normalize line endings
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


# 启动应用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
