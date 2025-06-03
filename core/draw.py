import os
from argparse import ArgumentParser
from setting import Options
from proto import Protocol
from parser import parser as ProtoParser
from svg import draw_protocol, global_setting


parser = ArgumentParser(description="Draw protocol diagrams from text files.")
parser.add_argument("-f", "--file", type=str, required=True, help="Input file to process")
parser.add_argument("-t", "--format", action="store_true", help="Format the code before processing")
parser.add_argument("-d", "--draw", action="store_true", help="Draw the protocol diagram")
# -o, --output
parser.add_argument("-o", "--output", type=str,
                    help="Output file for the diagram (default: './proto-sketch/output/NAME.svg')")
parser.add_argument("--options", type=str, nargs='*', help="Set options in the format key=value")
parser.add_argument("--options-help", action="store_true",
                    help="Show available options and their default values")
parser.add_argument("--no-cache", action="store_true",
                    help="Disable caching of generated images")
args = parser.parse_args()

# Check if the user requested help for options
if args.options_help:
    print("Available options and their default values:")
    folder_description = {
        "work": "[WORK_FOLDER], The working directory where all files are stored.",
        "cache": "[CACHE_FOLDER], The directory for caching files.",
        "output": "[OUTPUT_FOLDER], The directory for output files.",
        "arrow": "[ARROW_FOLDER], The directory for arrow files."
    }
    for key in folder_description:
        print(f"  folder:{key}={folder_description[key]}")
    exit()

# Get options from command line arguments
options = Options()
if args.options:
    for option in args.options:
        if '=' not in option:
            print(f"Invalid option format: {option}. Use key=value format.")
            exit()
        key, value = option.split('=', 1)
        if key.startswith("folder:"):
            folder_key = key.replace("folder:", "").strip()
            if folder_key in options.folder:
                options.folder[folder_key] = value
            else:
                print(f"Unknown folder option: {key}")
                exit()
        else:
            print(f"Unknown option: {key}")
options.create_folder()
global_setting(options)


# Check if the input file exists
file = args.file
if not file:
    print("No file specified. Use -f or --file to specify the input file.")
    exit()
if not os.path.exists(file):
    print(f"File not found: {file}")
    exit()
with open(file, "r", encoding="utf8") as f:
    psl_code = f.read()

proto: Protocol = ProtoParser.parse(psl_code, debug=False)
if not proto:
    print("Parsing failed")
    exit()

using_cache = not args.no_cache
if args.format:
    proto.preprocess(cache=using_cache)
    formatted_code = proto.dump()
    print(formatted_code)
elif args.draw:
    if args.output:
        output_file = args.output
    else:
        output_file = os.path.join(options.folder["output"], f"{proto.name}.svg")
    draw_protocol(proto, output_file, cache=using_cache)
