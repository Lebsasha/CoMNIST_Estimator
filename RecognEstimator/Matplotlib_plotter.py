import csv
import os.path

import matplotlib.pyplot as plt


def get_data(path: str):
    f = open(path)
    reader = csv.reader(f)
    itr = reader.__iter__()
    random_words = itr.__next__()[1:]
    # Skip unnecessary data
    _ = itr.__next__()
    _ = itr.__next__()
    _ = itr.__next__()
    _ = itr.__next__()
    _ = itr.__next__()
    quality_row = itr.__next__()
    quality = []
    while len(quality_row) == 0 or not quality_row[0].startswith("q ="):
        if (len(quality_row)) != 0:
            quality.append(float(quality_row[1]))
        quality_row = itr.__next__()
    f.close()
    return random_words, quality


file_bin = os.path.join('Out', 'last_data_b1.csv')
file_without_bin = os.path.join('Out', 'last_data_b0.csv')

random_words_b1, quality_b1 = get_data(file_bin)
random_words_b0, quality_b0 = get_data(file_without_bin)
# quality_b0 = quality_b0[1:]
# quality_b0 = [i - 1 for i in quality_b0]

assert len(random_words_b0) == len(random_words_b1)


x_b1 = [i + 1 for i in range(len(quality_b1))]
x_b0 = [i + 1 for i in range(len(quality_b0))]
ticks = [i + 1 for i in range(max(len(quality_b1), len(quality_b0)))]

plt.figure()
plt.plot(x_b1, quality_b1, x_b0, quality_b0)
plt.xticks(ticks)
plt.grid(visible=True)
plt.title(f'Зависимость количества ошибок в распознавании букв\nот количества букв в слове при {len(random_words_b1)} слов')
plt.xlabel('Количество букв')
plt.ylabel('Количество ошибок')
plt.legend(['С бинаризацией', 'Без бинаризации'])
plt.savefig(f'{len(random_words_b1)}_err.jpg', dpi=150)
plt.show()

plt.figure()
num_of_letters_in_max_word_b1 = max([len(i) for i in random_words_b1])
x_b1 = [i + 1 for i in range(num_of_letters_in_max_word_b1)]
plt.hist([len(i) for i in random_words_b1], bins=x_b1, density=False, histtype='step')
num_of_letters_in_max_word_b0 = num_of_letters_in_max_word_b1
# num_of_letters_in_max_word_b0 = max([len(i) for i in random_words_b0])
# x_b0 = [i + 1 for i in range(num_of_letters_in_max_word_b0)]
# plt.hist([len(i) for i in random_words_b0], bins=x_b0, density=False, histtype='step')
plt.xticks([i + 1 for i in range(max(num_of_letters_in_max_word_b1, num_of_letters_in_max_word_b0))])
plt.grid(visible=True)
plt.title(f'Гистограмма длины исследованных {len(random_words_b1)} слов')
plt.savefig(f'{len(random_words_b1)}_hist.jpg', dpi=150)
plt.show()
