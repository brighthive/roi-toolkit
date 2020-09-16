####### Summ

setwd('/Users/mattlerner/roi/sbir-roi/testing/testing-data')

races = c("Martian", "Venusian", "Earthling", "Neptunian")
gender = c("Wan", "Moman")
programs = c("Electrical Engineering", "Art History", "Underwater Basket-Weaving")
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
  frame_ <- cbind(race = as.character(rep(combos[i, 'race'],number.in.group)), gender = as.character(rep(combos[i, 'gender'],number.in.group)), earnings_start = earnings_start, earnings_end = earnings_end, age = ages, program=as.character(rep(combos[i, 'program'],number.in.group)), program_start=program_start, program_end=program_end, education_level=combos[i, 'education.level'])
  frames_ <- rbind(frames_, frame_)
}

frames_$state = "08"

write.csv(frames_,"test_microdata.csv")
