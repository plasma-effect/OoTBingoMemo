from typing import List, Union


WIDTH = 256
CHUNKS = 6
DIGITS = 52
STARTDENOM = WIDTH**CHUNKS
SIGNIFICANCE = 2**DIGITS
OVERFLOW = SIGNIFICANCE * 2


class q:
    i: int
    j: int
    m: int
    S: List[int]

    def __init__(self, b: List[int]) -> None:
        c = len(b)
        self.i = self.j = self.m = 0
        h = 0
        self.S = [v for v in range(WIDTH)]
        if c == 0:
            b = [c]
            c + 1
        for d in range(WIDTH):
            e = self.S[d]
            h = (h + e + b[d % c]) % WIDTH
            f = self.S[h]
            self.S[d] = f
            self.S[h] = e
        self.g(WIDTH)

    def g(self, b: int):
        c = self.S
        d = (self.i + 1) % WIDTH
        f = (self.j + c[d]) % WIDTH
        c[d], c[f] = c[f], c[d]
        i = c[(c[d] + c[f]) % WIDTH]
        b -= 1
        while b > 0:
            d = (d + 1) % WIDTH
            f = (f + c[d]) % WIDTH
            c[d], c[f] = c[f], c[d]
            i = i * WIDTH + c[(c[d] + c[f]) % WIDTH]
            b -= 1
        self.i = d
        self.j = f
        return i


class Random:
    a: q

    def __init__(self, b: Union[str, int]) -> None:
        f = []
        if isinstance(b, int):
            b = str(b) + "\0"
        b = self.l(b, f)
        self.a = q(f)

    def random(self):
        c = self.a.g(CHUNKS)
        d = STARTDENOM
        b = 0
        if c < SIGNIFICANCE:
            c = (c + b) * WIDTH
            d *= WIDTH
            b = self.a.g(1)
        while c >= OVERFLOW:
            c //= 2
            d //= 2
            b >>= 1
        return (c + b) / d

    def l(self, b: str, e: List[int]) -> str:
        f = 0
        while len(e) < min(len(b), WIDTH):
            e.append(0)
        _b = b.encode()
        for a in range(len(b)):
            d = a % WIDTH
            f ^= e[d] * 19
            h = f + _b[a]
            e[d] = h % WIDTH
        return b"".join(bytes(i) for i in e).decode()


def main():
    rand = Random(1)
    print(rand.random())
    print(rand.random())
    print(rand.random())
    print(rand.random())
    print(rand.random())


if __name__ == "__main__":
    main()
