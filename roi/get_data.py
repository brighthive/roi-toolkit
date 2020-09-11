import pandas as pd
from roi import settings, macrostats
from datetime import date

def all_mean_wages():
	return(pd.read_csv(settings.File_Locations.mean_wages_location))

def hs_grads_mean_wages():
	return(pd.read_csv(settings.File_Locations.hs_mean_wages_location))

def mincer_params():
	return(pd.read_pickle(settings.File_Locations.mincer_params_location))

def cpi_adjustments():
	base_year = date.today().year - 1
	cpi = macrostats.BLS_API.get_cpi_adjustment_range(base_year - 19, base_year) # need to be connected to the internet to fetch BLS data
	return(cpi)