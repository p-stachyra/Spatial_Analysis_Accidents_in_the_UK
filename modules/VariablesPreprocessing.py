import sys
import os
import pandas as pd
import geopandas as gpd
from pyproj import CRS
from tqdm import tqdm
import re


class DataPreprocessing:
    def __init__(self, districts_path="Local_authorities.shp", attributes_path="attributes.txt",
                 output_dir="data/", data_dir="data/", print_progress=False):
        try:
            self.main_dir = re.sub(r"\\", r"/", os.path.dirname(os.getcwd()))+"/"
            self.data_dir = data_dir
            data_files = os.listdir(self.main_dir + data_dir)
            dfs_list = list(filter(re.compile("Optimized_UK").match, data_files))
            dfs_list = [self.main_dir+data_dir + x for x in dfs_list]
            li = []
            self.print_progress = print_progress
            if self.print_progress:
                print("Loading optimized data")
            for f in dfs_list:
                li.append(pd.read_csv(f, index_col=0, header=0))
            self.accidents_df = pd.concat(li, axis=0, ignore_index=True)

            self.districts = gpd.read_file(self.main_dir+data_dir+districts_path)
            self.attributes = []
            with open(self.main_dir+attributes_path, 'r') as fh:
                for line in fh.readlines():
                    attribute = line.strip()
                    self.attributes.append(attribute)
            drop_attributes = ["Accident_Index", "Junction_Control", "Local_Authority_(District)"]
            self.attributes = [x for x in self.attributes if x not in drop_attributes]
            self.lat_lng = ["Latitude", "Longitude"]
            self.cat_attributes, self.num_attributes, self.group_attributes = [], [], []
            self.output_dir = output_dir

        except Exception as e:
            print("Error: %s" % e)
            sys.exit(-1)

    def formatVariables(self):
        """
        Reformat the dataframe by excluding unnecessary variables,
        renaming analyzed ones and merging categorical classes.
        Returns GeoDataFrame with CRS of original data.
        :return: 1 if successful
        """
        if self.print_progress:
            print("Formatting variables")

        # Include only analyzed attributes:
        self.accidents_df = self.accidents_df[self.attributes]

        # Rename variables
        self.accidents_df.rename(
            {
                # "index": "auth_id",
                "1st_Road_Class": "road_class",
                "Accident_Severity": "severity",
                "Carriageway_Hazards": "hazards",
                "Junction_Detail": "junction",
                "Light_Conditions": "dark",
                # "Local_Authority_(District)": "auth",
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
                # "road_class": {"A(M)": 'A', "Motorway": 'A', "Unclassified": np.nan},
                # for now leaving road class as it is
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
        # For now assigning 5 or more vehicles to one class:
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

        return 1

    def geoTransform(self):
        """
        Transform DataFrame to GeoDataFrame based on given geometry attributes
        :return: 1 if successful
        """
        if self.print_progress:
            print("Transforming to GeoDataFrame")
        crs = CRS("EPSG:4326")
        # geometry = [Point(x,y) for x,y in zip(df['longitude'], df['latitude'])]
        geometry = gpd.points_from_xy(self.accidents_df[self.lat_lng[1]], self.accidents_df[self.lat_lng[0]])
        self.accidents_df = gpd.GeoDataFrame(self.accidents_df, crs=crs, geometry=geometry)
        return 1

    def sjoinDistricts(self):
        """
        Join Accidents data with district (local authority) dataset
        :return: 1 if successful
        """
        if self.print_progress:
            print("Joining with Local Authorities data")
        # self.districts.plot(figsize=(10, 6))
        # print(self.districts.shape)
        self.accidents_df = self.accidents_df.to_crs(27700).sjoin(
            self.districts[["geometry", "LAD21NM"]], how="right", predicate="within"
        )

        # Set indices, drop nans, rename some of the columns
        self.accidents_df.rename({"LAD21NM": "auth"}, axis=1, inplace=True)
        self.accidents_df.dropna(subset=["index_left"], inplace=True)
        self.accidents_df['index_left'] = self.accidents_df['index_left'].astype(int)
        self.accidents_df.reset_index(inplace=True)
        self.accidents_df.set_index("index_left", inplace=True)
        self.accidents_df.index.rename("", inplace=True)
        self.accidents_df.drop(["Latitude", "Longitude", "time"], axis=1, inplace=True)
        self.accidents_df.sort_index(inplace=True)

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

        return 1

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
        to_sum = [x for x in list(one_hot.columns) if x in self.cat_attributes]
        agg_dict = dict(zip(to_sum, ["sum"] * len(to_sum)))
        agg_dict.update(dict(zip(self.group_attributes, ["first"] * 3)))

        # Store aggregated data
        if self.print_progress:
            print("Saving aggregated data")
        uk_crs = CRS("EPSG:27700")
        for i, d in enumerate(dfs_agg):
            # print(i, d.shape, y)
            buffer = pd.get_dummies(d, columns=self.cat_attributes)
            buffer = buffer.groupby("index").agg(agg_dict)
            dfs_agg[i] = gpd.GeoDataFrame(buffer, crs=uk_crs, geometry="geometry")
        # buffer = None

        # Save aggregated data
        if save:
            # if not os.path.isdir(self.output_dir):
            #     os.mkdir(self.output_dir)
            for d, y in tqdm(zip(dfs_agg, years)):
                d.to_file(self.main_dir + self.data_dir + f"aggregated_{y}.gpkg", driver="GPKG")

        if return_list:
            return dfs_agg
        else:
            return 1


# Example:
# dp = DataPreprocessing(print_progress=True)
# dp.formatVariables()
# dp.geoTransform()
# dp.sjoinDistricts()
# dp.aggregateDistricts(save=True)
