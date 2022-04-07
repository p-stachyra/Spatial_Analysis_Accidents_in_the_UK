import pandas as pd
import os
import re

class NormalizeTarget:
    def __init__(self, dataset, dir):
        self.dataset = pd.read_csv(dir+'/'+dataset, low_memory=False)
        self.dir = dir
        self.popFiles = []

    def getPopulationFiles(self):
        for filename in os.listdir(self.dir):
            if filename.startswith('population_2'):
                self.popFiles.append(filename)
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

    def mergePopulationToData(self, population):
        merged = self.dataset.merge(population, how='left', left_on=['Local_Authority_(District)', 'Year'], right_on=['laname21', 'year'])
        merged.dropna(inplace=True)
        merged.drop(['Unnamed: 0'], axis=1, inplace=True)
        return merged

    def normalization(self, target, data):
        data['normalized_target'] = data[target] / data['population']




