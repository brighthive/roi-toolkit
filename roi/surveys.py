import pandas as pd
from datetime import date
from roi import macro, settings, external
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import pickle

"""
This submodule contains classes and methods for working with data from surveys and for fitting models on that data.
As of this writing (12/09/2020), the only survey supported is the Current Population Survey (CPS).

See https://www.census.gov/programs-surveys/cps.html for details on the survey
See http://cps.ipums.org/ in order to download data.

Unfortunately, CPS microdata must be downloaded manually, and placed at the location specified in settings.File_Locations.cps_toplevel_extract.
Dowmloading up to 20 years of CPS data is recommended. Using more is not recommended, since a Mincer model fit to the data in this submodule
and since structural changes affecting the parameters yielded by this model may occur on longer timescales.

Because the CPS data is downloaded manually, repository maintainers or sophisticated users must ensure that their extract includes the following variables:
AGE
EDUC
INCTOT
INCWAGE
CPI99
YEAR
STATEFIP
ASECWT

For details on educatino codes, please visit https://cps.ipums.org/cps-action/variables/EDUC#codes_section


"""

class CPS_Ops(object):
	"""
	On init, this object reads in a CPS extract, calculates mean wages by age group across the whole population and for those whose
	highest level of education his high school, and sets properties of the class to dataframes with those contents.
	The class also offers functions for using this data to calculate average wage change across years, both given a single data point and
	given a data given multiple time periods, age groups, etc.

	Parameters:
		None

	Attributes:
		base_year             :   The base year to which all dollar amounts will be converted. Defaults to the last year before the current year
		microdata             :   The microdata read in from the CPS extract, with the following derived columns:
			            age_group              :  Uses AGE variable to bucket individuals into five age categories
			            hs_education_at_most   :  A dummy variable that takes the value 1 if an individual has at most a high school education and 0 otherwise
			            INCTOT_current         :  INCOT in current-year dollars
			            INCWAGE_current        :  INCWAGE in ciurrent-year dollars
		bls                   :   An instance of macro.BLS_Ops(), which is needed in order to do inflation corrections
		cpi_adjustment_factor :   The CPI adjustment factor for converting 1999 dollars into current-year dollars
		hs_grads_only         :   The subset of microdata containing only those with a maximum high-school education

	"""
	def __init__(self):
		self.base_year = date.today().year - 1
		self.microdata = pd.read_csv(settings.File_Locations.cps_toplevel_extract)
		self.microdata['age_group'] = pd.cut(self.microdata['AGE'], bins=[0,18,25,34,54,64,150], right=True, labels=['18 and under','19-25','26-34','35-54','55-64','65+']).astype(str)
		self.microdata['hs_education_at_most'] = (self.microdata['EDUC'] >= 73) & (self.microdata['EDUC'] < 90) & (self.microdata['AGE'] >= 18)# & (self.microdata['AGE'] <= 38)
		
		self.bls = macro.BLS_Ops()
		self.cpi_adjustment_factor = self.bls.get_single_year_adjustment_factor(1999, self.bls.max_cpi_year) # CPS data is converted into 1999 base, and then (below) we convert it into present-year dollars

		# TODO: Warn here about latest year of adjustment

		# adjust total personal income
		self.microdata.loc[self.microdata.INCTOT > 9999998, 'INCTOT'] = np.nan
		self.microdata['INCTOT_current'] = self.microdata['INCTOT'] * self.microdata['CPI99'] * self.cpi_adjustment_factor

		# adjust wages
		self.microdata.loc[self.microdata.INCWAGE > 9999998, 'INCWAGE'] = np.nan
		self.microdata['INCWAGE_current'] = self.microdata['INCWAGE'] * self.microdata['CPI99'] * self.cpi_adjustment_factor

		self.hs_grads_only = self.microdata[self.microdata.hs_education_at_most == True]
		self.get_all_mean_wages()
		self.get_hs_grads_mean_wages()

	def get_all_mean_wages(self):
		"""
		Returns a dataframe containing mean wages by year, state and age group
		"""
		mean_wages = self.microdata.groupby(['YEAR','STATEFIP','age_group']).apply(lambda x: pd.Series({"mean_INCWAGE":np.sum(x['INCWAGE_current'] * x['ASECWT'])/np.sum(x['ASECWT'])})).reset_index()
		self.all_mean_wages = mean_wages
		mean_wages.to_csv("{}/mean_wages.csv".format(settings.File_Locations.local_data_directory), index=False)
		return None

	def get_hs_grads_mean_wages(self):
		"""
		Returns a dataframe containing mean wages for high school graduates (maximum ed) by year, state and age group
		"""
		mean_wages = self.hs_grads_only.groupby(['YEAR','STATEFIP','age_group']).apply(lambda x: pd.Series({"mean_INCWAGE":np.sum(x['INCWAGE_current'] * x['ASECWT'])/np.sum(x['ASECWT'])})).reset_index()
		self.hs_grads_mean_wages = mean_wages
		mean_wages.to_csv("{}/hs_grads_mean_wages.csv".format(settings.File_Locations.local_data_directory), index=False)
		return None


	def get_mean_wage_by_ed_level(self, prereq_educ_level, program_educ_level, statefip, year = None, data = None):
		"""
		Calculate mean wages for individuals in a given state who are above a certain education level but below another one. Currently calculated for base year only.
		Please refer to https://cps.ipums.org/cps-action/variables/EDUC#codes_section for details on education codes

		The idea here is that an analyst may want to naively compare the raw average wage for program completers with the raw average wage for those who satisfy the
		prereq_educ_level for a given program but have not yet satisfied completed the level of education offered by the program (program_educ_level).

		This CAN NOT be used for causal attribution: composition effects of individaul training programs likely swamp any causal effects in most cases.
		HOWEVER, this method can be used in a more sophisticated way by passing a subset of self.microdata as the data argument. Analysts can use this
		method as part of a function that matches program participants against counterfactual wages by education, age group, and more.


		Parameters:
			prereq_educ_level   : str, CPS education recode code for the lower-bound education level
			program_educ_level  : str, CPS education recode code for the upper-bound education level
			statefip            : str, STATEFIP for a single state
			year                : int, defaults to None. If None, calculations will proceed using class self.base_year
			data                : pandas dataframe, defaults to None. If not None, should be a subset of self.microdata

		Returns:
			mean_wage           : float, A single number indicating the mean wage across the dataset for this group of people.
		"""

		if year is None:
			year = base_year
		else:
			year = year

		if data is None:
			data = self.microdata
		else:
			data = data

		max_ed = data[(data.EDUC >= prereq_educ_level) & (data.EDUC < program_educ_level) & (data.STATEFIP == statefip) & (data.YEAR == year)]
		mean_wage = np.sum(max_ed["INCWAGE_current"] * max_ed["ASECWT"]) / np.sum(max_ed["ASECWT"])
		return(mean_wage)

	def rudimentary_hs_baseline(self, statefip):
		"""
		This function uses the entire self.microdata dataset to calculate a naive (there's that word again) baseline
		projecting wages for high school graduates out to the 1- 5- and 10-year time horizons.

		It does this simply by divying up the CPS sample into groups of high school graduates of the appropriate ages,
		converting their wages into current dollars, and then projecting current traditional-aged HS grads' wages
		out to the appropriate time horizon.

		Parameters:
			statefip : str, State FIPS code, e.g. "08"

		Results:
			wage_projections : A dict containing 1, 5, and 10 year projections for high school graduates in a given state
		"""
		first_year = self.base_year - 10
		final_year = self.base_year

		baselines = self.microdata[self.microdata.STATEFIP == statefip]

		year1_hs_grads_young = baselines[(baselines.YEAR == first_year) & (baselines.AGE >= 18) & (baselines.AGE <= 24) & (baselines.EDUC >= 73) & (baselines.EDUC < 91)]
		year10_hs_grads_old = baselines[(baselines.YEAR == final_year) & (baselines.AGE >= 28) & (baselines.AGE <= 34) & (baselines.EDUC >= 73) & (baselines.EDUC < 91)]
		year10_hs_grads_young = baselines[(baselines.YEAR == final_year) & (baselines.AGE >= 18) & (baselines.AGE <= 24) & (baselines.EDUC >= 73) & (baselines.EDUC < 91)]

		# average wage for 18-24 HS graduates 10 years ago
		early_wage = np.sum(year1_hs_grads_young["INCWAGE_current"] * year1_hs_grads_young["ASECWT"]) / np.sum(year1_hs_grads_young["ASECWT"])

		# average wage for 28-34 HS graduates last year
		late_wage = np.sum(year10_hs_grads_old["INCWAGE_current"] * year10_hs_grads_old["ASECWT"]) / np.sum(year10_hs_grads_old["ASECWT"])

		# average wage for 18-24 HS graduates last year
		recent_wage = np.sum(year10_hs_grads_young["INCWAGE_current"] * year10_hs_grads_young["ASECWT"]) / np.sum(year10_hs_grads_young["ASECWT"])

		annualized_wage_growth = (late_wage / early_wage)**(1/10) - 1

		year1_projection = recent_wage * ((1+annualized_wage_growth)**1)
		year5_projection = recent_wage * ((1+annualized_wage_growth)**5)
		year10_projection = recent_wage * ((1+annualized_wage_growth)**10)

		wage_projections = {"year1":year1_projection, "year5":year5_projection, "year10":year10_projection}

		return(wage_projections)


	def frames_wage_change_across_years(self, ind_frame, start_year_column, end_year_column, age_group_start_column, statefip_column, hsgrads_only = True):
		"""
		Given a dataframe with individual microdata, add a new column describing the change in state-level wages
		for people in their age group across the provided time frame (e.g. time spent in educational/training program).

		This allows analysts to (in a simple way) correct the difference between post- and pre-program earnings for trend and for experience effects.

		Parameters:
		-----------
		ind_frame              :  Pandas DataFrame, Dataframe containing microdata for individuals
		start_year_column      :  str, Name of column containing individuals' years of entry into educational programs
		end_year_column        :  str, Name of column containing individuals' years of exit from educational programs
		age_group_start_column :  str, Name of column containing age groups. These are in ['18 and under','19-25','26-34','35-54','55-64','65+'].
		statefip_column        :  str, Name of column contianing state FIPS codes
		hsgrads_only           :  boolean, If true, we correct for macro trends using only data from high school graduates (max education)

		Returns
		-------
		A copy of the original dataframe ind_frame containing a new column ("wage_change") which expresses the average chabnge in earnings
		for individuals in their age group over the time frame they were in an educational program.
		"""

		if (hsgrads_only == False):
			cps_frame = self.all_mean_wages
		else:
			cps_frame = self.hs_grads_mean_wages
		merged_start = ind_frame.merge(cps_frame, left_on=[start_year_column, age_group_start_column, statefip_column], right_on=['YEAR','age_group','STATEFIP'], how='left')
		merged_both = merged_start.merge(cps_frame, left_on=[end_year_column, age_group_start_column, statefip_column], right_on=['YEAR','age_group','STATEFIP'], how='left', suffixes=('_start','_end'))
		merged_both['wage_change'] = merged_both['mean_INCWAGE_end'] - merged_both['mean_INCWAGE_start']
		return(merged_both)


	def fit_mincer_model(self):

		"""
		This function fits a modified Mincer model and saves the results. If results already exist,
		by default this uses the existing fit model in data/models.

		The Mincer model can be used to predict expected wages for a given individual given their age, and education
		(and their imputed work experience based on these variables). The Earnings_Premium() class in the metrics submoduel
		uses the Mincer model produced here to calculate individuals' (and programs') premia over expected wages.

		Reference:
			- https://www.nber.org/papers/w13780.pdf
			- https://www.nber.org/papers/w9732.pdf (see page 49 for sample information)

		Mincer models are commonly used in educational economics as a way of estimating returns to schooling and experience.
		As a fully predictive model of wages, they are of limited value (R2 ~ 0.15). This is because of individual-level
		heterogeneity with regard to endowments and opportunities. However, in this context we use them simply to get the
		following (fairly precisely estimated) coefficients:

		1) years of schooling
		2) interaction between work experience and years of schooling
		3) work experience
		4) work experience squared

		The inclusion of the interaction term (2) and the quadratic term (4) are intended to capture the differential returns
		to work experience across different levels of educational preparation (e.g. a marginal year of experience for a college grad
		may have a higher return than for a high school grad) and the diminishing returns to experience (e.g. for some levels of
		education, annual wages level off for late-career workers).
		"""

		data = self.microdata[(self.microdata.INCTOT_current > 0) & (self.microdata['AGE'] <= 65)]

		# recode years of schooling
		data['years_of_schooling'] = pd.cut(self.microdata['EDUC'], bins=[0, 60, 73, 81, 92, 111, 123, 124, 125], right=True, labels=[10,12,14,13,16,18,19,20]).astype(int)
		data['log_inctot'] = np.log(data['INCTOT_current'])
		data['work_experience'] = data['AGE'] - data['years_of_schooling'] - 6 # based on Heckman's work (NBER above)
		model = smf.ols("log_inctot ~ C(STATEFIP) + years_of_schooling + years_of_schooling:work_experience + work_experience + np.power(work_experience, 2)", data, missing='drop')
		results = model.fit()

		# save params only to module - if you save the whole model (not just params) it is very big (~1gb)
		params = results.params
		with open(settings.File_Locations.mincer_params_location,'wb') as f:
			pickle.dump(params,f)
		
		# save full model to data (for repo)
		results.save(settings.File_Locations.mincer_params_location)

		# get and save results
		self.mincer = results

		return(self)