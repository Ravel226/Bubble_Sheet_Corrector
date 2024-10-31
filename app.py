import cv2
import numpy as np
import streamlit as st
from PIL import Image

# Configuration Streamlit
st.title("Notes QCM")
st.write("Capture an image or upload an image and grade it")

# Option de sélection
option = st.radio("Choose input method:", ("Upload Image", "Camera"))

# Fonction pour détecter les cercles remplis
def detect_filled_circles(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)

    # Afficher l'image binaire pour le diagnostic
    st.image(thresh, caption="Binarized Image", channels="GRAY")

    # Détecter les contours des disques blancs
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled_circles = []
    for contour in contours:
        (x, y), radius = cv2.minEnclosingCircle(contour)
        if radius > 12.2 and radius < 25:  # Ajuster les valeurs de rayon selon les besoins
            # Vérifier le pourcentage de remplissage du cercle
            mask = np.zeros_like(thresh)
            cv2.circle(mask, (int(x), int(y)), int(radius), 255, -1)
            filled_area = cv2.bitwise_and(thresh, mask)
            filled_pixels = cv2.countNonZero(filled_area)
            total_pixels = np.pi * radius * radius
            fill_percentage = (filled_pixels / total_pixels) * 100

            if fill_percentage > 65:  # Ajuster le seuil de remplissage selon les besoins
                filled_circles.append((int(x), int(y), int(radius)))
    return filled_circles

# Fonction pour comparer les réponses
def compare_responses(student_circles, correct_circles, image, tolerance=30):
    student_answers = set()
    correct_answers = set()
    for circle in student_circles:
        x, y, r = circle
        student_answers.add((x, y))
    for circle in correct_circles:
        x, y, r = circle
        correct_answers.add((x, y))

    correct_count =  0
    for answer in student_answers:
        x, y = answer
        for correct_answer in correct_answers:
            cx, cy = correct_answer
            if abs(x - cx) <= tolerance and abs(y - cy) <= tolerance:
                correct_count += 1
                cv2.circle(image, answer, 10, (0, 255, 0), 2)  # Vert pour les bonnes réponses
                break
        else:
            cv2.circle(image, answer, 10, (0, 0, 255), 2)  # Rouge pour les mauvaises réponses

    return correct_count, len(correct_answers)

if option == "Camera":
    st.write("Take a photo using your device's camera.")
    
    img_file_buffer = st.camera_input("Take a photo")

    if img_file_buffer is not None:
        # Convertir l'image en format PIL
        img = Image.open(img_file_buffer)
        img = np.array(img)
        st.image(img, caption="Captured Image")

        # Détection des cercles remplis
        student_circles = detect_filled_circles(img)
        st.write(f"Nombre de cercles détectés : {len(student_circles)}")


elif option == "Upload Image":
    uploaded_file = st.file_uploader("Choose an image...", type="jpg")
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        img = np.array(img)
        st.image(img, channels="BGR")

        # Détection des cercles remplis
        student_circles = detect_filled_circles(img)
        st.write(f"Detected Circles : {len(student_circles)}")

# Téléchargement de l'image de la feuille de réponses originale
correct_file = st.file_uploader("Upload the correct answers sheet...", type="jpg")
if correct_file is not None:
    correct_img = Image.open(correct_file)
    correct_img = np.array(correct_img)
    st.image(correct_img, channels="BGR")

    # Détection des cercles remplis sur la feuille de réponses originale
    correct_circles = detect_filled_circles(correct_img)
    st.write(f"Detected Circles on the Correction Bubble sheet : {len(correct_circles)}")

    # Comparaison des réponses
    if 'student_circles' in locals():
        correct_count, total_questions = compare_responses(student_circles, correct_circles, captured_image if option == "Camera" else img)
        score = (correct_count / total_questions) * 100
        st.write(f"Student Score: {correct_count}/{total_questions} ({score:.2f}%)")
        st.image(captured_image if option == "Camera" else img, channels="BGR", caption="Results")