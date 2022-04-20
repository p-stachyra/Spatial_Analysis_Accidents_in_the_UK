#### Morans I on resiudals, LISA cluster map ####

setwd(dirname(dirname(rstudioapi::getSourceEditorContext()$path)))
rm(list = ls())
library(sf)
library(spdep)
library(tidyverse)
df = sf::st_read("data/normalized.gpkg")

# create list of weights
w <- poly2nb(df, queen=TRUE)
w_list <- nb2listw(w, style="W", zero.policy = T)


#### 1. Fit the model, perform Moran's I test ####
lm_formula <- casualties ~ road_class_1 + road_class_2 + road_class_3 +
  hazards_1 + junction_1 + dark_1 + vehicles_2 + vehicles_3 + 
  vehicles_4 + vehicles_5 + wet_1 + road_type_1 + road_type_2 + special_1 + 
  speed_1 + speed_2 + urban_1 + weather_1
linearMod <- lm(lm_formula, data = df)


##### 1.1. Identify outliers #####

# Created lagged target variable
df$s_casualties <- scale(df$casualties)
df$l_s_casualties <- lag.listw(w_list, df$s_casualties)

# identify(df$s_casualties, df$l_s_casualties, df$auth, cex = 0.8, plot=T)
df$s_casualties
out <- boxplot.stats(df$l_s_casualties)$out
out_2 <- boxplot.stats(df$s_casualties)$out
out_ind <- which(df$l_s_casualties %in% c(out))
out_ind_2 <- which(df$s_casualties %in% c(out_2))
outliers <- c(47, 119, 146, 153, 260, 293, 316, 65)

# Check if outliers were assigned properly
df$l_s_casualties[outliers]
df$s_casualties[outliers]

# Check which authorities are outliers, and create clean dataset
df$auth[outliers]
df_clean <- na.omit(df[-outliers,])


##### 1.2 Moran's I with and without outliers ####

# Calculate the Moran's Indicator 
mc <- moran.mc(linearMod$residuals, w_list, 1000, zero.policy = T)
mc

# Calculate Moran's indicator without outliers
w_o <- poly2nb(df_clean, queen=TRUE)
w_list_o <- nb2listw(w_o, style="W", zero.policy = T)
linearMod_o <- lm(lm_formula, data = df_clean)
mco <- moran.mc(linearMod_o$residuals, w_list_o, 1000, zero.policy = T)
mco


#### 2. Local Moran's plot, Lisa cluster map ####
##### 2.1 With outliers ####

# Local Moran's indicator
lmc <- localmoran(df$casualties, w_list, zero.policy = T)

# Moran's scatter plot
plot(x = df$s_casualties, y = df$l_s_casualties, 
     main = "Scatter plot of ",
     xlab = "Normalized number of casualties per county",
     ylab = "Lagged and normalized number of casualties"
)
abline(h = 0, v = 0)
abline(lm(df$l_s_casualties ~ df$s_casualties), lty = 3, lwd = 1.5, col = "red")

# Assign variation levels
df$quad_sig <- NA
df$quad_sig[(df$s_casualties >= 0 & df$l_s_casualties >= 0) & (lmc[, 5] <= 0.05)] <- 1
df$quad_sig[(df$s_casualties <= 0 & df$l_s_casualties <= 0) & (lmc[, 5] <= 0.05)] <- 2
df$quad_sig[(df$s_casualties >= 0 & df$l_s_casualties <= 0) & (lmc[, 5] <= 0.05)] <- 3
df$quad_sig[(df$s_casualties >= 0 & df$l_s_casualties >= 0) & (lmc[, 5] <= 0.05)] <- 4
df$quad_sig[(df$s_casualties <= 0 & df$l_s_casualties >= 0) & (lmc[, 5] <= 0.05)] <- 5 

# Plot Lisa cluster map
breaks <- seq(1, 5, 1)
labels <- c("high-High", "low-Low", "High-Low", "Low-High", "Not Signif.")
np <- findInterval(df$quad_sig, breaks)
colors <- c("red", "blue", "lightpink", "skyblue2", "white")
x11(); plot(df[c("s_casualties", "geom")], col = colors[np], 
            xlab='', ylab='', axes=F)
title("Lisa Cluster map", line=2, sub="")
legend("topleft", legend = labels, fill = colors, bty = "n")

df[c("s_casualties", "geom")] %>%
  x11() %>% ggplot(.) 
  + geom_sf(data = ., fill=s_casualties)
  # + scale_y_continuous(breaks = breaks)


##### 2.2 Without outliers ####

# Local Moran's scatter plot
plot(x = df_clean$s_casualties, y = df_clean$l_s_casualties, 
  main = "Local Moran's I Scatterplot of target variable without outliers",
  xlab = "Normalized number of casualties per county",
  ylab = "Lagged and normalized number of casualties"
)
abline(h = 0, v = 0)
abline(
  lm(df_clean$l_s_casualties ~ df_clean$s_casualties), 
  lty = 3, lwd = 1.5, col = "red"
)

# Assign variation levels
df_clean$quad_sig <- NA
df_clean$quad_sig[(df_clean$s_casualties >= 0 & df_clean$l_s_casualties >= 0) & (na.omit(lmc[, 5][-outliers]) <= 0.05)] <- 1
df_clean$quad_sig[(df_clean$s_casualties <= 0 & df_clean$l_s_casualties <= 0) & (na.omit(lmc[, 5][-outliers]) <= 0.05)] <- 2
df_clean$quad_sig[(df_clean$s_casualties >= 0 & df_clean$l_s_casualties <= 0) & (na.omit(lmc[, 5][-outliers]) <= 0.05)] <- 3
df_clean$quad_sig[(df_clean$s_casualties >= 0 & df_clean$l_s_casualties >= 0) & (na.omit(lmc[, 5][-outliers]) <= 0.05)] <- 4
df_clean$quad_sig[(df_clean$s_casualties <= 0 & df_clean$l_s_casualties >= 0) & (na.omit(lmc[, 5][-outliers]) <= 0.05)] <- 5 

# Lisa Cluster map 
breaks <- seq(1, 5, 1)
labels <- c("high-High", "low-Low", "High-Low", "Low-High", "Not Signif.")
np <- findInterval(df_clean$quad_sig, breaks)
colors <- c("red", "blue", "lightpink", "skyblue2", "white")
x11(); plot(df_clean[c("s_casualties", "geom")], col = colors[np])  #colors[np] manually sets the color for each county
mtext("Local Moran's I", cex = 1.5, side = 3, line = 1)
legend("topleft", legend = labels, fill = colors, bty = "n")
