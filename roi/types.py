import pandas as pd
from roi.settings import *
from pandas.api.types import is_numeric_dtype
import warnings

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
			raise Exception("Argument unique_identifier must uniquely identify rows in passed dataframe. Identifier '{}' has {} unique values for {} rows".format(identifier, str(unique_rows), str(rows_in_dataframe)))

		return None

	@staticmethod
	def readability_check(series):
		if (is_numeric_dtype(series)):
			warnings.warn("Column '{}' is numeric. Are you sure you want to calculate wage statistics across this variable? For human readability, it is advisable to use unique string or factor variables.".format(series.name))
		return(None)		


class Programs(Validator):
	def __init__(self, dataframe, unique_identifier, certification_granted, program_length=None, program_cost=None):
		self._validate_dataframe(data)
		self._validate_identifier(unique_identifier)

	def checkcert(self):
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
		unit_column_list = list(unit_column)

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
