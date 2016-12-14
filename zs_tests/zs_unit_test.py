class ZsUnitTest:
    HR_WIDTH = 60
    MARGIN_LINES = 3

    def __init__(self):
        self._log = []
        self.streaming = True

        self.hr_width = ZsUnitTest.HR_WIDTH
        self.full_width = ZsUnitTest.HR_WIDTH
        self.margin_lines = ZsUnitTest.MARGIN_LINES
        self.print_offset = 0

    def log(self, *args):
        message = args[0]
        if len(message) >= 2:
            if message[0] == "!" and message[1] in " shwurm":
                new_msg = message[3:]
                try:
                    arg = args[1]
                except IndexError:
                    arg = None
                {
                    "r": self.log_hr,
                    " ": self.log_margin,
                    "u": lambda: self.log_underlined_message(new_msg),
                    "h": lambda: self.log_header_message(new_msg),
                    "w": lambda: self.log_header_message(new_msg, arg),
                    "s": lambda: self.log_start_header(arg),
                    "m": lambda: self.log_method_header(arg)
                }[message[1]]()
                return

        message = (" " * self.print_offset) + message
        self._log.append(message)
        if self.streaming:
            print(message)

    def log_method_header(self, method):
        name, cls = method.__name__, method.__self__.__class__.__name__
        msg = "RUNNING METHOD {} IN {}".format(name, cls)

        self.log_header_message(msg)

    def log_start_header(self, cls):
        msg = "BEGINNING UNIT TESTS FOR {} CLASS".format(cls.__name__)

        self.print_offset = 0
        self.log_header_message(msg, w=self.full_width)
        self.print_offset = 1

    def log_header_message(self, message, w=0):
        if not w:
            w = len(message) + 4
            self.hr_width = w

        self.print_offset = 0
        self.log_hr("=")
        self.log("|{:^{}}|".format(message, w - 2))
        self.log_hr("=")
        self.print_offset = 1

    def log_underlined_message(self, message):
        line = "-" * len(message)
        self.log(message)
        self.log(line)

    def log_margin(self, l=0):
        if not l:
            l = ZsUnitTest.MARGIN_LINES

        self.log_hr()
        self.log("\n" * l)

    def log_hr(self, char="-"):
        self.log(char * self.hr_width)

    def log_matrix(self, *matrices, cw=2, co=0, ro=0, fill=" ", desc=None):
        l = len(matrices[0][0])
        offset = " "
        hr = "-"
        offset *= ro + (co * cw) + (co - 1)
        hr *= (l * cw) + (l - 1)
        hr = offset + hr

        self.log(hr)
        for matrix in matrices:
            for row in matrix:
                self.log_row(row, cw, co, ro, fill, desc)
            self.log(hr)

    def log_row(self, row, cw=2, co=0, ro=0, fill=" ", desc=None):
        row_len = len(row)
        s = "{:^" + str(cw) + "}"
        s = [s] * row_len
        s = "|".join(s)
        s = s.format(*row)
        s = ((fill * (cw + 1)) * co) + s
        s = (" " * ro) + s

        if desc:
            s += desc
        self.log(s)


