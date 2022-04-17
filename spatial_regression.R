#Loading Packages 
library("sf")
library("spdep")
library("tmap")
library("spatialreg")

gdf = st_read("data/normalized.gpkg")
names(gdf)
accidents_data = subset(gdf, select = -c(severity_1,severity_2) )

plot(accidents_data$geom)

barplot(accidents_data$casualties)

coordinates <- accidents_data %>%
  st_centroid() %>%
  st_geometry()

# create adjacency matrix

queen_cont <- poly2nb(accidents_data, queen=TRUE) #Queens Contiguity neighborhood
summary(queen_cont)

queen_cont_weights <- nb2listw(queen_cont, style="W", zero.policy = TRUE) #Queens neighborhood wights
summary(queen_cont_weights, zero.policy = TRUE)

# OLS model
equation = casualties ~ road_class_1 + road_class_2 + road_class_3 + hazards_1 + junction_1 + dark_1 + vehicles_2 + vehicles_3 + vehicles_4 + vehicles_5 + wet_1 + road_type_1 + road_type_2 + speed_1 + speed_2
linearMod <- lm(equation, data = accidents_data) 
summary(linearMod)
logLik(linearMod)
AIC(linearMod)
#################################################################################################
#Testing for spatial correlation
#################################################################################################

#We're gonna analyze whether the residuals of the OLS regression are spatially correlated
#For this test we're going to consider the 4 spatial weights matrices previously estimated

#Using the adjacency matrix
moran.adj = lm.morantest(linearMod, listw=queen_cont_weights, zero.policy = TRUE)
print(moran.adj)

#For each spatial weight matrix, we're going to estimate a spatial error and a spatial lag model.

#Estimating Spatial Error Model with adjacency W
error_adjacency = errorsarlm(casualties ~ road_class_1 + road_class_2 + road_class_3 + hazards_1 + junction_1 + dark_1 + vehicles_2 + 
	vehicles_3 + vehicles_4 + vehicles_5 + wet_1 + road_type_1 + road_type_2 + speed_1 + speed_2, data=accidents_data, listw=queen_cont_weights, zero.policy=TRUE)
summary(error_adjacency)

#Estimating Lag Error Model with adjacency W
lag_error_adjacency = lagsarlm(casualties ~ road_class_1 + road_class_2 + road_class_3 + hazards_1 + junction_1 + dark_1 + vehicles_2 + 
	vehicles_3 + vehicles_4 + vehicles_5 + wet_1 + road_type_1 + road_type_2 + speed_1 + speed_2, data=accidents_data, listw=queen_cont_weights, zero.policy=TRUE)
summary(lag_error_adjacency)
AIC(lag_error_adjacency)
AIC(error_adjacency)