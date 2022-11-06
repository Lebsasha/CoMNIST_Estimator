#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import json
import time

import flask
import flask_restful
from app import app, api

import image_proc
import model

DEBUG = False

@api.route("/api/word")
class Prediction(flask_restful.Resource):
    def post(self):
        """API that expects an b64 image as input, analyze it
        and returns the word it represents
        Language has to be provided as different alphabets are handled differently. Also, if image need to be binarized have to be supplied.
        Expected word can be provided too.
        Number of most probable letters also could be supplied (for debugging purpose) (default value of it is 1)

        :return: json
            a json containing the read word (string) and if expected word was provided,
            a b64 images flagging discrepancies between read and expected (if any)
        """
        start = time.time()

        # Read parameters
        data = flask.request.data.decode("utf-8")
        if len(data) != 0:
            params = json.loads(data)
        else:
            params = {}

        try:
            img_in = params['img']
            lang_in = params['lang']
            is_binarize = params['is_binarize']
        except KeyError:
            raise AttributeError('Not all necessary attributes supplied')

        try:
            word_in = params['word']
        except KeyError:
            word_in = None

        try:
            num_of_letters = int(params['num_of_letters'])
        except KeyError and TypeError:
            num_of_letters = 1


        # Ensure image has no header
        img_in = image_proc.b64_remove_header(img_in)

        # Convert image to process-able format
        img = image_proc.b64_preprocess(img_in, is_binarize)

        # Convert image to word
        response = dict()
        if lang_in == 'en':
            words_out = word_predictor_en(img, num_of_letters)
        elif lang_in == 'ru':
            words_out = word_predictor_ru(img, num_of_letters)
        else:
            raise AttributeError(f"'lang' parameter '{lang_in}' is nor 'en', nor 'ru'")
        if words_out.size != 0:
            word_out = ''.join(list(words_out[:, 0]))
        else:
            response['word'] = ""
            return json.dumps(response)

        response["word"] = word_out

        if DEBUG:
            print("Found word: %s" % word_out)
            if num_of_letters > 1:
                for i in range(1, num_of_letters):
                    print("Alternatively word could be %s" % ''.join(list(words_out[:, i])))

        # Compare read word with expected word
        if word_in is not None and len(word_in) != 0:
            img, correct = image_proc.score_word(word_in, words_out, img)
            response["correct"] = correct
            # Convert image back to base64 to be sent to the requestor
            response["img"] = image_proc.img_to_b64(img)

        if DEBUG:
            print("Time spent handling the request: %f" % (time.time() - start))

        return json.dumps(response)


if __name__ == "__main__":

    # Read arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", default=DEBUG, type=bool, help="Image shape")
    args = parser.parse_args()

    DEBUG = args.debug

    # Load model and start API
    print('Loading models')
    word_predictor_en = model.load_word_predictor("weights/comnist_keras_en.hdf5", lang_in='en')
    word_predictor_ru = model.load_word_predictor("weights/comnist_keras_ru.hdf5", lang_in='ru')
    print('Starting the API')
    app.run(host="0.0.0.0", port=5002)
