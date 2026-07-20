# Loan approval
This folder contains the datasets generated as part of the experiments using our algorithm to generate vulnerables datasets.
For this specific case, we set the sensible attribute to be `income`.

## Datasets
- `loan_1%.csv`: Dataset for Loan approval with 1% of vulnerables records.
- `loan_5%.csv`: Dataset for Loan approval with 5% of vulnerables records.
- `loan_10%.csv`: Dataset for Loan approval with 10% of vulnerables records.
- `loan_100%.csv`: Dataset for Loan approval with 100% of vulnerables records.

## Vulnerable Queries:
The vulnerable queries used to identify vulnerables records are:
```sql
SELECT AVG(income) FROM table WHERE city = 'New York';
SELECT AVG(income) FROM table WHERE city = 'Miami';
SELECT AVG(income) FROM table WHERE (credit_score >= 460 AND credit_score < 620);
SELECT AVG(income) FROM table WHERE (credit_score >= 380 AND credit_score < 460 OR credit_score >= 540 AND credit_score < 620);
SELECT AVG(income) FROM table WHERE (credit_score >= 340 AND credit_score < 380 OR credit_score >= 420 AND credit_score < 460 OR credit_score >= 500 AND credit_score < 540 OR credit_score >= 580 AND credit_score < 620);
SELECT AVG(income) FROM table WHERE (credit_score >= 320 AND credit_score < 340 OR credit_score >= 360 AND credit_score < 380 OR credit_score >= 400 AND credit_score < 420 OR credit_score >= 440 AND credit_score < 460 OR credit_score >= 480 AND credit_score < 500 OR credit_score >= 520 AND credit_score < 540 OR credit_score >= 560 AND credit_score < 580 OR credit_score >= 600 AND credit_score < 620);
SELECT AVG(income) FROM table WHERE (loan_amount >= 13800 AND loan_amount < 26600);
SELECT AVG(income) FROM table WHERE (loan_amount >= 7400 AND loan_amount < 13800 OR loan_amount >= 20200 AND loan_amount < 26600);
SELECT AVG(income) FROM table WHERE (loan_amount >= 4200 AND loan_amount < 7400 OR loan_amount >= 10600 AND loan_amount < 13800 OR loan_amount >= 17000 AND loan_amount < 20200 OR loan_amount >= 23400 AND loan_amount < 26600);
SELECT AVG(income) FROM table WHERE (loan_amount >= 2600 AND loan_amount < 4200 OR loan_amount >= 5800 AND loan_amount < 7400 OR loan_amount >= 9000 AND loan_amount < 10600 OR loan_amount >= 12200 AND loan_amount < 13800 OR loan_amount >= 15400 AND loan_amount < 17000 OR loan_amount >= 18600 AND loan_amount < 20200 OR loan_amount >= 21800 AND loan_amount < 23400 OR loan_amount >= 25000 AND loan_amount < 26600);
SELECT AVG(income) FROM table WHERE (years_employed >= 12 AND years_employed < 24);
SELECT AVG(income) FROM table WHERE (years_employed >= 6 AND years_employed < 12 OR years_employed >= 18 AND years_employed < 24);
SELECT AVG(income) FROM table WHERE (years_employed >= 3 AND years_employed < 6 OR years_employed >= 9 AND years_employed < 12 OR years_employed >= 15 AND years_employed < 18 OR years_employed >= 21 AND years_employed < 24);
SELECT AVG(income) FROM table WHERE (points >= 34 AND points < 58);
SELECT AVG(income) FROM table WHERE (points >= 22 AND points < 34 OR points >= 46 AND points < 58);
SELECT AVG(income) FROM table WHERE (points >= 16 AND points < 22 OR points >= 28 AND points < 34 OR points >= 40 AND points < 46 OR points >= 52 AND points < 58);
```