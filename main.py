from src.args import Args
from src.logger import Logger
from src.program import Program


if __name__ == "__main__":
    logger = Logger.get_instance()

    arg_parser = Args()
    args = arg_parser.parse_args()

    number_of_records = args.number_of_records
    population_value = args.population_value
    communality_value = args.communality_value
    titles = args.titles
    new_titles = args.new_titles
    sensitive_column = args.sensitive_column
    seed_value = args.seed
    # Remove duplicates while maintaining order
    columns_to_compress = [list(dict.fromkeys(x)) for x in args.columns_to_compress]
    start_date = args.start_date
    compressed_title = args.compressed_title
    interval_length = args.interval_length
    hadamard_order = args.hadamard_order
    number_of_decoys = args.number_of_decoys

    program = (
        Program(args.level, args.log_file)
        .set_number_of_records(number_of_records)
        .set_population_value(population_value)
        .set_communality_value(communality_value)
        .set_titles(titles)
        .set_new_titles(new_titles)
        .set_sensitive_column(sensitive_column)
        .set_seed_value(seed_value)
        .set_columns_to_compress(columns_to_compress)
        .set_start_date(start_date)
        .set_compressed_title(compressed_title)
        .set_interval_length(interval_length)
        .set_hadamard_order(hadamard_order)
        .set_number_of_decoys(number_of_decoys)
    )

    program.run()
