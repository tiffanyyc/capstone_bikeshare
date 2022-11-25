# Bikeshare Wizard

Capstone project by Anna Cheng, Tiffany Cheng, Tina Fang, Giulia Olsson, and Tres Pimental for UC Berkeley's Master of Information and Data Science program.

<img src="images/logo.PNG" width="120">

## Motivation

**Bikeshare Wizard forecasts bike and dock availability that will benefit thousands of users a day in Boston. Our mission is to make bikeshare more reliable and to ensure that it remains an attractive and climate-friendly form of transportation.** By combining historical trips data and real-time station status data from Boston's Bluebikes bikeshare system, we are applying two DeepAR time series models for our MVP. Currently, users rely on the real-time station status data provided in the Bluebikes app; however, there is no guarantee that that same number of bikes and docks will be available by the time the user arrives at the station. Our MVP provides forecasts in 15-minute increments up to 3 days for each station in the system, which allows users to plan their commutes ahead of time.

## Impact

Bikeshare is a popular form of transportation in many cities across the world, so the impact of our MVP is global. According to [Statista](https://www.statista.com/outlook/mmo/shared-mobility/shared-rides/bike-sharing/worldwide), bikeshare revenue will reach $8B in 2022 and the number of users is forecasted to grow to 1B by 2026. By improving the user experience for bikeshare through availability forecasts, bikeshare will be seen as a more reliable form of transportation and the number of users will grow. This is great for the climate since 1 mile biked (instead of driven) reduces CO2 emissions by 1 pound ([Scientific American](https://www.scientificamerican.com/article/is-bike-sharing-really-climate-friendly/)).

## User Interviews

To better understand how we can serve potential users, we conducted a series of interviews with current users of bikeshare in Boston and in New York City. We learned that some users wanted predictions from 10 mins to more than 1 day into the future, so we decided to provide forecasts in 15-minute increments for 3 days.

## Data and EDA

Boston's Bluebikes system releases monthly data on their [website](https://www.bluebikes.com/system-data) that date back to 2015. These data come in the form of trips completed and include information on start and end station and start and end timestamp. Across all the years of data, there were around 15 million trips taken spread across about 500 different stations. We did some data cleaning to remove trips that had a station longitude and/or latitude equal to 0.

The most frequently taken trips occurred around the MIT campus in Cambridge.

<img src="images/popular_trips.PNG" width="300">

There is strong seasonality in the number of trips taken per month over the years. It is also important to note that the pandemic impacted ridership as well. For this reason, we chose to restrict the data we build the models with to the timeframe of August 2020 through August 2022.

<img src="images/time_series.PNG" width="300">
