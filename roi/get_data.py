import pandas as pd
from roi import settings, macrostats, utilities
from datetime import date

def all_mean_wages():
	return(pd.read_csv(settings.File_Locations.mean_wages_location, converters={"state_code":utilities.check_state_code}))

def hs_grads_mean_wages():
	return(pd.read_csv(settings.File_Locations.hs_mean_wages_location, converters={"STATEFIP":utilities.check_state_code}))

def mincer_params():
	return(pd.read_pickle(settings.File_Locations.mincer_params_location))

def cpi_adjustments():
	return(pd.read_csv(settings.File_Locations.cpi_adjustments_location))

def bls_employment_series():
	return(pd.read_csv(settings.File_Locations.bls_employment_location, converters={"state_code":utilities.check_state_code})) # read in states with leading zeroes, per FIPS

def bls_laborforce_series():
	return(pd.read_csv(settings.File_Locations.bls_laborforce_location, converters={"state_code":utilities.check_state_code})) # read in states with leading zeroes, per FIPS

def bls_wage_series():
	return(pd.read_csv(settings.File_Locations.bls_wage_location, converters={"state_code":utilities.check_state_code})) # read in states with leading zeroes, per FIPS