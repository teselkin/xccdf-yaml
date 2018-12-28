class GenericParser(object):
    def __init__(self, generator, benchmark, parsed_args=None, output_dir=None,
                 shared_files=None):
        self.generator = generator
        self.benchmark = benchmark
        self.parsed_args = parsed_args
        self.shared_files = shared_files
