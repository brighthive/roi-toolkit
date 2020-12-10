# ROI Toolkit v0.9 (beta)

## Introduction

The costs of education are rising considerably faster than inflation. Students and their families make sizable investments--of time, tuition, and foregone earnings--but see a wide range of returns. Wage, employment, completion, and satisfaction outcomes vary dramatically, and students often lack the data necessary to make informed educational choices that can lead to a better future.

Universities, job training programs, policymakers, and workforce organizations face a similarly challenging information environment. Without clear data on student outcomes, institutions are sometimes flying blind: they lack the ability to rigorously evaluate and compare different programs. Without this capacity, it can be difficult to pinpoint areas of improvement and identify key shortcomings. Without reliable data on which areas need improvement, in other words, it's hard to know how to improve.

The organizations that exist to serve students and worker/learners desperately also need tools with which to assess the equity impacts of the programs they offer. One of the most persistent challenges in this domain lies with disentangling program effects from selection effects: do students from one program earn higher wages as a result of the program, or are students who will go on to earn high wages more likely to pick that program in the first place? Rigorous equity metrics can help programs start to answer questions like these, allowing them to invest in ways to ensure that educational programs serve all of the students they're intended to help.

The **Return on Investment (ROI) Toolkit** in this repository provides code and data for use in calculating these metrics, as well as documentation, reading material, and guidance for deploying them. It is intended for use by technical personnel and analytic staff at educational institutions and the organizations that support them. This code can be used to calculate key equity metrics, projected yearly and lifetime earnings, and other key indicators. It also contains methods for interacting with public datasets and APIs useful for conducting these calculations, including functionality to adjust for inflation, calculate state- and age-level mean earnings, and estimate socioeconomic status based on street address.

Students and workers of all ages in America desperately need greater transparency on the return on investment (ROI) for all degrees, credentials, and certificates. The ROI Toolkit is a first step on the road to delivering it.

## Status of the ROI Toolkit

The Toolkit is **open-source**. It can be forked or cloned by anyone. Moreover, pull requests can be submitted to the Toolkit's maintainers to fix bugs or add additional metrics or functionalities. Please note that use of the Toolkit does not imply BrightHive's endorsement of the setting or particular use of the calculated metrics.

## Principles

The following are principles that guided the development of the ROI Toolkit and that should be kept in mind by users and future contributors.

* **Comprehensibility**

    Metrics need to be easily understood by their users. Complexity reduces usability, and though some informative metrics are unavoidably “black box” for users without statistical training, we strive to make sure that recommended metrics are explainable to their potential users. Metrics should be easily interpretable for all stakeholders.

* **Statistical Validity**

    Metrics should defensibly estimate the real-world quantities they claim to measure. Though perfect statistical rigor may not be possible, we try to formulate metrics that reliably estimate the underlying phenomena they exist to represent.

* **Likely actual use**

    The deployment of ROI metrics will drive behavior change across their user base. We formulate metrics bearing in mind that measures developed using past data will be used to drive changes in the distribution of future data, and aim to select metrics which are likely to result in positive behavior change, and which are robust in the face of differing institutional incentives. We are mindful of [Goodhart's Law](https://en.wikipedia.org/wiki/Goodhart%27s_law) and [Campbell's Law](https://en.wikipedia.org/wiki/Campbell%27s_law).

## ROI Toolkit Quickstart

The module itself is in the `roi` subdirectory. Clone the repo, copy the roi directory to your project, and get started.

There are several main, well-documented submodules offering clear functionality to the analyst of intermediate sophistication.

* `metrics.py` contains return metrics for calculating earnings and employment premiums and time to completion statistics
* `equity.py` contains methods for calculating equity metrics of various kinds and for associating Census blocks groups with socioeconomic status
* `cost.py` contains methods for calculating loan repayment schedules and periods

There are also ancillary submodules offering methods that will be useful to more sophisticated technical users. These submodules are major dependencies of the three main modules.

* `external.py` contains methods for fetching macroeconomic data from the U.S. Bureau of Labor Statistics and for assigning Census geocodes to street addresses using the Census API.
* `types.py` offers simple validation methods for common data formats and a scaffold for future work in this vein.
* `surveys.py` contains methods for calculating summary statistics using data from the Current Population Survey and fitting a Mincer model on this data that is used to calculate earnings premiums in `metrics.py`.
* `macro.py` contains methods for using BLS data (downloaded in `external.py`) to produce easy-to-use time series for calculation.


## For maintainers

In addition to code, the module itself also ships with prepackaged data that is collected from the Bureau of Labor Statistics and structured. Maintainers can keep this data up to date by regularly running `setup.py`, which sits in the top level of this repo. This script fetches employment, labor force, wage, and inflation data from the Bureau of Labor Statistics' API, does some work on it, and saves it to a data directory within the module (the `roi` subdirectory) itself.

* In order to run `setup.py`, maintainers (and any user who wants to clone the whole repo and update the data) must have a key to the [BLS API](https://www.bls.gov/bls/api_features.htm), which should be stored as an environment variable named `BLS_API_KEY`.

* Maintainers will also need to manually download an extract of CPS data for (at most) the past twenty years. They can do so at [IPUMS](https://cps.ipums.org/cps/). This extract is used to produce summary data that is shipped with the module, and is necessary for fitting the Mincer model that is used to calculate earnings premiums in the `metrics` submodule. CPS extracts should be placed in the data folder, have their filepaths updated in `settings.File_Locations.cps_toplevel_extract`, and must contain the following variables:

	* `AGE`
	* `EDUC`
	* `INCTOT`
	* `INCWAGE`
	* `CPI99`
	* `YEAR`
	* `STATEFIP`
	* `ASECWT`

* Finally, maintainers should dowwnload a copy of the [Area Deprivation Index](https://www.neighborhoodatlas.medicine.wisc.edu/) block group-level data and place it in the `roi/data` subdirectory of this repo so that it will ship withe module, and update its filepath in `Settings.File_Locations.adi_location`.


## Background

### Socioeconomic Status and Area Deprivation Index

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

