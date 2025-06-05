import base64
from PIL import Image
from typing import List, Dict


class Protocol:
    def __init__(self, name, params):
        self.name = name
        self.params = params

        self.width = getattr(params, "width", "auto")
        self.width = int(self.width) if self.width != "auto" else self.width
        self.height = getattr(params, "height", "auto")
        self.height = int(self.height) if self.height != "auto" else self.height

        self.actors: List[Actor] = []
        self.pictures: List[Picture] = []
        self.draws: List[Draw] = []
        self.comments: Dict[int, List[Comment]] = {}

    def __str__(self):
        return self.dump()

    def add(self, declaration):
        if isinstance(declaration, Actor):
            self.actors.append(declaration)
        elif isinstance(declaration, Draw):
            self.draws.append(declaration)
        elif isinstance(declaration, Picture):
            self.pictures.append(declaration)
        elif isinstance(declaration, Comment):
            if len(self.draws) not in self.comments:
                self.comments[len(self.draws)] = [declaration]
            else:
                self.comments[len(self.draws)].append(declaration)
        else:
            raise ValueError("Unknown declaration")

    def dump(self):
        s = f"protocol {self.name}(width={self.width}, height={self.height})\n\n"

        def dump(obj):
            prefix = suffix = ""
            if obj.prefix_comment:
                prefix = obj.prefix_comment.dump() + "\n"
            if obj.suffix_comment:
                suffix = " " + obj.suffix_comment.dump()
            return f"{prefix}{obj.dump()}{suffix}"

        for picture in self.pictures:
            s += f"{dump(picture)}\n"
        s += "\n"

        for actor in self.actors:
            s += f"{dump(actor)}\n"
        s += "\n"

        for index, draw in enumerate(self.draws):
            if index in self.comments:
                for comment in self.comments[index]:
                    s += f"{comment.dump()}\n\n"
            s += f"{dump(draw)}\n\n"

        if len(self.draws) in self.comments:
            for i, c in enumerate(self.comments[len(self.draws)]):
                if i == 0:
                    s += f"{c.dump()}\n"
                else:
                    s += f"\n{c.dump()}\n"

        return s

    def preprocess(self, cache=False):
        # remove duplicates
        new_actors = []
        for actor in self.actors:
            if actor not in new_actors:
                new_actors.append(actor)
        self.actors = new_actors

        # check if all draws' actors are in the actors list
        for draw in self.draws:
            if draw.src not in self.actors:
                self.actors.append(Actor(draw.src, Params()))
            if draw.dst not in self.actors:
                self.actors.append(Actor(draw.dst, Params()))

        from .svg import precaculate
        proto_size = precaculate(self, cache=cache)
        self.width = proto_size[0] if self.width == "auto" else self.width
        self.height = proto_size[1] if self.height == "auto" else self.height


class Params:
    def __init__(self, params=[]):
        for key, value in params:
            setattr(self, key, value)

    def __str__(self):
        return str(vars(self))

    def dump(self):
        s = ""
        for index, data in enumerate(vars(self)):
            if index != 0:
                s += ", "
            s += f"{data[0]}={data[1]}"
        return s


class Message:
    def __init__(self, text=""):
        self.text = text

    def dump(self):
        return f'"{self.text}"'

    def escape(self):
        text = self.text
        text = text.replace("\\\\", "\\")
        text = text.replace("\\n", "\n")
        text = text.replace('\\"', '"')
        return text

    def __str__(self):
        return f'"{self.text}"'


class Draw:
    def __init__(self, src, dst, larrow, rarrow, text, params):
        self.prefix_comment = None
        self.suffix_comment = None
        self.src = src
        self.dst = dst
        self.larrow = larrow
        self.rarrow = rarrow
        self.message = Message(text)
        self.params = Params(params)

        self.gridy = getattr(self.params, "gridy", 'auto')
        self.gridy = int(self.gridy) if self.gridy != 'auto' else self.gridy

        self.width = getattr(self.params, "width", None)
        self.height = getattr(self.params, "height", None)
        if self.height == None:
            if self.src == self.dst:
                self.height = 9
            else:
                self.height = 6

        self.line_style = getattr(self.params, "line_style", None)
        self.arrow_style = getattr(self.params, "arrow_style", None)
        self.arrowl_style = getattr(self.params, "arrowl_style", None)
        self.arrowr_style = getattr(self.params, "arrowr_style", None)

    def __str__(self):
        return f"Draw: {self.src} {self.larrow} {self.rarrow} {self.dst} {self.message} {str(self.params)}"

    def dump_attrs(self):
        s = f"gridy={self.gridy}"
        if getattr(self, "width", None):
            s += f", width={self.width}"
        if getattr(self, "height", None):
            s += f", height={self.height}"
        if getattr(self, "line_style", None):
            s += f", line_style={self.line_style}"
        if getattr(self, "arrow_style", None):
            s += f", arrow_style={self.arrow_style}"
        else:
            if getattr(self, "arrowl_style", None):
                s += f", arrowl_style={self.arrowl_style}"
            if getattr(self, "arrowr_style", None):
                s += f", arrowr_style={self.arrowr_style}"
        return s

    def dump(self):
        def msg_dump():
            if "\n" in self.message.text:
                return f"{self.message.dump()}"
            else:
                return f"    {self.message.dump()}"
        if self.src == self.dst:
            return f"{self.src} ({self.dump_attrs()}):\n{msg_dump()}"
        else:
            return f"{self.src}{self.larrow}{self.rarrow}{self.dst} ({self.dump_attrs()}):\n{msg_dump()}"


class Actor:
    def __init__(self, name: str, params: Params):
        self.prefix_comment = None
        self.suffix_comment = None
        self.name = name
        self.params = params
        self.gridx = getattr(params, "gridx", 'auto')
        self.gridx = int(self.gridx) if self.gridx != 'auto' else self.gridx

    def __eq__(self, value):
        if isinstance(value, Actor):
            return value.name == self.name
        elif isinstance(value, str):
            return value == self.name
        else:
            return False

    def __ne__(self, value):
        return not self.__eq__(value)

    def __str__(self):
        return f"Actor: {self.name} {str(self.params)}"

    def __hash__(self):
        return hash(self.name)

    def dump_attrs(self):
        return f"gridx={self.gridx}"

    def dump(self):
        return f"actor {self.name} ({self.dump_attrs()})"


class Picture:
    def __init__(self, name, file, params):
        self.prefix_comment = None
        self.suffix_comment = None
        self.name = name
        self.file = file

        # read as base64
        with open(file, "rb") as f:
            self.binary = f.read()
        self.base64 = base64.b64encode(self.binary).decode("utf-8")

        width = getattr(params, "width", "auto")
        self.width = int(width) if width != "auto" else width
        height = getattr(params, "height", "auto")
        self.height = int(height) if height != "auto" else height

        img = Image.open(self.file)
        self.pixel_size = (img.size[0], img.size[1])

    def __str__(self):
        return f"Picture: {self.name} {self.file} {self.width} {self.height}"

    def dump(self):
        return f'picture {self.name}(width={self.width}, height={self.height}): "{self.file}"'


class Comment:
    def __init__(self, text):
        self.comments = [text]

    def __str__(self):
        return f"Comment: {self.comments}"

    def dump(self):
        return "\n".join([f"# {comment}" for comment in self.comments])

    def add(self, text):
        self.comments.append(text)
