#
# This is a Shiny web application. You can run the application by clicking
# the 'Run App' button above.
#
# Find out more about building applications with Shiny here:
#
#    https://shiny.posit.co/
#

library(shiny)
library(shinythemes)
library(plotly)
library(tidyverse)
library(dplyr)
library(readr)
library(stringr)

musk <- read.csv("all_musk_posts.csv")

#make sure tweet text is lowercase
musk <- musk %>%
  mutate(content_lower=tolower(fullText))

#keyword topic
musk <- musk %>%
  mutate(
    #this works on a first-match basis
    topic = case_when(
      str_detect(content_lower, "trump") ~ "Trump",
      str_detect(content_lower, "spacex") ~ "SpaceX",
      str_detect(content_lower, "tesla") ~ "Tesla",
      str_detect(content_lower, "doge|dogecoin") ~ "DOGE",
      str_detect(content_lower, "starlink") ~ "Starlink",
      str_detect(content_lower, "twitter") ~ "Twitter",
      TRUE ~ "Other"
    )
  )

#filter to past 5 years
musk <- musk %>%
  mutate(created_At = as.Date(createdAt)) %>%
  filter(created_At >= Sys.Date() - lubridate::years(5))

ui<-fluidPage(
  theme=shinytheme("darkly"),
  titlePanel("Musks's Tweet Topics and Engagement"), #title
  selectInput(
    inputId = "var1",
    label = "Select a numerical variable.",
    choices = c("retweetCount", "replyCount", "likeCount", "quoteCount", "viewCount"),
    selected = "likeCount"
  ),
  checkboxGroupInput(
    inputId = "selected_topics",
    label = "Select Topics: ",
    choices = unique(musk$topic),
    selected = unique(musk$topic)
  ),
  selectInput(
    inputId = "selected_graph",
    label = "Select graph type: ",
    choices = c("Scatterplot", "Bar Chart"),
    selected = "Scatterplot"
  ),
  mainPanel(plotlyOutput("boxplots"), width = 900, height=800)
)


server<-function(input, output){
  filtered_data <- reactive({
    musk %>% filter(topic %in% input$selected_topics)
  })
  
  output$boxplots<-renderPlotly({
    data <- filtered_data() #filtered data
    
    if (input$selected_graph == "Scatterplot"){
      ggplotly(ggplot(data, aes_string(x="created_At", y=input$var1,color ="topic"))+geom_point(alpha = 0.5) 
               +geom_smooth(method = "loess", se = FALSE)
               + theme_minimal()
               +labs(x="Date", y = input$var1, title = paste(input$var1, "by Topic Over the Past 5 Years"), color = "Topic") #user has string of things to choose for x and y, which is why we need aes_string
      )}
    else if (input$selected_graph == "Bar Chart"){
      ggplotly(ggplot(data, aes_string(x="topic", y= input$var1, fill = "topic"))+
                 stat_summary(fun = "mean", geom ="bar", position = "dodge")+
                 theme_minimal() + labs(x="Topic", y=paste("Average", input$var1), title = paste("Average", input$var1, "by Topic in the Last 5 Years"), fill = "Topic")
      )
    }
  })
}

shinyApp(ui, server)
