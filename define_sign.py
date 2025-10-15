import itertools
import random
elements = [0, 1, 2]
length = 8



def has_repeated_sign(pattern):

    for i in range(len(pattern)):
        if(pattern[i-1]==pattern[i]):
            return True
    return False

def rotate_tuple(t, n):
    n = n % len(t)
    rotated = t[n:] + t[:n]
    return rotated

def is_rotate_duplication(pattern,confirmed_patterns):

    for i in range(len(pattern)):
        rotated= rotate_tuple(pattern, i)

        # print(f"{pattern=}{i=}{rotated=}")
        if(rotated in confirmed_patterns):
            return True
    return False




def get_pattern():
    global elements ,length
    confirmed_patterns=[]
    for pattern in itertools.product(elements, repeat=length):

        if has_repeated_sign(pattern):
            continue
        if is_rotate_duplication(pattern,confirmed_patterns):
            continue
        # print(pattern)
        confirmed_patterns.append(pattern)
    return confirmed_patterns







# print(str(confirmed_patterns).replace("(","{"))



if __name__ == "__main__":
    confirmed_patterns=get_pattern()
    define_pattern=str(confirmed_patterns)
    define_pattern=define_pattern.replace("(","{")
    define_pattern=define_pattern.replace(")","}")
    define_pattern=define_pattern.replace("[","{")
    define_pattern=define_pattern.replace("]","}")

    print(define_pattern)

    with open("autoPattern_v2\signPattern.h", "w", encoding="utf-8") as f:
        f.write(f"//自動生成なのでここに書かないで\n\n")
        f.write(f"#define LIGHT_PATTERN_LENGTH {len(confirmed_patterns)}\n")
        f.write(f"#define LIGHT_PATTERN_TIME_LENGTH {length}\n")
        f.write("#define LIGHT_PATTERN ")
        f.write(define_pattern)
