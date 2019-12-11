setwd('/users/matt/desktop/work/brighthive/colorado sbir/roi tool/data')

races = c("Martian", "Venusian", "Earthling", "Neptunian")
gender = c("Wan", "Moman")

combos <- expand.grid(race=races, gender=gender)
frames_ <- data.frame()
for (i in 1:nrow(combos)) {
  sd <- abs(rnorm(1,0,4))
  mean <- abs(rnorm(1,10000,1000))
  data <- rnorm(100, mean, sd)
  frame_ <- cbind(race = as.character(rep(combos[i, 'race'],100)), gender = as.character(rep(combos[i, 'gender'],100)), data)
  frames_ <- rbind(frames_, frame_)
}

write.csv(frames_,"test_microdata.csv")
