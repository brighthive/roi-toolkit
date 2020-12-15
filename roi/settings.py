import os

dirname = os.path.dirname(__file__)

class File_Locations:

	local_data_directory = os.path.join(dirname,"data")

	"""
	Available from https://www.neighborhoodatlas.medicine.wisc.edu/
	"""

	adi_location = os.path.join(dirname,"data/adi/US_blockgroup_15.txt")


	"""
	Available from cps.ipums.org
	Current variables:
	LABFORCE
	EMPSTAT
	AGE
	EDUC
	INCWAGE
	STATEFIP
	CPI99
	INCTOT
	(ASECWT is included automatically)

	"""
	cps_toplevel_extract = os.path.join(dirname,"../data/cps/cps_00027.csv")


	"""
	Local files
	"""
	mincer_model_location = os.path.join(dirname,"..data/models/mincer.pickle")
	mincer_params_location = os.path.join(dirname, "data/mincer_params.pickle")
	cpi_adjustments_location = os.path.join(dirname, "data/bls/cpi_adjustment_range.csv")
	mean_wages_location = os.path.join(dirname, "data/mean_wages.csv")
	hs_mean_wages_location = os.path.join(dirname, "data/hs_grads_mean_wages.csv")
	bls_employment_location = os.path.join(dirname, "data/bls/bls_employment_series.csv")
	bls_laborforce_location = os.path.join(dirname, "data/bls/bls_laborforce_series.csv")
	bls_employment_rate_location = os.path.join(dirname, "data/bls/bls_employment_rate_series.csv")
	bls_wage_location = os.path.join(dirname, "data/bls/bls_wage_series.csv")

class Defaults:
	min_group_size = 30

class General:
	CPS_Age_Groups = ['18 and under','19-25','26-34','35-54','55-64','65+']