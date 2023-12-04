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

class EmailConfig:
    def __init__(self):
        f = open('config.yaml', 'r')
        config = yaml.safe_load(f)
        self.sender_email = config['email']['sender']
        self.smtp_server = config['email']['smtp-server']
        self.port = config['email']['port']
        self.subject=config['email']['subject']
        self.body=config['email']['body']
        self.app_password=config['email']['app-password']

class FetcherConfig:
    def __init__(self):
        f = open('config.yaml', 'r')
        config = yaml.safe_load(f)
        self.email = config['greenhouse']['email']
        self.candidate_file = config['greenhouse']['candidate_file']

