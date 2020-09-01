####### Summ

setwd('roi/sbir-roi')

races = c("Martian", "Venusian", "Earthling", "Neptunian")
gender = c("Wan", "Moman")
programs = c("Electrical Engineering", "Art History", "Underwater Basket-Weaving")

combos <- expand.grid(race=races, gender=gender, program=programs)
frames_ <- data.frame()
for (i in 1:nrow(combos)) {
  sd <- abs(rnorm(1,0,5000))
  mean <- abs(rnorm(1,35000,5000))
  real_premium <- abs(rnorm(1,10000,2000))
  earnings_start <- round(rnorm(100, mean, sd),0)
  earnings_end <- round(rnorm(100, mean+real_premium, sd),0)
  ages <- round(rnorm(100, 34, 15), 0)
  program_start <- round(rnorm(100, 2014,2),0)
  program_end <- round(program_start + abs(rnorm(100, 2, 2)),0)
  ages[ages < 18] <- 18
  frame_ <- cbind(race = as.character(rep(combos[i, 'race'],100)), gender = as.character(rep(combos[i, 'gender'],100)), earnings_start = earnings_start, earnings_end = earnings_end, age = ages, program=as.character(rep(combos[i, 'program'],100)), program_start=program_start, program_end=program_end)
  frames_ <- rbind(frames_, frame_)
}

frames_$state = "08"

write.csv(frames_,"data/test_microdata.csv")
