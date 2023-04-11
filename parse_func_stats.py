import argparse


def get_count(file_name: str) -> dict[str, int]:

    f = open(file_name, "r")
    counts: dict[str, int] = {}

    for line in f.readlines():
        func, alias_res = line.split()
        if func in counts:
            counts[func] = counts[func] + 1
        else:
            counts[func] = 0

    return counts


if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument("file", type=str, nargs="?", help="file to count")

    args = arg_parser.parse_args()
    counts = get_count(args.file)

    print(counts)
