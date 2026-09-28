# AI Health Mirror Pro

AI Health Mirror Pro is a BCA final-year project that demonstrates a smart hair and skin analysis system using Flask, OpenCV, TensorFlow-ready structure, SQLite, and a modern responsive UI.

## Project Overview

This project allows users to register, log in, upload or capture images of their hair and skin, process the images, and receive general wellness recommendations. The system uses OpenCV preprocessing and a demo AI engine that clearly identifies itself as a demo analysis model instead of claiming medical diagnosis.

## Features

- User registration and secure login/logout
- SQLite database persistence
- Hair and skin image upload and camera capture
- OpenCV validation and preprocessing
- Demo AI analysis flow with future TensorFlow replacement path
- Personal analysis history
- Dietary, hair-care, skin-care, home-remedy, and routine suggestions
- Dark mode and light mode
- Responsive modern interface

## Technology Stack

- Python
- Flask
- OpenCV
- TensorFlow-ready structure
- SQLite
- HTML5
- CSS3
- JavaScript
- Bootstrap 5
- Pillow
- NumPy

## Installation

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python app.py
```

Then open the browser at:

```text
http://127.0.0.1:5000/
```

## Project Structure

```text
AI_Health_Mirror_Pro/
├── app.py
├── database.db
├── requirements.txt
├── README.md
├── models/
│   ├── __init__.py
│   └── ai_model.py
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── hair_analysis.html
│   ├── skin_analysis.html
│   ├── result.html
│   ├── history.html
│   ├── recommendations.html
│   └── profile.html
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   ├── images/
│   └── uploads/
```

## Usage

1. Create an account or log in.
2. Go to Hair Analysis or Skin Analysis.
3. Upload an image or use live camera capture.
4. Submit the analysis.
5. View AI demo insights and personalized recommendations.
6. Review your history and profile details.

## Future Scope

- Real trained TensorFlow image classification model
- More advanced facial/hair segmentation
- Cloud deployment and analytics
- Wellness tracking and trend monitoring
- Mobile-first enhancements

## Disclaimer

This project is an educational prototype and is not intended to replace medical advice, diagnosis, or treatment. The AI analysis is demo-based and should be treated as a wellness support tool only.
