import numpy as np
import pandas as pd

class Summaries:

	def summary_by_group(frame_, grouping_factors, column_to_aggregate):
		grouped = frame_.groupby(grouping_factors, as_index=False)[column_to_aggregate].agg({'n':np.size,'mean':np.mean, 'median':np.median, 'sd':np.std, 'min':np.min, 'max':np.max})
		return(grouped)


class Dates:

	def combine(thign):
		return(None)

	def separate(thing):
		return(None)