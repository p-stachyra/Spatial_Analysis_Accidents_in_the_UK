import sys
import os
import pandas as pd
import numpy as np
import geopandas as gpd
from pyproj import CRS
from tqdm import tqdm


class DataPreprocessing:
    def __init__(self, dataset, districts_path="data/Local_authorities.shp", output_dir="data/", print_progress=False):
        try:

            self.print_progress = print_progress
            if self.print_progress:
                print("Loading dataset")

            # Load accidents dataset from memory
            self.accidents_df = dataset

            # Read local authorities (districts) data
            self.districts = gpd.read_file(districts_path)

            # Store Lat and Lang attribute names for GeoDataFrame creation
            self.lat_lng = ["Latitude", "Longitude"]

            # Store attribute names for join operation purposes
            self.cat_attributes, self.num_attributes, self.group_attributes = [], [], []

            # Output directory for aggregated data
            self.output_dir = output_dir

        except Exception as e:
            print("Error: %s" % e)
            sys.exit(-1)

    def formatVariables(self):
        """
        Reformat merging categorical classes.
        Returns GeoDataFrame with CRS of original data.
        :return: 1 if successful
        """

        if self.print_progress:
            print("Formatting variables")

        # Rename variables
        self.accidents_df.rename(
            {
                "1st_Road_Class": "road_class",
                "Accident_Severity": "severity",
                "Carriageway_Hazards": "hazards",
                "Junction_Detail": "junction",
                "Light_Conditions": "dark",
                "Number_of_Casualties": "casualties",
                "Number_of_Vehicles": "vehicles",
                "Road_Surface_Conditions": "wet",
                "Road_Type": "road_type",
                "Special_Conditions_at_Site": "special",
                "Speed_limit": "speed",
                "Time": "time",
                "Urban_or_Rural_Area": "urban",
                "Weather_Conditions": "weather",
                "Year": "year"
            },
            axis=1, inplace=True
        )

        # Reformat variables
        self.accidents_df.replace(
            {
                "road_class": {'A': 0, 'B': 1, 'C': 2, "A(M)": 0, "Motorway": 0, "Unclassified": 3},
                "severity": {"Slight": 0, "Serious": 1, "Fatal": 2},
                "hazards": {"None": 0},
                "junction": {"Not at junction or within 20 metres": 0},
                "dark": {"Daylight": 0},
                "wet": {"Dry": 0, "Data missing or out of range": 0},
                "road_type": {"Single carriageway": 0, "Dual carriageway": 1},
                "special": {"None": 0},
                # "speed": {30: 0, 60: 1},
                "urban": {"Rural": 0, "Urban": 1, "Unallocated": 1},
                "weather": {"Fine no high winds": 0, "Unknown": 0, "Data missing or out of range": 0}
            },
            inplace=True
        )
        self.accidents_df.loc[self.accidents_df["hazards"] != 0, "hazards"] = 1
        self.accidents_df.loc[self.accidents_df["junction"] != 0, "junction"] = 1
        self.accidents_df.loc[self.accidents_df["dark"] != 0, "dark"] = 1
        self.accidents_df.loc[self.accidents_df["vehicles"] >= 5, "vehicles"] = 5
        self.accidents_df.loc[self.accidents_df["wet"] != 0, "wet"] = 1
        self.accidents_df.loc[
            (self.accidents_df["road_type"] != 0) & (self.accidents_df["road_type"] != 1), "road_type"
        ] = 2
        self.accidents_df.loc[self.accidents_df["special"] != 0, "special"] = 1

        self.accidents_df.loc[self.accidents_df["speed"] <= 30, "speed"] = 0
        self.accidents_df.loc[
            (self.accidents_df["speed"] > 30) & (self.accidents_df["speed"] < 60), "speed"
            ] = 1
        self.accidents_df.loc[self.accidents_df["speed"] >= 60, "speed"] = 2

        self.accidents_df.loc[self.accidents_df["weather"] != 0, "weather"] = 1

        self.accidents_df.dropna(subset="speed", inplace=True)

        return 0

    def geoTransform(self):
        """
        Transform DataFrame to GeoDataFrame based on given geometry attributes
        :return: 1 if successful
        """
        if self.print_progress:
            print("Transforming to GeoDataFrame")

        # The data originally comes from epsg 4326
        crs = CRS("EPSG:4326")

        # Read latitude and longitude from attributes
        geometry = gpd.points_from_xy(self.accidents_df[self.lat_lng[1]], self.accidents_df[self.lat_lng[0]])

        # Overwrite existing dataset
        self.accidents_df = gpd.GeoDataFrame(self.accidents_df, crs=crs, geometry=geometry)

        return 0

    def sjoinDistricts(self):
        """
        Join Accidents data with district (local authority) dataset
        :return: 1 if successful
        """
        if self.print_progress:
            print("Joining with Local Authorities data")

        # Spatial join of accident points (reprojected)
        self.accidents_df = self.accidents_df.to_crs(27700).sjoin(
            self.districts[["geometry", "LAD21NM"]], how="right", predicate="within"
        )

        # Set indices, drop nans, rename some of the columns
        self.accidents_df.rename({"LAD21NM": "auth"}, axis=1, inplace=True)
        # Drop nans as we performed the right outer join
        self.accidents_df.dropna(subset=["index_left"], inplace=True)
        self.accidents_df['index_left'] = self.accidents_df['index_left'].astype(int)
        self.accidents_df.reset_index(inplace=True)
        self.accidents_df.set_index("index_left", inplace=True)
        self.accidents_df.index.rename("", inplace=True)
        self.accidents_df.drop(["Latitude", "Longitude", "time"], axis=1, inplace=True)
        self.accidents_df.sort_index(inplace=True)

        # After spatial join operation, change numerical and categorical datatypes to int
        self.num_attributes = [
            "index", "casualties"
        ]
        self.cat_attributes = [
            "road_class", "severity", "hazards", "junction", "dark", "vehicles",
            "wet", "road_type", "special", "speed", "urban", "weather"
        ]
        self.group_attributes = [
            "geometry", "year", "auth"
        ]
        self.accidents_df[self.num_attributes + self.cat_attributes] = \
            self.accidents_df[self.num_attributes + self.cat_attributes].astype("int")

        return 0

    def aggregateDistricts(self, save=False, return_list=False):
        """
        Groups data by year,county keys and aggregates attributes by sum.
        :param save: whether to save aggregated data (GeoPackage format)
        :param return_list: whether to return list of aggregated GeoDataFrames
        :return: list of GeoDataFrames aggregated by year and district (local authority)
        """
        if self.print_progress:
            print("Aggregating data")

        # Create a list of dataframes for each year
        years = list(self.accidents_df.year.unique().astype(int))
        dfs_agg = []
        for y in years:
            dfs_agg.append(self.accidents_df.loc[self.accidents_df['year'] == y])

        # Define aggregation scheme (dictionary) based on one of yearly datasets
        one_hot = pd.get_dummies(dfs_agg[0], columns=self.cat_attributes)
        to_sum = [x for x in list(one_hot.columns) if x not in self.group_attributes + self.num_attributes]
        agg_dict = dict(zip(to_sum, ["sum"] * len(to_sum)))
        agg_dict.update(dict(zip(self.group_attributes, ["first"] * 3)))

        # Aggregate data
        uk_crs = CRS("EPSG:27700")
        for i in range(len(dfs_agg)):
            one_hot = pd.get_dummies(dfs_agg[i], columns=self.cat_attributes)
            dfs_agg[i] = gpd.GeoDataFrame(
                one_hot.groupby("index").agg(agg_dict), crs=uk_crs, geometry="geometry"
            )

        # Save aggregated data
        if save:

            # Create output directory if doesn't exist
            if not os.path.isdir(self.output_dir):
                os.mkdir(self.output_dir)

            if self.print_progress:
                print("Saving aggregated data")

            # Save yearly datasets
            for d, y in tqdm(zip(dfs_agg, years)):
                d.to_file(self.output_dir + f"aggregated_{y}.gpkg", driver="GPKG")

        if return_list:
            return dfs_agg
        else:
            return 0


# Example:
# dp = DataPreprocessing(print_progress=True)
# dp.formatVariables()
# dp.geoTransform()
# dp.sjoinDistricts()
# dp.aggregateDistricts(save=True)
