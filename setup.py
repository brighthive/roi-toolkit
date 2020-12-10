import statsmodels.api as sm
import statsmodels.formula.api as smf
from roi.external import BLS_API, fetch_bls_data
from roi import utilities, external, settings, surveys
import pandas as pd
import pickle
import numpy as np


if __name__ == "__main__":

	fetch_bls_data(start_year = 2002, end_year = 2019)
	cps = surveys.CPS_Ops()
	model = cps.fit_mincer_model()
	exit()
