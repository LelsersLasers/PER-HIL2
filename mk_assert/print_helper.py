import colorama

colorama.just_fix_windows_console()

def print_assert(msg: str, passed: bool) -> None:
    prefix = f"Check: {msg} " if msg else "Check: "
    word = "SUCCESS" if passed else "FAILURE"
    color = colorama.Fore.GREEN if passed else colorama.Fore.RED
    print(f"{prefix}[{color}{word}{colorama.Style.RESET_ALL}]")
