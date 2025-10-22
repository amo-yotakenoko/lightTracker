import itertools
import random
import matplotlib.pyplot as plt
import numpy as np
elements = [0, 1, 2]
length = 5





def has_repeated_sign(pattern):

    for i in range(len(pattern)):
        if(pattern[i-1]==pattern[i]):
            return True
    return False

def rotate_tuple(t, n):
    n = n % len(t)
    rotated = t[n:] + t[:n]
    return rotated

def rotate_match(pattern1, pattern2):
    for i in range(len(pattern1)):
        reliability=0
        rotated1= rotate_tuple(pattern1, i)
        is_match=True
        for j in range(len(pattern1)):
            wildcard=rotated1[j]==-1 or pattern2[j]==-1

            if(not wildcard):
                 reliability+=1

            if (not wildcard and rotated1[j]!=pattern2[j]):
                is_match=False
                break
        if(is_match==True):
            return reliability
    return 0





def rotate_duplicate(pattern,confirmed_patterns):

    for i in range(len(pattern)):
        rotated= rotate_tuple(pattern, i)

        # print(f"{pattern=}{i=}{rotated=}")
        if(rotated in confirmed_patterns):
            return True
    return False




def get_pattern():

    global elements ,length
    confirmed_patterns=[]
    for pattern_tuple in itertools.product(elements, repeat=length):
        pattern=list( pattern_tuple)
        if has_repeated_sign(pattern):
            continue
        if rotate_duplicate(pattern,confirmed_patterns):
            continue
        # print(pattern)
        confirmed_patterns.append(pattern)

    return confirmed_patterns


# print(str(confirmed_patterns).replace("(","{"))
print("get_pattern()")
light_pattern=get_pattern()
print(f"{light_pattern=}")

marker_display_colors=plt.cm.rainbow(np.linspace(0, 1, len(light_pattern))) 


if __name__ == "__main__":
    define_pattern=str(light_pattern)
    define_pattern=define_pattern.replace("(","{")
    define_pattern=define_pattern.replace(")","}")
    define_pattern=define_pattern.replace("[","{")
    define_pattern=define_pattern.replace("]","}")

    print(define_pattern)

    with open("autoPattern_v2\signPattern.h", "w", encoding="utf-8") as f:
        f.write(f"//自動生成なのでここに書かないで\n\n")
        f.write(f"#define LIGHT_PATTERN_LENGTH {len(light_pattern)}\n")
        f.write(f"#define LIGHT_PATTERN_TIME_LENGTH {length}\n")
        f.write("#define LIGHT_PATTERN ")
        f.write(define_pattern)
