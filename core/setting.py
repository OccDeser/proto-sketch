import os

####################################
# Default setting for the project
####################################

# Picture Settings
PIC_DPI = 600
PIC_ZOOM = 8
PIC_MARGIN = 3

# Actor Settings
ACTOR_MIN_WIDTH = 8
ACTOR_MIN_SPAN = 25
ACTOR_MARGIN = 3

# Action Settings
ACTION_MIN_WIDTH = 6
ACTION_MARGIN = 3

# Message Settings
MSG_LINE_HEIGHT = 3
MSG_BOTTOM_MARGIN_PIXEL = 2

# Protocol Settings
PROTO_MARGIN = 3
END_MARGIN = 1
END_HEIGHT = 1
END_WIDTH = 20
END_ZOOM = 0.2
LINE_WIDTH = 1
GRID_SIZE = 10

# Folder Settings
ARROW_FOLDER = "arrow"
CACHE_FOLDER = ".proto-sketch/cache"
OUTPUT_FOLDER = ".proto-sketch/output"


####################################
# Setting options
####################################
class Options:
    def __init__(self):
        self.pic = {
            "dpi": PIC_DPI,
            "zoom": PIC_ZOOM,
            "margin": PIC_MARGIN
        }
        self.actor = {
            "min_width": ACTOR_MIN_WIDTH,
            "min_span": ACTOR_MIN_SPAN,
            "margin": ACTOR_MARGIN
        }
        self.action = {
            "min_width": ACTION_MIN_WIDTH,
            "margin": ACTION_MARGIN
        }
        self.message = {
            "line_height": MSG_LINE_HEIGHT,
            "bottom_margin_pixel": MSG_BOTTOM_MARGIN_PIXEL
        }
        self.protocol = {
            "margin": PROTO_MARGIN,
            "end_margin": END_MARGIN,
            "end_height": END_HEIGHT,
            "end_width": END_WIDTH,
            "end_zoom": END_ZOOM,
            "line_width": LINE_WIDTH,
            "grid_size": GRID_SIZE
        }
        self.folder = {
            "arrow": "arrow",
            "cache": CACHE_FOLDER,
            "output": OUTPUT_FOLDER
        }

    def create_folder(self):
        for folder in self.folder.values():
            if not os.path.exists(folder):
                os.makedirs(folder)

    def set_pic(self, dpi=PIC_DPI, zoom=PIC_ZOOM, margin=PIC_MARGIN):
        self.pic["dpi"] = dpi
        self.pic["zoom"] = zoom
        self.pic["margin"] = margin

    def set_actor(self, min_width=ACTOR_MIN_WIDTH, min_span=ACTOR_MIN_SPAN, margin=ACTOR_MARGIN):
        self.actor["min_width"] = min_width
        self.actor["min_span"] = min_span
        self.actor["margin"] = margin

    def set_action(self, min_width=ACTION_MIN_WIDTH, margin=ACTION_MARGIN):
        self.action["min_width"] = min_width
        self.action["margin"] = margin

    def set_message(self, line_height=MSG_LINE_HEIGHT, bottom_margin_pixel=MSG_BOTTOM_MARGIN_PIXEL):
        self.message["line_height"] = line_height
        self.message["bottom_margin_pixel"] = bottom_margin_pixel

    def set_protocol(self, margin=PROTO_MARGIN, end_margin=END_MARGIN, end_height=END_HEIGHT, end_width=END_WIDTH, end_zoom=END_ZOOM, line_width=LINE_WIDTH, grid_size=GRID_SIZE):
        self.protocol["margin"] = margin
        self.protocol["end_margin"] = end_margin
        self.protocol["end_height"] = end_height
        self.protocol["end_width"] = end_width
        self.protocol["end_zoom"] = end_zoom
        self.protocol["line_width"] = line_width
        self.protocol["grid_size"] = grid_size

    def set_folder(self, arrow="arrow", cache=CACHE_FOLDER, output=OUTPUT_FOLDER):
        self.folder["arrow"] = arrow
        self.folder["cache"] = cache
        self.folder["output"] = output
