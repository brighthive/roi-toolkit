import pandas as pd
import numpy as np
from roi import earnings, records, macrostats, get_data
import sys
#print(sys.modules.keys())


class Earnings_Premium:
	"""
	Methods for calculating the earnings premium and variations thereof.
	The earnings premium is interpretable as the expected increase in earnings an incoming student can expect at various intervals at the graduation from a program.
	It's calculated by taking the difference between pre- and post-program earnings and correcting for trend.
	Trend is calculated using CPS data for the change in average earned income for individuals in (a) a given age group with (b) a given qualification
	"""
	def calculate(dataframe, earnings_before_column, earnings_after_column, start_year_column, end_year_column, age_at_start, statefip):
		cps = earnings.CPS_Ops()
		dataframe['age_group_at_start'] = pd.cut(dataframe[age_at_start], bins=[0,18,25,34,54,64,150], right=True, labels=['18 and under','19-25','26-34','35-54','55-64','65+']).astype(str)
		dataframe['raw_earnings_change'] = dataframe[earnings_after_column] - dataframe[earnings_before_column]
		dataframe['years_in_program'] = dataframe[end_year_column] - dataframe[start_year_column]
		wage_change = cps.frames_wage_change_across_years(dataframe, start_year_column, end_year_column, 'age_group_at_start', statefip)
		wage_change['earnings_premium'] = wage_change['raw_earnings_change'] - wage_change['wage_change']
		return(wage_change)

if __name__ == "__main__":

	test_microdata = pd.read_csv("testing/testing-data/test_microdata.csv")
	cpi_adjustments = get_data.cpi_adjustments()
	test_microdata['fixed'] = macrostats.Adjustments.adjust_to_current_dollars(test_microdata, 'program_start', 'earnings_start', cpi_adjustments)
	exit()

	# create wage record from microdata
	test_records = records.WageRecord(data = test_microdata, unique_identifier="Unnamed: 0", unit_of_analysis="program")


	exit()

	print(test_microdata)
	exit()

	
	cps = earnings.CPS_Ops()
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


