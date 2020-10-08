import statsmodels.api as sm
import statsmodels.formula.api as smf
from roi.external import BLS_API
from roi import utilities, external, settings
from datetime import date
import pandas as pd
import pickle
import numpy as np

# This data is in the repo but not in the module
cps_extract_location = "data/cps/cps_00027.csv"
mincer_full_model_location = "data/models/mincer.pickle"

# This directory is for summary data to be shipped with the module
data_directory = "roi/data"
mincer_model_params_location = "{}/mincer_params.pickle".format(data_directory)
bls_employment_series_location = "{}/bls/bls_employment_series.csv".format(data_directory)
bls_laborforce_series_location = "{}/bls/bls_laborforce_series.csv".format(data_directory)
bls_wage_series_location = "{}/bls/bls_wage_series.csv".format(data_directory)

class CPS_Ops(object):
	"""
	On init, this object reads in a CPS extract, calculates mean wages by age group across the whole population and for those whose
	highest level of education his high school, and sets properties of the class to dataframes with those contents.

	The class also offers functions for using this data to calculate average wage change across years, both given a single data point and
	given a data given multiple time periods, age groups, etc.
	"""
	def __init__(self):
		self.base_year = date.today().year - 1
		self.microdata = pd.read_csv(cps_extract_location)
		self.microdata['age_group'] = pd.cut(self.microdata['AGE'], bins=[0,18,25,34,54,64,150], right=True, labels=['18 and under','19-25','26-34','35-54','55-64','65+']).astype(str)
		self.microdata['hs_education_at_most'] = (self.microdata['EDUC'] >= 73) & (self.microdata['EDUC'] < 90) & (self.microdata['AGE'] >= 18)# & (self.microdata['AGE'] <= 38)
		self.cpi_adjustment_factor = 1.5341408621736492 #BLS_API.get_cpi_adjustment(1999,self.base_year) # CPS data is converted into 1999 base, and then (below) we convert it into present-year dollars

		# adjust total personal income
		self.microdata.loc[self.microdata.INCTOT > 9999998, 'INCTOT'] = np.nan
		self.microdata['INCTOT_99'] = self.microdata['INCTOT'] * self.microdata['CPI99'] * self.cpi_adjustment_factor

		# adjust wages
		self.microdata.loc[self.microdata.INCWAGE > 9999998, 'INCWAGE'] = np.nan
		self.microdata['INCWAGE_99'] = self.microdata['INCWAGE'] * self.microdata['CPI99'] * self.cpi_adjustment_factor

		self.hs_grads_only = self.microdata[self.microdata.hs_education_at_most == True]
		self.get_all_mean_wages()
		self.get_hs_grads_mean_wages()
		self.get_cpi_adjustment_range()

	def get_all_mean_wages(self):
		# Return a dataframe containing mean wages by year, state and age group
		mean_wages = self.microdata.groupby(['YEAR','STATEFIP','age_group']).apply(lambda x: pd.Series({"mean_INCWAGE":np.sum(x['INCWAGE_99'] * x['ASECWT'])/np.sum(x['ASECWT'])})).reset_index()
		self.all_mean_wages = mean_wages
		mean_wages.to_csv("{}/mean_wages.csv".format(data_directory), index=False)
		return None

	def get_hs_grads_mean_wages(self):
		# Return a dataframe containing mean wages for high school graduates (maximum ed) by year, state and age group
		mean_wages = self.hs_grads_only.groupby(['YEAR','STATEFIP','age_group']).apply(lambda x: pd.Series({"mean_INCWAGE":np.sum(x['INCWAGE_99'] * x['ASECWT'])/np.sum(x['ASECWT'])})).reset_index()
		self.hs_grads_mean_wages = mean_wages
		mean_wages.to_csv("{}/hs_grads_mean_wages.csv".format(data_directory), index=False)
		return None

	def get_cpi_adjustment_range(self):
		bls_api = BLS_API()
		cpi_range = bls_api.get_cpi_adjustment_range(self.base_year - 19, self.base_year) # need to be connected to the internet to fetch BLS data
		cpi_range.to_csv("{}/cpi_adjustment_range.csv".format(data_directory), index=False)
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


	def fit_mincer_model(self, force_fit=False):

		"""
		This function fits a modified Mincer model and saves the results. If results already exist,
		by default this uses the existing fit model in data/models.

		For reference, see:
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

		'''# Check if a saved model exists. If it does, load and pass; if not, fit and pass

		if (path.exists(settings.File_Locations.model_location) & force_fit == False):
			self.mincer = sm.load(settings.File_Locations.model_location)
			return(self)
		else:
			pass'''

		data = self.microdata[(self.microdata.INCTOT_99 > 0) & (self.microdata['AGE'] <= 65)]

		# recode years of schooling
		data['years_of_schooling'] = pd.cut(self.microdata['EDUC'], bins=[0, 60, 73, 81, 92, 111, 123, 124, 125], right=True, labels=[10,12,14,13,16,18,19,20]).astype(int)
		data['log_inctot'] = np.log(data['INCTOT_99'])
		data['work_experience'] = data['AGE'] - data['years_of_schooling'] - 6 # based on Heckman's work (NBER above)
		model = smf.ols("log_inctot ~ C(STATEFIP) + years_of_schooling + years_of_schooling:work_experience + work_experience + np.power(work_experience, 2)", data, missing='drop')
		results = model.fit()

		# save params only to module - if you save the whole model (not just params) it is very big (~1gb)
		params = results.params
		with open(mincer_model_params_location,'wb') as f:
			pickle.dump(params,f)
		
		# save full model to data (for repo)
		results.save(mincer_full_model_location)

		# get and save results
		self.mincer = results

		return(self)

	def mincer_based_wage_change(self, state, prior_education, current_age, starting_wage, years_passed):
		"""
		Given a state, a prior education level (CPS EDUC code), the current age of an individual, their wage
		before entering an educational program, and the time they spent in the program, this function calculates
		their counterfactual wage change, e.g. it calculates what their expected current wage would be if they had
		not participated in the program.

		It achieves this by using the relevant coefficients from the modified Mincer model fit in fit_mincer_model() above,
		which approximate the value of an additional year of work experience given prior education and existing years
		of work experience.

		Parameters:
		-----------
		prior_education : int
			Integer code describing individuals' prior education level
			# see https://cps.ipums.org/cps-action/variables/EDUC#codes_section

		current_age : int
			Individuals' current age (post program)

		starting_wage : float
			Individuals' annual wage prior to starting educational program

		years_passed : int
			Program length, e.g. 2 years for an associate's degree

		Returns
		-------
		float: the expected counterfactual wage change for an individual over the time they were in a program, in present-year dollars.

		"""
		schooling_coef = self.mincer.params['years_of_schooling']
		schooling_x_exp_coef = self.mincer.params['years_of_schooling:work_experience']
		exp_coef = self.mincer.params['work_experience']
		exp2_coef = self.mincer.params['np.power(work_experience, 2)']
		years_of_schooling = pd.cut([prior_education], bins=[0, 60, 73, 81, 92, 111, 123, 124, 125], right=True, labels=[10,12,14,13,16,18,19,20]).astype(int)[0] # this is a hack to get years of schooling; using the pandas function here for symmetry

		# get values for calculation
		work_experience_current = current_age - years_of_schooling - 6 # based on Heckman
		work_experience_start = work_experience_current - years_passed

		# calculate
		# change in natural log is approximately equal to percentage change
		value_start = schooling_x_exp_coef*work_experience_start*years_of_schooling + exp_coef*work_experience_start + exp2_coef*(work_experience_start**2)
		value_end = schooling_x_exp_coef*work_experience_current*years_of_schooling + exp_coef*work_experience_current + exp2_coef*(work_experience_current**2)
		
		# results
		percentage_wage_change = value_end - value_start
		counterfactual_current_wage = starting_wage * (1+percentage_wage_change)
		counterfactual_wage_growth = counterfactual_current_wage - starting_wage

		return(counterfactual_wage_growth)

def fetch_bls_data():
	# series IDs for last 20 years of employment data
	start_year = 2002
	end_year = 2019
	bls = BLS_API()

	employment_dataframe = pd.DataFrame()
	wage_dataframe = pd.DataFrame()
	labor_force_dataframe = pd.DataFrame()

	for state_code in utilities.Data.state_crosswalk.values():

		emp_series_id = bls.employment_series_id(state_code=state_code)
		emp_raw_response = bls.get_series(emp_series_id, start_year, end_year)

		lf_series_id = bls.employment_series_id(state_code=state_code, measure_code="labor force")
		lf_raw_response = bls.get_series(lf_series_id, start_year, end_year)

		wage_series_id = bls.wage_series_id(state_code=state_code)
		wage_raw_response = bls.get_series(wage_series_id, start_year, end_year)

		try:
			employment = bls.parse_api_response(emp_raw_response)
			laborforce = bls.parse_api_response(lf_raw_response)
			wage = bls.parse_api_response(wage_raw_response)
		except Exception as E:
			print("Failed fetching data for {}".format(state_code))
			print(E)
			continue

		employment['state_code'] = state_code
		laborforce['state_code'] = state_code
		wage['state_code'] = state_code
		employment_dataframe = employment_dataframe.append(employment)
		wage_dataframe = wage_dataframe.append(wage)
		labor_force_dataframe = labor_force_dataframe.append(laborforce)
		print("Fetched BLS data for {}!".format(state_code))

	employment_dataframe.to_csv(bls_employment_series_location, index=False)
	labor_force_dataframe.to_csv(bls_laborforce_series_location, index=False)
	wage_dataframe.to_csv(bls_wage_series_location, index=False)

	# get cpi data
	cpi = bls.get_cpi_adjustment_range(start_year, end_year)
	cpi.to_csv(cpi_adjustments_location, index=False)

	return(None)

if __name__ == "__main__":

	fetch_bls_data()
	exit()

	cps = CPS_Ops()
	model = cps.fit_mincer_model()
	exit()
