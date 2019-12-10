import pandas as pd
import numpy as np
"""
TO do here:

- mean wages for all
- mean wages for employed
- use person weights
- account for inflation?
- ???

"""

pd.set_option('display.float_format', lambda x: '%.3f' % x)

class CPS_Extract_Data:
	"""
	Extract available at cps.ipums.org
	Current variables:
	LABFORCE
	EMPSTAT
	AGE
	EDUC
	INCWAGE
	STATEFIP
	CPI99
	(ASECWT is included automatically)

	"""
	filepath_to_csv = "../data/cps/cps_00024.csv"

class CPS_Ops(object):
	def __init__(self):
		self.microdata = pd.read_csv(CPS_Extract_Data.filepath_to_csv)
		self.microdata['age_group'] = pd.cut(self.microdata['AGE'], bins=[0,18,25,34,54,64,150], right=True).astype(str)
		self.microdata['hs_education_at_most'] = self.microdata['EDUC'] < 80
		self.microdata.loc[self.microdata.INCWAGE > 9999998, 'INCWAGE'] = np.nan
		self.microdata['INCWAGE_99'] = self.microdata['INCWAGE'] * self.microdata['CPI99']
		self.hs_grads_only = self.microdata[self.microdata.hs_education_at_most == 1]
		self.get_all_mean_wages()
		self.get_hs_grads_mean_wages()

	def get_all_mean_wages(self):
		mean_wages = self.microdata.groupby(['YEAR','STATEFIP','age_group']).apply(lambda x: pd.Series({"mean_INCWAGE":np.sum(x['INCWAGE_99'] * x['ASECWT'])/np.sum(x['ASECWT'])})).reset_index()
		self.all_mean_wages = mean_wages
		return None

	def get_hs_grads_mean_wages(self):
		mean_wages = self.hs_grads_only.groupby(['YEAR','STATEFIP','age_group']).apply(lambda x: pd.Series({"mean_INCWAGE":np.sum(x['INCWAGE_99'] * x['ASECWT'])/np.sum(x['ASECWT'])})).reset_index()
		self.hs_grads_mean_wages = mean_wages
		return None

	def wage_change_across_years(self, start_year, end_year, age_group_at_start, statefip):
		wage_start = self.all_mean_wages.loc[(self.all_mean_wages['YEAR'] == start_year) & (self.all_mean_wages['age_group'] == age_group_at_start) & (self.all_mean_wages['STATEFIP'] == statefip), 'mean_INCWAGE'].iat[0]
		wage_end = self.all_mean_wages.loc[(self.all_mean_wages['YEAR'] == end_year) & (self.all_mean_wages['age_group'] == age_group_at_start) & (self.all_mean_wages['STATEFIP'] == statefip), 'mean_INCWAGE'].iat[0]
		wage_change = wage_end - wage_start
		return(wage_change)

	def frames_wage_change_across_years(self, ind_frame, start_year_column, end_year_column, age_group_start_column, statefip_column):
		merged_start = ind_frame.merge(self.all_mean_wages, left_on=[start_year_column, age_group_start_column, statefip_column], right_on=['YEAR','age_group','STATEFIP'], how='left')
		merged_both = merged_start.merge(self.all_mean_wages, left_on=[end_year_column, age_group_start_column, statefip_column], right_on=['YEAR','age_group','STATEFIP'], how='left', suffixes=('_start','_end'))
		merged_both['wage_change'] = merged_both['mean_INCWAGE_end'] - merged_both['mean_INCWAGE_start']
		return(merged_both)

if __name__ == "__main__":
	
	cps = CPS_Ops()

	example_frames_to_merge = pd.DataFrame([{"age_group":'(25.0, 34.0]',"year_start":2010,"year_end":2014,"statefip":1},{"age_group":'(18.0, 25.0]',"year_start":2010,"year_end":2014,"statefip":1},{"age_group":'(25.0, 34.0]',"year_start":2009,"year_end":2011,"statefip":2},{"age_group":'(25.0, 34.0]',"year_start":2014,"year_end":2019,"statefip":2}])
	wage_change_example = cps.wage_change_across_years(2009,2012,'(25.0, 34.0]',1)
	wage_change_frame_example = cps.frames_wage_change_across_years(example_frames_to_merge,'year_start','year_end','age_group','statefip')
	print(wage_change_frame_example)
	exit()


