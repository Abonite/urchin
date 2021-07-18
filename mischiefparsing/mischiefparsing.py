class MischiefParsing():
    mischief_lines = []

    def __init__(self, encoding="UTF-8"):
        """Read Mischief"""

        with open("Mischef", "r", encoding=encoding) as mischief:
            self.mischief_lines = mischief.readlines()
            mischief.close()

    def commands():
        pass
