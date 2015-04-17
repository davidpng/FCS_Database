library(openCyto)
a <- read.ncdfFlowSet(fps)
f_sg <- fsApply(a, function(fr) {
  openCyto:::.singletGate(fr,
                          channels=c("FSC-A", "FSC-H"),
                          wider_gate=TRUE,
                          maxit=10,
                          prediction_level=0.9999) })


library(flowClust)
res1 <- flowClust::flowClust(x=a[[1]], varNames=c("SSC-H", "FSC-A"), K=1:8, B=100)
x<- criterion(res1, "BIC") - min(criterion(res1, "BIC"))
nc <- which(x / max(x) > 0.9)[1]
res1 <- res1[[nc]]

#res1@label
#res1@flagOutliers == FALSE
#Map(res1)

#filter2 <- tmixFilter(filterId='FvS', parameters=c("SSC-H", "FSC-A"), K=1:8, B=100)
#res2 <- filter(a[[10]], filter2)
#x<- criterion(res2, "BIC") - min(criterion(res2, "BIC"))
#nc <- which(x / max(x) > 0.9)[1]
#res2 <- res2[[nc]]
