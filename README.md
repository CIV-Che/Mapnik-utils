Mapnik-utils
============

Genereation tiles of map (OSM) utilities based on Python Mapnik library.

===== English content in down of file =================================

В репозитории Python скрипт для генерации тайлов карты (ОСМ) с помощью библиотеки
Mapnik (текущая версия 2.0.1). Скрипт код основан на скрипте из стандартного
пакета Маpnik-utils generate_tiles_multiprocess.py
(взят общий механизм распараллеливания и слегка измененный класс проекции Google) и
коде проекта psha/TileLite (взят принцип генерации карты метатайлами, который
решает проблему падения производительности генератора при
значениях mapnik.buffer_size достаточных для устранения эффекта обрезки надписей по
линиям и границам полигонов).

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

====== English content ================

In the repository Python script to generate. tile map (OSM) using the library
Mapnik (current version 2.0.1). The script code is based on a script from a
standard Package Mapnik-utils generate_tiles_multiprocess.py (taken general
mechanism of parallelization and slightly different class of projections
Google) and project code psha / TileLite (the principle is taken generate maps
metataylami that solves the problem of falling performance of the generator at
mapnik.buffer_size values sufficient to eliminate the effect of pruning on the
label lines and boundaries of polygons).

The script, as well as a prototype, designed tile generation for streaming
maps these values of the scale and the specified range, with a given processes
of generation (adjustable depending on the available in the processor cores
and free RAM). The generation is done using style maps (standard or custom).
Generated tiles add up to tile kesh specified directory root of the
repository.

Implemented generation of Multi-Processing both the polygon and the file-list
polygons, which is convenient for generation of separate regions with their
own, distinct from the main field Card terms and conditions (eg, cities need
to generate large values of zoom-zoom than it is for the general card).

When generating the list of polygons metatayla optimized for size the size of
the landfill. Size metatayla is given in units of the parties standard tile
(also a parameter). Size metatayla given only for maximum zoom (minimum scale)
and automatically converted to smaller zooms so that the cover on the all
levels of the same polygon.