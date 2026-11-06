def main():
    import sys,re
    for u in sorted(set(re.findall(r"https?://\S+", open(sys.argv[1]).read()))): print(u)
main()
