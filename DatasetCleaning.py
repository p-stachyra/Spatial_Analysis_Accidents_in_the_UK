import sys

class DatasetCleaning:
    def __init__(self, dataset, attributesFile):
        try:
            self.dataset = dataset
            # read the attributes from text file
            self.attributes = []
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
        # get number of nans per column
        with open("Missing-values-report.txt", 'w') as fh:
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
        self.dataset.to_csv(f"Optimized_{filename}.csv")

