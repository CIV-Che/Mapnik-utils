#!/usr/bin/env python

#
# This script for generate OSM tiles from coordinate list (part) taked with _make_lst_for_gen_tls.py script,
# This script run on any systep calculate cloud and get particulary list of all tiles coordinate need generated/
# You make define number of generator thread, file with particulary list and any others params.
#

from math import pi,cos,sin,log,exp,atan
from subprocess import call
import sys, os
import multiprocessing

try:
    import mapnik
except:
    import mapnik2 as mapnik

DEG_TO_RAD = pi/180
RAD_TO_DEG = 180/pi

MIN_ZOOM = 4
MAX_ZOOM = 17

MAP_FILE = "/osm/mapnik/osm.xml"
TILE_DIR = "/osm/tiles/"

# Define name of list-file from _make_lst_for_gen_tls.py (tiles-coord)
LIST_TILES = '/osm/update/part_0.list'

## Default number of rendering threads to spawn, should be roughly equal to number of CPU cores available
NUM_THREADS = 20


class GoogleProjection:

    def __init__(self,levels=18):
        self.Bc = []
        self.Cc = []
        self.zc = []
        c = 256
        for d in xrange(0,levels+1):
            e = c/2;
            self.Bc.append(c/360.0)
            self.Cc.append(c/(2 * pi))
            self.zc.append((e,e))
            c *= 2
                
    def fromPixelToLL(self,px,zoom):
        e = self.zc[zoom]
        f = (px[0] - e[0])/self.Bc[zoom]
        g = (px[1] - e[1])/-self.Cc[zoom]
        h = RAD_TO_DEG * ( 2 * atan(exp(g)) - 0.5 * pi)
        return (f,h)


class RenderThread:

    def __init__(self, tile_dir, mapfile, q, maxZoom):
        self.tile_dir = tile_dir
        self.q = q
        self.mapfile = mapfile
        self.maxZoom = maxZoom

    def render_tile(self, tile_uri, x, y, z):
        # Calculate pixel positions of bottom-left & top-right
        p0 = (x * 256, (y + 1) * 256)
        p1 = ((x + 1) * 256, y * 256)

        # Convert to LatLong (EPSG:4326)
        l0 = self.tileproj.fromPixelToLL(p0, z);
        l1 = self.tileproj.fromPixelToLL(p1, z);

        # Convert to map projection (e.g. mercator co-ords EPSG:900913)
        c0 = self.prj.forward(mapnik.Coord(l0[0],l0[1]))
        c1 = self.prj.forward(mapnik.Coord(l1[0],l1[1]))

        bbox = mapnik.Box2d(c0.x,c0.y, c1.x,c1.y)
        render_size = 256
        self.m.resize(render_size, render_size)
        self.m.zoom_to_box(bbox)
        # buffer_size regulate how many bigger around current tile, mapnik request object-data
        # (for matching tile with around tiles), default 128
        self.m.buffer_size = 1024

        # Render image with default Agg renderer
        im = mapnik.Image(render_size, render_size)
        mapnik.render(self.m, im)
        im.save(tile_uri, 'png256')


    def loop(self):
        
        self.m = mapnik.Map(256, 256)
        # Load style XML
        mapnik.load_map(self.m, self.mapfile, True)
        # Obtain <Map> projection
        self.prj = mapnik.Projection(self.m.srs)
        # Projects between tile pixel co-ordinates and LatLong (EPSG:4326)
        self.tileproj = GoogleProjection(self.maxZoom)
                
        while True:
            #Fetch a tile from the queue and render it
            r = self.q.get()
            if (r == None):
                self.q.task_done()
                break
            else:
                (name, tile_uri, x, y, z) = r

            ##Check existance current tile in fs and delete him if it empty-tile (because it may be hard link)
            if not os.path.isfile(tile_uri):
                self.render_tile(tile_uri, x, y, z)
            else:
                if os.stat(tile_uri)[6] == 103: os.remove(tile_uri)
                self.render_tile(tile_uri, x, y, z)

#            self.render_tile(tile_uri, x, y, z)

            ##Change most frequent empty tiles to hard-links
            if os.stat(tile_uri)[6] == 103:
                f = open(tile_uri, "r")
                c = f.read(44)
                f.close()
                if (ord(c[41]) == 242) and (ord(c[42]) == 239) and (ord(c[43]) == 233):
                    os.remove(tile_uri)
                    os.link('/osm/tiles/empty.tiles/land.png', tile_uri)
                elif (ord(c[41]) == 181) and (ord(c[42]) == 208) and (ord(c[43]) == 208):
                    os.remove(tile_uri)
                    os.link('/osm/tiles/empty.tiles/water.png', tile_uri)
                elif (ord(c[41]) == 174) and (ord(c[42]) == 209) and (ord(c[43]) == 160):
                    os.remove(tile_uri)
                    os.link('/osm/tiles/empty.tiles/wood.png', tile_uri)

            self.q.task_done()



def render_tiles(mapfile, tile_dir, minZoom=1, maxZoom=18, num_threads=NUM_THREADS):

    print "render_tiles(", mapfile, tile_dir, minZoom, maxZoom, ")"

    # Launch rendering threads
    queue = multiprocessing.JoinableQueue(96)
    renderers = {}
    for i in xrange(num_threads):
        renderer = RenderThread(tile_dir, mapfile, queue, maxZoom)
        render_thread = multiprocessing.Process(target=renderer.loop)
        render_thread.start()
        renderers[i] = render_thread

    if not os.path.isdir(tile_dir):
        os.mkdir(tile_dir)

    ## input expire tiles list file as string list (array)
    file_tiles = open(LIST_TILES, 'r')
    ## remove doubl elements of list
    list_tiles = set(file_tiles)
    file_tiles.close()
    ## evry string of list split on components
    list_tiles = set([tuple([int(coord) for coord in tile.strip().split('/')]) for tile in list_tiles])
    ## iterate for all tiles in tiles list
    os_path_isdir = os.path.isdir
    os_makedirs = os.makedirs
    queue_put = queue.put
    for tile in list_tiles:
        if tile[0] in xrange(MIN_ZOOM, MAX_ZOOM):
            tile_uri = tile_dir + str(tile[0]) + '/' + str(tile[1])
            if not os_path_isdir(tile_uri):
                os_makedirs(tile_uri)
            tile_uri = tile_uri + '/' + str(tile[2]) + '.png'
            # Submit tile to be rendered into the queue
            t = ('generator', tile_uri, tile[1], tile[2], tile[0])
            queue_put(t)

    # Signal render threads to exit by sending empty request to queue
    for i in xrange(num_threads):
        queue.put(None)
    # wait for pending rendering jobs to complete
    queue.join()
    for i in xrange(num_threads):
        renderers[i].join()



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
        tile_dir = tile_dir + '/'

    if (not os.path.isfile(LIST_TILES)):
        sys.exit('File from LIST_TILES %s not found' % LIST_TILES)

    # Initialise generate tiles
    render_tiles(mapfile, tile_dir, MIN_ZOOM, MAX_ZOOM, NUM_THREADS)
