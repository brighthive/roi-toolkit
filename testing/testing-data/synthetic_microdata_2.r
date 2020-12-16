setwd('/Users/mattlerner/roi/sbir-roi/testing/testing-data')

library(sigmoid)

####### Create programs data #########

# 7 sample programs
programs <- c("Electrical Engineering", "Art History", "Economics", "Anthropology", "Biology", "French Literature", "Philosophy")
degree <- c("BA","BA","MA","BA","AS","MA","BA")
length <- c(8,8,4,4,3,5,8)
cost_per_semester <- c(5000,7000,10000,4500,3000,6000,8000)
programs_frame <- data.frame(programs, degree, length, cost_per_semester)
write.csv(programs_frame, "programs.csv")


####### Summ

setwd('/Users/mattlerner/roi/sbir-roi/testing/testing-data')

races = c("White", "Black", "Asian or Pacific Islander", "Other")
gender = c("Male", "Female", "Other/unspecified")
programs <- c("Electrical Engineering", "Art History", "Economics", "Anthropology", "Biology", "French Literature", "Philosophy")
education.levels = c(0, 60, 73, 81, 92, 111, 123, 124, 125)

combos <- expand.grid(race=races, gender=gender, program=programs, education.level=education.levels)
frames_ <- data.frame()

# add in inflators for creating artificial inequalities in the dataset

# race
combos$race.inflator <-1
combos[combos$races == "White", "race.inflator"] <- 1
combos[combos$races == "Black", "race.inflator"] <- 0.95
combos[combos$races == "Asian or Pacific Islander", "race.inflator"] <- 1.1
combos[combos$races == "Other", "race.inflator"] <- 0.8

# gender inflator
combos$gender.inflator <- 1
combos[combos$gender == "Male", "gender.inflator"] <- 1
combos[combos$gender == "Female", "gender.inflator"] <- 1.1
combos[combos$gender == "Other/unspecified", "gender.inflator"] <- 0.85

# program inflator
combos$program.inflator <- 1
combos[combos$program == "Electrical Engineering", "program.inflator"] <- 1.7
combos[combos$program ==  "Art History", "program.inflator"] <- 1.1
combos[combos$program ==  "Economics", "program.inflator"] <- 1.4
combos[combos$program ==  "Anthropology", "program.inflator"] <- 0.8
combos[combos$program ==  "Biology", "program.inflator"] <- 0.9
combos[combos$program ==  "French Literature", "program.inflator"] <- 0.7
combos[combos$program ==  "Philosophy", "program.inflator"] <- 1.2

for (i in 1:nrow(combos)) {
  inflator <- combos[i,'program.inflator'] * combos[i,'race.inflator'] * combos[i,'gender.inflator']
  number.in.group <- abs(round(rnorm(1, 20, 8))) + 1
  additional.years <- rpois(number.in.group,2)
  sd <- abs(rnorm(1,0,5000))
  mean <- abs(rnorm(1,30000,5000))
  real_premium <- abs(rnorm(1,10000,2000))
  earnings_start <- round(rnorm(number.in.group, mean, sd),0)
  earnings_end <- round(rnorm(number.in.group, mean+real_premium, sd),0) * inflator
  ages <- round(rnorm(number.in.group, 34, 15), 0)
  program_start <- round(rnorm(number.in.group, 2014,2),0)
  program_end <- round(program_start + abs(rnorm(number.in.group, 2, 2)),0) + round(rnorm(number.in.group, combos[i, 'program.inflator'], 0.5))
  ages[ages < 18] <- 18
  completer <- rbinom(number.in.group, 1, rbeta(1,4,1+combos[i, 'program.inflator']))
  employed_at_end <- round(sigmoid(completer*2 + rnorm(number.in.group,0,0.2))) # employment as a partial function 
  employed_at_start <- round(sigmoid(-1 + completer*1.5 + rnorm(number.in.group,0,0.3))) # employment as a partial function 
  frame_ <- cbind(race = as.character(rep(combos[i, 'race'],number.in.group)), gender = as.character(rep(combos[i, 'gender'],number.in.group)), earnings_start = earnings_start, earnings_end = earnings_end, age = ages, program=as.character(rep(combos[i, 'program'],number.in.group)), program_start=program_start, program_end=program_end, education_level=combos[i, 'education.level'], completer=completer, employed_at_end=employed_at_end, employed_at_start=employed_at_start)
  frames_ <- rbind(frames_, frame_)
}

frames_$state = "08"

# Get addresses
# addresses are sourced from https://catalog.data.gov/dataset/home-health-care-agencies
address.file <- read.csv("Home_Health_Care_Agencies.csv")
address.file$full.address <- paste(address.file$Address,address.file$City, address.file$State, address.file$Zip)


sample.indices<- sample(nrow(frames_), replace = FALSE)
frames_$full_address <- address.file[sample.indices,'full.address']
frames_$Address <- address.file[sample.indices,'Address']
frames_$City <- address.file[sample.indices,'City']
frames_$State <- address.file[sample.indices,'State']
frames_$Zip <- address.file[sample.indices,'Zip']
frames_$id <- sample(1:nrow(frames_))
frames_$start_month <- sample(c(8,9,10), nrow(frames_), replace=TRUE)
frames_$end_month <- sample(c(5,6,7), nrow(frames_), replace=TRUE)
frames_$age <- as.numeric(as.character(frames_$age))

# set 5% of start and end earnings to NA
number.to.set = round(0.05*nrow(frames_))
frames_[sample(1:nrow(frames_),number.to.set), 'earnings_start'] <- NA
frames_[sample(1:nrow(frames_),number.to.set), 'earnings_end'] <- NA

write.csv(frames_,"test_microdata_2.csv")
