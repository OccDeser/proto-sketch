import sys
from parser import parser
from setting import Options
from svg import draw_protocol, global_setting

options = Options()
options.create_folder()
global_setting(options)

file = sys.argv[1]

with open(file, "r", encoding="utf8") as f:
    processed = f.read()

result = parser.parse(processed, debug=False)

if not result:
    print("Parsing failed")
    exit()

if "proto" in file:
    result.preprocess()
    with open(file.replace("proto", "processed"), "w", encoding="utf8") as f:
        f.write(result.dump())
else:
    draw_protocol(result, ".proto-sketch/output/test.svg",cache=False)
