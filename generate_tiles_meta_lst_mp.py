#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
This script for generate OSM tiles inside bounding boxes from list-file (for cities generation).
You make define path to tile dir, zooms you needed and any others params.

This script base on standart Mapnik-utils - generate_tiles_multiprocess.py
and TileLite psha fork (metatile mechanism).

This script oriented to improve performance and no have statistics analizer and other pancakes
"""
__author__ = 'Cheltsov Ivan (civ@ploha.ru)'
__copyright__ = 'Copyright 2012, Cheltsov Ivan'
__version__ = '0.1.0'
__license__ = 'LGPL'

from math import pi,cos,sin,log,exp,atan
from subprocess import call
import sys, os
import multiprocessing
import shutil
import string

try:
    import mapnik
except:
    import mapnik2 as mapnik

# Initiate params for tile generator

#-------------------------------------------------------------------------
#
# Change the following for different bounding boxes and zoom levels
#

# Default number of rendering threads to spawn, should be roughly equal to number of CPU cores available
NUM_THREADS = 32

MIN_ZOOM = 2
MAX_ZOOM = 17
TILE_DIR = "/osm/tiles"
MAP_FILE = "/osm/mapnik/osm.xml"
TILE_SIZE = 256 # Number pixels on side for standart tile

# Attention, for big META_SIZE (>10) and big NUM_THREADS (other on other computers)
# you need accuracy calculate memory using (else you take increase swap use and not enough memory errors)
META_SIZE = 64 # Number standart tiles on side metatile (for max zoom level!!!)
BUF_SIZE = 1024 # Number pixels on side for attached around the tile buffer image (for unstrip inscriptions on bound tile or metatile), defoult is 128

## Uncomment next line for read BBOXs from list-file (one bbox on line, splitter is ",").
## Or, uncomment any two lines with GEN_NAME and BBOX variables (for define variables in script)
GEN_NAME = "Russia, Cities bboxs"
BBOX_FILE = '/osm/data/city.ru.bbox'

SQ = 1.3 # Criteria of squared polygon

### Uncomment next string for use empty tile mechanism
#ONLY_NEW = bool(0)  # If ONLY_NEW = bool(1) then will not generate tile exist in tile cache


def minmax (a,b,c):
    a = max(a,b)
    a = min(a,c)
    return a


class GoogleProjection:
    def __init__(self,levels=18):
        self.Bc = []
        self.Cc = []
        self.zc = []
        self.Ac = []
	self.DEG_TO_RAD = pi/180
	self.RAD_TO_DEG = 180/pi
        c = TILE_SIZE
        for d in xrange(0,levels+1):
            e = c/2;
            self.Bc.append(c/360.0)
            self.Cc.append(c/(2 * pi))
            self.zc.append((e,e))
            self.Ac.append(c)
            c += c
                
    def fromLLtoPixel(self,ll,zoom):
        d = self.zc[zoom]
        e = round(d[0] + ll[0] * self.Bc[zoom])
        f = minmax(sin(self.DEG_TO_RAD * ll[1]),-0.9999,0.9999)
        g = round(d[1] + 0.5*log((1+f)/(1-f))*-self.Cc[zoom])
        return (e,g)
     
    def fromPixelToLL(self,px,zoom,ms=1):
        e = self.zc[zoom]
        f = (px[0] - e[0])/self.Bc[zoom]
        g = (px[1] - e[1])/-self.Cc[zoom]
        h = self.RAD_TO_DEG * ( 2 * atan(exp(g)) - 0.5 * pi)
        return (f,h)



class RenderThread:
    def __init__(self, tile_dir, mapfile, q, maxZoom):
        self.tile_dir = tile_dir
        self.q = q
        self.mapfile = mapfile
        self.maxZoom = maxZoom

    def render_tile(self, x, y, z, m_size):
        ## Calculate pixel positions of bottom-left & top-right
        p0 = (x*TILE_SIZE, (y+m_size)*TILE_SIZE)
        p1 = ((x+m_size)*TILE_SIZE, y*TILE_SIZE)

        ## Convert to LatLong (EPSG:4326)
        l0 = self.tileproj.fromPixelToLL(p0, z);
        l1 = self.tileproj.fromPixelToLL(p1, z);

        ## Convert to map projection (e.g. mercator co-ords EPSG:900913)
        c0 = self.prj.forward(mapnik.Coord(l0[0],l0[1]))
        c1 = self.prj.forward(mapnik.Coord(l1[0],l1[1]))

        ## Bounding box for the tile
        bbox = mapnik.Box2d(c0.x,c0.y, c1.x,c1.y)
        self.m.resize(m_size*TILE_SIZE, m_size*TILE_SIZE)
        self.m.zoom_to_box(bbox)
        self.m.buffer_size = BUF_SIZE  #Default is 128

	## Render metatile - improve performance rendering proc
        # Render image with default Agg renderer
        im = mapnik.Image(m_size*TILE_SIZE, m_size*TILE_SIZE)
	mapnik.render(self.m, im)
        for dx in xrange(0, m_size):
            dir_uri = os.path.join(TILE_DIR, '%s' % z, '%s' % (x+dx))
            # Make tile directory
            if not os.path.isdir(dir_uri):
                # Some processes may do this in one time (FS handle this but get exception)
                # handle this exception faster than multiprocess lock mechanism
                try: os.mkdir(dir_uri)
                except (OSError, IOError): pass

            for dy in xrange(0, m_size):
		## Calculate full one current tile uri
                tile_uri = os.path.join(dir_uri, '%s.%s' % ((y+dy), 'png'))
                # View one tile from metatile and save here
                im.view(dx*TILE_SIZE, dy*TILE_SIZE, TILE_SIZE, TILE_SIZE).save(tile_uri, 'png256')

#### If you need empty-tiles mechanism explore - comment previous string and uncomment next strings
#                if not os.path.isfile(tile_uri):
#                    # View one tile from metatile and save here
#                    im.view(dx*TILE_SIZE, dy*TILE_SIZE, TILE_SIZE, TILE_SIZE).save(tile_uri, 'png256')
#                elif not ONLY_NEW:
#                    os.remove(tile_uri) # Rewrite mode
#                    # View one tile from metatile and save here
#                    im.view(dx*TILE_SIZE, dy*TILE_SIZE, TILE_SIZE, TILE_SIZE).save(tile_uri, 'png256')
#                else: continue     # For only new tiles in cache generation
#
#                ## Check for empty tile was generated (and make hardlink on it)
#                # Handle probable exception (because of the overlaping extended by part of metatail polygons)
#                # and many processes may generate one metatile (FS handle this correct) - this fastest mechanism
#                try:
#                    if os.stat(tile_uri)[6] == 103:
#                        f = open(tile_uri, "r")
#                        c = f.read(44)
#                        f.close()
#                        if (ord(c[41]) == 242) and (ord(c[42]) == 239) and (ord(c[43]) == 233):
#                            os.remove(tile_uri)
#                            os.link('/osm/tiles/empty.tiles/land.png', tile_uri)
#                        elif (ord(c[41]) == 181) and (ord(c[42]) == 208) and (ord(c[43]) == 208):
#                            os.remove(tile_uri)
#                            os.link('/osm/tiles/empty.tiles/water.png', tile_uri)
#                        elif (ord(c[41]) == 174) and (ord(c[42]) == 209) and (ord(c[43]) == 160):
#                            os.remove(tile_uri)
#                            os.link('/osm/tiles/empty.tiles/wood.png', tile_uri)
#                except (OSError, IOError): pass



    def loop(self):
        
        self.m = mapnik.Map(TILE_SIZE, TILE_SIZE)
        # Load style XML
        mapnik.load_map(self.m, self.mapfile, True)
        # Obtain <Map> projection
        self.prj = mapnik.Projection(self.m.srs)
        # Projects between tile pixel co-ordinates and LatLong (EPSG:4326)
        self.tileproj = GoogleProjection(self.maxZoom)
                
        while True:
            # Fetch a tile from the queue and render it
            r = self.q.get()
            if (r == None):
                self.q.task_done()
                break
            else:
                (name, x, y, z, ms) = r
            self.render_tile(x, y, z, ms)
            self.q.task_done()



def render_tiles(bb_lst, mapfile, tile_dir, minZoom=1, maxZoom=18, name="unknown", num_threads=NUM_THREADS):

    # Launch rendering processes
    queue = multiprocessing.JoinableQueue(96)
    renderers = {}
    for i in xrange(num_threads):
        renderer = RenderThread(tile_dir, mapfile, queue, maxZoom)
        render_thread = multiprocessing.Process(target=renderer.loop)
        render_thread.start()
        renderers[i] = render_thread

    if not os.path.isdir(tile_dir):
        os.mkdir(tile_dir)

    gprj = GoogleProjection(maxZoom)
    LLtoPx = gprj.fromLLtoPixel

    # Making progressbar
    import progressbar
    widgets = ['Now generate progress: ', progressbar.SimpleProgress()]
    bar = progressbar.ProgressBar(widgets = widgets, maxval = len(bb_lst)+1).start()
    counter = 0

    # Iteration by bbox list
    for bbox in bb_lst:
        bar.update(counter)
        counter += 1

        ll0 = (bbox[0],bbox[3])
        ll1 = (bbox[1],bbox[2])

        # Calculate optimal size of metatile
        px = [[LLtoPx(ll0,z), LLtoPx(ll1,z)] for z in xrange(0, maxZoom+1)]
        min_max = 1 if (max(abs(px[z][0][0]-px[z][1][0]),abs(px[z][0][1]-px[z][1][1]))/min(abs(px[z][0][0]-px[z][1][0]), 
                   abs(px[z][0][1]-px[z][1][1]))) < SQ else 0

        # Calculate size of metatile for all zoom levels
        if min_max:
            meta_size = [int(min(META_SIZE, max(abs(px[z][0][0]-px[z][1][0]),abs(px[z][0][1]-px[z][1][1]))/TILE_SIZE+1) or 1) for z in xrange(0, maxZoom+1)]
        else:
            meta_size = [int(min(META_SIZE, min(abs(px[z][0][0]-px[z][1][0]),abs(px[z][0][1]-px[z][1][1]))/TILE_SIZE+1) or 1) for z in xrange(0, maxZoom+1)]

        # Pool to queue task for any zooms metatiles
        for z in xrange(minZoom, maxZoom+1):
            # check if we have directories in place
            zoom = "%s" % z
            if not os.path.isdir(tile_dir + zoom):
                os.mkdir(os.path.join(tile_dir, zoom))
            for mx in xrange(int(px[z][0][0]/TILE_SIZE), int(px[z][1][0]/TILE_SIZE)+1, meta_size[z]):
                # Validate x co-ordinate
                if (mx < 0) or (mx >= 2**z):
                    continue
                for my in xrange(int(px[z][0][1]/TILE_SIZE),int(px[z][1][1]/TILE_SIZE)+1, meta_size[z]):
                    # Validate x co-ordinate
                    if (my < 0) or (my >= 2**z):
                        continue
                    # Submit tile to be rendered into the queue
                    t = (name, mx, my, z, meta_size[z])
                    queue.put(t)

    # Signal render threads to exit by sending empty request to queue
    for i in xrange(num_threads):
        queue.put(None)
    # wait for pending rendering jobs to complete
    queue.join()
    for i in xrange(num_threads):
        renderers[i].join()

    bar.update(counter)
    bar.finish()



if __name__ == "__main__":
	
    try:
        mapfile = os.environ['MAPNIK_MAP_FILE']
    except KeyError:
        mapfile = MAP_FILE
    try:
        tile_dir = os.environ['MAPNIK_TILE_DIR']
    except KeyError:
        tile_dir = TILE_DIR

    if not tile_dir.endswith('/'):
        tile_dir += '/'

    # Start with an overview

    # Initialise Generate tiles with devision BBOX on little bloks for optimise generation,
    # or method read bbox from file.

    # method for read bboxs from list-file
    bbox_f = open(BBOX_FILE, 'r')
    lst = set(bbox_f)
    bbox_f.close()
    render_tiles(set([tuple([float(coord) for coord in bb.strip().split(',')]) for bb in lst]),
                 mapfile, tile_dir, MIN_ZOOM, MAX_ZOOM, GEN_NAME, NUM_THREADS)
