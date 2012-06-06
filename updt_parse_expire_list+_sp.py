#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
This script for make full coodrinate OSM tiles list from coordinate list
taked with osm2pgsql tool, and devide it full list to taked in NUM_PARTS
parts in LIST_DIR directory (for get it parts on another systems in
calculate cloud). This script parse list for append all tiles in all
zooms you need. osm2pgsql made compact list, it include tiles high
(small number) zoom, under him is never not (its tiles coord make parser
for all zoom from current+1 to MAX_ZOOM) and above low zoom (bigger zoom
number) tiles from, expanded to low, osm2pgsql-list parser generate all
zooms coord from MAX_ZOOM-1 to MIN_ZOOM for all tiles-coord in MAX_ZOOM.
This script put in parts with smallest number bigger number of tiles
with high (small number) zoom - its require increase calculate power in
system by this part You make define zooms you needed and any others
params.
"""
__author__ = 'Cheltsov Ivan (civ@ploha.ru)'
__copyright__ = 'Copyright 2012, Cheltsov Ivan'
__version__ = '0.1.0'
__license__ = 'LGPL'


import sys, os

MIN_ZOOM = 4
MAX_ZOOM = 17

# Define params for parse with poligons list mechanism
USE_POLY = 'true' # 'true' for check crossing lists
POLY_MIN_ZOOM = 15  # Must be > MIN_ZOOM
POLY_MAX_ZOOM = 17  # Must be < MAX_ZOOM
POLY_LIST = '/osm/data/city.ru.tiles'

# Define name of input tiles coordinate list file
LIST_TILES = '/osm/update/RU-diff.list'

# Define output list (parts) files dir
LIST_DIR = '/osm/update/'

# Define number parts of full list to output (number calculators in cloud)
NUM_PARTS = 1

############################################################

## Making parsing zoom down ################################
## function append tiles list lower zoom ones (expand zoom down)
def zoom_down_tiles(zoom=14, maxZoom=18, x=0, y=0):
    zoom += 1
    x += x   # optimized x*2
    y += y   # optimized y*2
    t_list_parse_down[zoom].update({(x, y), (x+1, y+1), (x, y+1), (x+1, y)})
    ## and recursive call for lower zooms
    if zoom < maxZoom:
        zoom_down_tiles(zoom, maxZoom, x, y)
        zoom_down_tiles(zoom, maxZoom, x+1, y+1)
        zoom_down_tiles(zoom, maxZoom, x, y+1)
        zoom_down_tiles(zoom, maxZoom, x+1, y)
## End zoom down ###########################################

# Main procedure
if __name__ == "__main__":

    if not LIST_DIR.endswith('/'):
        LIST_DIR = LIST_DIR + '/'

    if (not os.path.isfile(LIST_TILES)):
        sys.exit('File from LIST_TILES %s not found' % LIST_TILES)

    if not os.path.isdir(LIST_DIR):
        os.mkdir(LIST_DIR)

    # Initialise parsing
    print "parse tiles coordinate list for zooms from ", MIN_ZOOM, " to ", MAX_ZOOM

    ## input expire tiles list file as string list (array)
    file_tiles = open(LIST_TILES, 'r')

    ## remove doubl elements of list
    list_tiles = set(file_tiles)
    file_tiles.close()

    ## evry string of list split on components, analise him and generate new tiles coordinate list
    ## then convert him to one level up list with indexing by first coordinate of tile (zoom)
    list_tiles = [[int(coord) for coord in tile.strip().split('/')] for tile in list_tiles]

    ## create 3d normalised (to MIN_ZOOM) list (list tiles inside evry zoom changes to set for speed up)
    list_tiles = [set([(tile[1],tile[2]) for tile in list_tiles if tile[0] == z]) for z in xrange(MAX_ZOOM+1)]
    
    ## Zoom down iterate parsing ###########################
    print "Starting zoom down parsing process"          ####
    ## down zoom iteration
    t_list_parse_down = [set() for z in xrange(MAX_ZOOM+1)]
    for z in xrange(MAX_ZOOM-1, MIN_ZOOM-1, -1):
        ## Expand big tiles (zoom down) to high zooms tiles
        for tile in list_tiles[z]:
            zoom_down_tiles(z, MAX_ZOOM, tile[0], tile[1])
    ## End Zoom down #######################################

    ## Launch parsing processes (zoom up) ##################
    print "Start zoom up pasing procedure"
    t_list_parse_up = [set() for z in xrange(MAX_ZOOM+1)]

    ## up zoom iteration
    for z_base in xrange(MIN_ZOOM+1, MAX_ZOOM+1, 1):
        print "Current base zoom is ", z_base
        for tile in list_tiles[z_base]:
            x = tile[0]
            y = tile[1]
            for z in xrange(z_base-1, MIN_ZOOM-1, -1):
                x //= 2
                y //= 2
                ## Append tile in set (auto-uniquer)
                t_list_parse_up[z].add((x,y))
    ## End parsing processes (zoom up) #####################

    ## Joining tiles lists #################################
    for z in xrange(MIN_ZOOM, MAX_ZOOM+1):
        list_tiles[z].update(t_list_parse_down[z])
    for z in xrange(MIN_ZOOM, MAX_ZOOM+1):
        list_tiles[z].update(t_list_parse_up[z])

    ## Check crossing list expired tiles and list polygon tiles
    print "Crossing lists"
    if USE_POLY == 'true':
        ## input expire polys list file as string list (array)
        file_polys = open(POLY_LIST, 'r')

        ## remove doubl elements of list
        list_polys = set(file_polys)
        file_polys.close()

        ## evry string of list split on components, analise him and generate new polygons-tiles coordinate list
        ## then convert him to one level up list with indexing by first coordinate of tile (zoom)
        list_polys = [[int(coord) for coord in tile.strip().split('/')] for tile in list_polys]

        ## create 3d normalised (to POLY_MIN_ZOOM) list (list tiles inside evry zoom changes to set for speed up)
        list_polys = [set([(tile[1],tile[2]) for tile in list_polys if tile[0] == z]) for z in xrange(POLY_MAX_ZOOM+1)]

        for z in xrange(POLY_MIN_ZOOM, POLY_MAX_ZOOM+1):
            list_tiles[z] &= list_polys[z]

    ## End check ###########################################

    ## Flattening list
    print "Final steps"
    list_full = []
    for z in xrange(MIN_ZOOM, MAX_ZOOM+1):
        list_full += [[z,coord[0],coord[1]] for coord in list_tiles[z]]

    ## Devide full tiles coordinate list on parts
    parts = [list_full[p::NUM_PARTS] for p in xrange(NUM_PARTS)]

    ## Write parts of list to files
    for p in xrange(NUM_PARTS):
        f = open(LIST_DIR + 'part_' + ("%s" % p) + '.list', 'w')
        for t in parts[p]:
            f.write("%s/%s/%s\n" % (t[0], t[1], t[2]))
        f.close()
