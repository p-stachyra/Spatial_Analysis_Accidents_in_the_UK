import pandas as pd
import geopandas as gpd
import os
import re
from pyproj import CRS

class NormalizeTarget:
    def __init__(self, dir, target):
        self.dir = dir
        self.aggregatedData = []
        self.target = target
        self.norm_df = None

        for filename in os.listdir(self.dir):
            if filename.startswith('aggregated'):
                self.aggregatedData.append(gpd.read_file(dir + filename, index_col=0, header=0))
            else:
                continue

    def mergePopulationFiles(self):
        pop_path_list = list(filter(re.compile("population_[0-9]+").match, os.listdir(self.dir)))
        pop_path_list = [self.dir + x for x in pop_path_list]

        # Store list of population sub-datasets
        pop_list = []
        for f in pop_path_list:
            pop_year = pd.read_csv(f, index_col=0, header=0).reset_index()
            pop_year.columns = ["auth", "auth_id", "population"]
            pop_list.append(pop_year)

        # Concatenate list of sub-datasets
        pop_concat = pd.concat(pop_list, axis=0, ignore_index=True)

        # Aggregate concatenated dataset on local authority level
        pop_aggr = pop_concat.groupby("auth").aggregate({"auth_id": "first", "population": "sum"}).reset_index()
        return pop_aggr

    def aggregateData(self, geometry_attr, group_attr, drop_attr):
        data = pd.concat(self.aggregatedData, axis=0, ignore_index=True)
        data.drop(drop_attr, axis=1, inplace=True)

        # Define accidents aggregation scheme (agg_dict)
        agg_cols = [x for x in list(data.columns) if x not in [geometry_attr, group_attr]]
        agg_dict = dict(zip(agg_cols, ["sum"] * len(agg_cols)))
        agg_dict[geometry_attr] = "first"

        # Aggregate concatenated dataset on local authority level with aggregation scheme
        gdf_aggr = data.groupby(group_attr).aggregate(agg_dict)
        gdf_aggr.reset_index(inplace=True)

        return gdf_aggr, agg_cols


    def normalize(self, population, aggrGdf, cols):
        # Merge accidents data with population data, normalize attributes
        self.norm_df = aggrGdf.merge(population, on="auth", how="inner")
        self.norm_df[cols] = self.norm_df[cols].apply(lambda x: x / (self.norm_df["population"] / 10000))
        gpd.GeoDataFrame(self.norm_df, geometry="geometry", crs=CRS("EPSG:27700")).to_file(self.dir+"normalized.gpkg",
                                                                                            driver="GPKG")




