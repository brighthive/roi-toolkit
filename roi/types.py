import pandas as pd
from roi.settings import *
from pandas.api.types import is_numeric_dtype, is_float_dtype
import warnings
import numpy as np
from roi import utilities

"""
This submodule presents a scaffold for future work. Eventually, the ROI Toolkit should provide robust validation methods
to help analysts and enginners avoid common data integration, cleanliness, and structure issues. At present, it consists only
of a base class, Validator(), which does some basic checks that should apply to all data that is piped into the Toolkit.

Child classes add their own methods.

"""

class Validator:
	"""
	The data validation base class. This class contains no @classmethods or factory methods - it should not be used on its own.
	"""
	def _validate_dataframe(self, data):
		"""
		Check to see if data passed is a DataFrame. If not, throw error.

		Parameters:
			data : a pandas dataframe

		Returns:
			None
		"""
		if isinstance(data, pd.DataFrame):
			self.data = data
		else:
			raise TypeError("Objects must be instantiated with a Pandas DataFrame. Argument passed was {}".format(type(data)))
		return None

	def _validate_identifier(self, identifier):
		"""
		Ensure that there is one row per item, based on a unique identifier column.
		This method exists to ensure a best practice of including such a unique identifier column.
		It can be overridden by passing the dataframe's index column. This is not recommended.

		Note that this method will throw an error unless it is called in a class that has a .data attribute, such as a class that inherits from Validator().

		Parameters:
			identifier : A column name containing unique identifiers

		Returns:
			None
		"""

		if self.data[identifier].is_unique:
			self.unique_identifier = identifier
		else:
			unique_rows = list(set(self.data[identifier]))
			total_rows = len(self.data[identifier])
			raise Exception("Argument unique_identifier must uniquely identify rows in passed dataframe. Identifier '{}' has {} unique values for {} rows".format(identifier, str(unique_rows), str(total_rows)))

		return None

	@staticmethod
	def readability_check(series):
		"""
		A helper method that just checks to see if a column is numeric and warns the user if it's not.
		It is, as the name suggests, a readability check.

		Parameters:
			series : a pandas series

		Returns:
			None
		"""
		if (is_numeric_dtype(series)):
			warnings.warn("Column '{}' is numeric. Are you sure you want to calculate statistics across this variable? For human readability, it is advisable to use unique string or factor variables.".format(series.name))
		return(None)

	@staticmethod
	def nancheck(series):
		"""
		A helper method that checks to NaN values and warns the user if it finds them.
		As per the warning below, it should be used in the context of calculations that may use
		methods that ignore NaN values, such as e.g. numpy.nansum()

		Parameters:
			series : a pandas series

		Returns:
			None
		"""
		length = len(series)
		nans = pd.isna(series).sum()
		if nans > 0:
			warnings.warn("Column {} contains {} NA values ({}% of {}). Calculations on this column may EXCLUDE these empty observations.".format(series.name, nans, round(100*nans/length, 2), length))
		return(None)


class ProgramRecord(Validator):
	"""
	This class is a validation structure for data about programs, which should have, at the very least, unique identifiers for
	each program and a column describing the certification granted to completers. It does not automatically check length
	and cost, but does validation on those columns in they are provided.

	Parameters:
		data                   :   Pandas dataframe containing data about educational or training programs that must contain one row per program
		unique_identifier      :   Name of the column in data that contains unique identifier
		certification_granted  :   Column name containing certifications granted
		program_length         :   Optional name for column containing program length data.
		program_cost           :   Optional name for column containing program cost data.

	Attributes:
		certification          :   A pandas series containing the list of certifications passed in the certification_granted column
		certification_types    :   A list of unique certifications included in the certification_granted column

		(only if program_length is provided)
		mean_program_length    :   Mean length of programs in the dataset
		median_program_length  :   Median length of programs in the dataset
		program_length_sd      :   Standard deviation of length of programs in the dataset
		min_program_length     :   Minimum program length
		max_program_length     :   Maximum program length

		(only if cost is provided)
		mean_program_cost      :   Mean length of programs in the dataset
		median_program_cost    :   Median length of programs in the dataset
		program_cost_sd        :   Standard deviation of length of programs in the dataset
		min_program_cost       :   Minimum program length
		max_program_cost       :   Maximum program length
	"""
	def __init__(self, data, unique_identifier, certification_granted, program_length=None, program_cost=None):
		self._validate_dataframe(data)
		self._validate_identifier(unique_identifier)
		self._checkcert(certification_granted)
		self._check_program_length(program_length)

	def _checkcert(self, cert):
		"""
		Conduct a readability check on the certification_granted column and set related attributes.
		"""
		self.readability_check(self.data[cert])
		self.certification = cert
		self.certification_types = list(self.data[cert].unique())
		print("Programs data contains {} unique certification or degree types".format(str(len(self.certification_types))))
		return(None)

	def _check_program_length(self, program_length_column):
		"""
		Conduct validation and set attributes for summary statistics about program length

		Parameters:
			program_length_column : Name of column containing program length data

		Returns:
			None
		"""

		if (program_length_column is None):
			return(None)
		else:
			program_length = self.data[program_length_column]

		# check for nans
		self.nancheck(program_length)

		program_length_dtype = program_length.dtype

		if (is_numeric_dtype(program_length)):
			if (is_float_dtype(program_length)):
				warnings.warn("Column {} is float, e.g. it is formatted to include decimal points. Program lengths are typically expressed in quarters, semesters, or years. These units are typically whole numbers. Consider changing the type of this column to int".format(program_length.name))
		else:
			raise ValueError("Program length columns must be numeric! Column {} has type '{}'".format(program_length.name, program_length_dtype))

		# column description
		col_describe = program_length.describe()

		# Summary stats
		self.mean_program_length = col_describe['mean']
		self.median_program_length = col_describe['50%']
		self.program_length_sd = col_describe['std']
		self.min_program_length = col_describe['min']
		self.max_program_length = col_describe['max']

		print("Summary statistics for program length column '{}':".format(program_length.name))
		print(col_describe)

		return(None)

	def _check_program_cost(self, program_cost_column):
		"""
		Conduct validation and set attributes for summary statistics about program cost

		Parameters:
			program_cost_column : Name of column containing program cost data

		Returns:
			None
		"""

		if (program_cost_column is None):
			return(None)
		else:
			program_cost = self.data[program_cost_column]

		# check for nans
		self.nancheck(program_cost)

		program_cost_dtype = program_cost.dtype

		if not is_numeric_dtype(program_cost):
			raise ValueError("Program cost columns must be numeric! Column {} has type '{}'".format(program_cost_column, program_cost_dtype))

		# column description
		col_describe = program_cost.describe()

		# Summary stats
		self.mean_program_cost = col_describe['mean']
		self.median_program_cost = col_describe['50%']
		self.program_cost_sd = col_describe['std']
		self.min_program_cost = col_describe['min']
		self.max_program_cost = col_describe['max']

		print("Summary statistics for program length column '{}':".format(program_cost_column))
		print(col_describe)

		return(None)


class IndividualRecord(Validator):
	"""
	This class is a validation structure for information about individuals.

	Paramaters:
		data                :    A pandas dataframe containing information about individuals, with one row for eah
		unique_identifier   :    The name of the column in data containing unique identifiers
		unit_of_analysis    :    The name of the column denoting the primary unit of analysis for e.g. equity data, such as program or institution

	Attributes:
		group_counts        :    The number of individual groups / unique values of data[unit_of_analysis]
		unit                :    Identical to the value passed as the unit_of_analysis parameter
	"""
	def __init__(self, data, unique_identifier, unit_of_analysis):
		self._validate_dataframe(data)
		self._validate_identifier(unique_identifier)
		self._validate_unit(unit_of_analysis)

	def _validate_unit(self, unit_of_analysis):
		"""
		The unit of analysis is the level on which calculations like the earnings premium are calculated, e.g. the program or institution.
		IndividualRecord data must have a column that denotes this. If data represents only one institution or program, users must pass a
		column containing only one unique value.

		Parameters:
			unit_of_analysis : name of a column in the dataframe passed to IndividualRecoerd()

		Returns:
			None
		"""

		# Warn the user if a numeric column is passed
		unit_column = self.data[unit_of_analysis]

		self.readability_check(unit_column)

		# Identify if groups have fewer than min_group_size elements and create an attribute with group counts for later reference
		count_per_group = self.data.groupby(unit_of_analysis, as_index=False)[self.unique_identifier].count().rename(columns={self.unique_identifier:"count"})
		self.group_counts = count_per_group

		if (count_per_group['count'].min() < Defaults.min_group_size):
			warnings.warn("Some groups have fewer than {} individuals. By default, summary statistics for these groups may not be reported".format(Defaults.min_group_size))
			print("\nGroups with fewer than {} individuals:".format(Defaults.min_group_size))
			print(count_per_group[count_per_group['count'] < Defaults.min_group_size])
			print("\n")

		self.unit = unit_of_analysis

		return None



