import pandas as pd
import numpy as np
from datetime import date
from . import settings
from .macrostats import BLS_API
import statsmodels.api as sm
import statsmodels.formula.api as smf

"""
TO do here:

- mean wages for all
- mean wages for employed
- use person weights
- account for inflation?
- ???

"""

pd.set_option('display.float_format', lambda x: '%.3f' % x)


CPS_Education_Levels = [("GED",73),("BA",111),("MA",123),("PHD",125)]


class CPS_Ops(object):
	"""
	On init, this object reads in a CPS extract, calculates mean wages by age group across the whole population and for those whose
	highest level of education his high school, and sets properties of the class to dataframes with those contents.

	The class also offers functions for using this data to calculate average wage change across years, both given a single data point and
	given a data given multiple time periods, age groups, etc.
	"""
	def __init__(self):
		self.base_year = date.today().year - 1
		self.microdata = pd.read_csv(settings.File_Locations.cps_extract)
		self.microdata['age_group'] = pd.cut(self.microdata['AGE'], bins=[0,18,25,34,54,64,150], right=True, labels=['18 and under','19-25','26-34','35-54','55-64','65+']).astype(str)
		self.microdata['hs_education_at_most'] = (self.microdata['EDUC'] >= 73) & (self.microdata['EDUC'] < 90) & (self.microdata['AGE'] >= 18)# & (self.microdata['AGE'] <= 38)
		self.cpi_adjustment_factor = 1.5341408621736492#BLS_API.get_cpi_adjustment(1999,self.base_year) # CPS data is converted into 1999 base, and then (below) we convert it into present-year dollars

		# adjust total personal income
		self.microdata.loc[self.microdata.INCTOT > 9999998, 'INCTOT'] = np.nan
		self.microdata['INCTOT_99'] = self.microdata['INCTOT'] * self.microdata['CPI99'] * self.cpi_adjustment_factor

		# adjust wages
		self.microdata.loc[self.microdata.INCWAGE > 9999998, 'INCWAGE'] = np.nan
		self.microdata['INCWAGE_99'] = self.microdata['INCWAGE'] * self.microdata['CPI99'] * self.cpi_adjustment_factor

		self.hs_grads_only = self.microdata[self.microdata.hs_education_at_most == True]
		self.get_all_mean_wages()
		self.get_hs_grads_mean_wages()

	def get_all_mean_wages(self):
		# Return a dataframe containing mean wages by year, state and age group
		mean_wages = self.microdata.groupby(['YEAR','STATEFIP','age_group']).apply(lambda x: pd.Series({"mean_INCWAGE":np.sum(x['INCWAGE_99'] * x['ASECWT'])/np.sum(x['ASECWT'])})).reset_index()
		self.all_mean_wages = mean_wages
		return None

	def get_hs_grads_mean_wages(self):
		# Return a dataframe containing mean wages for high school graduates (maximum ed) by year, state and age group
		mean_wages = self.hs_grads_only.groupby(['YEAR','STATEFIP','age_group']).apply(lambda x: pd.Series({"mean_INCWAGE":np.sum(x['INCWAGE_99'] * x['ASECWT'])/np.sum(x['ASECWT'])})).reset_index()
		self.hs_grads_mean_wages = mean_wages
		return None

	def get_mean_wage_by_ed_level(self, prereq_educ_level, program_educ_level, statefip):
		"""
		Calculate mean wages for individuals in a given state who are above a certain education level but below another one. Currently calculated for 2019 only.

		Reference:
		-----------
		CPS education codes

		Parameters:
		-----------
		prereq_educ_level : str
			CPS education recode code for the lower-bound education level

		program_educ_level : str
			CPS education recode code for the upper-bound education level

		statefip : str
			End year and month of the period over which we want to identify $ wage change

		Returns
		-------
		A single number indicating the mean wage across the dataset for this group of people.
		"""
		max_ed = self.microdata[(self.microdata.EDUC >= prereq_educ_level) & (self.microdata.EDUC < program_educ_level) & (self.microdata.STATEFIP == statefip) & (self.microdata.YEAR == 2019)]
		mean_wage = np.sum(max_ed["INCWAGE_99"] * max_ed["ASECWT"]) / np.sum(max_ed["ASECWT"])
		return(mean_wage)

	def rudimentary_hs_baseline(self, statefip):
		first_year = self.base_year - 10
		final_year = self.base_year

		baselines = self.microdata[self.microdata.STATEFIP == statefip]

		year1_hs_grads_young = baselines[(baselines.YEAR == first_year) & (baselines.AGE >= 18) & (baselines.AGE <= 24) & (baselines.EDUC >= 73) & (baselines.EDUC < 91)]
		year10_hs_grads_old = baselines[(baselines.YEAR == final_year) & (baselines.AGE >= 28) & (baselines.AGE <= 34) & (baselines.EDUC >= 73) & (baselines.EDUC < 91)]
		year10_hs_grads_young = baselines[(baselines.YEAR == final_year) & (baselines.AGE >= 18) & (baselines.AGE <= 24) & (baselines.EDUC >= 73) & (baselines.EDUC < 91)]

		# average wage for 18-24 HS graduates 10 years ago
		early_wage = np.sum(year1_hs_grads_young["INCWAGE_99"] * year1_hs_grads_young["ASECWT"]) / np.sum(year1_hs_grads_young["ASECWT"])

		# average wage for 28-34 HS graduates last year
		late_wage = np.sum(year10_hs_grads_old["INCWAGE_99"] * year10_hs_grads_old["ASECWT"]) / np.sum(year10_hs_grads_old["ASECWT"])

		# average wage for 18-24 HS graduates last year
		recent_wage = np.sum(year10_hs_grads_young["INCWAGE_99"] * year10_hs_grads_young["ASECWT"]) / np.sum(year10_hs_grads_young["ASECWT"])

		annualized_wage_growth = (late_wage / early_wage)**(1/10) - 1

		year1_projection = recent_wage * ((1+annualized_wage_growth)**1)
		year5_projection = recent_wage * ((1+annualized_wage_growth)**5)
		year10_projection = recent_wage * ((1+annualized_wage_growth)**10)

		wage_projections = {"year1":year1_projection, "year5":year5_projection, "year10":year10_projection}

		return(wage_projections)

	def wage_change_across_years(self, start_year, end_year, age_group_at_start, statefip):
		"""
		Calculate mean wage change across years for individuals in a given state and age group.

		Parameters:
		-----------
		start_year : int
			CPS education recode code for the lower-bound education level

		end_year : int
			CPS education recode code for the upper-bound education level

		age_group_at_start : str
			One of ['18 and under','19-25','26-34','35-54','55-64','65+']. These are divvied up in the CPS data at init of the CPS_Ops object.

		statefip : str
			State FIPS code, e.g. "08"

		Returns
		-------
		A single number indicating the mean wage across the dataset for this group of people.
		"""
		wage_start = self.all_mean_wages.loc[(self.all_mean_wages['YEAR'] == start_year) & (self.all_mean_wages['age_group'] == age_group_at_start) & (self.all_mean_wages['STATEFIP'] == statefip), 'mean_INCWAGE'].iat[0]
		wage_end = self.all_mean_wages.loc[(self.all_mean_wages['YEAR'] == end_year) & (self.all_mean_wages['age_group'] == age_group_at_start) & (self.all_mean_wages['STATEFIP'] == statefip), 'mean_INCWAGE'].iat[0]
		wage_change = wage_end - wage_start
		return(wage_change)

	def frames_wage_change_across_years(self, ind_frame, start_year_column, end_year_column, age_group_start_column, statefip_column, hsgrads_only = True):
		"""
		Given a dataframe with individual microdata, add a new column describing the change in state-level wages
		for people in their age group across the provided time frame (e.g. time spent in educational/training program).

		Parameters:
		-----------
		ind_frame : Pandas DataFrame
			Dataframe containing microdata for individuals

		start_year_column : str
			Name of column containing individuals' years of entry into educational programs

		end_year_column : str
			Name of column containing individuals' years of exit from educational programs

		age_group_start_column : str
			Name of column containing age groups.
			These are in ['18 and under','19-25','26-34','35-54','55-64','65+'].

		statefip_column : str
			Name of column contianing state FIPS codes

		hsgrads_only : boolean
			If true, we correct for macro trends using only data from high school graduates (max education)

		Returns
		-------
		A dataframe containing a new column ("wage_change") which expresses the difference between pre- and post-program earnings corrected for trend.
		"""
		if (hsgrads_only == False):
			cps_frame = self.all_mean_wages
		else:
			cps_frame = self.hs_grads_mean_wages
		merged_start = ind_frame.merge(cps_frame, left_on=[start_year_column, age_group_start_column, statefip_column], right_on=['YEAR','age_group','STATEFIP'], how='left')
		merged_both = merged_start.merge(cps_frame, left_on=[end_year_column, age_group_start_column, statefip_column], right_on=['YEAR','age_group','STATEFIP'], how='left', suffixes=('_start','_end'))
		merged_both['wage_change'] = merged_both['mean_INCWAGE_end'] - merged_both['mean_INCWAGE_start']
		return(merged_both)

	# ADDRESS THIS
	# LINEAR REGRESSION SEEMS TO WORK HERE
	def fit_mincer_model(self, statefip):

		"""
		In Heckman's Mincer model, people with zero earnings are dropped: https://www.nber.org/papers/w13780.pdf
		Better reference: https://www.nber.org/papers/w9732.pdf  -- see page 49 for sample information
		"""

		data = self.microdata[(self.microdata.INCTOT_99 > 0) & (self.microdata['AGE'] <= 65)]# & (self.microdata.hs_education_at_most == True)]

		# recode years of schooling
		data['years_of_schooling'] = pd.cut(self.microdata['EDUC'], bins=[0, 60, 73, 81, 92, 111, 123, 124, 125], right=True, labels=[10,12,14,13,16,18,19,20]).astype(int)
		data['log_inctot'] = np.log(data['INCTOT_99'])
		data['work_experience'] = data['AGE'] - data['years_of_schooling'] - 6 # based on Heckman
		model = smf.ols("log_inctot ~ years_of_schooling + years_of_schooling:work_experience + work_experience + work_experience^2", data, missing='drop')
		results = model.fit()
		print(results.summary())
		self.hs_model_results = results
		return None

	# ADDRESS THIS
	def predicted_wages(self, EDUC, work_experience):
		model = self.hs_model_results
		X_to_predict = pd.DataFrame({"EDUC": EDUC, "work_experience":work_experience})
		X_to_predict['years_of_schooling'] = pd.cut(X_to_predict['EDUC'], bins=[0, 60, 73, 81, 92, 111, 123, 124, 125], right=True, labels=[10,12,14,13,16,18,19,20]).astype(int)
		predicted_wages = model.predict(exog=X_to_predict)
		return(predicted_wages)

if __name__ == "__main__":
	
	cps = CPS_Ops()
	model = cps.fit_mincer_model()
	exit()

	baselines = cps.get_wage_baselines(8)
	print(baselines)

	hs_wages = cps.get_mean_wage_by_ed_level(73, 111, 8)
	ba_wages = cps.get_mean_wage_by_ed_level(111, 123, 8)
	print(hs_wages)
	print(ba_wages)
	exit()

	example_frames_to_merge = pd.DataFrame([{"age_group":'26-34',"year_start":2010,"year_end":2014,"statefip":30},{"age_group":'19-25',"year_start":2010,"year_end":2014,"statefip":1},{"age_group":'26-34',"year_start":2009,"year_end":2011,"statefip":2},{"age_group":'26-34',"year_start":2014,"year_end":2019,"statefip":30}])
	wage_change_example = cps.wage_change_across_years(2009,2012,'26-34',1)
	wage_change_frame_example = cps.frames_wage_change_across_years(example_frames_to_merge,'year_start','year_end','age_group','statefip')
	print(wage_change_frame_example)
	exit()


