import pandas as pd

from DatasetCleaning import DatasetCleaning
from PopulationData import PopulationData

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

        population_data = PopulationData("population_data.csv", 2005, 2017)
        population_data.saveAnnualRecords(["laname21", "ladcode21"], "data")
        population_data.getPopulationsDataFrames(["laname21", "ladcode21"])
        dataframes = population_data.population_dataframes
        print(dataframes[0].head())


if __name__ == "__main__":
    driver = Main()
    driver.main()
