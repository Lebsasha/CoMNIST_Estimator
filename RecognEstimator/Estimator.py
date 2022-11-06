#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import requests
import enum

import random
import json
import difflib

import text2image

# Launch server
# import sys, os
# sys.path.insert(1, os.path.join(sys.path[0], '..', 'CharRecApi'))
#
# from CharRecApi import WordRecognitionServer

class Mode(enum.Enum):
    SingleWord = 1,
    Multiple = 2

if __name__ == '__main__':

    mode = Mode.SingleWord

    if mode == Mode.SingleWord:
        word = 'Привет'
        text2image.text2png(word, 'Привет')
        imgAsString = text2image.image2b64(text2image.text2image(word))
        response = requests.post('http://127.0.0.1:5002/api/word', json={'img': imgAsString, 'word': word, 'lang': 'ru', 'num_of_letters': 5, 'is_binarize':True})
        if response.ok:
            data = json.load(response.text)
            recognized_word = data['word']
        print(f'Got post for \'{word}\'')

    elif mode is Mode.Multiple:
        print('Initting')

        with open('Hunspell disctionaries/ru_RU.dic', 'r', encoding='utf-8') as f:
            all_words = [i for i in f]
        all_words = all_words[1:]
        for i in range(len(all_words)):
            all_words[i] = all_words[i][0 : all_words[i].find('/')]

        num_of_words = 10
        random_words = random.choices(population=all_words, k=num_of_words)

        print('Beginning')
        print('Guessed\tRecognized')

        quality_dict = dict()
        for word in random_words:
            imgAsString = text2image.image2b64(text2image.text2image(word))
            response = requests.post('http://127.0.0.1:5002/api/word', json={'img': imgAsString, 'word': word, 'lang': 'ru', 'num_of_letters': 5, 'is_binarize':True})
            if response.ok:
                data = json.load(response.text)
                recognized_word: str = data['word']
                word = word.upper()
                diff = difflib.SequenceMatcher(None, word, recognized_word).get_matching_blocks()
                est_of_quality = sum([i for i in diff[2]]) - len(word)
                quality_dict[word] = est_of_quality
                print(f'{word}\t{recognized_word}')
            else:
                print(f'Warning! Got error code {response.status_code} while recognising word {word}')


        overall_q = 0
        for word, i in quality_dict:
            overall_q += i

    else:
        pass
    pass
