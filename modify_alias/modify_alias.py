from subprocess import Popen, PIPE, run, DEVNULL


def get_result_from_output(output: str) -> str:
    return output.split(" ")[2][:-1]


def give_same_result(p, res: str):
    if res == "NoAlias":
        p.stdin.write("0\n")
    elif res == "MustAlias":
        p.stdin.write("1\n")
    elif res == "PartialAlias":
        p.stdin.write("2\n")
    elif res == "MayAlias":
        p.stdin.write("3\n")


# Runs the given compile command mapping AliasResults through substitutions
#
# Returns true if the modification was successful
def compile_with_substitutions(cmd: list[str], substitutions: dict[str, int],
                               output_file_name: str) -> bool:
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
    line = p.stdout.readline().strip()
    while not line.startswith("; ModuleID"):

        if line.startswith("Failed"):
            return False

        curr_result = line.split(" ")[2][:-1]
        p.stdin.write(str(substitutions[curr_result]) + "\n")

        p.stdin.flush()
        line = p.stdout.readline().strip()

    output_file = open(output_file_name, 'w')
    while line != "":
        line = p.stdout.readline()
        output_file.write(line)

    return True


def get_ll_file(compiler_path: str, input_file: str) -> None:
    cmd = compiler_path + " -S -emit-llvm -I/usr/include/csmith-2.3.0 -Xclang -disable-llvm-passes -o csmith/file2.ll " + input_file + " -O1"
    run(cmd.split(" "), stdout=DEVNULL, stderr=DEVNULL, text=True)


# Given a command that runs opt, returns the number of MayAlias queries
#
# Returns -1 if the command or an input fails
def get_count_may_alias_queries(cmd: list[str]) -> int:

    p = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
    line = p.stdout.readline().strip()
    count = 0

    while not line.startswith("; ModuleID"):

        if line.startswith("Failed"):
            return -1

        curr_result = get_result_from_output(line)
        if curr_result == "MayAlias":
            count = count + 1
        give_same_result(p, curr_result)

        p.stdin.flush()
        line = p.stdout.readline().strip()

    return count


# Returns true if the modification was successful
#
# change_to is 0 for NoAlias, 1 for MusAlias, 2 for PartialAlias, 3 for MayAlias
def execute_with_modifications(cmd: list[str], modify_index: int,
                               change_to: int) -> bool:

    p = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
    line = p.stdout.readline().strip()
    index = 0
    while not line.startswith("; ModuleID"):

        if line.startswith("Failed"):
            return False

        curr_result = get_result_from_output(line)
        if curr_result == "MayAlias" and index == modify_index:
            p.stdin.write(str(change_to) + "\n")
        else:
            give_same_result(p, curr_result)

        if curr_result == "MayAlias":
            index = index + 1

        p.stdin.flush()
        line = p.stdout.readline().strip()

    output_file = open("files_sache/file" + str(modify_index) + ".ll", 'w')
    while line != "":
        line = p.stdout.readline()
        output_file.write(line)

    return True


def compile_file(index: int) -> bool:
    cmd = [
        '../llvm-project/build_ast/bin/clang', '-Os',
        "files_sache/file" + str(index) + ".ll", '-o',
        "files_sache/file" + str(index) + ".out"
    ]
    p = run(cmd, stdout=DEVNULL, stderr=DEVNULL, text=True)
    return p.returncode == 0


def measure_outputsize(file: str) -> int:
    cmd = ['llvm-size', file]
    p = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
    if p.stderr != "":
        print(p.stderr)
        return -1
    second_line = p.stdout.split("\n")[1]
    line_list = second_line.split("\t")
    # The other results are more info on where size is: test, data, bss
    return int(line_list[3])
