Mapnik-utils
============

Genereation tiles of map (OSM) utilities based on Python Mapnik library.

===== English content in down of file =================================

Описание
--------

В этом репозитории - Python-скрипт (generate_tiles_meta_mp.py) для генерации тайлов
карты (ОСМ) с помощью библиотеки Mapnik (текущая версия 2.0.1). Код скрипта основан
на скрипте из стандартного пакета Маpnik-utils generate_tiles_multiprocess.py
(взят общий механизм распараллеливания и слегка измененный класс проекции Google) и
коде проекта psha/TileLite (взят принцип генерации карты метатайлами, который
решает проблему падения производительности генератора при
значениях mapnik.buffer_size достаточных для устранения эффекта обрезки надписей
расположенных по линиям и границам полигонов).

Скрипт, как и прототип, предназначен для потоковой генерации тайлов карты в
указанных значениях масштаба и указанном полигоне, с заданным
количеством процессов генерации (настраивается в зависимости от
имеющихся в системе ядер процессора и свободной оперативной памяти).
Генерация осуществляется с использованием стиля карты
(стандартного, или пользовательского). Сгенерированные тайлы складываются в
тайловый кэшь, заданный директорией корня хранилища.

Реализована многопроцессная генерация как по полигону, так и по файлу-списку
полигонов, который удобен для генерации отдельных регионов со
своими, отличными от основного поля карты условиями (например, города нужно
генерировать с большими значениями зума-масштаба чем принято для общей
карты).

При генерации по списку полигонов размер метатайла оптимизируется под размер
полигона. Размер метатайла задается в единицах сторон стандартного тайла (тоже
параметр). Размер метатайла задается только для максимального уровня зума
(минимального масштаба) и автоматически пересчитывается для меньших зумов так
чтобы накрывать на всех уровнях одинаковый полигон.

Кроме описанного скрипта в репозитории доступна пара скриптов применяемых для
полного обновления тайлового хранилища вслед за обновлением базы ОСМ. Скрипт
updt_parse_expire_list+_sp.py просматривает список устаревших тайлов, сгенерированный
утилитой osm2pgsql при обновлении базы ОСМ. В этот список добавляются требующие
обновления тайлы на всех уровнях зума (утилита генерирует свернутый список).
Имеется возможность оставить в больших уровнях зума только тайлы вошедшие в
список полигонов (например населенных пунктов). Второй скрипт обновляет
хранилище в соответствие с полученным списком тайлов - в этом случае механизм
метатайлов не используется (выставляется большой mapnik.buffer_size для исключения обрезки
надписей) т.к. в таком приложении он неэффективен.


Возможности 
-----------

- Потоковый (пакетный) многопроцессный генератор тайлов по данным из базы данных ОСМ
  отформатированных файлом стиля.

- Источники данных - аналогично исходному пакету Mapnik-utils.

- Возможность модификации стиля генерируемой карты.

- Экономия дискового пространства заменой "пустых" (одноцветных) тайлов жесткими
  ссылками.

- Увеличенная производительность (при отсутствии артефактов на карте) за счет
  использования механизма метатайлов.

- Производительность увеличена настолько, что можно использовать полную перегенацию
  карты после обновления данных в базе (источнике данных) вместо специального
  механизма обновления тайлового хранилища (затрачиваемое в этом случае время будет
  примерно вдвое больше чем со скриптами обновления).

- Реализован механизм генерации по файлу-списку полигонов.

- Механизм генерации по списку полигонов оптимизирован и может использоваться для
  генерации тайлов с разными условиями на разных уровнях зума (например при
  генерации на больших зумах только полигонов нас.пунктов).

- Реализован механиз обновления по списку устаревших тайлов osm2pgsql с учетом
  списка полигонов для генерации на больших уровнях зума.


Зависимости
-----------

Для нормальной работы скриптов необходимо наличие установленных:

- Библиотеки Mapnik (с зависимостями).

- Пакет Mapnik-utils (нужен только файл стиля с зависимостями).

- Стандартного пакета Python (проверено на версии 2.7).

- Дополнительного модуля Python - progressbar (использование не обязательно -
  можно отключить).

- Одной из СУБД (с георасширениями) работа с которыми поддерживается Mapnik -
  рекомендуется Postgresql + PostGIS .


Установка
---------

Установите все обратные зависимости (пакеты от которых зависят скрипты).
Скачайте скрипты в любую удобную директорию (если установлен пакет Mapnik-utils
удобно в его директорию). В заголовочной части скриптов настройте параметры 
(в соответствие с подробными комментариями). Можно пользоваться.
Готовить файл полигонов населенных пунктов можно дополнительным скриптом, но нужна база данных
ОСМ с другой структурой "Slippy Map" (дополнительная база, которую потребуется поддерживать в 
актуальном состоянии - взвесте все за и против такого подхода). Алтернативный способ - 
забрать список с общего ресурса.


====== English content ================

Description
-----------

This repository - Python-script (generate_tiles_meta_mp.py) to generate the
tile map (OSM) using the library Mapnik (current version 2.0.1). Script code
is based on a script from a standard package Mapnik-utils
generate_tiles_multiprocess.py (Taken by a common mechanism for
parallelization and a slightly different class of projections of Google), and
project code psha / TileLite (taken the principle of generating a map
metataylami that solves the problem of performance degradation when the
generator mapnik.buffer_size values sufficient to eliminate the effect of
clipping labels located on the lines and boundaries of polygons).

The script, as well as a prototype, designed to stream generating tile map in
these values of the specified size and range, with a given
processes of generation (adjustable depending on the
available in the processor cores and free memory).
Generated by using a map style
(Standard or custom). Generated tiles add up to
tile cache specified repository root directory.

Implemented as a Multi-Processing for the generation of a polygon, and the
file-list polygons, which is convenient for the generation of separate regions
with their own, distinct from the main field maps of the conditions (for
example, the city should to generate with large zoom-zoom than is for total
card).

When generating the list of polygons metatayla size is optimized for size
landfill. Metatayla size is specified in units of standard tile sides (also
parameter). Size metatayla set for maximum zoom
(Minimum scale) and will automatically be converted to smaller zooms so
to be covered at all levels of the same polygon.

Also described in the script repository is available a couple of scripts used
for the complete renovation tile store after updating the database OSM. Script
updt_parse_expire_list + _sp.py through the list of old tiles generated by the
utility for updating the database osm2pgsql OSM. The list is added to require
updating tiles at all levels of zoom (utility generates a collapsed list).
There is an opportunity to leave high levels of zoom, only the tiles included
in the list of polygons (eg settlements).The second script updates the
repository in accordance with the given list of tiles - in this case, the
mechanism is not used metataylov (mapnik.buffer_size exhibited large to avoid
clipping labels) as in this application, it is inefficient.


Capabilities
------------

Streaming (batch) Multi-Processing tile generator for data from the OSM
database formatted file style.

- Data sources - similar to the original package Mapnik-utils.

- Ability to modify style of the generated maps.- Save space by replacing
  "empty" (monochrome) rigid tile  references.

- Increased productivity (in the absence of artifacts on the map) due
  to  using the mechanism metataylov.

- Capacity increased so much that you can use the full peregenatsiyu  map
  data is updated in the database (data source) instead of a
  special  mechanism for updating tile store (in this case takes the time to
  be  about twice more than the scripts update).

- The mechanism of generation of file-list of polygons.

- The mechanism of generating a list of polygons optimized and can be used
  to  generation of tiles with different conditions at different levels of
  zoom (for eg  generation in large suburban zumah only polygons).

- Implemented a mechanism to update the list of outdated tile osm2pgsql
  given  list of polygons to generate at high levels of zoom.


Depending on
------------

For normal operation, you must have installed scripts:

- Library of Mapnik (with dependencies).

- Package Mapnik-utils (only style file with dependencies).

- The standard package of Python (tested with version 2.7).

- Additional module Python - progressbar (use is not necessarily -  can be
  disabled).

- One of the database (with georasshireniyami) work that is supported by
  Mapnik - recommend Postgresql + PostGIS.


Installation
------------

Install any reverse dependencies (packages depending on which
scripts).Download the scripts in any convenient directory (if installed
Mapnik-utilscomfortable in its directory). In the header of the script set the
parameters(In accordance with detailed comments). You can use it.Prepare a
file of polygons of settlements can be an additional script, but need a
databaseOSM with a different structure "Slippy Map" (extra base, which will
require support indate - cock the pros and cons of this approach). Alternativ
way - pick list from a shared resource.
