# attack-smt
Generating Aggregate Analytics Susceptible to De-anonymization

# Requirements
First we need to install the `glpk-utils` package, which provides the tools for solving linear programming problems:
```bash
apt install glpk-utils
```

Then we need to install the required Python packages:
```bash
pip install -r requirements.txt
```

## Docker Container
Alternatively, you can run the project in a Docker container. The [Dockerfile](Dockerfile) is provided in the root directory of the project. To build the Docker image, run:
```bash
chmod +x Dockerfile
./setup.sh
```

This will build the Docker image and install all the required dependencies. Also, it will run the container in interactive mode, allowing you to run the project inside the container.

# Usage

## Main Tool: Generating Vulnerable Datasets

The main tool (`main.py`) generates datasets with aggregate analytics that are susceptible to de-anonymization attacks.

### Command Syntax
```bash
python main.py --number-of-records NUMBER_OF_RECORDS [OPTIONS]
```

### Required Arguments
- `--number-of-records NUMBER_OF_RECORDS` - Number of records to generate in the table

### Optional Arguments

#### Table Generation Parameters
- `--population-value FLOAT` - Population value for table generation (default: 0.5)
  Controls how many rows each query involves
- `--communality-value FLOAT` - Communality value for table generation (default: 0.25)
  Controls the overlap/relation between queries
- `--titles [TITLES ...]` - List of initial column titles
- `--new-titles [NEW_TITLES ...]` - List of new titles to add to the table
- `--sensitive-column SENSITIVE_COLUMN` - Name of the sensitive column (default: depends on dataset)
- `--seed SEED` - Seed for random number generation (for reproducibility)
- `--number-of-decoys INT` - Number of decoy rows to add to the table (default: 0)

#### Hadamard Construction
- `--hadamard-order INT` - Construct a Hadamard matrix of specified order

#### Column Compression
- `--columns-to-compress [COLUMNS ...]` - List of columns to compress (can be used multiple times)
- `--compressed-title TITLE` - Title for the compressed column (default: "column_compressed")
- `--interval-length LENGTH` - Length of the interval for compression
- `--start-date START_DATE` - Start date for date-based compression (format: YYYY-MM-DD)

#### Logging
- `--level LEVEL` - Set the logging level (DEBUG, INFO, CREATION) (default: INFO)
- `--log-file LOG_FILE` - Path to the log file where logs will be saved

### Basic Examples

#### Example 1: Simple table with 8 records
```bash
python main.py --number-of-records 8
```

#### Example 2: Table with specific population and communality values
Generate a table of size 16 where each query has 10 rows involved and the relation between queries is 6:
```bash
python main.py --number-of-records 16 --level creation --population-value 0.625 --communality-value 0.375
```

#### Example 3: Table with custom parameters
Generate a table of size 10 where each query has 8 rows involved and the relation between queries is 7:
```bash
python main.py --number-of-records 10 --population-value 0.8 --communality-value 0.7
```

#### Example 4: Table with decoy rows
Generate a table with decoy rows to add noise:
```bash
python main.py --number-of-records 20 --number-of-decoys 5 --population-value 0.5 --communality-value 0.25
```

#### Example 5: Reproducible generation with seed
```bash
python main.py --number-of-records 16 --seed 42 --population-value 0.625 --communality-value 0.375
```

# Development
For the development of this project, we created a devcontainer that contains all the necessary tools and libraries to run the project.

>[!IMPORTANT]
> To use the devcontainer, you need to have `docker` installed on your machine. Once you have `docker` installed, you can open the project in Visual Studio Code and it will prompt you to reopen the project in the devcontainer.