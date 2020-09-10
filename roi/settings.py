import os

dirname = os.path.dirname(__file__)

class File_Locations:

	"""
	Available from https://www.neighborhoodatlas.medicine.wisc.edu/
	"""
	adi_location = os.path.join(dirname,"../data/adi-download/US_blockgroup_15.txt")

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
	cps_extract = os.path.join(dirname,"../data/cps/cps_00027.csv")

	mincer_model_location = os.path.join(dirname,"../data/models/mincer.pickle")
	mincer_params_location = os.path.join(dirname, "../data/mincer_params.pickle")

class Defaults:
	min_group_size = 30