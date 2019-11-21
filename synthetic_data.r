library(readxl)
library(tidyverse)

# set working directory here
setwd("/users/matt/desktop/work/brighthive/colorado sbir/roi tool")

doc.1year <- read_xlsx("Original EdPays File.xlsx", 2) %>% mutate(years_after_completion = 1)
doc.5year <- read_xlsx("Original EdPays File.xlsx", 3) %>% mutate(years_after_completion = 5)
doc.10year <- read_xlsx("Original EdPays File.xlsx", 4) %>% mutate(years_after_completion = 10)

# create employment premkums
doc.1year$employment_premium <- round(rnorm(nrow(doc.1year), 0.3, 0.2),2)
doc.5year$employment_premium <- round(rnorm(nrow(doc.5year), 0.3, 0.2),2)
doc.10year$employment_premium <- round(rnorm(nrow(doc.10year), 0.3, 0.2),2)

doc <- rbind(doc.1year, doc.5year, doc.10year) %>% mutate (annual_earnings = `Annual Earnings ($)`) %>% select (-c(`Annual Earnings ($)`, EntityId, Completers, `COMPLETERS WITH WAGE COUNT`, `%Completers with wage data`))

doc[doc$employment_premium < -1 | doc$employment_premium > 1, 'employment_premium']  = 0.2

# create earnings premium column
doc$earnings_premium <- as.numeric(doc$annual_earnings) - 10000

#### creating program-level statistics
programs <- doc.1year %>% select(ENTITYNAME, CIPCode, DegreeLevelId, DEGREE)

# program length
programs$program_length = NA
programs[programs['DEGREE'] == "Doctoral Degree", "program_length"] <- sample(c(16,20),nrow(programs[programs['DEGREE'] == "Doctoral Degree", "program_length"]),replace=TRUE)
programs[programs['DEGREE'] == "Master's Degree", "program_length"] <- sample(c(4,5),nrow(programs[programs['DEGREE'] == "Master's Degree", "program_length"]),replace=TRUE)
programs[grepl("Associate",programs['DEGREE']), "program_length"] <- sample(c(2,3,4,5),nrow(programs[grepl("Associate",programs['DEGREE']), "program_length"]),replace=TRUE)
programs[grepl("Certificate",programs['DEGREE']), "program_length"] <- sample(c(1,2,3,4),nrow(programs[grepl("Certificate",programs['DEGREE']), "program_length"]),replace=TRUE)
programs[programs['DEGREE'] == "Bachelor's Degree", "program_length"] <- sample(c(8,10),nrow(programs[programs['DEGREE'] == "Bachelor's Degree", "program_length"]),replace=TRUE)

# graduation rate
programs$completion_rate <- round(rnorm(nrow(programs), 0.6, 0.15),2)
programs[programs$completion_rate < 0 | programs$completion_rate > 1, 'completion_rate']  = 0.6
programs$program_cost <- round(rnorm(nrow(programs),15000,5000),-3)/programs$program_length

# combine
final <- merge(doc, programs, by=c('ENTITYNAME','CIPCode','DEGREE','DegreeLevelId'))
final[final$annual_earnings == "Insufficient Data", 'annual_earnings'] <- NA

write.csv(final, "synthetic_data.csv")