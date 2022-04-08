import sys
import os

class DatasetCleaning:
    def __init__(self, dataset, attributesFile):

        # A constant for specifying the maximal file size that can be hosted in a remote repository.
        # The size should be in MB
        MAX_FILESIZE = 100
        # A constant for specifying the maximal number of times the program will attempt to find the optimal
        # number of splits for dividing the dataset into chunks.
        # Basically, the maximal number of chunks we seek.
        MAX_ITER = 10

        # ensure that data
        if not os.path.isdir("data"):
            os.mkdir("data")

        try:
            # deep copy of the dataset so that the warnings can be avoided
            self.dataset = dataset.copy(deep=True)

            # A field for storing attributes of interest
            # the assumption is that the attributes are stored in a text file and can be loaded during later
            # steps of execution.
            self.attributes = []

            # get the size of the dataframe, as objects weighting more than MAX_FILESIZE cannot
            # be added to the remote repository.
            self.dataframe_size_mb = self.dataset.memory_usage().sum() / 1_000_000

            # to keep track on how many pieces the dataset must be split to,
            # perform a number of trials to determine the optimal number of splits
            self.optimal_splits = -1
            # run tests to find the optimal number of splits that must be applied to fragment the dataset
            for i in range(1, MAX_ITER):
                # check if chunk is smaller than MAX_FILESIZE
                if (self.dataframe_size_mb / i < MAX_FILESIZE):
                    # if it is, this is the optimal split
                    optimum = i
                    self.optimal_splits = optimum
                    break

            # read the attributes names which must be included in the analysis
            # this is our selection for this research and should be treated as a
            # global decision regarding the whole workflow.
            with open(attributesFile, 'r') as fh:
                for line in fh.readlines():
                    attribute = line.strip()
                    self.attributes.append(attribute)

            # a field for saving a fragmented dataset which contains smaller chunks of the dataframe so that
            # they are no bigger than MAX_FILESIZE
            # if the dataset does not have to be fragmented (as we do not care of the file limits), the dataset can be
            # optimized as a whole and saved using saveDataset() method. In such case, methods splitDataset(),
            # saveFragmentedDataset(), constants MAX_FILESIZE, MAX_ITER and the field optimal_splits are meaningless.
            # the field for saving fragmented dataset will be empty list
            self.fragmented_dataset = []

        except Exception as e:
            print("Error: %s" % e)
            sys.exit(-1)

    def selectAttributes(self):
        """
        A "void" (in practice returns None) method which overwrites the dataset field with a dataset containing
        only the selected attributes, which can be found in attributes.txt file.
        """
        self.dataset = self.dataset[self.attributes]

    def reportMissingValues(self):
        """
        A method for generating a report on missing values found in the dataset.
        The generated text file contains frequencies of missing values for each attribute
        as well as the ratio of missing values to all records.
        :return: status if successful (0) or unsuccessful (-1)
        """
        status = -1

        # ensure that the report can be saved to a separate directory for storing workflow reports.
        if not os.path.isdir("reports"):
            os.mkdir("reports")

        try:
            # get number of nans per attribute
            with open("reports/Missing-values-report.txt", 'w') as fh:
                fh.write("Missing Values in the dataset:\n")
                for column in self.dataset.columns:
                    n_nans = self.dataset[column].isnull().sum()
                    if n_nans > 0:
                        fh.write(
                            f"[ MISSING VALUES ] {column} : {n_nans}. Ratio to all records: {round(n_nans / len(self.dataset[column]), 3)}\n")
                    else:
                        fh.write(f"{column} : {n_nans}\n")
            status = 0

        except Exception as e:
            print("Error: %s" % e)

        return status

    def removeMissingValues(self):
        """
        A method to tackle the problem of missing values - remove them.
        This method can be problematic for further research if many missing values are detected.
        For checking how many of the missing values were found for each attribute, run reportMissingValues() method first
        and check the report on missing values saved to reports/Missing-values-report.txt

        :return: status if successful (0) or unsuccessful (-1)
        """
        status = -1
        try:
            self.dataset.dropna(axis=0, how="any", thresh=None, subset=None, inplace=True)
            status = 0
        except Exception as e:
            print("Error: %s" % e)

        return status

    def optimizeDatatypes(self):
        """
        A method for changing the data types of attributes. The method performs conditional tests to determine the
        range of integers (the assumption is that the dataset contains integers for numeric values) and selects the
        data type which can hold the values of a certain attribute with minimal memory cost.
        :return: status if successful (0) or unsuccessful (-1)
        """
        # the assumption here is that there are no fractions,
        # as we have speed limits, number of vehicles, number of casualties
        # and year - all relatively small integers
        status = -1

        try:
            for column in self.dataset.columns:
                datatype = self.dataset[column].dtypes
                if datatype != "object":
                    minimal = self.dataset[column].min()
                    maximal = self.dataset[column].max()
                    if ((minimal >= 0) & (maximal < 256)):
                        self.dataset[column] = self.dataset[column].astype("uint8")
                    elif ((minimal >= 0) & (maximal < 65535)):
                        self.dataset[column] = self.dataset[column].astype("uint16")
            status = 0

        except Exception as e:
            print("Error %s" % e)

        return status

    def splitDataset(self):
        """
        A method for splitting the dataset into chunks so that each of them can be saved to a separate file
        which does not exceed the specified file size limit.
        The method replies on optimal_splits field which is determined using a for loop in the constructor - the dataset
        will be split to the same number of chunks as the optimal_splits number.
        :return: status if successful (0) or unsuccessful (-1)
        """

        status = -1

        # The number of splits will be the optimal splits - 1, as the last split should
        # take all the skipped fractions of the dataset, so the last chunk will contain the records which we
        # discarded by using int data type for specifying previous split ranges.
        splits = self.optimal_splits - 1

        try:
            # the size of a single chunk of the dataset
            one_part_size = int(self.dataset.shape[0] / self.optimal_splits)

            # keeping track of the min and max index to split the dataset
            lower_boundary = 0
            upper_boundary = one_part_size

            # split the dataset to the optimal_splits - 1 parts.
            for i in range(splits):
                self.fragmented_dataset.append(self.dataset.iloc[lower_boundary:upper_boundary])
                lower_boundary += one_part_size
                upper_boundary += one_part_size
            # The last part which was not included in the for loop must be added so that the dataset is complete
            self.fragmented_dataset.append(self.dataset.iloc[lower_boundary:])

            # if all successful, change status to 0 exitcode
            status = 0

        except Exception as e:
            print("Error: %s" % e)

        return status

    def saveDataset(self, directory, filename):
        """
        :param directory: Directory to which the optimized dataset will be saved
        :param filename: Output file's name of the optimized dataset
        :return: status if successful (0) or unsuccessful (-1)
        """
        if not os.path.isdir(directory):
            os.mkdir(directory)

        status = -1

        try:
            self.dataset.to_csv(f"{directory}/Optimized_{filename}.csv")
            status = 0

        except Exception as e:
            print("Error %s" % e)

        return status

    # Python does not support method overloading by default, so instead of overloading saveDataset
    # allowing it to take additional parameter of fragmented dataset, another method is created.
    def saveFragmentedDataset(self, directory, filename):
        """

        :param directory: Directory to which the optimized dataset will be saved
        :param filename: Output file's name of the optimized dataset
        :return: status if successful (0) or unsuccessful (-1)
        """

        if not os.path.isdir(directory):
            os.mkdir(directory)


        if (len(self.fragmented_dataset) == 0):
            print("Error: the dataset was not fragmented properly. Use splitDataset() method to fragment the dataset.")
            return -1

        status = -1

        try:
            file_index = 1
            for dataset_chunk in self.fragmented_dataset:
                dataset_chunk.to_csv(f"{directory}/Optimized_{filename}_{file_index}.csv")
                file_index += 1
            status = 0

        except Exception as e:
            print("Error %s" % e)

        return status


