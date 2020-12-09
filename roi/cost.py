import numpy as np

class Compound_Interest_Loan:
	"""
	Methods for calculating loan-related values. All methods in this class take either individual scalars or numpy arrays.
	"""
	def amount_to_be_paid_after_n_periods(principal, rate, duration, n_periods_passed): # this includes future interest payments
		"""
		Given a principal, rate, loan term, and number of periods, calculates the amount to be paid by the borrower until the loan comes do.
		Please note that this INCLUDES INTEREST PAYMENTS.

		Note as well that, given simply the current balance of a debt, this method can be used to calculate the amount to be paid for
		the duration of the loan (it doesn't need to be the principal at loan origination).

		The method is period-agnostic. It can take years, months, semesters -- as long as all parameters reflect this unit.

		Parameters:
			principal			:	The amount borrowed, e.g. 
			loan				:	The interest rate, e.g. 5% = 0.05 per period.
			duration			:	The number of periods over which we are calculalating, e.g. 30 periods for a 30 year 
			n_periods_passed 	:	The number of periods since the principal was borrowed.

		Returns:
			balance_remaining 	: The full amount the borrower will pay until the term of the loan is over, INCLUDING INTEREST

		"""
		period_payment = Compound_Interest_Loan.calculate_period_payment(principal, rate, duration)
		amount_paid = n_periods_passed * period_payment
		balance_remaining = (period_payment*duration) - amount_paid
		return(balance_remaining)

	# compounded
	def calculate_period_payment(principal, rate, duration):
		"""
		Given a principal, rate, and duration, calculates the payment per period under the following assumptions:
		1) The borrower will pay an equal amount for each payment
		2) The borrower pays for -duration- periods, and does not owe afterward.

		Parameters:
			principal		:	The amount borrowed, e.g. 
			rate			:	The interest rate, e.g. 5% = 0.05 per period.
			duration		:	The number of periods over which we are calculalating, e.g. 30 periods for a 30 year 

		Returns:
			period_payment 	:	The amount owed by the borrower each period, including interest
		"""
		numerator = principal*rate
		denominator = 1 - (1/(np.power((1+rate), duration)))
		period_payment = numerator/denominator
		return(period_payment)

	def periods_to_pay_off(current_balance, rate, payment_amount):
		"""
		Calculates how long it will take to pay off a loan under the prevailing conditions.

		Parameters:
			current_balance		:	The amount currently owed by the borrower, not including future interest
			rate 				:	The interest rate, e.g. 5% = 0.05 per period.
			payment_amount		:	The amount the borrower intends or is able to pay 

		Returns:
			periods 			:	Number of periods until the loan is fully paid (zero balance)
		"""
		numerator = -1 * np.log(1 - (rate*current_balance/payment_amount))
		denominator = np.log(1 + rate)
		periods = numerator/denominator

		return(periods)
