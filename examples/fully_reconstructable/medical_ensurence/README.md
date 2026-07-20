# Medical Ensurence
This folder contains the datasets generated as part of the experiments using our algorithm to generate vulnerables datasets.
For this specific case, we set the sensible attribute to be `charges`.

## Datasets
- `medical_ensurence_100%.csv`: Dataset for Medical Ensurence with 100% of vulnerables records.

## Vulnerable Queries:
The vulnerable queries used to identify vulnerables records are:
```sql
SELECT AVG(charges) FROM table WHERE region = 'southwest';
SELECT AVG(charges) FROM table WHERE region = 'northeast';
SELECT AVG(charges) FROM table WHERE (age >= 32 AND age < 46);
SELECT AVG(charges) FROM table WHERE (age >= 25 AND age < 32 OR age >= 39 AND age < 46);
SELECT AVG(charges) FROM table WHERE (children >= 2 AND children < 5);
SELECT AVG(charges) FROM table WHERE (children >= 1 AND children < 3 OR children >= 3 AND children < 5);
SELECT AVG(charges) FROM table WHERE (bmi >= 28 AND bmi < 40);
SELECT AVG(charges) FROM table WHERE (bmi >= 22 AND bmi < 28 OR bmi >= 34 AND bmi < 40);
```