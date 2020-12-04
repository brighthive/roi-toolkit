import numpy as np

class Compound_Interest_Loan:
	"""
	This class takes either individual scalars or numpy arrays.
	"""
	def amount_to_be_paid_after_n_periods(principal, rate, duration, n_periods_passed): # this includes future interest payments
		period_payment = Compound_Interest_Loan.calculate_period_payment(principal, rate, duration)
		amount_paid = n_periods_passed * period_payment
		balance_remaining = (period_payment*duration) - amount_paid
		return(balance_remaining)

	# compounded
	def calculate_period_payment(principal, rate, duration):
		numerator = principal*rate
		denominator = 1 - (1/(np.power((1+rate), duration)))
		return(numerator/denominator)

	def periods_to_pay_off(current_balance, rate, payment_amount, final_balance=0):
		numerator = -1 * np.log(1 - (rate*current_balance/payment_amount))
		denominator = np.log(1 + rate)
		return(numerator/denominator)