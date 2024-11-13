import subprocess
import sys

def main():
    try:
        subprocess.run(" ". join(["python rawrand.py ", *sys.argv[1:]]))
    except:
        pass

    subprocess.run("reset.bat", creationflags=subprocess.CREATE_NO_WINDOW)

if __name__ == "__main__":
    main()
