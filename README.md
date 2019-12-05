# SBIR-ROI

This repository contains scripts related to the ongoing ROI metrics project being piloted in Colorado. As of 12/5/2019 these scripts are for prototyping purposes only.

### Contents

- **macrostats**

Scripts and functions related to macroeconomic statistics. Currently this folder just contains *macrostats.py*, which pulls data from the Bureau of Labor Statistics (BLS) API and provides some basic calculation functions, such as the functionality to calculate the change in employment in a given state over a provided time frame.

- **ses**

Scripts and functions related to socioeconomic status calculation. Currently this folder just contains *ses.py*, which includes methods that call the U.S. Census Geocoding API in order to convert street addresses into block group-level FIPS geocodes, and which determine the deprivation (SES) quintile for a given geocode based on ADI data.

- **data**

Data read in or produced by these scripts. Currently contains ADI statistics downloaded from an external source (see below).

- **calcs.py**

Methods that will be necessary in ultimate ROI calculations, such as Theil Index calculation or sinmple aggregation across groups.

### Background

#### Socioeconomic Status and Area Deprivation Index

We are interested in calculating socioeconomic status because of its evident correlation, above and beyond income and poverty status, with health, crime, employment and educational achievement. For equity asssessment purposes, we want to be able to identify possible disparities between groups of prospective students whose differing life circumstances and genuine challenges may not be adequately captured by the existing data.

The apparent relationship between SES and many other parameters of interest offers a scalable means of approximately identifying opportunity and disadvantage, broadly defined, with limited data.

There are several potential avenues for constructing SES. For some background, please see:

- [Census-based socioeconomic indicators for monitoring injury causes in the USA: a review](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4518757/)
- [Validating the Use of Census Data on Education as a Measure of Socioeconomic Status in an Occupational Cohort](https://www.ncbi.nlm.nih.gov/pubmed/30451561)
- [Measuring Socioeconomic Status (SES) in the NCVS: Background, Options, and Recommendations](https://www.bjs.gov/content/pub/pdf/Measuring_SES-Paper_authorship_corrected.pdf)
- [Constructing a Time-Invariant Measure of the Socio-economic Status of U.S. Census Tracts](https://link.springer.com/article/10.1007%2Fs11524-015-9959-y)

A commonly used SES index is the National Cancer Institute's factor analysis-based [method](https://seer.cancer.gov/seerstat/databases/census-tract/index.html) (Further background [here](https://www.ncbi.nlm.nih.gov/pubmed/24178398) and [here](https://www.ncbi.nlm.nih.gov/pubmed/9794168)) However, this data is not immediately available for our use at present.

We ultimately use the [Area Deprivation Index](https://www.neighborhoodatlas.medicine.wisc.edu/), a methodology based on the American Community Survey (ACS) 5-year estimates. Presently, this repository uses the 2011-2015 ACS estimates, but the easy availability of the ACS data and the transparency of the methodology enables us to continue calculating these indices in the event that the full dataset is taken offline.

ADI indices are given on a 0-100 scale, with lower indices representing less deprivation and higher SES, and higher indices representing more deprivation and lower SES.

Methodological reading:
- [Neighborhood socioeconomic disadvantage and 30-day rehospitalization: a retrospective cohort study](https://www.ncbi.nlm.nih.gov/pubmed/25437404)
- [Area deprivation and widening inequalities in US mortality, 1969-1998](https://www.ncbi.nlm.nih.gov/pubmed/12835199)

