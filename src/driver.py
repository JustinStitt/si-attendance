from attendance import Attendance


def main():
    bot = Attendance()
    bot.signIn(cwid="888148632", course="CPSC-375-01")


if __name__ == "__main__":
    main()
