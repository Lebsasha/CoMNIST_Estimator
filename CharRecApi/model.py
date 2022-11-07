# -*- coding: utf-8 -*-

import os
import string
import numpy as np
from keras.layers import Dense, Convolution2D, Activation, MaxPooling2D, Dropout, Flatten
import keras.models

import image_proc

WEIGHTS_BACKUP = "weights/comnist_keras.hdf5"
SIZE = 32

INF = 10**9

def load_model(weights_filename, nb_classes):
    """Get the convolutional model to be used to read letters

    :param weights_filename: string
        path to the training weigths
    :param nb_classes: int
        number of expected output classes
    :return: mode: keras.model
        the convolutional model
    """
    if weights_filename is None:
        weights_filename = WEIGHTS_BACKUP

    # fix random seed for reproducibility
    np.random.seed(7)

    # number of convolutional filters to use
    nb_filters = 32
    nb_filters2 = 64
    nb_filters3 = 128
    # size of pooling area for max pooling
    pool_size = (2, 2)
    # convolution kernel size
    kernel_size = (3, 3)

    input_shape = (SIZE, SIZE, 1)

    # create model
    model = keras.models.Sequential()

    model.add(Convolution2D(nb_filters,
                            (kernel_size[0], kernel_size[1]),
                            padding='valid',
                            input_shape=input_shape,
                            activation='relu'))
    model.add(Convolution2D(nb_filters2,
                            (kernel_size[0], kernel_size[1]),
                            activation='relu'))
    model.add(MaxPooling2D(pool_size=pool_size))

    model.add(Convolution2D(nb_filters3,
                            (kernel_size[0], kernel_size[1]),
                            activation='relu'))
    model.add(MaxPooling2D(pool_size=pool_size))

    model.add(Flatten())
    model.add(Dense(512,
                    activation='relu'))
    model.add(Dense(256,
                    activation='relu'))

    model.add(Dense(nb_classes))

    # load weights
    if os.path.exists(weights_filename):
        model.load_weights(weights_filename)

    # Finally compile model (required to make predictions)
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    print(f"Successfully loaded weights from file '{weights_filename}' and created model")

    return model

import tensorflow as tf
def load_letter_predictor(weights_filename, lang_in):
    """Create a function that will classify images to letters

    :param weights_filename: string
        path to the training weigths
    :param lang_in: string
        language in which the letters are written
    :return: function
        a function that convert an image to a letter
    """

    if lang_in == 'en':
        LETTERS = string.ascii_uppercase
    elif lang_in == 'ru':
        LETTERS = u'IАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'  # 33 + 1 because of possible misrecognition of letter 'Ы'
    else:
        raise AttributeError('Incorrect language passed to model')

    num_of_classes = len(LETTERS)
    model = load_model(weights_filename, num_of_classes)

    def letter_predictor(img, nb_output):
        """Reshape and resize images before classifying

        :param img: PIL.Image
            image of a single letter
        :param nb_output: int
            return the n first most probable letters identified on the image
        :return: string
            the first and second most probable letters represented by the image
        """
        img = image_proc.crop_resize(img, -1)
        img = image_proc.pad_resize(img, SIZE)
        img = np.reshape(img, (1, SIZE, SIZE, 1))

        # Compute probability for each possible letter
        # proba_list = model.predict(img, verbose=0)[0]  # TODO Change in occurrence of performance issues
        proba_list = model(img, training=False)[0].numpy()
        probable_letters_list = []
        for _ in range(nb_output):
            # Get index of most probable letter not already identified
            ind = int(np.argmax(proba_list))
            # Add this lette to the output list
            probable_letters_list.append(LETTERS[ind])
            # Remove most probable letter from probability list
            proba_list[ind] = -INF

        return probable_letters_list

    return letter_predictor


def load_word_predictor(weights_filename, lang_in):
    """Create a function that will convert images to words

    :param weights_filename: string
        path to the training weigths
    :param lang_in: string
        language in which the letters are written
    :return: function
        a function that convert an image to a word
    """
    letter_predictor = load_letter_predictor(weights_filename, lang_in)

    def word_predictor(img, nb_output):
        """Splits image of word into one image per letter

        :param img: PIL.Image
            image of a word
        :param nb_output: int
            return the n first most probable letters identified on the image
        :return: string
            the word represented by the image
        """

        cropped_letters = image_proc.crop_letters(img)
        # word = np.empty((len(cropped_letters), nb_output), dtype=object)
        word_as_list = []  # List<List<str>>
        # nb_letters = 0
        for i in range(len(cropped_letters)):
            letters = letter_predictor(cropped_letters[i], nb_output)
            # Deal with exception of letter 'Ы', which is possibly made of two distinct blocks
            exceptional_letter = False
            if lang_in == 'ru':
                if letters[0] == 'I':
                    if len(word_as_list) >= 1 and word_as_list[-1] == 'Ь':
                        word_as_list[-1][0] = u'Ы'
                        exceptional_letter = True
                    else:
                        letters = ['Т']*nb_output  # If we recognized pure 'I', maybe it was 'Т'
            if not exceptional_letter:
                word_as_list.append(letters)
                # nb_letters += 1

        word = np.array(word_as_list)
        return word

    return word_predictor
