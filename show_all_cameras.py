import cv2
import threading

def get_available_cameras():
    """
    利用可能なカメラのインデックスをスキャンしてリストを返す。
    """
    available_cameras = []
    index = 0
    while True:
        # カメラを試しに開いてみる
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            # 10個まで試して開けなければ終了
            if index > 200:
                break
            index += 1
            continue
        
        # 開けたらインデックスをリストに追加
        available_cameras.append(index)
        cap.release()
        index += 1
    return available_cameras

def show_camera_feed(camera_index):
    """
    指定されたインデックスのカメラフィードをウィンドウに表示する。
    """
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"エラー: カメラ {camera_index} を開けませんでした。")
        return

    window_name = f"Camera {camera_index}"
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"エラー: カメラ {camera_index} からフレームを読み込めませんでした。")
            break

        cv2.imshow(window_name, frame)

        # 他のウィンドウがアクティブでもキー入力を受け付ける
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyWindow(window_name)

def main():
    """
    システムに接続されているすべてのカメラを検出し、それぞれの映像を
    個別のウィンドウで表示する。
    """
    print("利用可能なカメラをスキャンしています...")
    camera_indices = get_available_cameras()

    if not camera_indices:
        print("利用可能なカメラが見つかりませんでした。")
        return

    print(f"見つかったカメラ: {camera_indices}")
    print("各カメラのウィンドウで 'q' キーを押すと、そのウィンドウが閉じます。")
    
    # 各カメラの表示を別々のスレッドで実行
    # threads = []
    # for index in camera_indices:
    #     thread = threading.Thread(target=show_camera_feed, args=(index,))
    #     threads.append(thread)
    #     thread.start()

    # for thread in threads:
    #     thread.join()
    
    caps = [cv2.VideoCapture(i, cv2.CAP_DSHOW) for i in camera_indices]

    for cap in caps:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # 自動露出を有効にする

    while True:
        frames = []
        for i, cap in enumerate(caps):
            ret, frame = cap.read()
            if ret:
                camera_index = camera_indices[i]
                cv2.imshow(f"Camera {camera_index}", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    for cap in caps:
        cap.release()

    cv2.destroyAllWindows()
    print("すべてのカメラフィードを閉じました。")

if __name__ == '__main__':
    main()
