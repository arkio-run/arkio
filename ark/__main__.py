__all__ = ("main",)


def main() -> None:
    from ark.patch import patch_all

    patch_all()

    from ark.bin.ark import main as _main

    _main()


if __name__ == "__main__":
    main()
