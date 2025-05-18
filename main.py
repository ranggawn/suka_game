import streamlit as st
import random
import cv2
import numpy as np
import time
from cvzone.HandTrackingModule import HandDetector
from tensorflow.keras.models import load_model
from PIL import Image
from io import BytesIO

# --- Page config ---
st.set_page_config(page_title="Suit & Math Game", layout="wide")
st.title("🤜👊🤚 Suit & Math Game")

# --- Cache resources ---
@st.cache_resource
def load_resources():
    model = load_model("rock_paper_scissors_model_whithoutmask2.h5")
    detector = HandDetector(maxHands=1)
    imgs = {
        '1': cv2.cvtColor(cv2.imread("Resources/1.png", cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA),
        '2': cv2.cvtColor(cv2.imread("Resources/2.png", cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA),
        '3': cv2.cvtColor(cv2.imread("Resources/3.png", cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
    }
    sounds = {
        'point': open("Resources/point.wav","rb").read(),
        'fail': open("Resources/fail.wav","rb").read(),
        'win': open("Resources/win.wav","rb").read(),
        'lose': open("Resources/lose.wav","rb").read()
    }
    return model, detector, imgs, sounds

model, detector, img_dict, sfx = load_resources()

# --- Session state ---
if 'step' not in st.session_state:
    st.session_state.update({
        'step': 'instructions',
        'player_name': '',
        'scores': {'AI':0, 'Player':0},
        'question': '',
        'options': [],
        'correct': None,
        'selected': None,
        'result': None
    })

# --- Helper functions ---
def generate_question():
    op = random.choice(['+','-','*','/'])
    if op=='+': a,b=random.randint(1,20),random.randint(1,20); ans=a+b
    if op=='-': a,b=random.randint(5,20),random.randint(1,20); ans=a-b
    if op=='*': a,b=random.randint(1,10),random.randint(1,10); ans=a*b
    if op=='/': b=random.randint(1,10); ans=random.randint(1,10); a=b*ans
    q=f"{a} {op} {b} = ?"
    opts=[ans]
    while len(opts)<3:
        w=ans+random.choice([-3,-2,-1,1,2,3])
        if w>=0 and w not in opts: opts.append(w)
    random.shuffle(opts)
    return q, opts, ans

# --- UI Steps ---
if st.session_state.step=='instructions':
    st.markdown("""
    *Selamat datang di Game Suit & Matematika!*
    - Suit (batu/gunting/kertas) melawan AI
    - Kalah = jawab soal matematika
    - Poin 5 lebih dulu menang
    """)
    if st.button('Lanjut'): st.session_state.step='name'

elif st.session_state.step=='name':
    name = st.text_input('Masukkan nama kamu:', '')
    if st.button('MULAI') and name.strip():
        st.session_state.player_name = name.strip()
        st.session_state.step='play'

elif st.session_state.step=='play':
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"{st.session_state.player_name}: {st.session_state.scores['Player']}")
        st.subheader(f"AI: {st.session_state.scores['AI']}")
        if st.button('Suit!'):
            cap = cv2.VideoCapture(0)
            time.sleep(2)
            ret, frame = cap.read(); cap.release()
            if not ret: st.error('Kamera gagal'); st.stop()
            frame = cv2.flip(frame,1)
            hands, _ = detector.findHands(frame, draw=False)
            if hands:
                f=hands[0]['bbox']; x,y,w,h=f
                crop=frame[y:y+h, x:x+w]
                pred=np.argmax(model.predict(np.expand_dims(cv2.resize(crop,(224,224)),0)/255.0))
                player=pred+1; ai=random.randint(1,3)
                col2.image(img_dict[str(ai)], use_column_width=True)
                col2.image(img_dict[str(player)], use_column_width=True)
                if player==ai: st.write('Draw')
                elif (player-ai)%3==1: st.audio(sfx['point']); st.write('Win'); st.session_state.scores['Player']+=1
                else:
                    st.audio(sfx['fail']); st.write('Lose');
                    st.session_state.scores['AI']+=1
                    q,opts,ans = generate_question();
                    st.session_state.update({'question':q,'options':opts,'correct':ans,'step':'question'})
            else: st.warning('Tidak terdeteksi tangan')
    # check end
    if max(st.session_state.scores.values())>=5:
        winner = 'Menang' if st.session_state.scores['Player']>st.session_state.scores['AI'] else 'Kalah'
        st.audio(sfx['win'] if winner=='Menang' else sfx['lose'])
        st.success(f'Game selesai: Kamu {winner}!')
        if st.button('Main Lagi'): st.session_state.update({'scores':{'AI':0,'Player':0},'step':'instructions'})

elif st.session_state.step=='question':
    st.write('*SOAL MATEMATIKA*')
    st.write(st.session_state.question)
    choice = st.radio('Pilih jawaban:', st.session_state.options)
    if st.button('Kirim Jawaban'):
        if choice==st.session_state.correct: st.success('Benar!'); st.session_state.scores['Player']+=1
        else: st.error('Salah!'); st.session_state.scores['AI']+=1
        st.session_state.step='play'
