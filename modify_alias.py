from subprocess import Popen, PIPE, run, DEVNULL


def get_ll_file():
    cmd = "../llvm-project/build_ast/bin/clang -S -emit-llvm -I/usr/include/csmith-2.3.0 -Xclang -disable-llvm-passes -o csmith/file2.ll csmith/file2.c -O1"
    run(cmd.split(" "), stdout=DEVNULL, stderr=DEVNULL, text=True)


def get_count_may_alias_queries(cmd) -> int:

    p = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
    line = p.stdout.readline().strip()
    count = 0

    while not line.startswith("; ModuleID"):

        if line.startswith("Failed"):
            return -1

        curr_result = line.split(" ")[2][:-1]
        if curr_result == "NoAlias":
            p.stdin.write("0\n")
        elif curr_result == "MustAlias":
            p.stdin.write("1\n")
        elif curr_result == "PartialAlias":
            p.stdin.write("2\n")
        elif curr_result == "MayAlias":
            p.stdin.write("3\n")
            count = count + 1
        else:
            print(line)
            print("Unknown result: " + curr_result)
            return -1

        p.stdin.flush()
        line = p.stdout.readline().strip()

    return count


# Returns true if the modification was successful
#
# change_to is 0 for NoAlias, 1 for MusAlias, 2 for PartialAlias, 3 for MayAlias
def execute_with_modifications(cmd: list[str], modify_index: int, change_to: int) -> bool:

    p = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True)
    line = p.stdout.readline().strip()
    index = 0
    while not line.startswith("; ModuleID"):

        if line.startswith("Failed"):
            return False

        curr_result = line.split(" ")[2][:-1]
        if curr_result == "MayAlias" and index == modify_index:
            index = index + 1
            p.stdin.write(str(change_to) + "\n")
        elif curr_result == "NoAlias":
            p.stdin.write("0\n")
        elif curr_result == "MustAlias":
            p.stdin.write("1\n")
        elif curr_result == "PartialAlias":
            p.stdin.write("2\n")
        elif curr_result == "MayAlias":
            p.stdin.write("3\n")
        else:
            print("Unknown result: " + curr_result)
            return False

        p.stdin.flush()
        line = p.stdout.readline().strip()

    output_file = open("files_sache/file" + str(modify_index) + ".ll", 'w')
    while line != "":
        line = p.stdout.readline()
        output_file.write(line)

    return True


def compile_file(index: int) -> bool:
    cmd = ['../llvm-project/build_ast/bin/clang', '-Os', "files_sache/file" + str(index) + ".ll", '-o', "files_sache/file" + str(index) + ".out"]
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


get_ll_file()

cmd = ['../llvm-project//build_interact/bin/opt', '-Os', 'csmith/file2.ll', '-S']

count = get_count_may_alias_queries(cmd)

print("Count is " + str(count))

for i in range(count):
    if not execute_with_modifications(cmd, i, 1):
        print("Modification failed for " + str(i))

print("Done with modifications")

# Compile groundtruth
run(['../llvm-project/build_ast/bin/clang', '-Os', "csmith/file2.ll", '-o', "files_sache/file.out"], stdout=DEVNULL, stderr=DEVNULL, text=True)

for i in range(count):
    if i % 10 == 0:
        print("Compiling " + str(i))
    if not compile_file(i):
        print("Compilation failed for " + str(i))

print("Done with compilation")

# Measure groundtruth
true_size = measure_outputsize("files_sache/file.out")
print("True size is " + str(true_size))

for i in range(count):
    size = measure_outputsize("files_sache/file" + str(i) + ".out")
    if size == -1:
        print("Size measurement failed for " + str(i))
    elif size != true_size:
        print(str(i) + ": " + str(size))
