import csv
import os.path

import matplotlib.pyplot as plt

f = open(os.path.join('Out', 'last_data.csv'))
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

x = [i + 1 for i in range(len(quality))]

plt.plot(x, quality)
plt.xticks(x)
plt.grid(visible=True)
plt.title(f'Зависимость количества ошибок в распознавании букв\nот количества букв в слове при {len(random_words)} слов')
plt.xlabel('Количество букв')
plt.ylabel('Количество ошибок')
plt.savefig(f'{len(random_words)}_err.jpg', dpi=150)
plt.show()

num_of_letters_in_max_word = max([len(i) for i in random_words])
plt.figure()
x = [i + 1 for i in range(num_of_letters_in_max_word)]
plt.hist([len(i) for i in random_words], bins=x, density=True)
plt.xticks(x)
plt.title(f'Гистограмма длины исследованных {len(random_words)} слов')
plt.grid(visible=True)
plt.savefig(f'{len(random_words)}_hist.jpg', dpi=150)
plt.show()
