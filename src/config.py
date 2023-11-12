import yaml

class EvaluationConfig:
    def __init__(self):
        f = open('config.yaml', 'r')
        config = yaml.safe_load(f)
        self.resume_folder = config['resume-folder']
        self.jd_file = config['jd-file']
        self.role = config['role']
        self.criteria = config['criteria']
        self.model = config['model']

