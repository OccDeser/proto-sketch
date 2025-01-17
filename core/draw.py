import sys
from parser import parser
from svg import draw_protocol

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
    draw_protocol(result, cache=False)
