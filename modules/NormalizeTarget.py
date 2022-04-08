import pandas as pd
import geopandas as gpd
import os
import re

class NormalizeTarget:
    def __init__(self, dir, target):
        # self.dataset = pd.read_csv(dir+'/'+dataset, low_memory=False)
        self.dir = dir
        self.popFiles = []
        self.aggregatedData = []
        self.target = target

    def getFiles(self):
        for filename in os.listdir(self.dir):
            if filename.startswith('population_2'):
                self.popFiles.append(filename)
            elif filename.startswith('aggregated'):
                self.aggregatedData.append(filename)
            else:
                continue

    def mergePopulationFiles(self):
        data = []
        for filename in self.popFiles:
            pop = pd.read_csv(os.path.join(self.dir, filename))
            pop.rename({filename.split('.')[0]:'population'}, axis=1, inplace=True)
            pop['year'] = re.findall('[0-9]+', filename)[0]
            pop['year'] = pop['year'].astype(int)
            data.append(pop)
        return pd.concat(data)

    def groupPopulationPerAuth(self, data, auth):
        print(data.groupby(auth, as_index=False).mean()[[auth, 'population']])
        return data.groupby(auth, as_index=False).mean()[[auth, 'population']]

    def mergePopulationToData(self, population, auth_names):
        normalized_data = []
        for file in self.aggregatedData:
            data = gpd.read_file(self.dir+'/'+file)
            data = data.merge(population, how='left', left_on='auth', right_on=auth_names[1])
            data.dropna(inplace=True)
            # data['normalized_target'] = data[self.target] / data['population']
            # print(data['normalized_target'])
            # print(data.shape)
        # print(data.head())
        print(data.columns)
        # self.dataset.drop(['Unnamed: 0'], axis=1, inplace=True)

    def normalization(self, data):
        self.dataset['normalized_target'] = self.dataset[self.target] / self.dataset['population']




