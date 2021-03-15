myvar = 0

def main(abc: int = globals()["myvar"]):
    print(abc)

if __name__ == "__main__":
    main(2)