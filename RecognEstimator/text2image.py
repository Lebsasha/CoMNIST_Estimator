# coding=utf8
import os
import sys
from io import BytesIO
import base64
import PIL
import PIL.Image, PIL.ImageDraw, PIL.ImageFont


def text2image(text, color="#000", bgcolor="#FFF", fontfullpath=os.path.join("Fonts", "CourierNew.ttf"), fontsize=20, leftpadding=3, rightpadding=3,
               width=200, top_padding=2, bottom_padding=2, isDebug=False) -> PIL.Image:

    REPLACEMENT_CHARACTER = u'\uFFFD'
    NEWLINE_REPLACEMENT_STRING = ' ' + REPLACEMENT_CHARACTER + ' '

    # ImageFont.lo
    font = PIL.ImageFont.load_default() if fontfullpath is None else PIL.ImageFont.truetype(fontfullpath, fontsize)

    text = text.replace('\n', NEWLINE_REPLACEMENT_STRING)

    lines = []
    line = u""

    for word in text.split():
        if isDebug:
            print(word)
        if word == REPLACEMENT_CHARACTER:  # give a blank line
            lines.append(line[1:])  # slice the white space in the begining of the line
            line = u""
            lines.append(u"")  # the blank line
        elif font.getlength(line + ' ' + word) <= (width - rightpadding - leftpadding):
            line += ' ' + word
        else:  # start a new line
            lines.append(line[1:])  # slice the white space in the begining of the line
            line = u""

            # TODO: handle too long words at this point
            if font.getlength(word) < (width - rightpadding - leftpadding):
                line += ' ' + word  # for now, assume no word alone can exceed the line width
            else:
                # raise NotImplementedError('Handling of too big words not implemented')
                # list = textwrap.wrap(text, width=30)
                print(f'Warning! Truncating word while trying to fit word \'{word}\' in image with width {width}', file=sys.stderr)
                line += ' ' + word

    if len(line) != 0:
        lines.append(line[1:])  # add the last line

    font_bounding_box = font.getbbox(text)
    font_top_padding = font_bounding_box[1]
    line_height = top_padding + (font_bounding_box[3] - font_top_padding) + bottom_padding
    img_height = line_height * (len(lines))  # + 1) # For linkback (see below)

    img = PIL.Image.new("RGB", (width, img_height), bgcolor)
    draw = PIL.ImageDraw.Draw(img)

    y = top_padding - font_top_padding
    for line in lines:
        draw.text((leftpadding, y), line, color, font=font)
        y += line_height

    # # prepare linkback
    # linkback = "created via http://ourdomain.com"
    # fontlinkback = ImageFont.load_default()  # truetype('font.ttf', 8)
    # linkbackx = fontlinkback.getsize(linkback)[0]
    # linkback_height = fontlinkback.getsize(linkback)[1]
    # # end of linkback
    #
    # # add linkback at the bottom
    # draw.text((width - linkbackx, img_height - linkback_height), linkback, color, font=fontlinkback)

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
