# -*- coding: utf-8 -*-

import base64
import io
import difflib
import re
import sys

import numpy as np
import PIL.Image, PIL.ImageOps
import cv2

import image_disp

import matplotlib.pyplot as plt

def load(imfile="Greg.png"):
    """
    Loads an image from a file
    (Essentially for testing purposes)
    Returns an image
    """
    with PIL.Image.open(imfile) as image:
        img = image.copy()
    img = img.convert("L")
    return img


def get_intensity(im, horizontal):
    """
    Returns an array of the intensity along the requested dimension
    """
    if horizontal:
        return 255 / np.mean(im, axis=0) - 1
    else:
        return 255 / np.mean(im, axis=1) - 1


def next_position(im, start_position, blank, horizontal):
    """
    Helper function
    In image, identifies the next area after start position that is
    either blank or not blank.
    Scan can happen horizontally or vertically
    """
    intensity = get_intensity(im, horizontal=horizontal)
    intensity = intensity[start_position:]
    if blank:
        next_lim = np.argmax(intensity == 0)
    else:
        next_lim = np.argmax(intensity > 0)
    return start_position + next_lim

def last_position(im, start_position, blank, horizontal):
    """
    Helper function
    In image, identifies the last area after start position that is
    either blank or not blank.
    Scan can happen horizontally or vertically
    """
    intensity = get_intensity(im, horizontal=horizontal)
    intensity = intensity[start_position:]
    inverted_intensity = intensity[::-1]
    if blank:
        next_lim = np.argmax(inverted_intensity == 0)
    else:
        next_lim = np.argmax(inverted_intensity > 0)
    return start_position + (len(inverted_intensity) - next_lim)


def get_contours(im):
    """
    Identifies letters contours for our image
    Returns an array with upper left and lower right coordinate of each box
    """
    max_nb_letters = 150
    boxes = np.empty((max_nb_letters, 4), dtype=int)
    intensity_h = get_intensity(im, horizontal=True)
    next_lim, right_lim = 0, 0
    actual_num_of_letters = 0

    # horizontal_countours   
    while (next_lim < len(intensity_h)) & (actual_num_of_letters < max_nb_letters):
        left_lim = next_position(im, next_lim, blank=False, horizontal=True)
        # we have reached the last letter followed by blank
        if left_lim == next_lim:
            break
        right_lim = next_position(im, left_lim, blank=True, horizontal=True)
        # we have reached last letter which is next to right frame
        if right_lim == left_lim:
            right_lim = len(intensity_h)
        # else:
        #     right_lim -= 1
        next_lim = right_lim + 1
        boxes[actual_num_of_letters, 0] = left_lim
        boxes[actual_num_of_letters, 2] = right_lim
        actual_num_of_letters += 1

    # Reduce the box size to the number of letters
    boxes = boxes[:actual_num_of_letters, :]

    # vertical_countours   
    height = im.height
    for j in range(boxes.shape[0]):
        left_lim = boxes[j, 0]
        right_lim = boxes[j, 2]
        letter_im = im.crop(box=(left_lim, 0, right_lim, height))
        low_lim = next_position(letter_im, 0, blank=False, horizontal=False)
        high_lim = last_position(letter_im, low_lim, blank=False, horizontal=False)
        # top of the letter is next to the frame
        if high_lim == low_lim:
            high_lim = height
        # else:
        #     high_lim -= 1
        boxes[j, 1] = low_lim
        boxes[j, 3] = high_lim

    return boxes


def get_spaces(im):
    """
    Identifies spaces contours for our image
    There is always one more space than number of letters
    Returns an array with upper left and lower right coordinate of each box
    """
    width = im.width
    contours = get_contours(im)

    nb_cont = contours.shape[0]
    spaces = np.empty((nb_cont + 1, 4), dtype=int)

    left = 0
    for i in range(nb_cont):
        spaces[i] = [left, contours[i, 1], contours[i, 0] + 1, contours[i, 3]]
        left = contours[i, 2] - 1
    spaces[nb_cont] = [left, contours[-1, 1], width - 1, contours[-1, 3]]
    return spaces


def get_space_loc(diff, miss, length):
    """
    Identify the locations of the missing letters
    Returns an array of space positions, with 1 = missing, O = ok
    """
    diff2 = np.zeros(len(diff))
    j = 1
    for i in range(len(diff)):
        if diff[i] == 0:
            diff2[i] = j
            j += 1

    miss2 = np.zeros(len(miss))
    j = 1
    for i in range(len(miss)):
        if miss[i] == 0:
            miss2[i] = j
            j += 1

    pos_miss = np.zeros(length + 1, dtype=int)
    prev = 1
    for i, val in enumerate(miss2):
        if i == 0 and miss[0] == 1:
            pos_miss[0] = 1
        if val == 0 and prev != 0 and i > 0:
            index = np.where(diff2 == prev)[0]
            pos_miss[index + 1] = 1
        prev = val
    return pos_miss


def crop_letters(im):
    """Crop letters according to get_contours
    """
    return [pad_resize(im.crop(contour), -1) for contour in get_contours(im)]


def crop_resize(im, size):
    """ 
    Crops image to remove as much whitespace as possible
    If size is set to anything greater than 0, resize the image to a square
    
    Returns: an image object of the desized size
    """

    # Compute vertical intensity
    intensity_v = get_intensity(im, horizontal=False)

    # Compute vertical limits
    v_min = np.max([0, np.argmax(intensity_v > 0)])
    v_max = np.min([len(intensity_v) - np.argmax(intensity_v[::-1] > 0) - 1, len(intensity_v)])

    # Compute horizontal intensity
    intensity_h = get_intensity(im, horizontal=True)

    # Compute horizontal limits
    h_min = np.max([0, np.argmax(intensity_h > 0)])
    h_max = np.min([len(intensity_h) - np.argmax(intensity_h[::-1] > 0) - 1, len(intensity_h)])

    img = im.crop(box=(h_min, v_min, h_max, v_max))

    if size > 0:
        img = img.resize((size, size))

    return img


def pad_resize(im, size):
    """ 
    Adds white margins to image to make it square
    If size is set to anything greater than 0, resizes the image
    
    Returns: an image object of the desized size
    """

    height = im.height
    width = im.width

    npim = np.array(im)

    shape = np.max([width, height])
    new_npim = np.zeros((shape, shape))
    new_npim[:, :] = 255
    diff = np.abs(width - height)
    stride = diff // 2

    if height > width:
        # letter is wide
        new_npim[:, stride:stride + width] = npim
    elif width > height:
        # letter is high
        new_npim[stride:stride + height, :] = npim
    else:
        new_npim = npim

    img = PIL.Image.fromarray(new_npim.astype(np.uint8))
    img = img.convert("L")

    if size > 0:
        img = img.resize((size, size))
    plt.figure(); plt.imshow(img); plt.show()
    return img

def score_word(word_in, words_out, img):
    """
    Compares expected word and read word, flag discrepancies

    :param word_in: string
        the expected word
    :param words_out: string
        the read word
    :param img: PIL.Image
        the original image
    :return: [PIL.Image, int]
        in case of discrepancies, an image highlighting wrong/missing letters
        otherwise returns image unchanged, and flag if it changed
    """
    correct = 0

    # Get the most likely word
    word_out = ''.join(list(words_out[:,0]))

    # Handle case with expected/predicted of equal length
    diff = np.zeros(len(word_out))
    if len(word_in) == len(word_out):
        for i in range(len(word_in)):
            options = ''.join(list(words_out[i,:]))
            if word_in[i] not in options:
                diff[i] = 1
        # If discrepancies exist, gray out wrong letters
        if sum(diff) != 0:
            img = image_disp.gray_out_letter(img, *np.where(diff == 1))
        # Else pretend the predicted word is exactly what was expected
        else:
            correct = 1

    # Handle case with expected/predicted of different length
    else:
        s = difflib.SequenceMatcher(None, word_in, word_out)
        match = s.get_matching_blocks()
        diff = np.ones(len(word_out))
        miss = np.ones(len(word_in))
        for i in range(len(match) - 1):
            low_miss = match[i][0]
            low_diff = match[i][1]
            high = match[i][2]
            diff[low_diff:low_diff + high] = 0
            miss[low_miss:low_miss + high] = 0

        # Draw contours
        # img = image_disp.draw_contours(img)

        # Gray out wrong letters
        img = image_disp.gray_out_letter(img, *np.where(diff == 1))
        # Flag missing letters
        if len(word_in) != len(word_out):
            space_pos_miss = get_space_loc(diff, miss, len(word_out))
            img = image_disp.flag_missing_letter(img, *np.where(space_pos_miss == 1))

    return img, correct


def img_to_b64(img):
    """
    Helper function
    Converts image to base64
    """
    in_mem_file = io.BytesIO()
    img.save(in_mem_file, format="PNG")  # Or jpeg
    in_mem_file.seek(0)
    img_bytes = in_mem_file.read()

    base64_encoded_result_bytes = base64.b64encode(img_bytes)
    base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')
    return base64_encoded_result_str


def b64_to_img(img64):
    """
    Helper function
    Converts base64 to image
    """
    return PIL.Image.open(io.BytesIO(base64.b64decode(img64)))

def b64_remove_header(im):
    """Removes the b64 header

    :param im: b64 image with header (or not)
    :return: b64 img without b64 header
    """
    img = im
    if img[:4] == "data":
        img = re.sub(r'data:image/[^;]+;base64,', r'', img)
    return img

def b64_preprocess(im, is_binarize):
    """Converts b64 image to Image and ensure it has proper background/properties

    :param im: raw b64 image
    :param is_binarize if image must be binarized
    :return: img: image
    """

    # Convert to object of class Image
    img = b64_to_img(im)

    # Add a white background to the image
    if img.mode == 'RGBA' or img.mode == 'RGBa':
        try:
            blank = PIL.Image.new('L', img.size, color=255)
            img.paste(blank, (0, 0), mask=img)
        except Exception as e:
            print(f'Warning! When trying to add background catch exception {repr(e)}', file=sys.stderr)

    img = img.convert("L")

    # Get negative of image in case it is white on black
    if np.mean(np.array(img)) < 128:
        img = PIL.ImageOps.invert(img)
        print("Inverted image")

    if is_binarize:
        # Binarize image
        # img_np = np.array(img)
        # bin_threshold = 128
        # img = (img_np > bin_threshold) * 255
        img_bin: np.ndarray = cv2.threshold(np.array(img), 128, 255, cv2.THRESH_OTSU)[1]
        img = PIL.Image.fromarray(img_bin)

    return img
