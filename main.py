import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import time
import random
import pygame
from tensorflow.keras.models import load_model

# Load model Keras
model = load_model("rock_paper_scissors_model_whithoutmask2.h5")

# Inisialisasi pygame
pygame.init()
sfx_point = pygame.mixer.Sound("Resources/point.wav")
sfx_fail = pygame.mixer.Sound("Resources/fail.wav")

# Webcam setup
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# Detektor tangan
detector = HandDetector(maxHands=1)

# Variabel game
startGame = False
stateResult = False
showQuestion = False
scores = [0, 0]
timer = 0
initialTime = 0
rounds = 0
totalRounds = 3
result = ""
playerMove = ""
aiMove = ""

# Gambar
imgBackground = cv2.imread("Resources/BG.png")
imgAI = None
imgPlayerMove = None

# Input nama pemain
playerName = input("Masukkan nama pemain: ")

def get_prediction(img_hand):
    try:
        # Resize gambar sesuai ukuran input model (224x224)
        img_resized = cv2.resize(img_hand, (224, 224))
        
        # Normalisasi gambar (dibagi 255 untuk mendapatkan nilai 0-1)
        img_array = np.expand_dims(img_resized, axis=0) / 255.0
        
        # Prediksi menggunakan model
        prediction = model.predict(img_array, verbose=0)
        
        # Ambil kelas dengan probabilitas tertinggi
        class_id = np.argmax(prediction)
        
        # Definisi kelas sesuai indeks
        classes = ["rock", "paper", "scissors"]
        
        return classes[class_id]
    except Exception as e:
        print(f"Error dalam prediksi: {e}")
        return None

# Loop utama game
while True:
    # Ambil frame dari webcam
    success, img = cap.read()
    if not success:
        print("Gagal mengambil gambar dari webcam")
        break
        
    # Flip horizontal untuk tampilan mirror
    img = cv2.flip(img, 1)
    
    # Deteksi tangan
    hands, img = detector.findHands(img)
    
    # Overlay webcam ke background
    imgBackground[234:234+480, 310:310+640] = img
    
    # Game logic
    if startGame and not stateResult and not showQuestion:
        if hands:
            hand = hands[0]
            x, y, w, h = hand['bbox']
            
            # Pastikan bbox tidak keluar dari frame
            x = max(0, x)
            y = max(0, y)
            w = min(w, img.shape[1] - x)
            h = min(h, img.shape[0] - y)
            
            # Crop gambar tangan
            cropped_hand = img[y:y+h, x:x+w]
            
            # Pastikan crop tidak kosong
            if cropped_hand.size > 0 and w > 20 and h > 20:
                # Prediksi gerakan
                playerMove = get_prediction(cropped_hand)
                
                if playerMove:
                    # Load gambar sesuai prediksi
                    imgPlayerMove = cv2.imread(f"Resources/{playerMove.capitalize()}.png", cv2.IMREAD_UNCHANGED)
                    
                    # AI membuat gerakan acak
                    aiMove = random.choice(["rock", "paper", "scissors"])
                    imgAI = cv2.imread(f"Resources/{aiMove.capitalize()}.png", cv2.IMREAD_UNCHANGED)
                    
                    # Tentukan pemenang
                    if playerMove == aiMove:
                        result = "Draw"
                    elif (playerMove == "rock" and aiMove == "scissors") or \
                         (playerMove == "paper" and aiMove == "rock") or \
                         (playerMove == "scissors" and aiMove == "paper"):
                        result = "Win"
                        scores[1] += 1
                        sfx_point.play()
                    else:
                        result = "Lose"
                        scores[0] += 1
                        sfx_fail.play()
                    
                    # Set state dan timer
                    stateResult = True
                    initialTime = time.time()
                    rounds += 1
    
    # Tampilkan gerakan AI
    if imgAI is not None:
        imgBackground[120:120+200, 920:920+200] = imgAI
    
    # Tampilkan gerakan Player
    if imgPlayerMove is not None:
        imgBackground[120:120+200, 100:100+200] = imgPlayerMove
    
    # Tampilkan hasil
    if stateResult:
        cv2.putText(imgBackground, result, (480, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 255), 4)
        
        # Reset setelah beberapa detik
        if time.time() - initialTime > 2:
            stateResult = False
            startGame = False
            imgAI = None
            imgPlayerMove = None
            
            # Cek apakah game sudah selesai
            if rounds >= totalRounds:
                showQuestion = True
    
    # Tanya apakah ingin bermain lagi
    if showQuestion:
        msg = f"{playerName}, ingin bermain lagi? (Y/N):"
        cv2.putText(imgBackground, msg, (100, 700), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.imshow("RPS Game", imgBackground)
        key = cv2.waitKey(0)
        if key == ord('y') or key == ord('Y'):
            rounds = 0
            scores = [0, 0]
            showQuestion = False
        else:
            break
    
    # Tampilkan skor
    cv2.putText(imgBackground, f"{playerName}: {scores[1]}", (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
    cv2.putText(imgBackground, f"AI: {scores[0]}", (950, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
    
    # Tampilkan petunjuk
    cv2.putText(imgBackground, "Tekan 'S' untuk mulai", (400, 700), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Tampilkan frame
    cv2.imshow("RPS Game", imgBackground)
    
    # Keyboard input
    key = cv2.waitKey(1)
    if key == ord('s'):
        startGame = True
    elif key == ord('q'):
        break  # keluar dari game jika tekan 'q'

# Release semua resource
cap.release()
cv2.destroyAllWindows()