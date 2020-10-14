import pandas as pd
import numpy as np
from roi import utilities
import seaborn as sns
from matplotlib import pyplot as plt

#sns.set_theme(style="whitegrid") # set seaborn theme

class Metric():
	def __init__(self, unique_groups, grouped_values):
		self.unique_groups = unique_groups
		self.grouped_values = grouped_values
		self.ungrouped_observations = np.concatenate(self.grouped_values).flatten()
		self.n_groups = len(self.unique_groups)
		self.n = len(self.ungrouped_observations)
		self.viz = self.simple_viz(self.unique_groups, self.grouped_values)

	# factory method
	@classmethod
	def from_dataframe(cls, frame, group_columns, value_column):
		unique_groups, grouped_values = utilities.dataframe_groups_to_ndarray(frame, group_columns, value_column)
		cls.summary = utilities.multiple_describe(frame, group_columns, value_column)
		return(cls(unique_groups, grouped_values))

	@staticmethod
	def simple_viz(unique_groups, grouped_values):
		x = np.array(grouped_values)
		fig, ax = plt.subplots(1,1)
		plot = sns.boxplot(data = x, labels=[unique_groups], ax = ax, orient='h', showfliers=False) # annotate interpretation
		ax.set_yticklabels(unique_groups)
		fig.tight_layout()
		plt.close()
		return(fig)

class Theil_T(Metric):
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
		xi_over_mu[xi_over_mu < 0] = 0
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

	def Ratio_From_DataFrame(dataframe, variable_of_concern, grouping_variable):
		groups, values = dataframe_groups_to_ndarray(dataframe, grouping_variable, variable_of_concern)

		zero_or_less = (np.concatenate(values).flatten() <= 0).sum()
		if (zero_or_less > 0):
			raise ValueError("Variable provided contains zero or negative values. The Theil T index works only with positive values.")

		t_ratio = Theil_T.Calculate_Ratio(values)
		return(t_ratio)


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

	def Ratio_From_DataFrame(dataframe, variable_of_concern, grouping_variable):
		groups, values = dataframe_groups_to_ndarray(dataframe, grouping_variable, variable_of_concern)

		zero_or_less = (np.concatenate(values).flatten() <= 0).sum()
		if (zero_or_less > 0):
			raise ValueError("Variable provided contains zero or negative values. The Theil T index works only with positive values.")

		l_ratio = Theil_L.Calculate_Ratio(values)
		return(l_ratio)


class Variance_Analysis:
	# decomposition of income inequality by subgroups: http://www.fao.org/3/a-am342e.pdf
	# To reduce dependencies and improve flexibility, we implement our own ANOVA
	# should implement both bayesian (nonparametric) and frequentist (parametric) anova
	# Please note that in this implementation, np.var calculates the POPULATION variance, not the SAMPLE variance

	def Variance_Components(array_of_groups, array_of_values):
		ungrouped_observations = np.concatenate(array_of_values).flatten()
		n = len(ungrouped_observations)
		total_variance = np.var(ungrouped_observations)

		group_variances = [np.var(group) for group in array_of_values]
		group_weights = np.asarray([len(group)/n for group in array_of_values])
		within_group_means = [np.mean(group) for group in array_of_values]

		within_group_variance = np.sum(group_variances * group_weights)
		cross_group_variance = np.var(within_group_means)
		
		return(total_variance, within_group_variance, cross_group_variance)

	def Ratio(array_of_groups, array_of_values):
		total_variance, within_group_variance, cross_group_variance = ANOVA.Variance_Components(array_of_groups, array_of_values)
		return(cross_group_variance/total_variance)

	def Analysis(array_of_groups, array_of_values):
		return(None)



'''
		self.unique_groups = unique_groups
		self.grouped_values = grouped_values
		self.ungrouped_observations = np.concatenate(self.grouped_values).flatten()
		self.n_groups = len(self.unique_groups)
		self.n = len(self.ungrouped_observations)
		self.viz = self.simple_viz(self.unique_groups, self.grouped_values)
'''


class Gini(Metric):
	# Please note as well that the Gini index is not perfectly decomposable, and contains a residual element K
	# 
	def calculate(self):
		self.G_within = self.gini_within(self.grouped_values)
		self.G_between = self.gini_between(self.grouped_values)
		self.G_overall = self.gini(self.ungrouped_observations)
		self.residual = self.G_overall - (self.G_within + self.G_between)
		self.ratio = self.G_between / self.G_overall

	@staticmethod
	def gini_within(array_of_values):
		ungrouped_observations = np.concatenate(array_of_values).flatten()
		n = len(ungrouped_observations)
		group_shares = np.asarray([len(group)/n for group in array_of_values])
		value_shares = np.asarray([np.nansum(group)/np.nansum(ungrouped_observations) for group in array_of_values])
		group_weights = value_shares * group_shares
		ginis = np.array([Gini.gini(group) for group in array_of_values])
		G_within = np.nansum(ginis * group_weights)
		return(G_within)

	@staticmethod
	def gini_between(array_of_values):
		means_replaced = np.concatenate([np.repeat(np.nanmean(group), len(group)) for group in array_of_values])
		G_between = Gini.gini(means_replaced)	
		return(G_between)

	@staticmethod
	def gini(values):
		n = len(values)
		xbar = np.nanmean(values)
		ad = np.array([abs(i - j) for i in values for j in values])
		G = np.nansum(ad)/(2*n*n*xbar)
		return(G)


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




