#!/usr/bin/R

loadData <- function(file, N=Inf) {
  a <- read.table(file, h=T, sep="\t", nrows=N)
  a <- a[, 2:ncol(a)]
  a <- a[which(a$ctiA != a$ctiB), ]
  a <- a[which(a$ctiA < a$ctiB), ]
  a$same_day <- a$same_day == 'True'
  a$case <- a$case == 'True'
  a$cyt <- a$cyt == 'True'
  a$assay <- a$assay == 'True'
  a$emd_dist_s <- a$emd_dist / 10000
  a$emd_dist_sl <- log(a$emd_dist_s)
  return(a)
}

calcData <- function(a) {

  print(dim(a))
  print(table(a$case))
  print(with(a[which(a$case), ], mean(emd_dist_s)))
  print(with(a[which(!a$case), ], mean(emd_dist_s)))

  at <- with(a, t.test(emd_dist_sl[which(a$case)], emd_dist_sl[which(!a$case)], alternative='two.sided', paired=FALSE, var.equal=FALSE))
  print(at$p.value)

  print(with(a, summary(lm(emd_dist_sl ~ case))))
  print(with(a, summary(lm(emd_dist_sl ~ assay))))
  print(with(a, summary(lm(emd_dist_sl ~ cyt))))

}
