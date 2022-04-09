import geopandas as gpd
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW

class AnalyzeGWR:
    def __init__(self, geopackage, dependent_variable, independent_variables):

        self.dataset = gpd.read_file(geopackage)
        self.dependent_variable = self.dataset[dependent_variable].values
        self.independent_variables = self.dataset[independent_variables].values

        self.g_coords = []

        for row in zip(self.dataset.geometry.centroid.x, self.dataset.geometry.centroid.y):
            self.g_coords.append(row)

        self.selector = None
        self.bandwidth = None
        self.results = None

    def calibrateRegression(self):
        status = -1
        try:
            self.selector = Sel_BW(self.g_coords, self.dependent_variable, self.independent_variables)
            self.bandwidth = self.selector.search(bw_min=2)
            status = 0
        except Exception as e:
            print("Error %s" % e)
        return status

    def fitRegression(self):

        status = -1

        if (self.bandwidth == None):
            return status

        try:
            self.results = GWR(self.g_coords, self.dependent_variable, self.independent_variables, self.bandwidth).fit()
            status = 0

        except Exception as e:
            print("Error: %s" % e)

        return status