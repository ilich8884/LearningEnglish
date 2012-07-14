LearningEnglish
===============
Работает приложение очень просто - вы создаете словарь, оно "прогоняет" вас по этому словарю, поправляя при необходимости. При каждом запуске нужно ответить правильно определенное кол-во раз, после чего программа завершиться.

## Настройки
Настроить путь к словарю, к файлу для сохранения статистики, периодичность повторения уроков, кол-во правильных ответов, которое будет требовать программа - можно в файле config.json.
Пути к словарю или файлу со статистикой, нужно указывать либо полный, либо относительно файла main.py.

## Словарь
В словаре допускается указывать несколько вариантов перевода через запятую, программа засчитает любой из этих ответов за правильный. Так же не играет значения регистр введенного слова и пробелы в конце или в начале. Если вы по ошибке добавите в словарь несколько одинаковых английских слов, при загрузке переводы дубликатов будут объединены.
Пример словаря находится в файле - dict.json.

## Установка
Скрипт написан на python 2.6, поэтому требуется его установить, вполне вероятно что он будет работать и на других версиях python 2.x.
Запустить скрипт можно вот такой командой: «%path_to_Python26%\pythonw.exe %path_to_main.py%\main.py».