"""Thanks to for helping me find my way around gdb databases.

https://github.com/rouault/dump_gdbtable/wiki/FGDB-Spec

The first table in a database, a00000001.gdbtable, lists all the
tables in the database, including itself.

There is no table that lists all tables that do not list themselves.

For the database of NOAA flood data that I am exploring, the first 20
rows are as follows:

0            GDB_SystemCatalog           0     None
1                   GDB_DBTune           0     None
2              GDB_SpatialRefs           0     None
3                    GDB_Items           0     None
4                GDB_ItemTypes           0     None
5        GDB_ItemRelationships           0     None
6    GDB_ItemRelationshipTypes           0     None
7               GDB_ReplicaLog           2     None
8             MA_slr_depth_0ft           0     None
9    fras_ras_MA_slr_depth_0ft           0     None
10   fras_aux_MA_slr_depth_0ft           0     None
11   fras_blk_MA_slr_depth_0ft           0     None
12   fras_bnd_MA_slr_depth_0ft           0     None
13           MA_slr_depth_10ft           0     None
14  fras_ras_MA_slr_depth_10ft           0     None
15  fras_aux_MA_slr_depth_10ft           0     None
16  fras_blk_MA_slr_depth_10ft           0     None
17  fras_bnd_MA_slr_depth_10ft           0     None
18            MA_slr_depth_1ft           0     None
19   fras_ras_MA_slr_depth_1ft           0     None
...



"""


import argparse
from pathlib import Path
import struct
from collections import deque, Counter
from pprint import pprint

import gdal

import numpy as n
from blume import magic, farm

from matplotlib import pyplot as plt

import geopandas

class Shark(magic.Ball):

    TABLES = dict(
        catalog=1,
        config=2,
        coords=3,
        layers=4,
    )
    
    def __init__(self, path='.', name='MA'):

        super().__init__()

        self.path = Path(path)

        self.depths = list(range(0, 11))

        self.name = name


    async def start(self):
        
        pprint(self.load_table(1).head(self.topn))

        tables = self.load_table(self.TABLES['catalog'])
        print(tables.index)
        table_lookup = {}
        for ix,name in enumerate(tables.Name):
            table_lookup[name] = ix + 1
            print(name)

        self.table_lookup = table_lookup
        #return

        config = self.load_table(self.TABLES['config'])
        print(config.head())

        coords = self.load_table(self.TABLES['coords'])
        print(coords.head())

        layers = self.load_table(self.TABLES['layers'])


    async def run(self):
        
        # FIXME.  These come in fours ras, aux, blk and bnd.
        # blk is the actual raster data.
        # bnd has data about the geometry of the grid
        # -- coords has more esoteric coordinate reference info.
        for database in sorted(self.path.glob('*.gdbtable')):
            print(database)
            # maybe not do this, it can take a while
            print('loading with geopandas may take a while')
            df = geopandas.read_file(database, rows=self.topn)

            print(df.columns)
            print(len(df))
            print(df.head(self.topn))

    def load_table(self, n=1):
        """ Load a table """
        df = geopandas.read_file(self.path / f'a{n:08x}.gdbtable')
        return df

    def make_index(self):

        for depth in self.depths:
            df = self.get_table(depth)

    def get_table(depth):

        name = f'{self.name}_slrLdepth_{depth}ft'

        df = open_database(self.path, self.table_lookup[name])

        return df
                               
def open_database(path, n):

    return gdal.ogr.Open(str(Path(path) / f'a{n:08x}.gdbtable'))


def generate_features(df):
    
    layer = df.GetLayer(0)

    data = []
    for item in range(layer.GetFeatureCount()):
        feature = layer.GetFeature(item + 1)
        yield feature.items()


if __name__ == '__main__':

    parser = magic.Parser()
    parser.add_argument('-topn', type=int, default=20)

    shark = Shark()
    
    shark.update(parser.parse_args())

    magic.run(shark.start())
    
    magic.run(shark.run())
