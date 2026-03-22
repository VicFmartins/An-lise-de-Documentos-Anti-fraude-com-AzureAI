from __future__ import annotations


def only_digits(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def validate_cpf(value: str) -> bool:
    digits = only_digits(value)
    if len(digits) != 11 or len(set(digits)) == 1:
        return False

    for step in (9, 10):
        total = sum(int(digits[index]) * ((step + 1) - index) for index in range(step))
        digit = ((total * 10) % 11) % 10
        if digit != int(digits[step]):
            return False
    return True


def validate_cnpj(value: str) -> bool:
    digits = only_digits(value)
    if len(digits) != 14 or len(set(digits)) == 1:
        return False

    def calc(base: str, weights: list[int]) -> int:
        total = sum(int(digit) * weight for digit, weight in zip(base, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    first = calc(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second = calc(digits[:12] + str(first), [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return digits[-2:] == f"{first}{second}"
