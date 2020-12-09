import pandas as pd
import numpy as np
from roi import utilities
import seaborn as sns
from matplotlib import pyplot as plt
import warnings

"""

### Equity metrics ###

This submodule contains methods for calculating equity metrics. Each metric has its own class, inherited from the Metric()
class, which provides useful attributes for all metrics. Each equity metric coded here is a measure that is generally
decomposable into within- and between-group inequality. As such, each method also provides two attributes.

(1) is .overall, which provides the value of the index being calculated (Variance, Gini, Theil-L or Theil T). In order to do so,
each metric calculates the decomposition of both within- and between-group values of the given metric, e.g. between-group Gini or
within-group Gini. 

(2) is .ratio, which is the ratio of between-group inequality to overall inequality. This is interpretable, broadly speaking,
as the amount of variation that is accounted for by intergroup variation. As such, it takes a value from 0 to 1, where 0 indicates
that none of the variation across the provided value is accounted for by intergroup differences. This is an indicator for, or proxy of,
inequality across groups.

Ideally, variation in individual outcomes is driven only by individual differences, instead of group membership. Therefore, the closer
the value of .ratio is to 1, the more outcomes seem to be accounted for by group membership, and the "worse" the inequality situation is.

The values of .overall and .ratio should be taken as clues for future investigation of possible inequalities or inequities, not as
metrics that themselves demonstrate disparate treatment, bias, or discrimination. Intergroup difference is not itself evidence of
discrimination or bias. However, where discrimination or bias is at play, intergroup difference is likely to appear.

Please note that all methods here IGNORE NA VALUES.

References
-----------
https://seer.cancer.gov/help/hdcalc/inference-methods/individual-level-survey-sample-1/measures-of-relative-disparity/theil-index-t
https://utip.lbj.utexas.edu/papers/utip_14.pdf
https://www.usi.edu/media/3654811/Analysis-of-Inequality.pdf
https://en.wikipedia.org/wiki/Theil_index
http://www.fao.org/3/a-am342e.pdf

### Area Deprivation Index ###


"""

class Metric():
	"""
	This is equity Metric() parent class from which all the equity child metric classes inherit.

	Parameters:
		unique_groups           :   A numpy array containing the names or values of different groups within a population e.g. np.array(['Men','Women'])
		grouped_values          :   A list of numpy arrays, each of which contains values for one and only one group. This list should be ordered according
							to the value of unique_groups (above), e.g. [np.array([values for men]), np.array(values for women)]

	Attributes:
		unique_groups           :   The value passed as an argument for unique_groups
		grouped_values          :   The value passed as an argument for grouped_values
		ungrouped_observations  :   A single numpy array of all observations, ordered by group
		n_groups                :   The number of unique groups passed in unique_groups
		n                       :   The number of values across all groups
		viz                     :   A Seaborn boxplot offering a simple visualization of cross-group variation
		nans                    :   The number of NaN values passed to the class

	"""
	def __init__(self, unique_groups, grouped_values):
		self.unique_groups = unique_groups
		self.grouped_values = grouped_values
		self.ungrouped_observations = np.concatenate(self.grouped_values).flatten()
		self.n_groups = len(self.unique_groups)
		self.n = len(self.ungrouped_observations)
		self.viz = self.simple_viz(self.unique_groups, self.grouped_values)
		self.nans = np.sum(np.isnan(self.ungrouped_observations))

		if self.nans > 0:
			warnings.warn("Data passed contains {} NA values. All equity metrics are calculated by ignoring NA values, in effect dropping them. Please ensure that you have a strategy for dealing with these missing values. If values are not missing at random, e.g. if individuals with missing values have common traits, then ALL METRICS calculated will be biased.".format(self.nans))

		# add nan handling

	# factory method
	@classmethod
	def from_dataframe(cls, frame, group_columns, value_column, sample=False):
		"""
		This factory method allows us to pass a dataframe directly to any equity metric class instead of having to create numpy arrays from it

		Parameters:
			frame			:	A dataframe
			group_columns	:	The name of the column that denotes groups, or a list of columns on which to group
			value_column	:	The name of the column that contains values to be analyzed
			sample			:	If False, will use the whole dataset. Otherwise, should be a number denoting the size of the sample to take. Defaults to False.
		"""
		if sample != False:
			warnings.warn("When sample == True, Metric() will use the value of sample to create a random subset of values that it will use for all calculations. This number will be stored as attribute .samplesize.")
			if not isinstance(sample, int):
				raise ValueError("If not False, sample must be an integer")
			else:
				frame = frame.sample(sample)
		unique_groups, grouped_values = utilities.dataframe_groups_to_ndarray(frame, group_columns, value_column)
		cls.summary = utilities.multiple_describe(frame, group_columns, value_column)
		cls.sample = sample
		return(cls(unique_groups, grouped_values))

	@staticmethod
	def simple_viz(unique_groups, grouped_values):
		"""
		This produces a box plot that allows the analyst to quickly and visually assess differences betweenb groups

		Parameters:
			unique_groups	:	A numpy array containing the names or values of different groups within a population e.g. np.array(['Men','Women'])
			grouped_values	:	A list of numpy arrays, each of which contains values for one and only one group. This list should be ordered according
								to the value of unique_groups (above), e.g. [np.array([values for men]), np.array(values for women)]

		Return:
			fig				:	A complete Seaborn boxplot that can be displayed or saved to disk

		"""
		x = np.array(grouped_values)
		fig, ax = plt.subplots(1,1)
		plot = sns.boxplot(data = x, labels=[unique_groups], ax = ax, orient='h', showfliers=False) # annotate interpretation
		ax.set_yticklabels(unique_groups)
		fig.tight_layout()
		plt.close()
		return(fig)

class Theil_T(Metric):
	"""
	Class provides methods for calculating individual terms in the Theil T index. See references for more detail.
	The Theil index is perfectly decomposable into between- and within-group inequality. It works only using
	positive values, which makes it unsuitable for assessing inequality across values that may take any
	value across the entire real line (e.g. net worth, or any kind of difference).

	Relative to the Theil L, the Theil T metric is sensitive to changes at the top end of the distribution.

	"""

	def calculate(self):
		self.within = self.first_term(self.grouped_values)
		self.between = self.second_term(self.grouped_values)
		self.overall = self.within + self.between
		self.ratio = self.between / self.overall

		if min(self.ungrouped_observations < 0):
			raise ValueError("Theil indices can be calculated using only positive values. Data passed contains negative values. If you have negative values, use the Gini() or Variance_Analysis() equity metric classes")

	@staticmethod
	def theil_within_group(vector_of_values):
		"""
		T_i in the Theil index expression
		
		Parameter - Numpy vector or array of values
		Returns - Scalar (float)

		"""
		x = vector_of_values # for readability
		N = len(x)
		mu = np.nanmean(x)
		xi_over_mu = x / mu
		xi_over_mu[xi_over_mu < 0] = 0
		ln_xi_over_mu = np.log(xi_over_mu)
		theil = (1/N)*np.nansum(xi_over_mu * ln_xi_over_mu)
		return theil

	@staticmethod
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
		x_i_bar = np.nanmean(array)
		s_i = (N_i/N) * (x_i_bar/mu)
		return s_i

	@staticmethod
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
		mu = np.nanmean(full_population)
		T_i = np.array([Theil_T.theil_within_group(group) for group in list_of_groups])
		s_i = np.array([Theil_T.s_i(group, N=N, mu=mu) for group in list_of_groups])
		first_term = np.nansum(T_i * s_i)
		return first_term

	@staticmethod
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
		mu = np.nanmean(full_population)
		s_i = np.array([Theil_T.s_i(group, N=N, mu=mu) for group in list_of_groups])
		x_i = np.array([np.nanmean(group) for group in list_of_groups])
		second_term = np.nansum(s_i * np.log(x_i / mu))
		return second_term

class Theil_L(Metric):
	"""
	Class provides methods for calculating individual terms in the Theil T index. See references for more detail.
	The Theil index is perfectly decomposable into between- and within-group inequality. It works only using
	positive values, which makes it unsuitable for assessing inequality across values that may take any
	value across the entire real line (e.g. net worth, or any kind of difference).

	Relative to the Theil L, the Theil T metric is sensitive to changes at the top end of the distribution.

	"""
	def calculate(self):
		self.within = self.first_term(self.grouped_values)
		self.between = self.second_term(self.grouped_values)
		self.overall = self.within + self.between
		self.ratio = self.between / self.overall

		if min(self.ungrouped_observations < 0):
			raise ValueError("Theil indices can be calculated using only positive values. Data passed contains negative values. If you have negative values, use the Gini() or Variance_Analysis() equity metric classes")

	@staticmethod
	def theil_within_group(vector_of_values):
		"""
		T_i in the Theil index expression
		
		Parameter - Numpy vector or array of values
		Returns - Scalar (float)

		"""
		x = vector_of_values # for readability
		N = len(x)
		mu = np.nanmean(x)
		mu_over_xi = mu / x
		ln_mu_over_xi = np.log(mu_over_xi)
		theil = (1/N)*np.nansum(ln_mu_over_xi)
		return theil

	@staticmethod
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

	@staticmethod
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
		mu = np.nanmean(full_population)
		L_i = np.array([Theil_L.theil_within_group(group) for group in list_of_groups])
		s_i = np.array([Theil_L.s_i(group, N=N) for group in list_of_groups])
		first_term = np.nansum(L_i * s_i)
		return first_term

	@staticmethod
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
		mu = np.nanmean(full_population)
		s_i = np.array([Theil_L.s_i(group, N=N) for group in list_of_groups])
		x_i = np.array([np.nanmean(group) for group in list_of_groups])
		second_term = np.nansum(s_i * np.log(mu / x_i))
		return second_term


class Variance_Analysis(Metric):
	"""
	This class offers the simplest possible decomposition of variation: it calculates population
	variance for a provided set of values, including between- and within- decompositions and the
	amount of variation accounted for by between-group differences.

	Please note that in this implementation, np.var calculates the POPULATION variance, not the SAMPLE variance.
	The assumption made here is that the data provided (e.g. linked education and UI records) represents the entirety
	of the population of interest.

	"""

	def calculate(self):
		self.within = self.variance_within(self.grouped_values, self.n)
		self.between = self.variance_between(self.grouped_values)
		self.overall = self.total_variance(self.ungrouped_observations)
		self.ratio = self.between / self.overall
		self.residual = self.overall - (self.within + self.between) # this should equal zero because variance decomposes perfectly, but floating-point meshugas could result in weirdness

	@staticmethod
	def variance_within(array_of_values, n):
		"""
		Parameters:
			array_of_values			:	A list of numpy arrays, each of which contains values for a particular group
			n						:	The total number of values/observations across all groups (should be identical to np.concatenate(array_of_values).size)

		Returns:
			within_group_variance	:	A scalar identifying the total within-group variance in tha dataset

		"""
		group_variances = [np.nanvar(group) for group in array_of_values]
		group_weights = np.asarray([len(group)/n for group in array_of_values])
		within_group_variance = np.nansum(group_variances * group_weights)
		return(within_group_variance)

	@staticmethod
	def variance_between(array_of_values):
		"""
		Parameters:
			array_of_values			:	A list of numpy arrays, each of which contains values for a particular group

		Returns:
			within_group_variance	:	A scalar identifying the total between-group variance in tha dataset

		"""
		within_group_means = [np.nanmean(group) for group in array_of_values]
		cross_group_variance = np.nanvar(within_group_means)
		return(cross_group_variance)

	@staticmethod
	def total_variance(observations):
		"""
		This is a standard variance calculation that ignores NaNs. As a sanity check, it should be identical to
		within-group variance plus between-group variance for any dataset.

		Parameters:
			observations			:	A single numpy array

		Returns:
			total_variance			:	A scalar identifying the total variance of the provided values

		"""
		total_variance = np.nanvar(observations)
		return(total_variance)


class Gini(Metric):
	"""
	The Gini index will be familiar to many users from its deployment as an income or wealth inequality metric in the settings
	of macroeconomics, international developmnent, and comparative politics. Please note that the Gini index is NOT perfectly
	decomposable into between- and within-group inequalities. It also contains a dimensionless residual element that is 
	positive when individuals' relative positions to other individuals WITHIN their respective groups tend to differ from their
	positions in the overall distribution without reference to groups.
	
	A .ratio attribute is also provided here, as the residual value is not meaningfully large enough to disrupt the interpretability of the ratio.
	"""
	def calculate(self):
		self.within = self.gini_within(self.grouped_values)
		self.between = self.gini_between(self.grouped_values)
		self.overall = self.gini(self.ungrouped_observations)
		self.residual = self.overall - (self.within + self.between)
		self.ratio = self.between / self.overall

	@staticmethod
	def gini_within(array_of_values):
		"""
		Available as a static method, this method allows the calculation of within-group Gini, which is an overall measure of the
		'evenness' of a distribution of any value. Lower values denote greater equality, with 0 representing absolute equality and 1
		representing all value accruing to a single individual.

		Parameters:
			array_of_values		:	A numpy array of numeric values

		Returns:
			G_within			:	Within-group Gini

		"""
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
		"""
		Available as a static method, this method allows the calculation of between-group Gini, which is, generally speaking,
		a simple measure of the dispersal of group means.

		Parameters:
			array_of_values		:	A list of numpy arrays, each containing values for a particular group

		Returns:
			G_between			:	Between-group Gini
		"""
		means_replaced = np.concatenate([np.repeat(np.nanmean(group), len(group)) for group in array_of_values])
		G_between = Gini.gini(means_replaced)	
		return(G_between)

	@staticmethod
	def gini(values):
		"""
		Given an array of values of any type, calculates the Gini index.

		Parameters:
			values	:	A numpy array

		Returns:
			G		:	The value of the Gini coefficient for the provided values
		"""
		n = len(values)
		xbar = np.nanmean(values)
		ad = np.array([abs(i - j) for i in values for j in values])
		G = np.nansum(ad)/(2*n*n*xbar)
		return(G)


class ADI(object):
	"""
	The ROI Toolkit is packaged with the Area Deprivation Statistics, which can be downloaded from: https://www.neighborhoodatlas.medicine.wisc.edu/

	This object, at init, simply reads in the raw textfile of ADI indices at the block group level and forms it into quintiles.
	It currently uses the ADI based on the 2011-2015 ACS 5-year estimates.

	The ADI data is produced at the Census block group level, but block groups containing less than 100 persons, 30 housing units, or those with >33% of pop
	living in group quarters are suppressed with the value "PH". In this class, ADI indices are coerced to numeric, so suppressed indices are coerced to NaN.

	At init, ADI indices are bucketed into quintiles. IMPORTANT: Lower quintiles are HIGHER-SES. Higher quintiles are more deprived.

	Obviously, in order to use this class, you will need to have individual observations associated with Census block groups.
	This can be accomplished with the 'Census' class in the 'external' submodule.

	Instances of the ADI() class take no arguments on init - they simply read in the ADI data and prepare it for use.
	"""
	def __init__(self):
		adi_location = settings.File_Locations.adi_location
		adi = pd.read_csv(adi_location, sep=',', dtype="str") # read in ADI by block group from text file
		adi['adi_natrank_numeric'] = pd.to_numeric(adi['adi_natrank'], errors='coerce')
		adi['adi_quintile'] = pd.qcut(adi['adi_natrank_numeric'], [0, 0.2, 0.4, 0.6, 0.8, 1], labels=["0-20","20-40","40-60","60-80","80-100"])
		self.adi_frame = adi
		return None

	def get_quintile_for_geocode(self, fips_geocode):
		"""
		Parameters:
		-----------
		fips_geocode : str
			Twelve-digit FIPS code

		adi_frame : Pandas DataFrame
			ADI Dataframe produced above in ADI.get_adi_frame()

		Returns
		-------
		A single string value such as "0-20" denoting the deprivation percentile of the provided block group.
		"""
		slice_ = self.adi_frame.loc[self.adi_frame.fips == fips_geocode, 'adi_quintile'].iat[0]
		return(slice_)

	def get_quintile_for_geocodes_frame(self, dataframe, geocode_column_name):
		"""
		Parameters:
		-----------
		dataframe : Pandas Dataframe
			Dataframe with a column containing geocode

		geocode_column_name : str
			Name of column in dataframe containing geocodes

		Returns
		-------
		The original dataframe with an "adi_quintile" column containing the ADI quintile.

		Notes
		-------
		Geocodes often contain leading zeroes, so be sure that the input column is correctly formatted! It should be an object or str.
		"""

		adi_ranks_only = self.adi_frame[['fips', 'adi_quintile']]
		geocodes_merged = dataframe.merge(adi_ranks_only, left_on=geocode_column_name, right_on='fips', how='left', indicator=True)

		# count up the merges
		count_merged = np.sum(geocodes_merged._merge == "both")
		count_unmerged = len(dataframe) - count_merged
		print("Geocode merge: Merged {} of {} observations in input dataframe ({}%)".format(str(count_merged), str(count_unmerged), str(round(100*count_merged/len(dataframe), 2))))

		# a little bit of error handling
		if (count_merged == 0):
			print ("Merged 0 of {} observations in input dataframe! Make sure that geocodes have been read in the correct format and watch out for the removal of leading zeroes!".format(str(len(dataframe))))

		del geocodes_merged['_merge']
		del geocodes_merged['fips']

		return(geocodes_merged['adi_quintile'].to_numpy())

