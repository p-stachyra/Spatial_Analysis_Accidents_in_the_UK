import geopandas as gpd
from modules.AnalyzeGWR import AnalyzeGWR

target = ["casualties"]

independent_variables = ['weather_0', 'weather_1']
# 'road_class_0', 'road_class_1', 'road_class_2', 'road_class_3',
#                          'severity_0', 'severity_1', 'severity_2', 'hazards_0', 'hazards_1',
#                          'junction_0', 'junction_1', 'dark_0', 'dark_1', 'vehicles_1',
#                          'vehicles_2', 'vehicles_3', 'vehicles_4', 'vehicles_5', 'wet_0',
#                          'wet_1', 'road_type_0', 'road_type_1', 'road_type_2', 'special_0',
#                          'special_1', 'speed_0', 'speed_1', 'speed_2', 'urban_0', 'urban_1',



gwr = AnalyzeGWR("data/normalized.gpkg", target, independent_variables)
gwr.calibrateRegression()
gwr.fitRegression()
results = gwr.results
print(results.summary())