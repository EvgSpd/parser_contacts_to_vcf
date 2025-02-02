# parser contacts from vcf json excel to vcf
Собирает контакты (фио, номер) из json vcf exel (xls) и сохраняет в форматах vcf и xls - для редактирования.
Контакты объединяются по совпадению фио или номера
После редактииования xls возможно конвертировать в vcf только его.
bat файлы для запуска различаются лишь аргументами - разрешениями обрабатываемых файлов

Для запуска поместите файлы со списками контактов в туже дирректорию где и py файл с батником либо в поддирректоории. 
Не изменяет входные файлы, только создает новые с суфиксом _all/

Если у вас совсем старая версия vcf 2.1: в функция есть закоменченная строка для подобного случая.



agregate contacts from files in folder and subfolders to vcf and json format

work with vcf version 2.1/3.0, json, and json export from telegram desktop client.

Features: merge duplicates by number records different subscriber numbers in one card 

Dependencies: Python 3.5+ required

USAGE: 
bat: Move the files into the folder with your cotacts files and run the .bat file (start_contacts_parser.bat)

with console: python agregate_contacts_to_vcf.py vcf,json
