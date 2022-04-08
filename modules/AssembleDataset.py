import pandas as pd
import os

class AssembleDataset:
    def __init__(self, pattern, data_directory):
        self.pattern = pattern
        self.directory = data_directory
        self.dataset_chunks = []
        self.dataset = None

    def assembleFromCSVFiles(self):
        """
        A method for assembling chunks of dataset in memory from separate CSV files.
        To run properly, the class must be instantiated with the common pattern in names of CSV files of interest
        And with the directory the method will search through for these files.
        The method appends the datasets read from disk to the dataset_chunks field and performs concatenation of
        these chunks to build a dataframe containing all the records of the complete dataset.
        It sets the None field dataset to the assembled dataset before finishing execution.

        :return: status if successful (0) or unsuccessful (-1)
        """

        status = -1

        try:
            # iterate over the directory passed by the constructor to the class instance looking for
            # CSV files which contain a provided pattern.
            for file in os.listdir(self.directory):
                if (self.pattern in file):
                    self.dataset_chunks.append(pd.read_csv(f"{self.directory}/{file}", low_memory=False))

            self.dataset = pd.concat(self.dataset_chunks)
            status = 0

        except Exception as e:
            print("Error: %s" % e)

        return status


