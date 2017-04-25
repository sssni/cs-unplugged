from .Error import Error


class CouldNotFindConfigFileError(Error):
    '''Raised when a yaml file cannot be found
    '''

    def __init__(self, config_file_path):
        '''
        '''
        super().__init__()
        self.config_file_path = config_file_path

    def __str__(self):
        return self.base_message.format(filename=self.config_file_path) + self.missing_file_suggestions
