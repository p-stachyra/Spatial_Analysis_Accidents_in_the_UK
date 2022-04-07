import pandas as pd

from modules.DatasetCleaning import DatasetCleaning
from modules.PopulationData import PopulationData
from modules.VariablesPreprocessing import DataPreprocessing


# main driver class
class Main:
    def main(self):
        dataset = pd.read_csv("data/Accident_Information.csv", low_memory=False)
        dc = DatasetCleaning(dataset, "attributes.txt")
        dc.selectAttributes()
        dc.reportMissingValues()
        dc.removeMissingValues()
        dc.optimizeDatatypes()
        dc.splitDataset(dataset, save=True)
        print(dc.dataset.dtypes)

        dp = DataPreprocessing(print_progress=True)
        dp.formatVariables()
        dp.geoTransform()
        dp.sjoinDistricts()
        dp.aggregateDistricts(save=True)

        population_data = PopulationData("data/population_data.csv", 2005, 2017)
        population_data.saveAnnualRecords(["laname21", "ladcode21"], "data")
        population_data.getPopulationsDataFrames(["laname21", "ladcode21"])
        dataframes = population_data.population_dataframes
        print(dataframes[0].head())


if __name__ == "__main__":
    driver = Main()
    driver.main()
