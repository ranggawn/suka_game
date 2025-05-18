import random
import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import time
import pygame
import numpy as np

pygame.init()
pygame.mixer.init()
sfx_point = pygame.mixer.Sound("Resources/point.wav")
sfx_fail = pygame.mixer.Sound("Resources/fail.wav")
sfx_win = pygame.mixer.Sound("Resources/win.wav")
sfx_lose = pygame.mixer.Sound("Resources/lose.wav")

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

detector = HandDetector(maxHands=1)

playerName = ""
playerNameInput = ""
inputActive = False

# Game states
stateResult = False
startGame = False
scores = [0, 0]
musicStarted = False
showQuestion = False
selectedAnswer = -1
waitingForQuestion = False
triggerQuestionTime = 0
questionTime = 0
question = ""
options = []
correctAnswer = 0

# Popup flags
displayInstructions = True
showNameInput = False
showEndPopup = False
endMessage = ""

# Mouse click handler
def mouseClick(event, x, y, flags, param):
    global displayInstructions, showNameInput, playerName, startGame, showEndPopup, scores, playerNameInput
    if displayInstructions and event == cv2.EVENT_LBUTTONDOWN:
        if 500 <= x <= 780 and 475 <= y <= 535:
            displayInstructions = False
            showNameInput = True

    elif showNameInput and event == cv2.EVENT_LBUTTONDOWN:
        if 500 <= x <= 780 and 400 <= y <= 470 and playerNameInput.strip() != "":
            playerName = playerNameInput.strip()
            showNameInput = False
            startGame = False

    elif showEndPopup and event == cv2.EVENT_LBUTTONDOWN:
        if 500 <= x <= 780 and 400 <= y <= 470:
            scores = [0, 0]
            showEndPopup = False
            displayInstructions = True
            playerNameInput = ""

    elif showQuestion and event == cv2.EVENT_LBUTTONDOWN:
        total_width = 3 * 120 + 2 * 40
        start_x = 640 - total_width // 2
        y_top = 300
        for i in range(3):
            opt_x = start_x + i * (120 + 40)
            if opt_x <= x <= opt_x + 120 and y_top <= y <= y_top + 120:
                global selectedAnswer
                selectedAnswer = i

cv2.namedWindow("BG")
cv2.setMouseCallback("BG", mouseClick)

# Soal matematika
def generateMathQuestion():
    operation = random.choice(["+", "-", "*", "/"])
    if operation == "+":
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        correct = a + b
        question = f"{a} + {b} = ?"
    elif operation == "-":
        a = random.randint(5, 20)
        b = random.randint(1, a)
        correct = a - b
        question = f"{a} - {b} = ?"
    elif operation == "*":
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        correct = a * b
        question = f"{a} x {b} = ?"
    elif operation == "/":
        b = random.randint(1, 10)
        correct = random.randint(1, 10)
        a = b * correct
        question = f"{a} / {b} = ?"

    options = [correct]
    while len(options) < 3:
        wrong = correct + random.choice([-3, -2, -1, 1, 2, 3])
        if wrong != correct and wrong not in options and wrong >= 0:
            options.append(wrong)
    random.shuffle(options)

    return question, options, correct

endTransitionStarted = False
endTransitionTime = 0

while True:
    imgBG = cv2.imread("Resources/BG.png")
    success, img = cap.read()
    imgScaled = cv2.resize(img, (0, 0), None, 0.875, 0.875)
    imgScaled = imgScaled[:, 80:480]
    hands, img = detector.findHands(imgScaled)

    # === Instruction Popup ===
    if displayInstructions:
        instructions = [
            "Selamat datang di Game Suit & Matematika!",
            "- Gunakan tangan untuk suit melawan AI (batu/gunting/kertas)",
            "- Jika kamu kalah, kamu harus jawab soal matematika",
            "- Yang mencapai 5 poin duluan yang akan menang",
            "- Tekan tombol 'S' setiap ingin memulai suit!"
        ]

        padding = 40
        width = max([cv2.getTextSize(t, cv2.FONT_HERSHEY_PLAIN, 2.2, 3)[0][0] for t in instructions]) + 2 * padding
        height = len(instructions) * 50 + 140
        cx, cy = 640, 360
        x1, y1 = cx - width // 2, cy - height // 2
        x2, y2 = cx + width // 2, cy + height // 2

        overlay = imgBG.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (50, 50, 50), -1)
        imgBG = cv2.addWeighted(overlay, 0.85, imgBG, 0.15, 0)

        for i, line in enumerate(instructions):
            cv2.putText(imgBG, line, (x1 + padding, y1 + 60 + i * 50), cv2.FONT_HERSHEY_PLAIN, 2.2, (255, 255, 255), 3)

        cv2.rectangle(imgBG, (cx - 160, y2 - 80), (cx + 160, y2 - 20), (0, 255, 0), -1)
        cv2.putText(imgBG, "SELANJUTNYA", (cx - 130, y2 - 35), cv2.FONT_HERSHEY_PLAIN, 2.5, (0, 0, 0), 3)

    # === Input Nama Popup ===
    elif showNameInput:
        prompt = "Masukkan nama kamu:"
        width = 500
        height = 250  # Tambah tinggi agar ada ruang antar elemen
        cx, cy = 640, 360
        x1, y1 = cx - width // 2, cy - height // 2
        x2, y2 = cx + width // 2, cy + height // 2

        # Latar gelap transparan
        overlay = imgBG.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (50, 50, 50), -1)
        imgBG = cv2.addWeighted(overlay, 0.85, imgBG, 0.15, 0)

        # Teks prompt
        cv2.putText(imgBG, prompt, (x1 + 40, y1 + 70), cv2.FONT_HERSHEY_PLAIN, 2.5, (255, 255, 255), 3)

        # Kotak input
        input_box_top = y1 + 110
        input_box_bottom = input_box_top + 50
        cv2.rectangle(imgBG, (x1 + 40, input_box_top), (x2 - 40, input_box_bottom), (255, 255, 255), -1)

        # Tampilkan teks yang diketik
        cv2.putText(imgBG, playerNameInput, (x1 + 50, input_box_top + 38), cv2.FONT_HERSHEY_PLAIN, 2.5, (0, 0, 0), 2)

        # Tombol START dengan jarak yang nyaman
        start_button_top = input_box_bottom + 30
        start_button_bottom = start_button_top + 50
        cv2.rectangle(imgBG, (cx - 140, start_button_top), (cx + 140, start_button_bottom), (0, 255, 0), -1)
        cv2.putText(imgBG, "MULAI", (cx - 60, start_button_bottom - 10), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 4)


    # === End Game Popup ===
    elif showEndPopup:
        text_size = cv2.getTextSize(endMessage, cv2.FONT_HERSHEY_PLAIN, 4, 4)[0]
        width = text_size[0] + 100
        height = text_size[1] + 160
        cx, cy = 640, 360
        x1, y1 = cx - width // 2, cy - height // 2
        x2, y2 = cx + width // 2, cy + height // 2

        overlay = imgBG.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (50, 50, 50), -1)
        imgBG = cv2.addWeighted(overlay, 0.85, imgBG, 0.15, 0)

        cv2.putText(imgBG, endMessage, (cx - text_size[0] // 2, y1 + 80), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
        cv2.rectangle(imgBG, (cx - 140, y2 - 80), (cx + 140, y2 - 20), (0, 255, 0), -1)
        cv2.putText(imgBG, "Coba Lagi", (cx - 90, y2 - 35), cv2.FONT_HERSHEY_PLAIN, 2.5, (0, 0, 0), 4)

    else:
        if waitingForQuestion and time.time() - triggerQuestionTime > 1.5:
            waitingForQuestion = False
            showQuestion = True
            questionTime = time.time()
            question, options, correctAnswer = generateMathQuestion()
            selectedAnswer = -1

        if startGame and not showQuestion and not waitingForQuestion:
            if not stateResult:
                timer = time.time() - initialTime
                cv2.putText(imgBG, str(int(timer)), (605, 435), cv2.FONT_HERSHEY_PLAIN, 6, (0, 0, 0), 4)

                if timer > 3:
                    stateResult = True
                    timer = 0

                    if hands:
                        playerMove = None
                        hand = hands[0]
                        fingers = detector.fingersUp(hand)

                        if fingers == [0, 0, 0, 0, 0]:
                            playerMove = 1
                        elif fingers == [1, 1, 1, 1, 1]:
                            playerMove = 2
                        elif fingers == [0, 1, 1, 0, 0]:
                            playerMove = 3

                        randomNumber = random.randint(1, 3)
                        imgAI = cv2.imread(f'Resources/{randomNumber}.png', cv2.IMREAD_UNCHANGED)
                        imgBG = cvzone.overlayPNG(imgBG, imgAI, (149, 310))

                        if (playerMove == 1 and randomNumber == 3) or \
                           (playerMove == 2 and randomNumber == 1) or \
                           (playerMove == 3 and randomNumber == 2):
                            scores[1] += 1
                            sfx_point.play()
                        elif (playerMove == 3 and randomNumber == 1) or \
                             (playerMove == 1 and randomNumber == 2) or \
                             (playerMove == 2 and randomNumber == 3):
                            waitingForQuestion = True
                            triggerQuestionTime = time.time()

        if showQuestion:
            imgBG = cv2.imread("Resources/BG-pure.png")
            timeLeft = 10 - int(time.time() - questionTime)
            if timeLeft < 0:
                timeLeft = 0

            cv2.putText(imgBG, f"Time Left: {timeLeft}s", (950, 50), cv2.FONT_HERSHEY_PLAIN, 2.5, (0, 0, 255), 3)

            question_x = 640 - cv2.getTextSize(question, cv2.FONT_HERSHEY_PLAIN, 4, 3)[0][0] // 2
            cv2.putText(imgBG, question, (question_x, 220), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 3)

            total_width = 3 * 120 + 2 * 40
            start_x = 640 - total_width // 2
            y = 300

            for i, opt in enumerate(options):
                x = start_x + i * (120 + 40)
                color = (255, 255, 255)
                if selectedAnswer != -1 or timeLeft == 0:
                    if options[i] == correctAnswer:
                        color = (0, 255, 0)
                    elif i == selectedAnswer:
                        color = (0, 0, 255)

                cv2.rectangle(imgBG, (x, y), (x + 120, y + 120), color, -1)
                text = str(opt)
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_PLAIN, 3, 3)[0]
                text_x = x + (120 - text_size[0]) // 2
                text_y = y + (120 + text_size[1]) // 2
                cv2.putText(imgBG, text, (text_x, text_y), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 3)

            if timeLeft == 0 or selectedAnswer != -1:
                cv2.imshow("BG", imgBG)
                cv2.waitKey(1)
                time.sleep(1.5)
                showQuestion = False
                stateResult = False
                if selectedAnswer == -1 or options[selectedAnswer] != correctAnswer:
                    scores[0] += 1
                    sfx_fail.play()

        if not showQuestion:
            imgBG[234:654, 791:1191] = imgScaled

        if stateResult and not showQuestion:
            imgBG = cvzone.overlayPNG(imgBG, imgAI, (149, 310))

        if not showQuestion:
            cv2.putText(imgBG, str(scores[0]), (410, 215), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
            cv2.putText(imgBG, str(scores[1]), (1112, 215), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
            cv2.putText(imgBG, "AI", (205, 210), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 4)

            gradasi_x = 810
            gradasi_width = 265
            max_len = 13

            if len(playerName) > max_len:
                playerName = playerName[:max_len]

            fontScale = 2.8 if len(playerName) <= 8 else 2.4 if len(playerName) <= 12 else 2.0
            text_size = cv2.getTextSize(playerName, cv2.FONT_HERSHEY_PLAIN, fontScale, 4)[0]
            text_x = (gradasi_x + (gradasi_width - text_size[0]) // 2) - 6
            cv2.putText(imgBG, playerName, (text_x, 210), cv2.FONT_HERSHEY_PLAIN, fontScale, (255, 255, 255), 4)

        if not endTransitionStarted and (scores[0] >= 5 or scores[1] >= 5):
            endTransitionStarted = True
            endTransitionTime = time.time()

        if endTransitionStarted and time.time() - endTransitionTime > 2.5:  # 2.5 detik delay
            if scores[0] >= 5:
                endMessage = "Kamu Kalah!"
                sfx_lose.play()
            else:
                endMessage = "Kamu Menang!"
                sfx_win.play()
            showEndPopup = True
            endTransitionStarted = False  # reset supaya bisa main lagi


    cv2.imshow("BG", imgBG)
    key = cv2.waitKey(1)

    if key == ord("s") and not displayInstructions and not showNameInput and not showEndPopup:
        startGame = True
        initialTime = time.time()
        stateResult = False
        if not musicStarted:
            pygame.mixer.music.load("Resources/background.mp3")
            pygame.mixer.music.play(-1)
            musicStarted = True

    elif key == 27:
        break

    # Nama dari keyboard
    if showNameInput and key != -1:
        if key in [8, 127]:
            playerNameInput = playerNameInput[:-1]
        elif 32 <= key <= 126 and len(playerNameInput) < 15:
            playerNameInput += chr(key)

cap.release()
cv2.destroyAllWindows()
