import redis
import src.utils as utils

class EvaluationCache:
    def __init__(self):
        self._cache = redis.Redis(host='localhost', port=6379, db=0)
    
    def _get_key(self, file_path):
        return f'{file_path}-eval'
    
    def _set(self, file_path, eval):
        self._cache.set(self._get_key(file_path), eval)
        return

    def evaluate_with_cache(self, file_path, fallback):
        content = self._cache.get(self._get_key(file_path))
        if content is None:
            content = fallback(file_path)
            self._set(file_path, content)
        return content

    def clear_all_evaluations(self, resume_folder):
        for file in utils.get_all_files_in(resume_folder):
            self._cache.delete(self._get_key(file))
