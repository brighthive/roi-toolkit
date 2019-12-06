import pandas as pd
import numpy as np

class Supporting:
	def group_aggregation(dataframe, aggregation_category_list, variable_to_aggregate, aggregation_method):
		aggregated_name = "{}_{}".format(aggregation_method, variable_to_aggregate)
		aggregated = test_microdata.groupby(aggregation_category_list)[variable_to_aggregate].aggregate(aggregation_method).reset_index().rename(columns={variable_to_aggregate:aggregated_name})		
		return aggregated

class Theil:
	def theil_t_within_group(vector_of_values):
		# currently takes only positive values and may only ever take positive values
		x = vector_of_values # for readability
		N = len(x)
		mu = np.mean(x)
		xi_over_mu = x / mu
		ln_xi_over_mu = np.log(xi_over_mu)
		theil = (1/N)*np.sum(xi_over_mu*ln_xi_over_mu)
		return theil

	def theil_t_across_groups(vector_of_values):
		#?
		return None

if __name__ == "__main__":
	test_microdata = pd.read_csv("data/test_microdata.csv")
	mean_along_axes = Supporting.group_aggregation(test_microdata, ['race','gender'],'data','mean')
	sum_along_axes = Supporting.group_aggregation(test_microdata, ['race','gender'],'data','sum')


	#x = abs(np.random.uniform(0,100,100000))
	x = np.concatenate([np.repeat(3,1000), np.repeat(2,1000)])
	print(x)
	theil = Theil.theil_t_within_group(x)
	print(theil)