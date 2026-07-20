# CGPA
This folder contains the datasets generated as part of the experiments using our algorithm to generate vulnerables datasets.
For this specific case, we set the sensible attribute to be `CGPA`.

## Datasets
- `cgpa_100%.csv`: Dataset for CGPA with 100% of vulnerables records.

## Vulnerable Queries:
The vulnerable queries used to identify vulnerables records are:
```sql
SELECT AVG(CGPA) FROM table;
SELECT AVG(CGPA) FROM table WHERE projects_completed = '1';
SELECT AVG(CGPA) FROM table WHERE intership_experience = 'true';
SELECT AVG(CGPA) FROM table WHERE placement = 'true';
SELECT AVG(CGPA) FROM table WHERE (IQ >= 136 AND IQ < 272);
SELECT AVG(CGPA) FROM table WHERE ((IQ >= 68 AND IQ < 136) OR (IQ >= 204 AND IQ < 272));
SELECT AVG(CGPA) FROM table WHERE ((IQ >= 34 AND IQ < 68) OR (IQ >= 102 AND IQ < 136) OR (IQ >= 170 AND IQ < 204) OR (IQ >= 238 AND IQ < 272));
SELECT AVG(CGPA) FROM table WHERE ((IQ >= 17 AND IQ < 34) OR (IQ >= 51 AND IQ < 68) OR (IQ >= 85 AND IQ < 102) OR (IQ >= 119 AND IQ < 136) OR (IQ >= 153 AND IQ < 170) OR (IQ >= 187 AND IQ < 204) OR (IQ >= 221 AND IQ < 238) OR (IQ >= 255 AND IQ < 272));
SELECT AVG(CGPA) FROM table WHERE (prev_sem_result >= 10 AND prev_sem_result < 20);
SELECT AVG(CGPA) FROM table WHERE ((prev_sem_result >= 5 AND prev_sem_result < 10) OR (prev_sem_result >= 15 AND prev_sem_result < 20));
SELECT AVG(CGPA) FROM table WHERE (accademic_performance >= 4 AND accademic_performance < 8);
SELECT AVG(CGPA) FROM table WHERE ((accademic_performance >= 2 AND accademic_performance < 4) OR (accademic_performance >= 6 AND accademic_performance < 8));
SELECT AVG(CGPA) FROM table WHERE ((accademic_performance >= 1 AND accademic_performance < 2) OR (accademic_performance >= 3 AND accademic_performance < 4) OR (accademic_performance >= 5 AND accademic_performance < 6) OR (accademic_performance >= 7 AND accademic_performance < 8));
SELECT AVG(CGPA) FROM table WHERE (communication_skills >= 4 AND communication_skills < 8);
SELECT AVG(CGPA) FROM table WHERE ((communication_skills >= 2 AND communication_skills < 4) OR (communication_skills >= 6 AND communication_skills < 8));
SELECT AVG(CGPA) FROM table WHERE ((communication_skills >= 1 AND communication_skills < 2) OR (communication_skills >= 3 AND communication_skills < 4) OR (communication_skills >= 5 AND communication_skills < 6) OR (communication_skills >= 7 AND communication_skills < 8));
```