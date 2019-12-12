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
	(ASECWT is included automatically)

	"""
	cps_extract = os.path.join(dirname,"../data/cps/cps_00024.csv")