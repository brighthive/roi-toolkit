library(readxl)
library(tidyverse)

# set working directory here
setwd("/users/mattlerner/roi")

edpays.file.name <- "sbir-roi/data/edpays/ROI2019_Earnings_1_5_10_CIP4_Suppressed.xlsx"

doc.1year <- read_xlsx(edpays.file.name, 2) %>% mutate(years_after_completion = 1)
doc.5year <- read_xlsx(edpays.file.name, 3) %>% mutate(years_after_completion = 5)
doc.10year <- read_xlsx(edpays.file.name, 4) %>% mutate(years_after_completion = 10)

doc <- rbind(doc.1year, doc.5year, doc.10year) %>% mutate (annual_earnings = `Annual Earnings ($)`) %>% select (-c(`Annual Earnings ($)`, EntityId, Completers, `COMPLETERS WITH WAGE COUNT`, `%Completers with wage data`))

# combine
final <- doc
final[final$annual_earnings == "Insufficient Data", 'annual_earnings'] <- NA

# edit CIPCODE
final$CIPCode <- gsub("([0-9][0-9])([0-9][0-9])","\\1.\\2",final$CIPCode)
final[final$CIPCode == "-1", "CIPCode"] <- ""

# ADD IN HS BASELINE HERE
# this is entered here manually, but comes from the rudimentary_hs_baseline() function in cps_loader.py()

write.csv(final, "sbir-roi/data/edpays/edpays_data_for_pairin.csv")


#######

m <- quap(
  alist(
    perc.protein ~ dnorm(a + c + B*mass, sd),
    a ~ dnorm(0, 0.5),
    c ~ dnorm(0, 0.011),
    B ~ dnorm(0, 0.2),
    sd ~ dexp(1)
  ), data=milk
)