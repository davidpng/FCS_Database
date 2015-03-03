###
##  Some R functions for analyzing QC data
##

library(RSQLite)
library(dplyr)
library(ggplot2)
library(MASS)
library(zoo)
library(scales)
#==================================
tube_types <- c('B ALL MRD', 'B Cells New', 'Myeloid 1', 'Myeloid 2',
                'Myeloid 4', 'Plasma Cell NEW', 'T4', 'T Cell',
                'T Cells New', 'WBC')
#==================================
loadDB <- function(dbfile) {
  sqlite <- dbDriver("SQLite")
  db <- dbConnect(sqlite, dbfile)
  return(db)
}
#===========================
genQuery <- function(dbfile, cols='*', table='full_PmtHistos', qstring=NULL, tube_type=NULL, Channel_Number=NULL, Channel_Name=NULL, limit=NULL, date_range=NULL, Antigen=NULL) {

   if (is.null(qstring)) {
     # SELECT
     if (!is.list(cols)) {
       qstring <- paste("select", cols, "from", table, sep=' ')
     } else {
       qstring <- paste("select",
                        paste(cols, collapse=', '),
                        "from", table, sep=' ')
     }

     #WHERE
     if (!is.null(tube_type) || !is.null(Channel_Number) || !is.null(Channel_Name)
         || !is.null(date_range)) {
       where_list <- list()
       if (!is.null(tube_type)) {
         where_list <- c(where_list, paste("tube_type = '", tube_type, "'", sep=""))
       }
       if (!is.null(Channel_Number)) {
         where_list <- c(where_list, paste("Channel_Number = '", Channel_Number, "'", sep=""))
       }
       if (!is.null(Antigen)) {
         where_list <- c(where_list, paste("Antigen = '", Antigen, "'", sep=""))
       }
        if (!is.null(Channel_Name)) {
         where_list <- c(where_list, paste("Channel_Name = '", Channel_Name, "'", sep=""))
       }
       if (!is.null(date_range)) {
         where_list <- c(where_list, paste("datetime(date) BETWEEN '", date_range[1], "' AND '",
                                           date_range[2], "'", sep=""))
       }
     }
     qstring <- paste(qstring, 'WHERE', paste(where_list, collapse=' AND '), sep=' ')

     # LIMIT
     if (!is.null(limit)) {
       qstring <- paste(qstring, "LIMIT", limit, sep=" ")
     }
   }
   return(qstring)
 }
#===============================
plotHistos_Name<- function(dbfile,
                       dir='test',
                       table='full_PmtHistos',
                       params=c('FSC-H', 'FSC-A', 'SSC-H', 'SSC-A'),
                       tts=tube_types,
                       cyts=c('1', '2'),
                           testing=FALSE,
                       ...) {

  db <- loadDB(dbfile)

  cols <- list('cytnum', 'date', 'Channel_Name', 'bin', 'density')
  for (param in params) {
    for (tt in tts) {
      qstring <- genQuery(dbfile=dbfile, cols=cols, table=table,
                          tube_type = tt, Channel_Name=param, ...)
      print(qstring)
      res <- dbSendQuery(db, qstring)

      histos <- tbl_df(dbFetch(res, n=-1))
      histos$date <- as.POSIXct(histos$date, "%Y-%m-%d %H:%M:%S")
      histos <- histos %>% arrange(date, bin)

      bins <- as.numeric(as.character(sort(unique(histos$bin))))

      for (cyt in cyts) {
        g <- list()
        df <- histos %>%
          filter(cytnum == cyt)

        png(paste(dir,
                  paste('Histos.raster', param, tt, cyt, 'png', sep='.'),
                  sep='/'),
            max(ceiling(nrow(df)/400), 1250),
            max(ceiling(nrow(df)/2000), 500))

        dates <- table(df$date)
        df$order <- sort(rep(1:length(dates), as.numeric(dates)))

        # Truncate density so that top outliers don't overload
        max_density <- as.numeric(quantile(df$density,c(0.9999),
                                           na.rm=T))
        df$density[which(df$density >= max_density)] = max_density

        # Figure out X axis
        dates <- format(df$date, "%Y")
        if (length(unique(dates)) == 1) { dates <- format(df$date, "%Y-%m") }
        if (length(unique(dates)) == 1) { dates <- format(df$date, "%Y-%m-%d") }
        date_changes <- c(1, which(dates[1:(length(dates)-1)] != dates[2:length(dates)])+1)

        g[[cyt]] <- df %>%
          ggplot(aes(x=order, y=bin, fill=density))
        g[[cyt]] <- g[[cyt]] + geom_tile()
        g[[cyt]] <- g[[cyt]] + scale_x_discrete(name = 'Date',
                                                breaks=df$order[date_changes],
                                                labels=dates[date_changes]) +
                                                  theme(axis.text=element_text(size=20, face='bold'))
        g[[cyt]] <- g[[cyt]] + labs(title=paste('1d histogram for ',
                                        param, '_', tt, ' [', cyt, ']', sep=''))
        plot(g[[cyt]])
        dev.off()
      }
      rm(histos)
      dbClearResult(res)
    }
  }
  dbDisconnect(db)
}
#====================================
plotHistos_Antigen <- function(dbfile,
                               dir='test',
                               table='full_PmtHistos',
                               antigens=c("HLA-DR", "CD15", "CD33", "CD19", "CD117", "CD13", "CD38", "CD34",
                           "CD71", "CD45"),
                               tts=tube_types,
                               cyts=c('1', '2'),
                               testing=FALSE,
                               log10_flag=FALSE,
                               ...) {

  db <- loadDB(dbfile)

  cols <- list('cytnum', 'date', 'Channel_Name', 'bin', 'density')
  for (antigen in antigens) {
    for (tt in tts) {
      qstring <- genQuery(dbfile=dbfile, cols=cols, table=table,
                          tube_type = tt, Antigen=antigen, ...)
      print(qstring)
      res <- dbSendQuery(db, qstring)

      histos <- tbl_df(dbFetch(res, n=-1))
      histos$date <- as.POSIXct(histos$date, "%Y-%m-%d %H:%M:%S")
      histos <- histos %>% arrange(date, bin)

      bins <- as.character(sort(unique(histos$bin)))

      for (cyt in cyts) {
        g <- list()
        df <- histos %>%
          filter(cytnum == cyt)

        png(paste(dir,
                  paste('Histos.raster', antigen, tt, cyt, 'png', sep='.'),
                  sep='/'),
            max(ceiling(nrow(df)/400), 1250),
            max(ceiling(nrow(df)/2000), 500))

        dates <- table(df$date)
        df$order <- sort(rep(1:length(dates), as.numeric(dates)))

        # Figure out X axis
        dates <- format(df$date, "%Y")
        if (length(unique(dates)) == 1) { dates <- format(df$date, "%Y-%m") }
        if (length(unique(dates)) == 1) { dates <- format(df$date, "%Y-%m-%d") }
        date_changes <- c(1, which(dates[1:(length(dates)-1)] != dates[2:length(dates)])+1)

        # Truncate density so that top outliers don't overload
        max_density <- as.numeric(quantile(df$density,c(0.9999),
                                           na.rm=T))
        df$density[which(df$density >= max_density)] = max_density

        if (log10_flag) { df$density[which(df$density < 1)] = 1 }

        bins_label <- sapply(c(bins[seq(0,100,20)]),
                             function (x) { format(as.numeric(x), digits=1)})

        if (!log10_flag) {
          g[[cyt]] <- df %>%
            ggplot(aes(x=order, y=bin, fill=density))
        } else {
          g[[cyt]] <- df %>%
            ggplot(aes(x=order, y=bin, fill=log10(density)))
        }
        g[[cyt]] <- g[[cyt]] + geom_tile()
        g[[cyt]] <- g[[cyt]] + scale_x_discrete(name = 'Date',
                                                breaks=df$order[date_changes],
                                                labels=dates[date_changes]) +
                                                  theme(axis.text=element_text(size=20, face='bold'))
        g[[cyt]] <- g[[cyt]] + labs(title=paste('1d histogram for ',
                                        antigen, '_', tt, ' [', cyt, ']', sep=''))

        plot(g[[cyt]])
        dev.off()
      }
      rm(histos)
      dbClearResult(res)
    }
  }
  dbDisconnect(db)
}
#====================================

#================================
# Multiple plot function
#
# ggplot objects can be passed in ..., or to plotlist (as a list of ggplot objects)
# - cols:   Number of columns in layout
# - layout: A matrix specifying the layout. If present, 'cols' is ignored.
#
# If the layout is something like matrix(c(1,2,3,3), nrow=2, byrow=TRUE),
# then plot 1 will go in the upper left, 2 will go in the upper right, and
# 3 will go all the way across the bottom.
#
multiplot <- function(..., plotlist=NULL, file, cols=1, layout=NULL) {
  require(grid)

  # Make a list from the ... arguments and plotlist
  plots <- c(list(...), plotlist)

  numPlots = length(plots)

  # If layout is NULL, then use 'cols' to determine layout
  if (is.null(layout)) {
    # Make the panel
    # ncol: Number of columns of plots
    # nrow: Number of rows needed, calculated from # of cols
    layout <- matrix(seq(1, cols * ceiling(numPlots/cols)),
                    ncol = cols, nrow = ceiling(numPlots/cols))
  }

 if (numPlots==1) {
    print(plots[[1]])

  } else {
    # Set up the page
    grid.newpage()
    pushViewport(viewport(layout = grid.layout(nrow(layout), ncol(layout))))

    # Make each plot, in the correct location
    for (i in 1:numPlots) {
      # Get the i,j matrix positions of the regions that contain this subplot
      matchidx <- as.data.frame(which(layout == i, arr.ind = TRUE))

      print(plots[[i]], vp = viewport(layout.pos.row = matchidx$row,
                                      layout.pos.col = matchidx$col))
    }
  }
}
