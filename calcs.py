import pandas as pd
import numpy as np

def dataframe_to_ndarray(dataframe):
	return None

class Supporting:
	def group_aggregation(dataframe, aggregation_category_list, variable_to_aggregate, aggregation_method):
		aggregated_name = "{}_{}".format(aggregation_method, variable_to_aggregate)
		aggregated = test_microdata.groupby(aggregation_category_list)[variable_to_aggregate].aggregate(aggregation_method).reset_index().rename(columns={variable_to_aggregate:aggregated_name})		
		return aggregated

class Theil_T:
	def theil_within_group(vector_of_values):
		# T_i
		# currently takes only positive values and may only ever take positive values
		x = vector_of_values # for readability
		N = len(x)
		mu = np.mean(x)
		xi_over_mu = x / mu
		ln_xi_over_mu = np.log(xi_over_mu)
		theil = (1/N)*np.sum(xi_over_mu * ln_xi_over_mu)
		return theil

	def s_i(array, N, mu):
		N_i = len(array)
		x_i_bar = np.mean(array)
		s_i = (N_i/N) * (x_i_bar/mu)
		return s_i

	def first_term(array_of_groups):
		N = array_of_groups.size
		mu = np.mean(array_of_groups)
		T_i = np.apply_along_axis(Theil_T.theil_within_group, 1, array_of_groups)
		s_i = np.apply_along_axis(Theil_T.s_i, 1, array_of_groups, N=N, mu=mu)
		first_term = np.sum(T_i * s_i)
		return first_term

	def second_term(array_of_groups):
		N = array_of_groups.size
		mu = np.mean(array_of_groups)
		s_i = np.apply_along_axis(Theil_T.s_i, 1, array_of_groups, N=N, mu=mu)
		x_i = np.apply_along_axis(np.mean, 1, array_of_groups)
		second_term = np.sum(s_i * np.log(x_i / mu))
		return second_term

	def Calculate_Index(array_of_groups):
		Index = Theil_T.first_term(array_of_groups) + Theil_T.second_term(array_of_groups)
		return Index

	def Calculate_Ratio(array_of_groups):
		first_term = Theil_T.first_term(array_of_groups)
		second_term = Theil_T.second_term(array_of_groups)
		ratio = second_term / (first_term + second_term)
		return ratio

if __name__ == "__main__":
	#test_microdata = pd.read_csv("data/test_microdata.csv")
	#mean_along_axes = Supporting.group_aggregation(test_microdata, ['race','gender'],'data','mean')
	#sum_along_axes = Supporting.group_aggregation(test_microdata, ['race','gender'],'data','sum')

	#x = abs(np.random.uniform(0,100,100000))
	x = np.concatenate([np.repeat(3,1000), np.repeat(3,1000)])
	y = np.concatenate([np.repeat(3.1,1000), np.repeat(3.1,1000)])
	z = np.array([x,y])
	answer = Theil_T.Calculate_Ratio(z)
	print(answer)
	exit()
	theil = Theil_T.theil_within_group(x)
	print(theil)