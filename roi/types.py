import pandas as pd
from roi.settings import *
from pandas.api.types import is_numeric_dtype, is_float_dtype
import warnings
import numpy as np
from roi import utilities

class Validator:
	def _validate_dataframe(self, data):
		"""
		Check to see if data passed is a DataFrame. If not, throw error.
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
		if (is_numeric_dtype(series)):
			warnings.warn("Column '{}' is numeric. Are you sure you want to calculate statistics across this variable? For human readability, it is advisable to use unique string or factor variables.".format(series.name))
		return(None)

	@staticmethod
	def nancheck(series):
		length = len(series)
		nans = pd.isna(series).sum()
		if nans > 0:
			warnings.warn("Column {} contains {} NA values ({}% of {}). Calculations on this column will EXCLUDE these empty observations.".format(series.name, nans, round(100*nans/length, 2), length))
		return(None)


class Programs(Validator):
	def __init__(self, data, unique_identifier, certification_granted, program_length=None, program_cost=None):
		self._validate_dataframe(data)
		self._validate_identifier(unique_identifier)
		self._checkcert(certification_granted)
		self._check_program_length(program_length)

	def _checkcert(self, cert):
		self.readability_check(self.data[cert])
		self.certification = cert
		self.certification_types = list(self.data[cert].unique())
		print("Programs data contains {} unique certification or degree types".format(str(len(self.certification_types))))
		return(None)

	def _check_program_length(self, program_length_column):

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

	def _check_program_cost(self, program_cost):
		if (program_cost is None):
			return(None)
		return(None)


class WageRecord(Validator):
	def __init__(self, data, unique_identifier, unit_of_analysis):
		self._validate_dataframe(data)
		self._validate_identifier(unique_identifier)
		self._validate_unit(unit_of_analysis)

	def _validate_unit(self, unit_of_analysis):
		"""
		The unit of analysis is the level on which calculations like the earnings premium are calculated, e.g. the program or institution.
		WageRecord data must have a column that denotes this. If data represents only one institution or program, users must pass a
		column containing only one unique value.
		"""

		# Warn the user if a numeric column is passed
		unit_column = self.data[unit_of_analysis]

		self.readability_check(unit_column)

		# Identify if groups have fewer than min_group_size elements and create an attribute with group counts for later reference
		count_per_group = self.data.groupby(unit_of_analysis, as_index=False)[self.unique_identifier].count().rename(columns={self.unique_identifier:"count"})
		self.group_counts = count_per_group

		if (count_per_group['count'].min() < Defaults.min_group_size):
			warnings.warn("Some groups have fewer than {} individuals. By default, summary statistics for these groups will not be reported".format(Defaults.min_group_size))
			print("\nGroups with fewer than {} individuals:".format(Defaults.min_group_size))
			print(count_per_group[count_per_group['count'] < Defaults.min_group_size])
			print("\n")

		self.unit = unit_of_analysis

		return None

	@classmethod
	def from_education_and_wage(WageRecord_object, Programs_Object, Student_Object, Wage_Object):
		return(None)

class Metric:
	def __init__(self, dataframe):
		self.data = dataframe
		self.individual_stats = None
		self.group_stats = None




