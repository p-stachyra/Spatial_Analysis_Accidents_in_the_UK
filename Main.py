import pandas as pd

from DatasetCleaning import DatasetCleaning

# main driver class
class Main:
    def main(self):
        dataset = pd.read_csv("Accident_Information.csv", low_memory=False)
        dc = DatasetCleaning(dataset, "attributes.txt")
        dc.selectAttributes()
        dc.reportMissingValues()
        dc.removeMissingValues()
        dc.optimizeDatatypes()
        dc.saveDataset("Accidents_UK")
        print(dc.dataset.dtypes)


if __name__ == "__main__":
    driver = Main()
    driver.main()
