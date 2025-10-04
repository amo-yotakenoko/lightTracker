

# .envファイルが存在する場合にのみ読み込む
ifneq ($(wildcard .env),)
include .env
endif

PI_USER = pi
PI_HOST = 192.168.11.52
REMOTE_DIR = /home/pi/lightTracker
LOCAL_FILE = light.py
SSH_KEY = ~/.ssh/id_ed25519  # パスフレーズなし鍵推奨

deploy:
	rsync -avz -e "ssh -i $(SSH_KEY)" $(LOCAL_FILE) $(PI_USER)@$(PI_HOST):$(REMOTE_DIR)/
	ssh -t -i $(SSH_KEY) $(PI_USER)@$(PI_HOST) "cd $(REMOTE_DIR)&& sudo .venv/bin/python $(LOCAL_FILE)"


# Arduino
BOARD_FQBN = arduino:avr:uno
SKETCH = lightTracker
AUTOPATTERN_SKETCH = autopattern


.PHONY: upload arduino port autopattern

arduino:
	cmd.exe /C "arduino-cli compile --fqbn $(BOARD_FQBN) --build-path build-lightTracker $(SKETCH)"
	cmd.exe /C "arduino-cli upload -p $(PORT) --fqbn $(BOARD_FQBN) --input-dir build-lightTracker $(SKETCH)"

autopattern:
	@echo "Using port: $(PORT)"
	cmd.exe /C "arduino-cli compile --fqbn $(BOARD_FQBN) --build-path build-autopattern $(AUTOPATTERN_SKETCH)"
	cmd.exe /C "arduino-cli upload -p $(PORT) --fqbn $(BOARD_FQBN) --input-dir build-autopattern $(AUTOPATTERN_SKETCH)"


port:
	 cmd.exe /C "arduino-cli board list"

board:
	cmd.exe /C "python chArUco_board.py"

main:
	 cmd.exe /C "python main.py"


camtest:
	 cmd.exe /C "python show_all_cameras.py"


imgclr:
	rm *.jpg