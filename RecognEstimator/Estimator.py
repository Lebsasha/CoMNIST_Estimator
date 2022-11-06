#!/usr/bin/env python
#  -*- coding: utf-8 -*-

# Builtin imports
import csv
import os
import time
from typing import List
import requests
import enum
import random
import json
import difflib
import shutil

# Dependency imports
import matplotlib.pyplot as plt

# Local imports
import text2image

# Launch server together with client (alternatevely, run 'python WordRecognitionServer.py')
# import sys, os
# sys.path.insert(1, os.path.join(sys.path[0], '..', 'CharRecApi'))
#
# from CharRecApi import WordRecognitionServer

class Mode(enum.Enum):
    SingleWord = 1,
    Multiple = 2

if __name__ == '__main__':

    # For debug
    mode = Mode.Multiple

    # Modeling arguments
    is_binarize = True
    text2image_params = {'fontpath': os.path.join("Fonts", "Consolas.ttf"), 'fontsize': 40}
    num_of_words = 100

    # Some other arguments
    output_folder = 'Out'

    if mode is Mode.Multiple:

        begin_time = time.time()

        print('Initializing')

        with open('Hunspell disctionaries/ru_RU.dic', 'r', encoding='utf-8') as f:
            all_words = [i for i in f]
        all_words = all_words[1:]
        for i in range(len(all_words)):
            all_words[i] = all_words[i][0 : all_words[i].find('/')]

        random.seed(0)
        random_words: List[str] = random.choices(population=all_words, k=num_of_words)

        print('Guessed\t\tRecognized')

        quality_raw = [0] * num_of_words
        recognized_words = ['']*num_of_words
        current_word = 0
        for word in random_words:
            word = word.upper()
            imgAsString = text2image.image2b64(text2image.text2image(word, **text2image_params))
            response = requests.post('http://127.0.0.1:5002/api/word', json={'img': imgAsString, 'word': word, 'lang': 'ru',
                                                                             'num_of_letters': 1, 'is_binarize': is_binarize})
            if response.ok:
                data = json.loads(json.loads(response.text))
                recognized_word: str = data['word']
                word = word.upper()
                diff = difflib.SequenceMatcher(None, word, recognized_word).get_matching_blocks()
                est_of_quality = len(word) - sum([i[2] for i in diff])
                quality_raw[current_word] = est_of_quality
                recognized_words[current_word] = recognized_word
                print(f'{current_word}. {word}\t\t{recognized_word}')
            else:
                print(f'Warning! Got error code {response.status_code} while recognising word {word}')
            current_word += 1

        elapsed_time = time.time() - begin_time
        print(f'Elapsed {elapsed_time}')

        overall_quality = 0
        overall_quality_norm = 0
        max_len_of_word = max([len(w) for w in random_words])
        quality_array = [0] * max_len_of_word
        quality_num = [0] * max_len_of_word
        for i in range(len(quality_raw)):
            overall_quality += quality_raw[i]
            overall_quality_norm += quality_raw[i] / len(random_words[i])
            quality_array[len(random_words[i]) - 1] += quality_raw[i]
            quality_num[len(random_words[i]) - 1] += 1
        for i in range(len(quality_array)):
            if quality_num[i] != 0:
                quality_array[i] /= quality_num[i]

        pretty_time = time.strftime('%Y %m %d %H.%M.%S', time.localtime())

        plt.figure()
        x = [i + 1 for i in range(len(quality_array))]
        plt.plot(x, quality_array)
        plt.xticks(x)
        plt.grid(visible=True)
        plt.savefig(os.path.join(output_folder, f"{pretty_time}.jpg"), dpi=150)
        plt.show()

        csv_file_path = os.path.join(output_folder, f'{pretty_time}.csv')
        with open(csv_file_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow([f"random_words: ", *random_words])
            writer.writerow([f"recognized words: ", *recognized_words])
            writer.writerow([f"quality_array: "])
            writer.writerows([[i + 1, quality_array[i]] for i in range(len(quality_array))])
            writer.writerow(["q = ", f"{overall_quality:2f}", "q_norm = ", f"{overall_quality_norm:2f}"])
            writer.writerow(["Elapsed: ", f"{elapsed_time}"])

        shutil.copy2(csv_file_path, os.path.join(output_folder, 'last_data.csv'))

        print('End')


    elif mode == Mode.SingleWord:
        word = 'Привет'
        # word ='Свежеприготовленный пирог'
        word = word.upper()
        text2image.text2png(word, f'{word}.png', **text2image_params)
        imgAsString = text2image.image2b64(text2image.text2image(word, **text2image_params))
        response = requests.post('http://127.0.0.1:5002/api/word', json={'img': imgAsString, 'word': word, 'lang': 'ru',
                                                                         'num_of_letters': 5, 'is_binarize': is_binarize})
        if response.ok:
            data = json.loads(json.loads(response.text))
            recognized_word = data['word']
            print(f'Got post for \'{word}\': {recognized_word}')
        else:
            print(f'Got post with {response.status_code} code (reason: {response.reason})')

    else:
        pass
    pass
