# coding=utf8

# Builtins
import enum
import os
import sys
from io import BytesIO
import base64
from typing import Optional

# Dependencies
import PIL
import PIL.Image, PIL.ImageDraw, PIL.ImageFont

class WidthFittingAlgo(enum.Enum):
    Text_as_is = 0,
    At_least_one_word = 1,
    Manually = 2

def text2image(text, color="#000", bgcolor="#FFF", fontpath=os.path.join("Fonts", "OcrABeckerRus_Lat.otf"), fontsize=20, left_padding=3, right_padding=3,
               top_padding=2, bottom_padding=2, width_fit_algo: WidthFittingAlgo = WidthFittingAlgo.Text_as_is, width_manual: Optional[int] = None
               ) -> PIL.Image:

    font = PIL.ImageFont.load_default() if fontpath is None else PIL.ImageFont.truetype(fontpath, fontsize)

    if width_fit_algo == WidthFittingAlgo.Text_as_is:
        lines = text.splitlines()
        max_line = max(lines, default="", key=lambda l: len(l))
        max_line_size = font.getbbox(max_line)
        width = left_padding + max_line_size[2] - max_line_size[0] + right_padding
    elif width_fit_algo == WidthFittingAlgo.At_least_one_word:
        max_len_word = max(text.split(), default="", key=lambda w: len(w))
        max_len_word_size = font.getbbox(max_len_word)
        width = left_padding + max_len_word_size[2] - max_len_word_size[0] + right_padding
    elif width_fit_algo == WidthFittingAlgo.Manually:
        if width_manual is not None:
            width = width_manual
        else:
            raise AttributeError(f'Width fit algo set to manual, but manual width not supplied')
    else:
        raise AttributeError(f"Couldn't find {width_fit_algo.name}")

    NEWLINE_REPLACEMENT_CHARACTER = u'\uFFFD'
    NEWLINE_REPLACEMENT_STRING = ' ' + NEWLINE_REPLACEMENT_CHARACTER + ' '
    text = text.replace('\n', NEWLINE_REPLACEMENT_STRING)

    lines = []
    line = u""

    for word in text.split():
        if word == NEWLINE_REPLACEMENT_CHARACTER:  # give a blank line
            lines.append(line)  # slice the white space in the begining of the line
            lines.append(u"")  # the blank line
            line = u""
        # Try to append current word in line
        elif font.getlength(line + ' ' if line != u'' else '' + word) <= (width - right_padding - left_padding):
            if line == u"":
                line = word
            else:
                line += u' ' + word
        elif len(line) != 0:  # Couldn't append word, try to start a new line
            lines.append(line)
            line = u"" + word
        else:  # Handle too long words
            print(f'Warning! Truncating word \'{word}\' while trying to fit in image with width {width}', file=sys.stderr)
            line += ' ' + word
            # raise NotImplementedError('Handling of too big words not implemented')

    if len(line) != 0:
        lines.append(line)  # add the last line

    font_bounding_box = font.getbbox(text)
    font_top_padding = font_bounding_box[1]
    line_height = top_padding + (font_bounding_box[3] - font_top_padding) + bottom_padding
    img_height = line_height * (len(lines))

    img = PIL.Image.new("RGB", (width, img_height), bgcolor)
    draw = PIL.ImageDraw.Draw(img)

    y = top_padding - font_top_padding
    for line in lines:
        draw.text((left_padding, y), line, color, font=font)
        y += line_height

    return img

def text2png(text: str, path_to_save: str, **args) -> None:

    img = text2image(text, **args)
    if not path_to_save.endswith('.png'):
        path_to_save += '.png'
    img.save(path_to_save, format='png')
    return

def image2b64(img: PIL.Image) -> str:

    buffered = BytesIO()
    img.save(buffered, format='png')  # Or jpeg
    img_bytes = base64.b64encode(buffered.getvalue())
    img_str = img_bytes.decode('ascii')
    return img_str


if __name__ == '__main__':
    # test functions
    # text2png(u"This is\na\ntest папа şğıöç zaa xd ve lorem hipster", 'test.png', fontfullpath=r"TimesNewRomanPsmt.ttf")
    text2png(u"This is a test папа şğıöç", 'test1.png', fontfullpath=os.path.join("Fonts", "TimesNewRomanPsmt.ttf"))
