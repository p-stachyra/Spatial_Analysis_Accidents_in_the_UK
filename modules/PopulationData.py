import pandas as pd
import os

class PopulationData:
    def __init__(self, filename, min_year, max_year):
        # load the population CSV files
        self.dataset = pd.read_csv(filename, low_memory=False)
        # a list to store dataframes for each year
        self.population_dataframes = []

        # prepare all the columns for yearly population
        self.population_by_year = []
        for column in self.dataset.columns:
            # select only files regarding the population data
            if ("population" in column):
                # get only the attributes between min_year (inclusive) and max_year (inclusive)
                if ((int(column.split("_")[-1]) >= min_year) & (int(column.split("_")[-1]) <= max_year)):
                    self.population_by_year.append(column)

    def saveAnnualRecords(self, groupby_attributes, output_directory):
        """

        :param groupby_attributes: the attribute to perform grouping of records
        :param output_directory: the directory to save all of the population CSV files
        :return: status if successful (0) or unsuccessful (-1)
        """

        status = -1

        try:
            # prepare directory to store records
            if not os.path.isdir(output_directory):
                os.mkdir(output_directory)

            # save the records grouped by year
            for year in self.population_by_year:
                # check if NT standard
                if (os.name == "nt"):
                    pd.DataFrame(self.dataset.groupby(groupby_attributes)[year].sum()).to_csv(f"{output_directory}\\{year}.csv")
                # otherwise use a forward slash
                else:
                    pd.DataFrame(self.dataset.groupby(groupby_attributes)[year].sum()).to_csv(f"{output_directory}/{year}.csv")
            status = 0

        except Exception as e:
            print("Error %s" % e)

        return status

    def getPopulationsDataFrames(self, groupby_attributes):
        """

        :param groupby_attributes: the attribute to perform grouping of records
        :return: status if successful (0) or unsuccessful (-1)
        """
        status = -1

        try:
            for year in self.population_by_year:
                self.population_dataframes.append(pd.DataFrame(self.dataset.groupby(groupby_attributes)[year].sum()))
            status = 0
        except Exception as e:
            print("Error %s" % e)

        return status
