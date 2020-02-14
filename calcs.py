import pandas as pd
import numpy as np
from modules import cps_loader

def dataframe_groups_to_ndarray(dataframe, groupby_columns, value_to_groups):
	"""
	This method takes a pandas dataframe and yields a numpy array of arrays containing values split up by group.

	Parameters:
	-----------
	dataframe : Pandas DataFrame
		Dataframe containing microdata with object or factor variables denoting groups

	groupby_columns : list(str)
		list of column names e.g. "gender" or "race"

	value_to_groups : str
		Column name containing the value which will be split into groups

	Returns
	-------
	A tuple: (numpy[N] with group names, multidimensional array with as many sub-arrays (N) as groups)
	"""
	grouped = dataframe.groupby(groupby_columns)[value_to_groups].apply(lambda x: np.array(x.values))
	groups = np.array(grouped.index)
	list_of_values = np.array(grouped)
	return (groups, list_of_values)

class Supporting:
	"""
	Class for miscellaneous supporting calculation functions.
	"""
	def group_aggregation(dataframe, aggregation_category_list, variable_to_aggregate, aggregation_method):
		"""
		This method is just a shortener for a groupby aggregation.

		Parameters:
		-----------
		dataframe : Pandas DataFrame
			Dataframe containing microdata

		aggregation_category_list : list(str)
			list of column names e.g. "gender" or "race"

		variable_to_aggregate : str
			Column name containing the value which will be aggregated

		aggregation_method: str
			Function name e.g. "mean" or "sum." Must be a legit function!

		Returns
		-------
		A dataframe with column for the aggregated value. If method is X and original value is Y, the aggregated column is X_Y.
		"""
		aggregated_name = "{}_{}".format(aggregation_method, variable_to_aggregate)
		aggregated = test_microdata.groupby(aggregation_category_list)[variable_to_aggregate].aggregate(aggregation_method).reset_index().rename(columns={variable_to_aggregate:aggregated_name})		
		return aggregated

class Theil_T:
	"""
	Class provides methods for calculating individual terms in the Theil T index, as well as
	(1) a function for calculating the index itself and
	(2) a function calculating a ratio denoting the proportion of inequality accounted for by cross-group inequality

	Please note that the Theil index takes only positive values!

	Reference
	-----------
	https://seer.cancer.gov/help/hdcalc/inference-methods/individual-level-survey-sample-1/measures-of-relative-disparity/theil-index-t

	https://utip.lbj.utexas.edu/papers/utip_14.pdf

	https://www.usi.edu/media/3654811/Analysis-of-Inequality.pdf

	"""
	def theil_within_group(vector_of_values):
		"""
		T_i in the Theil index expression
		
		Parameter - Numpy vector or array of values
		Returns - Scalar (float)

		"""
		x = vector_of_values # for readability
		N = len(x)
		mu = np.mean(x)
		xi_over_mu = x / mu
		ln_xi_over_mu = np.log(xi_over_mu)
		theil = (1/N)*np.sum(xi_over_mu * ln_xi_over_mu)
		return theil

	def s_i(array, N, mu):
		"""
		s_i in the Theil index expression
		
		Parameters:
		-----------
		array : numpy vector or array
			Values of variable

		N : float
			size of population

		mu : float
			Average value of variable across population

		Returns
		-------
		Float
		"""
		N_i = len(array)
		x_i_bar = np.mean(array)
		s_i = (N_i/N) * (x_i_bar/mu)
		return s_i

	def first_term(list_of_groups):
		"""
		First term (sum of within-group inequalities) in the Theil index formula
		
		Parameters:
		-----------
		list_of_groups : list of numpy arrays
			Array[N] of arrays representing N subgroups

		Returns
		-------
		Scalar representing the first term value of the Theil index formula
		"""
		full_population = np.concatenate(list_of_groups)
		N = len(full_population)
		mu = np.mean(full_population)
		T_i = np.array([Theil_T.theil_within_group(group) for group in list_of_groups])
		s_i = np.array([Theil_T.s_i(group, N=N, mu=mu) for group in list_of_groups])
		first_term = np.sum(T_i * s_i)
		return first_term

	# FIX THIS SHIT UP
	def second_term(list_of_groups):
		"""
		Second term (sum of cross-group inequalities) in the Theil index formula
		
		Parameters:
		-----------
		array_of_groups : numpy multidimensional vector
			Array[N] of arrays representing N subgroups

		Returns
		-------
		Scalar representing the second term value of the Theil index formula
		"""
		full_population = np.concatenate(list_of_groups)
		N = len(full_population)
		mu = np.mean(full_population)
		s_i = np.array([Theil_T.s_i(group, N=N, mu=mu) for group in list_of_groups])
		x_i = np.array([np.mean(group) for group in list_of_groups])
		second_term = np.sum(s_i * np.log(x_i / mu))
		return second_term

	def Calculate_Index(array_of_groups):
		"""
		The actual Theil Index: sum of within-group and cross-group inequality
		
		Parameters:
		-----------
		array_of_groups : numpy multidimensional vector
			Array[N] of arrays representing N subgroups

		Returns
		-------
		Scalar representing the Theil index
		"""

		Index = Theil_T.first_term(array_of_groups) + Theil_T.second_term(array_of_groups)
		return Index

	def Calculate_Ratio(array_of_groups):
		"""
		Ratio between second term of index (cross-group inequality) and the full index.
		Roughly interpretable as the portion of inequality that is accounted for by cross-group inequality.
		
		Parameters:
		-----------
		array_of_groups : numpy multidimensional vector
			Array[N] of arrays representing N subgroups

		Returns
		-------
		Scalar representing the ratio
		"""
		first_term = Theil_T.first_term(array_of_groups)
		second_term = Theil_T.second_term(array_of_groups)
		ratio = second_term / (first_term + second_term)
		return ratio

class Theil_L:
	"""
	Class provides methods for calculating individual terms in the Theil L index, as well as
	(1) a function for calculating the index itself and
	(2) a function calculating a ratio denoting the proportion of inequality accounted for by cross-group inequality

	Please note that the Theil index takes only positive values!

	Reference
	-----------
	https://seer.cancer.gov/help/hdcalc/inference-methods/individual-level-survey-sample-1/measures-of-relative-disparity/theil-index-t

	https://utip.lbj.utexas.edu/papers/utip_14.pdf

	https://www.usi.edu/media/3654811/Analysis-of-Inequality.pdf

	"""
	def theil_within_group(vector_of_values):
		"""
		T_i in the Theil index expression
		
		Parameter - Numpy vector or array of values
		Returns - Scalar (float)

		"""
		x = vector_of_values # for readability
		N = len(x)
		mu = np.mean(x)
		mu_over_xi = mu / x
		ln_mu_over_xi = np.log(mu_over_xi)
		theil = (1/N)*np.sum(ln_mu_over_xi)
		return theil

	def s_i(array, N):
		"""
		s_i in the Theil index expression
		
		Parameters:
		-----------
		array : numpy vector or array
			Values of variable

		N : float
			size of population

		mu : float
			Average value of variable across population

		Returns
		-------
		Float
		"""
		N_i = len(array)
		s_i = (N_i/N)
		return s_i

	def first_term(list_of_groups):
		"""
		First term (sum of within-group inequalities) in the Theil index formula
		
		Parameters:
		-----------
		list_of_groups : list of numpy arrays
			Array[N] of arrays representing N subgroups

		Returns
		-------
		Scalar representing the first term value of the Theil index formula
		"""
		full_population = np.concatenate(list_of_groups)
		N = len(full_population)
		mu = np.mean(full_population)
		L_i = np.array([Theil_L.theil_within_group(group) for group in list_of_groups])
		s_i = np.array([Theil_L.s_i(group, N=N) for group in list_of_groups])
		first_term = np.sum(L_i * s_i)
		return first_term

	# FIX THIS SHIT UP
	def second_term(list_of_groups):
		"""
		Second term (sum of cross-group inequalities) in the Theil index formula
		
		Parameters:
		-----------
		array_of_groups : numpy multidimensional vector
			Array[N] of arrays representing N subgroups

		Returns
		-------
		Scalar representing the second term value of the Theil index formula
		"""
		full_population = np.concatenate(list_of_groups)
		N = len(full_population)
		mu = np.mean(full_population)
		s_i = np.array([Theil_L.s_i(group, N=N) for group in list_of_groups])
		x_i = np.array([np.mean(group) for group in list_of_groups])
		second_term = np.sum(s_i * np.log(mu / x_i))
		return second_term

	def Calculate_Index(array_of_groups):
		"""
		The actual Theil Index: sum of within-group and cross-group inequality
		
		Parameters:
		-----------
		array_of_groups : numpy multidimensional vector
			Array[N] of arrays representing N subgroups

		Returns
		-------
		Scalar representing the Theil index
		"""

		Index = Theil_L.first_term(array_of_groups) + Theil_L.second_term(array_of_groups)
		return Index

	def Calculate_Ratio(array_of_groups):
		"""
		Ratio between second term of index (cross-group inequality) and the full index.
		Roughly interpretable as the portion of inequality that is accounted for by cross-group inequality.
		
		Parameters:
		-----------
		array_of_groups : numpy multidimensional vector
			Array[N] of arrays representing N subgroups

		Returns
		-------
		Scalar representing the ratio
		"""
		first_term = Theil_L.first_term(array_of_groups)
		second_term = Theil_L.second_term(array_of_groups)
		ratio = second_term / (first_term + second_term)
		return ratio


class Earnings_Premium:
	"""
	Methods for calculating the earnings premium and variations thereof.
	The earnings premium is interpretable as the expected increase in earnings an incoming student can expect at various intervals at the graduation from a program.
	It's calculated by taking the difference between pre- and post-program earnings and correcting for trend.
	Trend is calculated using CPS data for the change in average earned income for individuals in (a) a given age group with (b) a given qualification
	"""
	def calculate(dataframe, earnings_before_column, earnings_after_column, start_year_column, end_year_column, age_at_start, statefip):
		cps = cps_loader.CPS_Ops()
		dataframe['age_group_at_start'] = pd.cut(dataframe[age_at_start], bins=[0,18,25,34,54,64,150], right=True, labels=['18 and under','19-25','26-34','35-54','55-64','65+']).astype(str)
		dataframe['raw_earnings_change'] = dataframe[earnings_after_column] - dataframe[earnings_before_column]
		dataframe['years_in_program'] = dataframe[end_year_column] - dataframe[start_year_column]
		wage_change = cps.frames_wage_change_across_years(dataframe, start_year_column, end_year_column, 'age_group_at_start', statefip)
		wage_change['earnings_premium'] = wage_change['raw_earnings_change'] - wage_change['wage_change']
		return(wage_change)

if __name__ == "__main__":

	
	cps = cps_loader.CPS_Ops()
	model = cps.fit_mincer_model(36)
	wagedif = cps.mincer_based_wage_change(36, 92, 30, 10000, 4)
	wagedif2 = cps.mincer_based_wage_change(36, 92, 55, 50000, 4)
	print(wagedif)
	print(wagedif2)
	exit()
	predicted_wages = cps.predicted_wages([73,111],[4,10])
	print(predicted_wages)
	exit()	

	'''
	#baselines = cps.rudimentary_hs_baseline(8)

	exit()
	test_microdata = pd.read_csv("data/test_microdata.csv")
	premium_calc = Earnings_Premium.calculate(test_microdata, 'earnings_start', 'earnings_end', 'program_start', 'program_end','age','state')

	print(premium_calc)
	exit()
	'''

	#x = abs(np.random.uniform(0,100,100000))
	x = np.concatenate([np.repeat(1,1000), np.repeat(200,2000)])
	y = np.concatenate([np.repeat(13,1000), np.repeat(2,10000)])

	z = [x,y]
	answer_T = Theil_T.Calculate_Ratio(z)
	answer_L = Theil_L.Calculate_Ratio(z)
	print(answer_T)
	print(answer_L)

	# decomposition background
	# http://siteresources.worldbank.org/PGLP/Resources/PMch6.pdf

	# right now the within group is N x the overall index


