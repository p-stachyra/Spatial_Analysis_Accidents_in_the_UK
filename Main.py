import pandas as pd

from modules.DatasetCleaning import DatasetCleaning
from modules.PopulationData import PopulationData
from modules.AssembleDataset import AssembleDataset
from modules.VariablesPreprocessing import DataPreprocessing
from modules.NormalizeTarget import NormalizeTarget


# main driver class
class Main:
    def main(self):
        dataset = pd.read_csv("data/Accident_Information.csv", low_memory=False)
        dc = DatasetCleaning(dataset, "attributes.txt")
        dc.selectAttributes()
        dc.reportMissingValues()
        dc.removeMissingValues()
        dc.optimizeDatatypes()
        dc.splitDataset()

        # print(dc.dataset.dtypes)
        # print("Shapes")
        # print("General dataset shape:", dc.dataset.shape)
        # print("Fragmented dataset shape:", pd.concat(dc.fragmented_dataset).shape)
        # dc.saveFragmentedDataset("data", "Fragmented_UK_Accidents")
        # assembler = AssembleDataset("Fragmented", "data")
        # assembler.assembleFromCSVFiles()
        # optimized_dataset = assembler.dataset
        # print("Reassembled dataset shape:", optimized_dataset.shape)
        # optimized_dataset.drop(columns=["Unnamed: 0"], inplace=True)
        # print(optimized_dataset.columns)
        # print(optimized_dataset["Local_Authority_(District)"].value_counts())

        dp = DataPreprocessing(dc.dataset, print_progress=True)
        dp.formatVariables()
        dp.geoTransform()
        dp.sjoinDistricts()
        dp.aggregateDistricts(save=True)

        # TODO
        # as we are not able to upload the Accidents_Information file anyway,
        # use the dataset already in memory
        # dc.dataset: the object in memory optimized, current dataset
        # this is the same dataset as the Accidents_Information, but with selected attributes (which are in
        # attributes.txt) and with optimal data types.
        # pass this object to the DataPreprocessing class

        # TODO
        # Take the average population across these 12 years and normalize casualties counts with it.

        nt = NormalizeTarget("data/", "casualties")
        population_df = nt.mergePopulationFiles()
        aggrData, aggCols = nt.aggregateData("geometry", "auth", ["Accident_Index", "Local_Authority_(District)", "year",
                                                                  "index"])
        nt.normalize_gdf(population_df, aggrData, aggCols)

        # population_data = PopulationData("data/population_data.csv", 2005, 2017)
        # population_data.saveAnnualRecords(["laname21", "ladcode21"], "data")
        # population_data.getPopulationsDataFrames(["laname21", "ladcode21"])
        # dataframes = population_data.population_dataframes
        #print(dataframes[0].head())


if __name__ == "__main__":
    driver = Main()
    driver.main()
