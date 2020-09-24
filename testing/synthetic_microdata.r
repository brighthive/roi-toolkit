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

races = c("Martian", "Venusian", "Earthling", "Neptunian")
gender = c("Wan", "Moman")
programs <- c("Electrical Engineering", "Art History", "Economics", "Anthropology", "Biology", "French Literature", "Philosophy")
education.levels = c(0, 60, 73, 81, 92, 111, 123, 124, 125)

combos <- expand.grid(race=races, gender=gender, program=programs, education.level=education.levels)
frames_ <- data.frame()

for (i in 1:nrow(combos)) {
  number.in.group <- abs(round(rnorm(1, 20, 8)))
  sd <- abs(rnorm(1,0,5000))
  mean <- abs(rnorm(1,35000,5000))
  real_premium <- abs(rnorm(1,10000,2000))
  earnings_start <- round(rnorm(number.in.group, mean, sd),0)
  earnings_end <- round(rnorm(number.in.group, mean+real_premium, sd),0)
  ages <- round(rnorm(number.in.group, 34, 15), 0)
  program_start <- round(rnorm(number.in.group, 2014,2),0)
  program_end <- round(program_start + abs(rnorm(number.in.group, 2, 2)),0)
  ages[ages < 18] <- 18
  completer <- rbinom(number.in.group, 1, rbeta(1,4,1))
  employed_at_end <- round(sigmoid(completer*2 + rnorm(number.in.group,0,0.2))) # employment as a partial function 
  frame_ <- cbind(race = as.character(rep(combos[i, 'race'],number.in.group)), gender = as.character(rep(combos[i, 'gender'],number.in.group)), earnings_start = earnings_start, earnings_end = earnings_end, age = ages, program=as.character(rep(combos[i, 'program'],number.in.group)), program_start=program_start, program_end=program_end, education_level=combos[i, 'education.level'], completer=completer, employed_at_end=employed_at_end)
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

write.csv(frames_,"test_microdata.csv")
