from pylibcli import default, command, run


@default
def main():
    print("Hello world!")

if __name__ == '__main__':
    run()
