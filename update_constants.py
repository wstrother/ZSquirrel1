from os.path import join
CONSTANTS_PATH = "zs_constants"
CONFIG_PATH = "config"


def make_sections(lines):
    sections = []
    current = []

    i = 0
    for line in lines:
        c = line[0]
        if c == "#":
            if i > 0:
                sections.append(current)
                current = []
            i += 1

        current.append(line)

        if lines.index(line) == len(lines) - 1:
            sections.append(current)

    return sections


def make_constants(section, p=False):
    constants = []
    for line in section:
        if line == "\n":
            constants.append(line)

        elif len(line.split()) == 1:
            line = line.strip("\n")
            line += " = \"{}\"\n".format(line.lower())
            constants.append(line)

        elif len(line.split("= ")) == 2:
            lhs, rhs = line.split("= ")[0].strip(), line.split("= ")[1][:-1]

            if "," in rhs:
                rhs = "({})".format(rhs)
                if p:
                    rhs = "join" + rhs
            line = "{} = {}\n".format(lhs, rhs)
            constants.append(line)

    return constants


def make_files(lines):
    sections = make_sections(lines)
    for section in sections:
        header = section[0]
        if header[1] != "#":
            file_name = header[2:].replace(" ", "_").strip("\n").lower()
            file_name += ".py"

            print(file_name)
            file = open(join(CONSTANTS_PATH, file_name), "w")

            p = file_name == "paths.py"
            if p:
                file.write("from os.path import join\n")

            constants = make_constants(section[1:], p)
            for line in constants:
                print(line, end="")
                file.write(line)
            file.close()


def update_constants():
    cfg_path = join(CONFIG_PATH, "zs.constants")
    cfg_file = open(cfg_path, "r")
    cfg = [line for line in cfg_file]
    cfg_file.close()

    make_files(cfg)

if __name__ == "__main__":
    update_constants()
