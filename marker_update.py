import colorsys
import random
import time
import numpy as np
from arduino_controller import led_set, led_show, led_clear
import math
import arduino_controller
import keyboard 
# RGB順
marker_bgrs = [np.array([0, 0, 1]), np.array([0, 1, 0]), np.array([1, 0, 0])]


def run_marker_tracking_loop(cameras, marker_id_to_color_id):
    active_marker_offset=0

    arduino_controller.initialize()
    # while not all_markers_are_color_2(cameras):
    #     print("タイミング同期待ち")


    now_sync_flg = False
    sync_start_time = None
    sync_end_time = time.time()
    sync_span_time = None
    signal_start_time = None
    signal_count = 0

    try:
        while True:
            time.sleep(0.00001)
            is_sync = all_markers_are_color_2(cameras)

            # --- sync開始 ---
            if not now_sync_flg and is_sync:
                now_sync_flg = True
                if sync_end_time is not None:
                    sync_span_time = time.time() - sync_end_time  # 前回終了からの周期
                    sync_start_time = time.time()
                    print(f"{sync_span_time=}")

            # --- sync終了 ---
            if now_sync_flg and not is_sync:
                now_sync_flg = False
                sync_end_time = time.time()
                signal_start_time = time.time()
                signal_count = 0

            if keyboard.is_pressed('a'):
                for cam in cameras:
                    for marker in cam.markers:
                        marker.reset_probability_distribution()

            # --- sync周期が確定している場合のみ処理 ---
            if sync_span_time is not None and signal_start_time is not None:
                signal_time = time.time() - signal_start_time

                # signal_count のタイミング判定
                if sync_span_time / 30 * (signal_count) <= signal_time:
                    signal_count += 1
                    print(f"{signal_count=}")
                    # update_leds_sequentially(signal_count-1, marker_id_to_color_id)
                    update_leds_pattern( marker_id_to_color_id,signal_count+1)

                    for cam in cameras:
                        cam.probability_update()





               
                


            # update_leds_sequentially(active_marker_offset,marker_id_to_color_id)
            # time.sleep(0.2)
            # if all_markers_are_color_2(cameras):
            #     while all_markers_are_color_2(cameras):
            #         print("タイミング同期待ち2")
                    
            #     active_marker_offset=0
            #     # time.sleep(0.1)
            #     for cam in cameras:      
            #         for marker in cam.markers:       
            #             marker.reset_probability_distribution()

            # update_leds_pattern( marker_id_to_color_id,active_marker_offset)
            # active_marker_offset+=1
            
            # # update_leds_min_entropy(marker_id_to_color_id,cameras)


            # if all_markers_are_color_2(cameras):
            #     while all_markers_are_color_2(cameras):
            #         print("タイミング同期")
            #     active_marker_offset=0



            # update_leds_pattern( marker_id_to_color_id,active_marker_offset)
            # active_marker_offset+=1
            # time.sleep(0.4)
            # print(active_marker_offset,marker_id_to_color_id)
            # for cam in cameras:            
            #     cam.probability_update()
            # time.sleep(0.1)
            # time.sleep(0.2)

            # print("update")


    finally:
        print("clearing led")
        # led_clear()

def all_markers_are_color_2(cameras):
    if not cameras or not all(cam.markers for cam in cameras):
        return False

    markers = [marker for cam in cameras for marker in cam.markers]
    total = len(markers)
    count_color2 = sum(marker.marker_color_id == 2 for marker in markers)

    return count_color2 >= total / 2



# def update_leds(active_marker_offset):
#     marker_id_to_color={}
#     for i in range(3):
#         h=i/3
#         if(active_marker_offset%2)==0:
#             h+=(1/3)/2
#         r, g, b = colorsys.hsv_to_rgb(h, 1, 1)

#         marker_id=active_marker_offset%10+i*10

#         marker_id_to_color[marker_id]=(int(r*255),int(g*255),int(b*255))

#     for marker_id,rgb in marker_id_to_color.items():
#         # print(f"LED {marker_id} {rgb}")
#         led_set(marker_id,rgb)

#     led_show()


# def update_leds(active_marker_offset, marker_id_to_color):
#     marker_id_to_color.clear()
#     # for i in range(3):
   
#     marker_id=active_marker_offset%30

#     marker_id_to_color[marker_id]=(0,255,0)

#     for marker_id,rgb in marker_id_to_color.items():
#         # print(f"LED {marker_id} {rgb}")
#         led_set(marker_id,rgb)

#     led_show()



# from collections import defaultdict

# led_last_used = {}

def update_leds_randum(active_marker_offset, marker_id_to_color):
    global led_last_used
    marker_id_to_color.clear()

    colors = []
    color_length = 3
    for i in range(color_length):
        h = i / color_length
        r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
        colors.append((int(r * 255), int(g * 255), int(b * 255)))

    # 1. オフセット値ごとにLEDをグループ化
    offset_to_leds = defaultdict(list)
    for led_id, offset in led_last_used.items():
        offset_to_leds[offset].append(led_id)

    # 2. 未使用のLEDと、使用済みのLEDの優先順位リストを作成
    all_leds = set(range(30))
    used_leds = set(led_last_used.keys())
    unused_leds = list(all_leds - used_leds)
    random.shuffle(unused_leds)  # 未使用LEDはランダム

    # 優先順位リストの作成
    candidate_leds = list(unused_leds)

    # offsetが小さい順（古い順）に並べ、同じ古さのLEDはシャッフルして追加
    sorted_offsets = sorted(offset_to_leds.keys())
    for offset in sorted_offsets:
        led_group = offset_to_leds[offset]
        random.shuffle(led_group)
        candidate_leds.extend(led_group)

    # 3. 点灯するLEDを選択
    leds_to_light = candidate_leds[:color_length]

    # 4. 選択したLEDの最終使用時刻を更新
    for led_id in leds_to_light:
        led_last_used[led_id] = active_marker_offset
        # 履歴が溜まりすぎないように、一定数を超えたら古いものから削除
        if len(led_last_used) > 30:
            oldest_led = min(led_last_used, key=led_last_used.get)
            del led_last_used[oldest_led]

    # 5. LEDを点灯
    for i, led_id in enumerate(leds_to_light):
        marker_id_to_color[led_id] = colors[i]

    for marker_id, rgb in marker_id_to_color.items():
        led_set(marker_id, rgb)

    led_show()


# 順番
def update_leds_sequentially(active_marker_offset, marker_id_to_color_id):

    for i in range(30):
        marker_id_to_color_id[i] = 0
    marker_id_to_color_id[active_marker_offset%30] =1

    # for marker_id,rgb in enumerate( marker_id_to_color_id):

    #     led_set(marker_id,tuple( (np.array(marker_bgrs[marker_id_to_color_id[marker_id]])*100).astype(int) ))

    # led_show()

# 最小エントロピーを目指す
def update_leds_min_entropy( marker_id_to_color_id,cameras):

    probability_distribution_sum= np.zeros(30, dtype=float)
    for cam in cameras:
        for m in cam.markers:
            probability_distribution_sum+= m.probability_distribution

    # 値が同じ時にランダムにするために微小な乱数を足す
    noise = np.random.rand(len(probability_distribution_sum)) * 1e-9
    indices_desc = np.argsort(probability_distribution_sum + noise)[::-1]
    # print(indices_
    # desc)
    pattern= [0,1,2]
    # pattern= [0,1,1,2,2,2,2]
    for i,marker_id in enumerate(indices_desc):

        marker_id_to_color_id[marker_id] = pattern[i%len(pattern)]


    


    for marker_id,rgb in enumerate( marker_id_to_color_id):
        # if(marker_id%2!=0):
        #     continue
        led_set(marker_id,tuple( (np.array(marker_bgrs[marker_id_to_color_id[marker_id]])*100).astype(int) ))

    led_show()

# cycle_begin_timer=0

# 固定パターン
def update_leds_pattern( marker_id_to_color_id,active_marker_offset):
 
    for i in range(30):
        marker_id_to_color_id[i] = (i // int(math.pow(2, (active_marker_offset % 5)))) % 2

    # for i in range(30):
    #     marker_id_to_color_id[i] = 0
    # marker_id_to_color_id[active_marker_offset%30] =1

    # for marker_id,rgb in enumerate( marker_id_to_color_id):
    #     led_set(marker_id,tuple( (np.array(marker_bgrs[marker_id_to_color_id[marker_id]])*100).astype(int) ))
    # led_show()