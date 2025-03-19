import os
import svgwrite
import base64
from typing import Tuple
from math import floor
from hashlib import sha256
from proto import Actor, Draw, Picture, Message, Protocol, Params
from setting import Options
from PIL import Image

import matplotlib.pyplot as plt
plt.rcParams['font.family'] = ['Times New Roman','SimSun']
# plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['axes.unicode_minus'] = False

"""Picture Settings"""
PIC_DPI = None
PIC_ZOOM = None
PIC_MARGIN = None

"""Actor Settings"""
ACTOR_MIN_WIDTH = None
ACTOR_MIN_SPAN = None
ACTOR_MARGIN = None

"""Action Settings"""
ACTION_MIN_WIDTH = None
ACTION_X_MARGIN = None
ACTION_Y_MARGIN = None

"""Message Settings"""
MSG_LINE_HEIGHT = None
MSG_BOTTOM_MARGIN_PIXEL = None

"""Protocol Settings"""
PROTO_MARGIN = None
END_MARGIN = None
END_HEIGHT = None
END_WIDTH = None
END_ZOOM = None
LINE_WIDTH = None
GRID_SIZE = None

"""folder settings"""
ARROW_FOLDER = None
CACHE_FOLDER = None


def global_setting(options: Options):
    """Picture Settings"""
    global PIC_DPI, PIC_ZOOM, PIC_MARGIN
    PIC_DPI = options.pic['dpi']
    PIC_ZOOM = options.pic['zoom']
    PIC_MARGIN = options.pic['margin']
    """Actor Settings"""
    global ACTOR_MIN_WIDTH, ACTOR_MIN_SPAN, ACTOR_MARGIN
    ACTOR_MIN_WIDTH = options.actor['min_width']
    ACTOR_MIN_SPAN = options.actor['min_span']
    ACTOR_MARGIN = options.actor['margin']
    """Action Settings"""
    global ACTION_MIN_WIDTH, ACTION_X_MARGIN, ACTION_Y_MARGIN
    ACTION_MIN_WIDTH = options.action['min_width']
    ACTION_X_MARGIN = options.action['x_margin']
    ACTION_Y_MARGIN = options.action['y_margin']
    """Message Settings"""
    global MSG_LINE_HEIGHT, MSG_BOTTOM_MARGIN_PIXEL
    MSG_LINE_HEIGHT = options.message['line_height']
    MSG_BOTTOM_MARGIN_PIXEL = options.message['bottom_margin_pixel']
    """Protocol Settings"""
    global PROTO_MARGIN, END_MARGIN, END_HEIGHT, END_WIDTH, END_ZOOM, LINE_WIDTH, GRID_SIZE
    PROTO_MARGIN = options.protocol['margin']
    END_MARGIN = options.protocol['end_margin']
    END_HEIGHT = options.protocol['end_height']
    END_WIDTH = options.protocol['end_width']
    END_ZOOM = options.protocol['end_zoom']
    LINE_WIDTH = options.protocol['line_width']
    GRID_SIZE = options.protocol['grid_size']
    """folder settings"""
    global ARROW_FOLDER, CACHE_FOLDER
    ARROW_FOLDER = options.folder['arrow']
    CACHE_FOLDER = options.folder['cache']


def svg_hash_name(component):
    return sha256(str(component).encode()).hexdigest()

def trim_image(input_path, output_path):
    img = Image.open(input_path)
    img = img.convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        trimmed_img = img.crop(bbox)
        trimmed_img.save(output_path)

def create_message_picture(msg: Message, cache=True) -> Picture:
    sid = svg_hash_name(msg)
    png_path = f"{CACHE_FOLDER}/{sid}.png"

    if not cache or not os.path.exists(png_path):
        fig, ax = plt.subplots(figsize=(0.01, 0.01))
        ax.text(0.5, 0.5, msg.escape(), fontsize=20, ha='center', va='top', transform=ax.transAxes)
        ax.axis('off')
        fig.savefig(png_path, dpi=PIC_DPI, transparent=True, bbox_inches='tight', pad_inches=1)
        plt.close(fig)
        trim_image(png_path, png_path)

    msg_pic = Picture(sid, png_path, Params([]))
    msg_pic.pixel_size = (floor(msg_pic.pixel_size[0] / PIC_ZOOM),
                          floor(msg_pic.pixel_size[1] / PIC_ZOOM))
    return msg_pic


def create_actor_picture(actor: Actor, gsize=10, cache=True):
    # create message picture
    actor_pic = create_message_picture(Message(actor.name), cache=cache)
    # caculate size
    size = [floor(actor_pic.pixel_size[0] / gsize) + PIC_MARGIN,
            floor(actor_pic.pixel_size[1] / gsize) + PIC_MARGIN]
    size[0] = size[0] if size[0] % 2 == 0 else size[0] + 1
    size[0] = size[0] if size[0] > ACTOR_MIN_WIDTH else ACTOR_MIN_WIDTH
    return tuple(size), actor_pic


def create_action_picture(draw: Draw, gsize=10, cache=True):
    assert draw.src == draw.dst, "Action picture only support self action"
    # create message picture
    action_pic = create_message_picture(draw.message, cache=cache)
    # caculate size
    size = [floor(action_pic.pixel_size[0] / gsize) + PIC_MARGIN,
            floor(action_pic.pixel_size[1] / gsize) + PIC_MARGIN]
    size[0] = size[0] if size[0] % 2 == 0 else size[0] + 1
    size[0] = size[0] if size[0] > ACTION_MIN_WIDTH else ACTION_MIN_WIDTH
    return tuple(size), action_pic


def create_arrow_picture(draw: Draw, gsize=10, cache=True):
    assert draw.src != draw.dst, "Arrow picture only support arrow action"
    # create message picture
    arrow_pic = create_message_picture(draw.message, cache=cache)
    # caculate size
    size = (floor(arrow_pic.pixel_size[0] / gsize) + 1, MSG_LINE_HEIGHT)
    return size, arrow_pic


def draw_picture(pic: Picture, pixel_size: Tuple[int, int]) -> str:
    # draw picture with the pixel size
    sid = svg_hash_name(pic)
    dwg = svgwrite.Drawing(f"{sid}.svg", profile="tiny", size=pixel_size)
    png_url = f"data:image/png;base64,{pic.base64}"
    dwg.add(dwg.image(href=png_url, insert=(0, 0), size=pixel_size))
    svg_base64 = base64.b64encode(dwg.tostring().encode()).decode("utf-8")
    return f"data:image/svg+xml;base64,{svg_base64}"


def draw_actor(actor, pic: Picture, pixel_size: Tuple[int, int]) -> str:
    # create svg
    sid = svg_hash_name(actor)
    dwg = svgwrite.Drawing(f"{sid}.svg", profile="tiny", size=pixel_size)
    # calculate image insert position
    width, height = pixel_size
    pic_width, pic_height = pic.pixel_size
    insert = (floor((width-pic_width)/2), floor((height-pic_height)/2)+PIC_MARGIN/2)
    # add image
    png_url = f"data:image/png;base64,{pic.base64}"
    dwg.add(dwg.image(href=png_url, insert=insert, size=pic.pixel_size))
    svg_base64 = base64.b64encode(dwg.tostring().encode()).decode("utf-8")
    return f"data:image/svg+xml;base64,{svg_base64}"


def draw_action(action, pic: Picture, pixel_size: Tuple[int, int]) -> str:
    # create svg
    sid = svg_hash_name(action)
    dwg = svgwrite.Drawing(f"{sid}.svg", profile="tiny", size=pixel_size)
    width, height = pixel_size
    pic_width, pic_height = pic.pixel_size
    insert = (floor((width-pic_width)/2), round((height-pic_height)/2))
    # add image
    png_url = f"data:image/png;base64,{pic.base64}"
    dwg.add(dwg.image(href=png_url, insert=insert, size=pic.pixel_size))
    svg_base64 = base64.b64encode(dwg.tostring().encode()).decode("utf-8")
    return f"data:image/svg+xml;base64,{svg_base64}"


def draw_arrow(arrow: Draw, pic: Picture, pixel_size: Tuple[int, int]) -> str:
    # create svg
    sid = svg_hash_name(arrow)
    dwg = svgwrite.Drawing(f"{sid}.svg", profile="tiny", size=pixel_size)
    # add message image
    png_url = f"data:image/png;base64,{pic.base64}"
    msg_insert = (floor((pixel_size[0] - pic.pixel_size[0])/2),
                  floor((pixel_size[1] - pic.pixel_size[1])/2))
    dwg.add(dwg.image(href=png_url, insert=msg_insert, size=pic.pixel_size))

    # add line
    # TODO: costomize line style
    arrow_width = 10
    arrow_height = 8
    line_y = msg_insert[1] + pic.pixel_size[1] + MSG_BOTTOM_MARGIN_PIXEL
    x0 = 0
    x1 = pixel_size[0]
    if arrow.larrow != '-':
        x0 = arrow_width/2
    if arrow.rarrow != '-':
        x1 -= arrow_width/2
    dwg.add(dwg.line(start=(x0, line_y), end=(x1, line_y),
                     stroke="black", stroke_width=LINE_WIDTH))

    def add_arrow(direction, arrow_x):
        if direction == 'left':
            arrow_svg = f"{ARROW_FOLDER}/default/left.svg"
        else:
            arrow_svg = f"{ARROW_FOLDER}/default/right.svg"
        with open(arrow_svg, "rb") as f:
            arrow_svg = f.read()
        arrow_svg = base64.b64encode(arrow_svg).decode("utf-8")
        arrow_y = line_y - arrow_height/2
        arrow_insert = (arrow_x, arrow_y)
        arrow_url = f"data:image/svg+xml;base64,{arrow_svg}"
        dwg.add(dwg.image(href=arrow_url, insert=arrow_insert, size=(arrow_width, arrow_height)))

    # add arrow
    # TODO: costomize arrow style
    if arrow.larrow == '<':
        add_arrow('left', 0)
    elif arrow.larrow == '>':
        add_arrow('right', 0)
    if arrow.rarrow == '<':
        add_arrow('left', pixel_size[0] - arrow_width)
    elif arrow.rarrow == '>':
        add_arrow('right', pixel_size[0] - arrow_width)

    svg_base64 = base64.b64encode(dwg.tostring().encode()).decode("utf-8")
    return f"data:image/svg+xml;base64,{svg_base64}"


def draw_protocol(proto: Protocol, outfile: str, cache=True):
    proto.preprocess()

    # create svg
    pixel_width = proto.width * GRID_SIZE
    pixel_height = proto.height * GRID_SIZE
    pixel_size = (pixel_width, pixel_height)
    dwg = svgwrite.Drawing(outfile, profile="tiny", size=pixel_size)

    # draw actors
    actor_height = 0
    proto_ypixel = PROTO_MARGIN * GRID_SIZE
    actor_xpixels = {actor.name: actor.gridx * GRID_SIZE for actor in proto.actors}
    for actor in proto.actors:
        actor_size, actor_pic = create_actor_picture(actor, gsize=GRID_SIZE, cache=cache)
        pixel_size = (actor_size[0] * GRID_SIZE, actor_size[1] * GRID_SIZE)
        actor_height = pixel_size[1]
        actor_xpixels[actor.name] += pixel_size[0] / 2
        actor_svg = draw_actor(actor, actor_pic, pixel_size)
        actor_xpixel = actor.gridx * GRID_SIZE
        insert = (actor_xpixel, proto_ypixel)
        # add rectange
        # TODO: costomize action style
        dwg.add(dwg.rect(insert=insert, size=pixel_size,
                         fill="white", stroke="black", stroke_width=LINE_WIDTH))
        dwg.add(dwg.image(href=actor_svg, insert=insert, size=pixel_size))

    # draw
    proto_ypixel += actor_height
    for draw in proto.draws:
        if draw.src == draw.dst:
            action_size, action_pic = create_action_picture(draw, gsize=GRID_SIZE, cache=cache)
            pixel_size = (action_size[0] * GRID_SIZE, action_size[1] * GRID_SIZE)
            action_svg = draw_action(draw, action_pic, pixel_size)
            insert_xpixel = floor(actor_xpixels[draw.src] - pixel_size[0] / 2)
            insert_ypixel = proto_ypixel + ACTION_Y_MARGIN * GRID_SIZE
            insert = (insert_xpixel, insert_ypixel)
            # add rectange
            # TODO: costomize action style
            dwg.add(dwg.rect(insert=insert, size=pixel_size,
                             fill="white", stroke="black", stroke_width=LINE_WIDTH, rx=10, ry=10))
            dwg.add(dwg.image(href=action_svg, insert=insert, size=pixel_size))
            proto_ypixel = insert[1] + pixel_size[1]
        else:
            arrow_reverse = {'<': '>', '>': '<', '-': '-'}
            if actor_xpixels[draw.src] > actor_xpixels[draw.dst]:
                draw.src, draw.dst = draw.dst, draw.src
                draw.larrow, draw.rarrow = draw.rarrow, draw.larrow
                draw.larrow = arrow_reverse[draw.larrow]
                draw.rarrow = arrow_reverse[draw.rarrow]
            draw_size, draw_pic = create_arrow_picture(draw, gsize=GRID_SIZE, cache=cache)
            pixel_size = (actor_xpixels[draw.dst] -
                          actor_xpixels[draw.src], draw_size[1] * GRID_SIZE)
            arrow_svg = draw_arrow(draw, draw_pic, pixel_size)
            insert = (actor_xpixels[draw.src], proto_ypixel)
            dwg.add(dwg.image(href=arrow_svg, insert=insert, size=pixel_size))
            proto_ypixel += pixel_size[1]

    # draw line
    # TODO: costomize line style
    proto_ypixel += END_MARGIN * GRID_SIZE
    y0 = PROTO_MARGIN * GRID_SIZE
    y1 = proto_ypixel
    for actor in proto.actors:
        x = actor_xpixels[actor.name]
        dwg.add(dwg.line(start=(x, y0), end=(x, y1), stroke="black", stroke_width=LINE_WIDTH))
    line_elements = dwg.elements[-len(proto.actors):]
    dwg.elements = line_elements + dwg.elements[:-len(proto.actors)]

    # draw end rect
    # TODO: costomize end style
    for actor in proto.actors:
        x = actor_xpixels[actor.name]
        width = END_WIDTH * GRID_SIZE * END_ZOOM
        height = END_HEIGHT * GRID_SIZE * END_ZOOM
        rect_insert = (x - width / 2, y1)
        dwg.add(dwg.rect(insert=rect_insert, size=(width, height),
                         fill="black", stroke="black", stroke_width=LINE_WIDTH))

    dwg.save()


def precaculate(proto: Protocol, cache=True):
    actor_heights = []
    item_widths = {}
    actors = []

    # Caculate actor size
    for actor in proto.actors:
        size, _ = create_actor_picture(actor, gsize=GRID_SIZE, cache=cache)
        actor_heights.append(size[1])
        item_widths[actor.name] = [size[0]]
        actors.append(actor.name)
    actor_height = max(actor_heights)

    # Caculate action size
    proto_height = PROTO_MARGIN + actor_height
    for draw in proto.draws:
        if draw.src == draw.dst:
            size, _ = create_action_picture(draw, gsize=GRID_SIZE, cache=cache)
            item_widths[draw.src].append(size[0])
        else:
            size, _ = create_arrow_picture(draw, gsize=GRID_SIZE, cache=cache)
            if actors.index(draw.src) < actors.index(draw.dst):
                item = f"{draw.src}->{draw.dst}"
            else:
                item = f"{draw.dst}->{draw.src}"
            if item not in item_widths:
                item_widths[item] = []
            item_widths[item].append(size[0])
        # set protocol height
        if draw.gridy != "auto" and draw.gridy > proto_height:
            proto_height = draw.gridy
        proto_height += size[1]
    proto_height += END_MARGIN + END_HEIGHT + PROTO_MARGIN

    # Caculate protocol size
    proto_width = 0
    for i in range(len(actors)):
        if i == 0:
            item1 = actors[i]
            item1_width = max(item_widths[item1])
            proto_width = PROTO_MARGIN + floor(item1_width/2)
        else:
            item1 = actors[i-1]
            item2 = f"{actors[i-1]}->{actors[i]}"
            item3 = actors[i]

            actor1_width = item_widths[item1][0]
            actor2_width = item_widths[item3][0]
            action_widths = [0]+item_widths[item1][1:] + item_widths[item3][1:]

            if item2 in item_widths:
                message_width = max(item_widths[item2])
            else:
                message_width = 0
            action_width = floor(max(action_widths) / 2) + ACTION_X_MARGIN
            actor_width = ACTOR_MARGIN + floor(actor1_width/2 + actor2_width/2)

            span = max([actor_width, action_width, message_width, ACTOR_MIN_SPAN])
            proto_width += span

        # set actor gridx
        if i == 0:
            proto.actors[i].gridx = PROTO_MARGIN
        else:
            proto.actors[i].gridx = proto_width - floor(actor2_width/2)

        if i == len(actors) - 1:
            item1 = actors[i]
            item1_width = max(item_widths[item1])
            proto_width += PROTO_MARGIN + floor(item1_width/2)

    return (proto_width, proto_height)
