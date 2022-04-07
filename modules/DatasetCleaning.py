import sys
import os

class DatasetCleaning:
    def __init__(self, dataset, attributesFile):
        if not os.path.isdir("data"):
            os.mkdir("data")

        try:
            # deep copy of the dataset so that the warnings can be surpressed
            self.dataset = dataset.copy(deep=True)
            # read the attributes from text file
            self.attributes = []
            self.dataframe_size_mb = self.dataset.memory_usage().sum() / 1_000_000
            self.optimal_splits = -1
            for i in range(1, 10):
                # check if chunk is smaller than 100MB
                if (self.dataframe_size_mb / i < 100):
                    optimum = i
                    self.optimal_splits = optimum
                    break

            with open(attributesFile, 'r') as fh:
                for line in fh.readlines():
                    attribute = line.strip()
                    self.attributes.append(attribute)
        except Exception as e:
            print("Error: %s" % e)
            sys.exit(-1)

    def selectAttributes(self):
        self.dataset = self.dataset[self.attributes]

    def reportMissingValues(self):
        if not os.path.isdir("reports"):
            os.mkdir("reports")

        # get number of nans per column
        with open("reports/Missing-values-report.txt", 'w') as fh:
            fh.write("Missing Values in the dataset:\n")
            for column in self.dataset.columns:
                n_nans = self.dataset[column].isnull().sum()
                if n_nans > 0:
                    fh.write(
                        f"[ MISSING VALUES ] {column} : {n_nans}. Ratio to all records: {round(n_nans / len(self.dataset[column]), 3)}\n")
                else:
                    fh.write(f"{column} : {n_nans}\n")

    def removeMissingValues(self):
        self.dataset.dropna(axis=0, how="any", thresh=None, subset=None, inplace=True)

    def optimizeDatatypes(self):
        # the assumption here is that there are no fractions,
        # as we have speed limits, number of vehicles, number of casualties
        # and year - all relatively small integers
        for column in self.dataset.columns:
            datatype = self.dataset[column].dtypes
            if datatype != "object":
                minimal = self.dataset[column].min()
                maximal = self.dataset[column].max()
                if ((minimal >= 0) & (maximal < 256)):
                    self.dataset[column] = self.dataset[column].astype("uint8")
                elif ((minimal >= 0) & (maximal < 65535)):
                    self.dataset[column] = self.dataset[column].astype("uint16")

    def saveDataset(self, filename):
        """
        :param filename: output file
        :return: None. Saves to disk
        """
        self.dataset.to_csv(f"data/Optimized_{filename}.csv")

    def splitDataset(self, dataframe, save=False):

        dataframes = []
        splits = self.optimal_splits - 1

        one_part_size = int(self.dataset.shape[0] / self.optimal_splits)
        lower_boundary = 0
        upper_boundary = one_part_size

        for i in range(splits):
            dataframes.append(self.dataset.iloc[lower_boundary:upper_boundary])
            lower_boundary += one_part_size
            upper_boundary += one_part_size
        dataframes.append(self.dataset.iloc[lower_boundary:])

        index = 0
        if (save):
            for dataframe in dataframes:
                index += 1
                dataframe.to_csv(f"data/Optimized_UK_{index}.csv")

        return dataframes

